#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 AI 에이전트 시스템 - CenterCrawlingBot 통합
비즈니스 로직 기반 멀티 에이전트 크롤링 시스템

주요 기능:
1. 검색 전략 AI 에이전트 (Google->Naver->Bing 순)
2. 데이터 검증 AI 에이전트 (주소-지역번호 매칭, 유사성 검사)
3. 리소스 관리자 (GCP e2-small 최적화)
4. PostgreSQL 직접 연동 (Pydantic 모델 기반)
5. 데이터 품질 등급 시스템 (A~F)
"""

import os
import re
import time
import json
import logging
import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from contextlib import contextmanager
import multiprocessing

# AI 관련
import google.generativeai as genai
from dotenv import load_dotenv

# 데이터베이스 관련
import psycopg2
import psycopg2.extras
from pydantic import BaseModel, Field, validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

# 웹 크롤링 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import requests

# 기존 시스템 모듈
from database.database import ChurchCRMDatabase
from database.models import Organization, CrawlingJob


# ==================== 설정 및 상수 ====================

load_dotenv()

# Gemini API 설정
GEMINI_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# 검색 엔진 우선순위
SEARCH_ENGINES = ['google', 'naver', 'bing']

# 데이터 품질 등급 기준
class DataQualityGrade(Enum):
    A = "A"  # 기관명 + 주소 + 전화번호 + 팩스 + 홈페이지 + 이메일
    B = "B"  # 기관명 + 주소 + 전화번호 + 팩스 + 홈페이지
    C = "C"  # 기관명 + 주소 + 전화번호 + 팩스
    D = "D"  # 기관명 + 주소 + 전화번호 + 홈페이지
    E = "E"  # 기관명 + 주소 + 전화번호
    F = "F"  # 기관명 + 주소

# 리소스 제약 조건
class ResourceConstraints:
    """리소스 제약 조건"""
    
    @staticmethod
    def get_optimal_workers() -> int:
        """최적 워커 수 계산"""
        try:
            # 시스템 메모리 확인
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            # GCP e2-small 감지 (2GB RAM, 0.5 vCPU)
            if memory_gb <= 2.5:
                return 1  # GCP e2-small은 단일 워커
            elif memory_gb <= 4:
                return 2  # e2-medium
            elif memory_gb <= 16:
                return min(4, cpu_count)  # 로컬 환경
            else:
                return min(8, cpu_count)  # 고성능 환경
                
        except:
            return 2  # 기본값


# ==================== Pydantic 모델 ====================

class CrawlingResult(BaseModel):
    """크롤링 결과 모델"""
    organization_id: Optional[int] = None
    name: str
    address: str
    phone: str = ""
    fax: str = ""
    homepage: str = ""
    email: str = ""
    mobile: str = ""
    
    # 메타데이터
    data_quality_grade: str = "F"
    crawling_source: str = ""
    validation_score: float = 0.0
    ai_confidence: float = 0.0
    crawled_at: datetime = Field(default_factory=datetime.now)
    
    # 검증 플래그
    phone_validated: bool = False
    fax_validated: bool = False
    address_validated: bool = False
    homepage_validated: bool = False
    email_validated: bool = False

    @validator('phone', 'fax', 'mobile')
    def validate_phone_format(cls, v):
        if not v:
            return v
        # 한국 전화번호 형식 검증
        phone_pattern = r'^(\d{2,3})-(\d{3,4})-(\d{4})$'
        if not re.match(phone_pattern, v):
            raise ValueError('전화번호 형식이 올바르지 않습니다')
        return v
    
    @validator('email')
    def validate_email_format(cls, v):
        if not v:
            return v
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('이메일 형식이 올바르지 않습니다')
        return v
    
    def calculate_quality_grade(self) -> str:
        """데이터 품질 등급 계산"""
        fields = [
            bool(self.name and self.address),  # 필수
            bool(self.phone),
            bool(self.fax),
            bool(self.homepage),
            bool(self.email),
            bool(self.mobile)
        ]
        
        if all(fields):
            return DataQualityGrade.A.value
        elif fields[0] and fields[1] and fields[2] and fields[3]:
            return DataQualityGrade.B.value
        elif fields[0] and fields[1] and fields[2]:
            return DataQualityGrade.C.value
        elif fields[0] and fields[1] and fields[3]:
            return DataQualityGrade.D.value
        elif fields[0] and fields[1]:
            return DataQualityGrade.E.value
        else:
            return DataQualityGrade.F.value


# ==================== AI 에이전트 기본 클래스 ====================

class BaseAgent:
    """AI 에이전트 기본 클래스"""
    
    def __init__(self, name: str, gemini_model=None):
        self.name = name
        self.logger = logging.getLogger(f"Agent.{name}")
        self.gemini_model = gemini_model
        self.metrics = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0
        }
    
    def _call_gemini(self, prompt: str, max_retries: int = 3) -> str:
        """Gemini API 호출 (재시도 로직 포함)"""
        for attempt in range(max_retries):
            try:
                self.metrics['requests_made'] += 1
                start_time = time.time()
                
                response = self.gemini_model.generate_content(prompt)
                result = response.text
                
                processing_time = time.time() - start_time
                self.metrics['total_processing_time'] += processing_time
                self.metrics['successful_requests'] += 1
                
                return result
                
            except Exception as e:
                self.metrics['failed_requests'] += 1
                if attempt == max_retries - 1:
                    self.logger.error(f"Gemini API 호출 실패 (최종): {e}")
                    return f"오류: {str(e)}"
                else:
                    self.logger.warning(f"Gemini API 호출 실패 (재시도 {attempt + 1}): {e}")
                    time.sleep(2 ** attempt)  # 지수 백오프
        
        return "오류: 최대 재시도 횟수 초과"


# ==================== 검색 전략 AI 에이전트 ====================

class SearchStrategyAgent(BaseAgent):
    """검색 전략 AI 에이전트"""
    
    def __init__(self, gemini_model=None):
        super().__init__("SearchStrategy", gemini_model)
        self.search_patterns = {
            'phone': [
                r'전화[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
                r'TEL[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
                r'T[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            ],
            'fax': [
                r'팩스[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
                r'fax[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
                r'F[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
                r'전송[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            'homepage': [
                r'https?://[^\s<>"\']+',
                r'www\.[^\s<>"\']+',
                r'[a-zA-Z0-9.-]+\.(com|co\.kr|or\.kr|go\.kr|net|org)[^\s<>"\']*'
            ]
        }
    
    def generate_search_queries(self, name: str, address: str, phone: str = "") -> List[Dict[str, str]]:
        """검색 쿼리 생성 전략"""
        queries = []
        
        # 지역 추출
        region = self._extract_region_from_address(address)
        
        # 비즈니스 로직에 따른 검색 쿼리 생성
        if name and address:
            # (1) 기관명 + 전화번호
            if phone:
                queries.append({
                    'query': f"{name} 전화번호",
                    'type': 'phone',
                    'priority': 1,
                    'validation_context': {'address': address, 'phone': phone}
                })
            
            # (2) 기관명 + 팩스번호
            queries.append({
                'query': f"{name} 팩스번호",
                'type': 'fax',
                'priority': 2,
                'validation_context': {'address': address, 'phone': phone}
            })
            
            # (3) 지역 + 기관명 + 전화번호 (검증 실패 시)
            if region:
                queries.append({
                    'query': f"{region} {name} 전화번호",
                    'type': 'phone',
                    'priority': 3,
                    'validation_context': {'address': address, 'region': region}
                })
            
            # (4) 기관명 + 홈페이지
            queries.append({
                'query': f"{name} 홈페이지",
                'type': 'homepage',
                'priority': 4,
                'validation_context': {'address': address}
            })
            
            # (5) 기관명 + 이메일
            queries.append({
                'query': f"{name} 이메일",
                'type': 'email',
                'priority': 5,
                'validation_context': {'address': address}
            })
        
        return sorted(queries, key=lambda x: x['priority'])
    
    def _extract_region_from_address(self, address: str) -> str:
        """주소에서 지역 추출"""
        regions = [
            '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
            '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'
        ]
        
        for region in regions:
            if region in address:
                return region
        
        return ""
    
    def analyze_search_results_with_ai(self, query: str, search_results: str, context: Dict) -> Dict[str, Any]:
        """AI를 통한 검색 결과 분석"""
        prompt = f"""
다음 검색 결과에서 '{query}'와 관련된 정보를 추출해주세요.

**검색 쿼리**: {query}
**검색 결과**:
{search_results[:3000]}

**검증 컨텍스트**:
{json.dumps(context, ensure_ascii=False, indent=2)}

**요청사항**:
1. 검색 결과에서 관련 정보 추출
2. 컨텍스트와의 일치성 검증
3. 신뢰도 점수 (0-1) 제공

**응답 형식** (JSON):
{{
    "extracted_info": "추출된 정보",
    "confidence_score": 0.0,
    "validation_passed": false,
    "validation_reason": "검증 결과 설명"
}}
"""
        
        try:
            response = self._call_gemini(prompt)
            # JSON 파싱 시도
            import json
            result = json.loads(response)
            return result
        except:
            return {
                "extracted_info": "",
                "confidence_score": 0.0,
                "validation_passed": False,
                "validation_reason": "AI 분석 실패"
            }


# ==================== 데이터 검증 AI 에이전트 ====================

class ValidationAgent(BaseAgent):
    """데이터 검증 AI 에이전트"""
    
    def __init__(self, gemini_model=None):
        super().__init__("Validation", gemini_model)
        self.region_area_codes = {
            '서울': ['02'],
            '부산': ['051'],
            '대구': ['053'],
            '인천': ['032'],
            '광주': ['062'],
            '대전': ['042'],
            '울산': ['052'],
            '세종': ['044'],
            '경기': ['031'],
            '강원': ['033'],
            '충북': ['043'],
            '충남': ['041'],
            '전북': ['063'],
            '전남': ['061'],
            '경북': ['054'],
            '경남': ['055'],
            '제주': ['064']
        }
    
    def validate_phone_with_address(self, phone: str, address: str) -> Dict[str, Any]:
        """전화번호와 주소 일치성 검증"""
        try:
            # 지역 추출
            region = self._extract_region_from_address(address)
            if not region:
                return {
                    'valid': False,
                    'reason': '주소에서 지역을 추출할 수 없음',
                    'confidence': 0.0
                }
            
            # 지역번호 추출
            area_code = phone.split('-')[0] if '-' in phone else phone[:3]
            
            # 지역번호 매칭
            expected_codes = self.region_area_codes.get(region, [])
            if area_code in expected_codes:
                return {
                    'valid': True,
                    'reason': f'{region} 지역의 올바른 지역번호 ({area_code})',
                    'confidence': 0.9
                }
            else:
                return {
                    'valid': False,
                    'reason': f'{region} 지역의 지역번호 불일치 (예상: {expected_codes}, 실제: {area_code})',
                    'confidence': 0.1
                }
                
        except Exception as e:
            return {
                'valid': False,
                'reason': f'검증 중 오류: {str(e)}',
                'confidence': 0.0
            }
    
    def check_phone_similarity(self, phone1: str, phone2: str) -> Dict[str, Any]:
        """전화번호 유사성 검사"""
        try:
            if not phone1 or not phone2:
                return {'similar': False, 'similarity_score': 0.0}
            
            # 숫자만 추출
            digits1 = re.sub(r'[^\d]', '', phone1)
            digits2 = re.sub(r'[^\d]', '', phone2)
            
            if len(digits1) != len(digits2):
                return {'similar': False, 'similarity_score': 0.0}
            
            # 자리수별 일치 확인
            matches = sum(1 for d1, d2 in zip(digits1, digits2) if d1 == d2)
            similarity_score = matches / len(digits1)
            
            # 80% 이상 유사하면 유사한 것으로 판단
            is_similar = similarity_score >= 0.8
            
            return {
                'similar': is_similar,
                'similarity_score': similarity_score,
                'different_digits': len(digits1) - matches
            }
            
        except Exception as e:
            return {'similar': False, 'similarity_score': 0.0}
    
    def validate_with_ai(self, result: CrawlingResult) -> Dict[str, Any]:
        """AI를 통한 종합 검증"""
        prompt = f"""
다음 크롤링 결과의 데이터 품질을 검증해주세요.

**기관 정보**:
- 기관명: {result.name}
- 주소: {result.address}
- 전화번호: {result.phone}
- 팩스번호: {result.fax}
- 홈페이지: {result.homepage}
- 이메일: {result.email}

**검증 항목**:
1. 전화번호와 주소의 지역 일치성
2. 팩스번호와 전화번호의 유사성 (1-4자리 차이 허용)
3. 이메일 형식 유효성
4. 홈페이지 URL 유효성
5. 전체적인 데이터 일관성

**응답 형식** (JSON):
{{
    "overall_valid": true,
    "validation_score": 0.85,
    "issues": [],
    "recommendations": []
}}
"""
        
        try:
            response = self._call_gemini(prompt)
            import json
            return json.loads(response)
        except:
            return {
                "overall_valid": False,
                "validation_score": 0.0,
                "issues": ["AI 검증 실패"],
                "recommendations": []
            }
    
    def _extract_region_from_address(self, address: str) -> str:
        """주소에서 지역 추출"""
        for region in self.region_area_codes.keys():
            if region in address:
                return region
        return ""


# ==================== 리소스 관리자 ====================

class ResourceManager:
    """리소스 관리자 - GCP e2-small 최적화"""
    
    def __init__(self):
        self.logger = logging.getLogger("ResourceManager")
        self.max_workers = ResourceConstraints.get_optimal_workers()
        self.current_workers = 0
        self.memory_threshold = 0.8  # 80% 메모리 사용률 제한
        self.cpu_threshold = 0.7     # 70% CPU 사용률 제한
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Gemini API 제한 관리
        self.gemini_rpm_limit = 2000  # Gemini 1.5 Flash RPM
        self.gemini_requests_per_minute = 0
        self.gemini_minute_start = time.time()
        
        self.logger.info(f"🔧 리소스 관리자 초기화: 최대 워커 {self.max_workers}개")
    
    def can_create_worker(self) -> bool:
        """워커 생성 가능 여부 확인"""
        if self.current_workers >= self.max_workers:
            return False
        
        # 메모리 사용률 확인
        memory_percent = psutil.virtual_memory().percent / 100
        if memory_percent > self.memory_threshold:
            self.logger.warning(f"⚠️ 메모리 사용률 높음: {memory_percent:.1%}")
            return False
        
        # CPU 사용률 확인
        cpu_percent = psutil.cpu_percent(interval=1) / 100
        if cpu_percent > self.cpu_threshold:
            self.logger.warning(f"⚠️ CPU 사용률 높음: {cpu_percent:.1%}")
            return False
        
        return True
    
    def can_call_gemini(self) -> bool:
        """Gemini API 호출 가능 여부 확인"""
        current_time = time.time()
        
        # 1분 경과 시 카운터 리셋
        if current_time - self.gemini_minute_start > 60:
            self.gemini_requests_per_minute = 0
            self.gemini_minute_start = current_time
        
        # RPM 제한 확인
        if self.gemini_requests_per_minute >= self.gemini_rpm_limit:
            self.logger.warning(f"⚠️ Gemini API RPM 제한 도달: {self.gemini_requests_per_minute}")
            return False
        
        return True
    
    def record_gemini_request(self):
        """Gemini API 요청 기록"""
        self.gemini_requests_per_minute += 1
    
    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'current_workers': self.current_workers,
            'max_workers': self.max_workers,
            'gemini_requests_per_minute': self.gemini_requests_per_minute
        }
    
    def start_monitoring(self):
        """시스템 모니터링 시작"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("📊 시스템 모니터링 시작")
    
    def _monitor_system(self):
        """시스템 모니터링 (백그라운드)"""
        while self.monitoring_active:
            try:
                stats = self.get_system_stats()
                
                # 경고 레벨 체크
                if stats['memory_percent'] > 85:
                    self.logger.warning(f"🚨 메모리 사용률 높음: {stats['memory_percent']:.1f}%")
                
                if stats['cpu_percent'] > 80:
                    self.logger.warning(f"🚨 CPU 사용률 높음: {stats['cpu_percent']:.1f}%")
                
                # 30초마다 체크
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ 시스템 모니터링 오류: {e}")
                break
    
    def stop_monitoring(self):
        """시스템 모니터링 중지"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)


# ==================== 메인 AI 에이전트 시스템 ====================

class EnhancedAIAgentSystem:
    """고도화된 AI 에이전트 시스템"""
    
    def __init__(self, db_url: str = None):
        self.logger = logging.getLogger("EnhancedAIAgentSystem")
        
        # 데이터베이스 연결
        self.db = ChurchCRMDatabase(db_url)
        
        # Gemini AI 모델 초기화
        self.gemini_model = self._initialize_gemini()
        
        # 에이전트 초기화
        self.search_agent = SearchStrategyAgent(self.gemini_model)
        self.validation_agent = ValidationAgent(self.gemini_model)
        
        # 리소스 관리자
        self.resource_manager = ResourceManager()
        self.resource_manager.start_monitoring()
        
        # 크롤링 상태
        self.current_job_id = None
        self.is_running = False
        
        self.logger.info("🚀 고도화된 AI 에이전트 시스템 초기화 완료")
    
    def _initialize_gemini(self):
        """Gemini AI 모델 초기화"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config=GEMINI_CONFIG
            )
            
            self.logger.info("🤖 Gemini AI 모델 초기화 성공")
            return model
            
        except Exception as e:
            self.logger.error(f"❌ Gemini AI 모델 초기화 실패: {e}")
            raise
    
    def start_crawling_job(self, job_name: str, started_by: str) -> int:
        """크롤링 작업 시작"""
        try:
            # 크롤링 작업 생성
            job_data = {
                'job_name': job_name,
                'status': 'RUNNING',
                'started_by': started_by,
                'started_at': datetime.now(),
                'config_data': {
                    'search_engines': SEARCH_ENGINES,
                    'max_workers': self.resource_manager.max_workers,
                    'gemini_model': 'gemini-1.5-flash'
                }
            }
            
            # 데이터베이스에 작업 저장
            query = """
                INSERT INTO crawling_jobs (job_name, status, started_by, started_at, config_data)
                VALUES (%(job_name)s, %(status)s, %(started_by)s, %(started_at)s, %(config_data)s)
                RETURNING id
            """
            
            result = self.db.execute_insert(query, job_data)
            self.current_job_id = result['id']
            self.is_running = True
            
            self.logger.info(f"📋 크롤링 작업 시작: {job_name} (ID: {self.current_job_id})")
            return self.current_job_id
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 작업 시작 실패: {e}")
            raise
    
    def process_organization_batch(self, organizations: List[Dict]) -> List[CrawlingResult]:
        """기관 배치 처리"""
        results = []
        
        for org_data in organizations:
            try:
                result = self.process_single_organization(org_data)
                if result:
                    results.append(result)
                    
                    # 데이터베이스에 저장
                    self.save_crawling_result(result)
                    
            except Exception as e:
                self.logger.error(f"❌ 기관 처리 실패: {org_data.get('name', 'Unknown')} - {e}")
                continue
        
        return results
    
    def process_single_organization(self, org_data: Dict) -> Optional[CrawlingResult]:
        """단일 기관 처리"""
        try:
            name = org_data.get('name', '')
            address = org_data.get('address', '')
            existing_phone = org_data.get('phone', '')
            
            if not name or not address:
                self.logger.warning(f"⚠️ 필수 정보 누락: {name}")
                return None
            
            self.logger.info(f"🔍 기관 처리 시작: {name}")
            
            # 검색 쿼리 생성
            search_queries = self.search_agent.generate_search_queries(
                name, address, existing_phone
            )
            
            # 크롤링 결과 초기화
            result = CrawlingResult(
                organization_id=org_data.get('id'),
                name=name,
                address=address,
                phone=existing_phone
            )
            
            # 각 검색 쿼리 실행
            for query_info in search_queries:
                if not self.resource_manager.can_call_gemini():
                    self.logger.warning("⚠️ Gemini API 제한으로 인한 대기")
                    time.sleep(60)  # 1분 대기
                
                # 검색 실행
                search_result = self._execute_search(query_info)
                
                if search_result and search_result.get('extracted_info'):
                    # 결과 검증
                    validation_result = self._validate_search_result(
                        search_result, query_info, result
                    )
                    
                    if validation_result['valid']:
                        self._update_result_with_search_data(
                            result, query_info['type'], search_result['extracted_info']
                        )
            
            # 최종 검증 및 품질 등급 계산
            final_validation = self.validation_agent.validate_with_ai(result)
            result.validation_score = final_validation.get('validation_score', 0.0)
            result.data_quality_grade = result.calculate_quality_grade()
            
            self.logger.info(f"✅ 기관 처리 완료: {name} (등급: {result.data_quality_grade})")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 기관 처리 오류: {org_data.get('name', 'Unknown')} - {e}")
            return None
    
    def _execute_search(self, query_info: Dict) -> Dict[str, Any]:
        """검색 실행"""
        # 실제 검색 로직은 기존 centercrawling.py의 검색 메서드를 활용
        # 여기서는 AI 분석 부분만 구현
        
        # 검색 결과 시뮬레이션 (실제로는 Selenium 크롤링 결과)
        search_results = "검색 결과 텍스트..."
        
        # AI 분석
        analysis_result = self.search_agent.analyze_search_results_with_ai(
            query_info['query'], search_results, query_info['validation_context']
        )
        
        return analysis_result
    
    def _validate_search_result(self, search_result: Dict, query_info: Dict, current_result: CrawlingResult) -> Dict[str, Any]:
        """검색 결과 검증"""
        extracted_info = search_result.get('extracted_info', '')
        query_type = query_info['type']
        
        if query_type == 'phone':
            return self.validation_agent.validate_phone_with_address(
                extracted_info, current_result.address
            )
        elif query_type == 'fax':
            similarity_check = self.validation_agent.check_phone_similarity(
                extracted_info, current_result.phone
            )
            return {
                'valid': similarity_check['different_digits'] <= 4,
                'reason': f"전화번호와 {similarity_check['different_digits']}자리 차이",
                'confidence': 1.0 - (similarity_check['different_digits'] / 10)
            }
        else:
            return {'valid': True, 'reason': '기본 검증 통과', 'confidence': 0.7}
    
    def _update_result_with_search_data(self, result: CrawlingResult, data_type: str, data: str):
        """검색 결과로 CrawlingResult 업데이트"""
        if data_type == 'phone':
            result.phone = data
            result.phone_validated = True
        elif data_type == 'fax':
            result.fax = data
            result.fax_validated = True
        elif data_type == 'homepage':
            result.homepage = data
            result.homepage_validated = True
        elif data_type == 'email':
            result.email = data
            result.email_validated = True
    
    def save_crawling_result(self, result: CrawlingResult):
        """크롤링 결과 데이터베이스 저장"""
        try:
            # Organization 테이블 업데이트
            query = """
                UPDATE organizations 
                SET phone = %(phone)s, fax = %(fax)s, homepage = %(homepage)s, 
                    email = %(email)s, mobile = %(mobile)s, 
                    ai_crawled = true, last_crawled_at = %(crawled_at)s,
                    crawling_data = %(crawling_data)s
                WHERE id = %(organization_id)s
            """
            
            crawling_data = {
                'data_quality_grade': result.data_quality_grade,
                'validation_score': result.validation_score,
                'ai_confidence': result.ai_confidence,
                'crawling_source': result.crawling_source,
                'validation_flags': {
                    'phone_validated': result.phone_validated,
                    'fax_validated': result.fax_validated,
                    'homepage_validated': result.homepage_validated,
                    'email_validated': result.email_validated
                }
            }
            
            params = {
                'phone': result.phone,
                'fax': result.fax,
                'homepage': result.homepage,
                'email': result.email,
                'mobile': result.mobile,
                'crawled_at': result.crawled_at,
                'crawling_data': json.dumps(crawling_data),
                'organization_id': result.organization_id
            }
            
            self.db.execute_update(query, params)
            self.logger.info(f"💾 크롤링 결과 저장 완료: {result.name}")
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 결과 저장 실패: {result.name} - {e}")
    
    def get_crawling_statistics(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_organizations,
                    COUNT(CASE WHEN ai_crawled = true THEN 1 END) as ai_crawled_count,
                    COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as phone_count,
                    COUNT(CASE WHEN fax IS NOT NULL AND fax != '' THEN 1 END) as fax_count,
                    COUNT(CASE WHEN homepage IS NOT NULL AND homepage != '' THEN 1 END) as homepage_count,
                    COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as email_count
                FROM organizations
            """
            
            result = self.db.execute_query(query, fetch_all=False)
            
            # 품질 등급별 통계
            quality_query = """
                SELECT 
                    crawling_data->>'data_quality_grade' as grade,
                    COUNT(*) as count
                FROM organizations 
                WHERE ai_crawled = true AND crawling_data IS NOT NULL
                GROUP BY crawling_data->>'data_quality_grade'
            """
            
            quality_stats = self.db.execute_query(quality_query)
            
            return {
                'total_organizations': result['total_organizations'],
                'ai_crawled_count': result['ai_crawled_count'],
                'contact_info': {
                    'phone': result['phone_count'],
                    'fax': result['fax_count'],
                    'homepage': result['homepage_count'],
                    'email': result['email_count']
                },
                'quality_grades': {stat['grade']: stat['count'] for stat in quality_stats if stat['grade']},
                'system_stats': self.resource_manager.get_system_stats()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 통계 조회 실패: {e}")
            return {}
    
    def stop_crawling(self):
        """크롤링 중지"""
        self.is_running = False
        self.resource_manager.stop_monitoring()
        
        if self.current_job_id:
            try:
                query = """
                    UPDATE crawling_jobs 
                    SET status = 'STOPPED', completed_at = %s 
                    WHERE id = %s
                """
                self.db.execute_update(query, (datetime.now(), self.current_job_id))
                self.logger.info(f"⏹️ 크롤링 작업 중지: {self.current_job_id}")
            except Exception as e:
                self.logger.error(f"❌ 크롤링 작업 중지 실패: {e}")
    
    def __del__(self):
        """소멸자"""
        try:
            self.stop_crawling()
        except:
            pass


# ==================== 사용 예제 ====================

def main():
    """메인 함수"""
    try:
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # AI 에이전트 시스템 초기화
        agent_system = EnhancedAIAgentSystem()
        
        # 크롤링 작업 시작
        job_id = agent_system.start_crawling_job("AI 에이전트 크롤링 테스트", "admin")
        
        # 테스트 데이터
        test_organizations = [
            {
                'id': 1,
                'name': '서울중앙교회',
                'address': '서울시 중구 명동',
                'phone': '02-1234-5678'
            },
            {
                'id': 2,
                'name': '부산해운대교회',
                'address': '부산시 해운대구',
                'phone': ''
            }
        ]
        
        # 배치 처리
        results = agent_system.process_organization_batch(test_organizations)
        
        # 통계 출력
        stats = agent_system.get_crawling_statistics()
        print(f"📊 크롤링 통계: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # 시스템 정리
        agent_system.stop_crawling()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
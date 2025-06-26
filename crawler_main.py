#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 크롤링 엔진 v2.0
advcrawler.py의 고급 크롤링 기능을 완전히 이식하여 통합
✅ app.py 완전 호환 (API 키, 콜백 함수 지원)
✅ 강화된 웹 크롤링 (차단 우회, 재시도 로직)
✅ AI 기반 연락처 추출 (Gemini API)
✅ 구글 검색 기반 연락처 검색
✅ 다단계 검증 (Parser + Validator + AI)
✅ 실시간 진행 상황 콜백
✅ 상세한 통계 및 모니터링
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))

import asyncio
import json
import time
import logging
import requests
import re
import random
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 프로젝트 설정 import
from utils.settings import *
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from utils.phone_utils import PhoneUtils
from utils.ai_helpers import AIModelManager
from utils.parser import WebPageParser
from utils.validator import ContactValidator

class UnifiedCrawler:
    """통합 크롤링 엔진 - app.py 호환성 유지"""
    
    def __init__(self, config_override=None, api_key=None, progress_callback=None):
        """초기화 - app.py 호환성을 위한 매개변수 추가"""
        self.config = config_override or CRAWLING_CONFIG
        self.logger = LoggerUtils.setup_crawler_logger()
        self.phone_utils = PhoneUtils()
        self.progress_callback = progress_callback
        
        # AI 매니저 초기화 (API 키 우선 처리)
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
        
        try:
            self.ai_manager = AIModelManager()
            self.use_ai = True
            self.logger.info("🤖 AI 모델 매니저 초기화 성공")
        except Exception as e:
            self.logger.warning(f"AI 모델 매니저 초기화 실패: {e}")
            self.ai_manager = None
            self.use_ai = False
        
        # 웹 파서 및 검증기 초기화
        try:
            self.web_parser = WebPageParser()
            self.validator = ContactValidator()
            self.logger.info("🔍 웹 파서 및 검증기 초기화 성공")
        except Exception as e:
            self.logger.warning(f"웹 파서/검증기 초기화 실패: {e}")
            self.web_parser = None
            self.validator = None
        
        # 구글 검색기 초기화 (지연 초기화)
        self.google_searcher = None
        
        # 크롤링 설정
        self.timeout = 15
        self.max_retries = 3
        self.delay_range = (2, 5)
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 통계 정보 (advcrawler.py 스타일로 확장)
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "ai_enhanced": 0,
            "contacts_found": 0,
            "api_calls_made": 0,
            "ai_failures": 0,
            "google_searches_performed": 0,
            "google_contacts_found": 0,
            "start_time": None,
            "end_time": None
        }
        
        self.logger.info("🚀 통합 크롤러 초기화 완료 - app.py 호환")
    
    async def process_organizations(self, organizations: List[Dict], options: Dict = None) -> List[Dict]:
        """조직/기관 목록 처리"""
        if not organizations:
            self.logger.warning("처리할 조직 데이터가 없습니다.")
            return []
        
        options = options or {}
        self.stats["start_time"] = datetime.now()
        self.stats["total_processed"] = len(organizations)
        
        self.logger.info(f"📊 총 {len(organizations)}개 조직 처리 시작")
        
        results = []
        save_interval = self.config.get("save_interval", 50)
        
        for i, org in enumerate(organizations, 1):
            try:
                # 단일 조직 처리
                processed_org = await self.process_single_organization(org, i)
                results.append(processed_org)
                
                self.stats["successful"] += 1
                
                # 중간 저장
                if i % save_interval == 0:
                    await self.save_intermediate_results(results, i)
                
                # 딜레이
                await asyncio.sleep(self.config.get("default_delay", 2))
                
            except Exception as e:
                self.logger.error(f"❌ 조직 처리 실패 [{i}]: {org.get('name', 'Unknown')} - {e}")
                self.stats["failed"] += 1
                
                # 실패한 경우에도 원본 데이터는 유지
                results.append(org)
        
        self.stats["end_time"] = datetime.now()
        
        # 최종 결과 저장
        final_file = await self.save_final_results(results)
        
        # 통계 출력
        self.print_final_statistics()
        
        return results
    
    async def process_single_organization(self, org: Dict, index: int) -> Dict:
        """단일 조직 처리"""
        org_name = org.get('name', 'Unknown')
        self.logger.info(f"🏢 처리 중 [{index}]: {org_name}")
        
        result = org.copy()
        
        try:
            # 1. 홈페이지 URL 검색 (없는 경우)
            if not result.get('homepage'):
                homepage = await self.search_homepage(org_name)
                if homepage:
                    result['homepage'] = homepage
                    self.logger.info(f"  ✅ 홈페이지 발견: {homepage}")
            
            # 2. 홈페이지에서 상세 정보 추출
            if result.get('homepage'):
                details = await self.extract_details_from_homepage(result['homepage'])
                result.update(details)
            
            # 3. 구글 검색으로 누락 정보 보완
            missing_fields = self.find_missing_fields(result)
            if missing_fields:
                google_results = await self.search_missing_info(org_name, missing_fields)
                result.update(google_results)
            
            # 4. 데이터 검증 및 정리
            result = self.validate_and_clean_data(result)
            
            self.logger.info(f"  ✅ 처리 완료: {org_name}")
            
        except Exception as e:
            self.logger.error(f"  ❌ 처리 실패: {org_name} - {e}")
            result['processing_error'] = str(e)
        
        return result
    
    async def process_json_file_async(self, json_file_path: str, test_mode: bool = False, test_count: int = 10, progress_callback=None) -> List[Dict]:
        """🔧 app.py 호환성을 위한 래퍼 메서드"""
        try:
            # JSON 파일 로드
            data = FileUtils.load_json(json_file_path)
            
            # 데이터 전처리 (app.py와 동일한 방식)
            organizations = []
            if isinstance(data, dict):
                for category, orgs in data.items():
                    if isinstance(orgs, list):
                        for org in orgs:
                            if isinstance(org, dict):
                                org["category"] = category
                                organizations.append(org)
            elif isinstance(data, list):
                organizations = [org for org in data if isinstance(org, dict)]
            
            # 테스트 모드 처리
            if test_mode and test_count:
                organizations = organizations[:test_count]
            
            # progress_callback 저장
            self.progress_callback = progress_callback
            
            # 처리 실행
            results = await self.process_organizations_with_callback(organizations)
            
            return results
            
        except Exception as e:
            self.logger.error(f"JSON 파일 처리 실패: {e}")
            return []
    
    async def process_organizations_with_callback(self, organizations: List[Dict]) -> List[Dict]:
        """콜백 함수가 있는 조직 처리"""
        if not organizations:
            return []
        
        self.stats["start_time"] = datetime.now()
        self.stats["total_processed"] = len(organizations)
        
        results = []
        
        for i, org in enumerate(organizations, 1):
            try:
                # 처리 시작 콜백
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    callback_data = {
                        'name': org.get('name', 'Unknown'),
                        'category': org.get('category', ''),
                        'homepage_url': org.get('homepage', ''),
                        'status': 'processing',
                        'current_step': f'{i}/{len(organizations)}',
                        'processing_time': 0
                    }
                    try:
                        self.progress_callback(callback_data)
                    except Exception as e:
                        self.logger.error(f"콜백 실행 실패: {e}")
                
                # 실제 처리
                start_time = time.time()
                processed_org = await self.process_single_organization(org, i)
                processing_time = time.time() - start_time
                
                results.append(processed_org)
                self.stats["successful"] += 1
                
                # 처리 완료 콜백
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    callback_data = {
                        'name': processed_org.get('name', 'Unknown'),
                        'category': processed_org.get('category', ''),
                        'homepage_url': processed_org.get('homepage', ''),
                        'status': 'completed',
                        'current_step': f'{i}/{len(organizations)}',
                        'processing_time': processing_time,
                        'phone': processed_org.get('phone', ''),
                        'fax': processed_org.get('fax', ''),
                        'email': processed_org.get('email', ''),
                        'address': processed_org.get('address', ''),
                        'extraction_method': processed_org.get('extraction_method', 'unified_crawler')
                    }
                    try:
                        self.progress_callback(callback_data)
                    except Exception as e:
                        self.logger.error(f"콜백 실행 실패: {e}")
                
                # 딜레이
                await asyncio.sleep(self.config.get("default_delay", 2))
                
            except Exception as e:
                self.logger.error(f"❌ 조직 처리 실패 [{i}]: {org.get('name', 'Unknown')} - {e}")
                self.stats["failed"] += 1
                
                # 실패 콜백
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    callback_data = {
                        'name': org.get('name', 'Unknown'),
                        'status': 'failed',
                        'error_message': str(e)
                    }
                    try:
                        self.progress_callback(callback_data)
                    except Exception as e:
                        self.logger.error(f"콜백 실행 실패: {e}")
                
                results.append(org)
        
        self.stats["end_time"] = datetime.now()
        return results
    
    async def search_homepage(self, org_name: str) -> Optional[str]:
        """홈페이지 URL 검색"""
        try:
            # 여기서는 간단한 구글 검색 시뮬레이션
            # 실제로는 selenium이나 requests를 사용
            search_query = f"{org_name} 홈페이지"
            self.logger.debug(f"🔍 홈페이지 검색: {search_query}")
            
            # TODO: 실제 검색 로직 구현
            # 현재는 None 반환
            return None
            
        except Exception as e:
            self.logger.error(f"홈페이지 검색 실패: {e}")
            return None
    
    async def extract_details_from_homepage(self, homepage_url: str) -> Dict:
        """홈페이지에서 상세 정보 추출 - advcrawler.py 로직 이식"""
        try:
            self.logger.info(f"🌐 홈페이지 분석: {homepage_url}")
            
            # 웹페이지 가져오기
            html_content = self.fetch_webpage_enhanced(homepage_url)
            if not html_content:
                return {"extraction_method": "homepage_crawling", "status": "fetch_failed"}
            
            # BeautifulSoup으로 파싱
            parsed_data = self.parse_with_bs4(html_content, homepage_url)
            
            # 기본 연락처 추출
            extracted_contacts = {}
            if self.web_parser:
                extracted_contacts = self.extract_with_parser(parsed_data)
            
            # 검증
            validated_contacts = {}
            if self.validator and extracted_contacts:
                validated_contacts = self.validate_with_validator(extracted_contacts)
            
            # AI 추가 추출
            ai_contacts = {}
            if self.use_ai and self.ai_manager:
                try:
                    ai_contacts = await self.enhance_with_ai(parsed_data, homepage_url)
                    self.stats["ai_enhanced"] += 1
                except Exception as e:
                    self.logger.warning(f"AI 추출 실패: {e}")
                    self.stats["ai_failures"] += 1
            
            # 결과 병합
            final_contacts = self.merge_extraction_results(validated_contacts, ai_contacts)
            
            extracted_data = {
                "extraction_method": "homepage_crawling",
                "extraction_timestamp": datetime.now().isoformat(),
                "source_url": homepage_url,
                "status": "completed",
                **final_contacts
            }
            
            if any(final_contacts.values()):
                self.stats["contacts_found"] += 1
                self.stats["successful_crawls"] += 1
            else:
                self.stats["failed_crawls"] += 1
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"홈페이지 분석 실패: {e}")
            self.stats["failed_crawls"] += 1
            return {"extraction_method": "homepage_crawling", "status": "error", "error": str(e)}
    
    async def search_missing_info(self, org_name: str, missing_fields: List[str]) -> Dict:
        """구글 검색으로 누락 정보 검색 - advcrawler.py 로직 이식"""
        try:
            self.logger.info(f"🔍 누락 정보 검색: {org_name} - {missing_fields}")
            
            # 구글 검색기 초기화 (지연 초기화)
            if not self.google_searcher:
                try:
                    self.google_searcher = GoogleContactSearcher()
                    self.logger.info("🔍 구글 검색기 초기화 성공")
                except Exception as e:
                    self.logger.warning(f"구글 검색기 초기화 실패: {e}")
                    return {}
            
            # 구글 검색으로 연락처 검색
            google_contacts = await self.google_searcher.search_organization_contacts(org_name)
            self.stats["google_searches_performed"] += 1
            
            if sum(len(v) for v in google_contacts.values()) > 0:
                self.stats["google_contacts_found"] += 1
            
            # 결과 변환 (missing_fields에 맞게)
            results = {}
            field_mapping = {
                'phone': google_contacts.get('phones', []),
                'fax': google_contacts.get('faxes', []),
                'email': google_contacts.get('emails', []),
                'address': google_contacts.get('addresses', [])
            }
            
            for field in missing_fields:
                if field in field_mapping and field_mapping[field]:
                    results[field] = field_mapping[field][0]  # 첫 번째 결과 사용
            
            return results
            
        except Exception as e:
            self.logger.error(f"누락 정보 검색 실패: {e}")
            return {}
    
    def find_missing_fields(self, org: Dict) -> List[str]:
        """누락된 필드 찾기"""
        required_fields = ["phone", "fax", "email", "address"]
        missing = []
        
        for field in required_fields:
            if not org.get(field) or str(org.get(field)).strip() == "":
                missing.append(field)
        
        return missing
    
    def validate_and_clean_data(self, org: Dict) -> Dict:
        """데이터 검증 및 정리"""
        try:
            # 전화번호 검증
            if org.get('phone'):
                org['phone'] = self.phone_utils.clean_phone_number(org['phone'])
                if not self.phone_utils.validate_phone_number(org['phone']):
                    org['phone_validation_error'] = "Invalid phone format"
            
            # 팩스번호 검증
            if org.get('fax'):
                org['fax'] = self.phone_utils.clean_phone_number(org['fax'])
            
            # 이메일 검증
            if org.get('email'):
                # 간단한 이메일 검증
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, org['email']):
                    org['email_validation_error'] = "Invalid email format"
            
            return org
            
        except Exception as e:
            self.logger.error(f"데이터 검증 실패: {e}")
            return org
    
    async def save_intermediate_results(self, results: List[Dict], count: int):
        """중간 결과 저장"""
        try:
            filename = generate_output_filename("intermediate", OUTPUT_DIR, count=count)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 중간 저장 완료: {filename} ({count}개)")
            
        except Exception as e:
            self.logger.error(f"중간 저장 실패: {e}")
    
    async def save_final_results(self, results: List[Dict]) -> str:
        """최종 결과 저장"""
        try:
            filename = generate_output_filename("enhanced_final", OUTPUT_DIR)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 최종 저장 완료: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"최종 저장 실패: {e}")
            return ""
    
    def print_final_statistics(self):
        """최종 통계 출력 - advcrawler.py 스타일로 확장"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*60)
        print("📊 크롤링 완료 통계")
        print("="*60)
        print(f"📋 총 처리: {self.stats['total_processed']}개")
        print(f"✅ 성공: {self.stats['successful']}개")
        print(f"❌ 실패: {self.stats['failed']}개")
        print(f"🌐 웹 크롤링 성공: {self.stats['successful_crawls']}개")
        print(f"🌐 웹 크롤링 실패: {self.stats['failed_crawls']}개")
        print(f"🔍 구글 검색 수행: {self.stats['google_searches_performed']}개")
        print(f"📞 구글에서 연락처 발견: {self.stats['google_contacts_found']}개")
        print(f"🤖 AI 호출: {self.stats['api_calls_made']}회")
        print(f"🎯 AI 성공: {self.stats['ai_enhanced']}개")
        print(f"⚠️ AI 실패: {self.stats['ai_failures']}개")
        print(f"📞 총 연락처 발견: {self.stats['contacts_found']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100
            print(f"📈 전체 성공률: {success_rate:.1f}%")
        
        if self.stats['successful_crawls'] + self.stats['failed_crawls'] > 0:
            crawl_success_rate = (self.stats['successful_crawls'] / (self.stats['successful_crawls'] + self.stats['failed_crawls'])) * 100
            print(f"🌐 웹 크롤링 성공률: {crawl_success_rate:.1f}%")
        
        if self.stats['api_calls_made'] > 0:
            ai_success_rate = (self.stats['ai_enhanced'] / self.stats['api_calls_made']) * 100
            print(f"🤖 AI 성공률: {ai_success_rate:.1f}%")
        
        if self.stats['google_searches_performed'] > 0:
            google_success_rate = (self.stats['google_contacts_found'] / self.stats['google_searches_performed']) * 100
            print(f"🔍 구글 검색 성공률: {google_success_rate:.1f}%")
        
        print(f"⏱️ 소요시간: {duration}")
        print(f"🚀 평균 처리시간: {duration.total_seconds()/self.stats['total_processed']:.2f}초/개")
        print("="*60)

    # ==================== advcrawler.py 핵심 메서드들 이식 ====================
    
    def fetch_webpage_enhanced(self, url: str, max_retries: int = 3) -> Optional[str]:
        """강화된 웹페이지 가져오기 (차단 우회) - advcrawler.py에서 이식"""
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        # 다양한 헤더 세트
        header_sets = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        ]
        
        for attempt in range(max_retries):
            try:
                # 헤더 로테이션
                headers = header_sets[attempt % len(header_sets)]
                
                self.logger.info(f"웹페이지 요청 시도 {attempt + 1}/{max_retries}: {url}")
                
                # 새 세션 생성 (필요시)
                if attempt > 0:
                    self.session.close()
                    self.session = requests.Session()
                
                # 헤더 설정
                self.session.headers.clear()
                self.session.headers.update(headers)
                
                response = self.session.get(
                    url, 
                    timeout=(10, 30),  # (연결, 읽기) 타임아웃
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    # 인코딩 설정
                    if response.encoding is None:
                        response.encoding = response.apparent_encoding or 'utf-8'
                    
                    content = response.text
                    
                    # 차단 페이지 감지
                    if self.is_blocked_content(content):
                        self.logger.warning(f"차단된 콘텐츠 감지 (시도 {attempt + 1}): {url}")
                        if attempt < max_retries - 1:
                            delay = random.uniform(5, 10)
                            time.sleep(delay)
                            continue
                        else:
                            return None
                    
                    self.logger.info(f"웹페이지 가져오기 성공: {url}")
                    return content
                    
                elif response.status_code == 403:
                    self.logger.warning(f"접근 거부 (403) - 시도 {attempt + 1}: {url}")
                    if attempt < max_retries - 1:
                        delay = random.uniform(10, 20)
                        time.sleep(delay)
                        continue
                        
                else:
                    self.logger.warning(f"HTTP 오류 {response.status_code} (시도 {attempt + 1}): {url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"타임아웃 (시도 {attempt + 1}): {url}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}): {url}")
            except Exception as e:
                self.logger.error(f"예상치 못한 오류 (시도 {attempt + 1}): {url} - {e}")
            
            # 재시도 전 대기
            if attempt < max_retries - 1:
                delay = random.uniform(3, 8)
                time.sleep(delay)
        
        self.logger.error(f"모든 시도 실패: {url}")
        return None

    def is_blocked_content(self, content: str) -> bool:
        """차단된 콘텐츠 감지"""
        if not content or len(content) < 100:
            return True
        
        block_indicators = [
            'access denied', 'forbidden', 'blocked', '접근이 거부', '차단된',
            'cloudflare', 'checking your browser', 'ddos protection', 'security check', 'captcha'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in block_indicators)

    def parse_with_bs4(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """BeautifulSoup으로 HTML 파싱"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 기본 정보 추출
            parsed_data = {
                'title': '',
                'meta_description': '',
                'all_text': '',
                'footer_text': '',
                'contact_sections': []
            }
            
            # 제목 추출
            title_tag = soup.find('title')
            if title_tag:
                parsed_data['title'] = title_tag.get_text().strip()
            
            # 메타 설명 추출
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                parsed_data['meta_description'] = meta_desc.get('content', '')
            
            # 전체 텍스트 추출 (스크립트, 스타일 제거)
            for script in soup(["script", "style"]):
                script.decompose()
            
            parsed_data['all_text'] = soup.get_text()
            
            # footer 영역 추출
            footer_elements = soup.find_all(['footer', 'div'], 
                                        class_=re.compile(r'footer|bottom|contact|info', re.I))
            footer_texts = []
            for footer in footer_elements:
                footer_text = footer.get_text().strip()
                if footer_text and len(footer_text) > 20:
                    footer_texts.append(footer_text)
            
            parsed_data['footer_text'] = '\n'.join(footer_texts)
            
            # 연락처 관련 섹션 추출
            contact_keywords = ['연락처', 'contact', '전화', 'phone', '팩스', 'fax', '이메일', 'email']
            contact_elements = soup.find_all(string=re.compile('|'.join(contact_keywords), re.I))
            
            for element in contact_elements[:10]:  # 최대 10개만
                parent = element.parent
                if parent:
                    section_text = parent.get_text().strip()
                    if len(section_text) > 10:
                        parsed_data['contact_sections'].append(section_text)
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"BS4 파싱 오류: {e}")
            return {'all_text': html_content[:5000]}  # 실패시 원본 텍스트 일부 반환

    def extract_with_parser(self, parsed_data: Dict[str, Any]) -> Dict[str, List]:
        """parser.py를 이용한 기본 추출"""
        try:
            # 전체 텍스트에서 연락처 정보 추출
            all_text = parsed_data.get('all_text', '')
            footer_text = parsed_data.get('footer_text', '')
            contact_sections = ' '.join(parsed_data.get('contact_sections', []))
            
            # 우선순위에 따라 텍스트 결합
            combined_text = f"{footer_text}\n{contact_sections}\n{all_text}"
            
            # parser로 추출
            extracted_contacts = self.web_parser.extract_contact_info(combined_text)
            
            self.logger.info(f"Parser 추출 완료: {len(extracted_contacts.get('phones', []))}개 전화번호, "
                           f"{len(extracted_contacts.get('faxes', []))}개 팩스번호, "
                           f"{len(extracted_contacts.get('emails', []))}개 이메일")
            
            return extracted_contacts
            
        except Exception as e:
            self.logger.error(f"Parser 추출 오류: {e}")
            return {'phones': [], 'faxes': [], 'emails': [], 'addresses': []}

    def validate_with_validator(self, extracted_data: Dict[str, List]) -> Dict[str, List]:
        """validator.py를 이용한 검증"""
        try:
            validated_data = {
                'phones': [],
                'faxes': [],
                'emails': [],
                'addresses': [],
                'postal_codes': []
            }
            
            # 전화번호 검증
            for phone in extracted_data.get('phones', []):
                is_valid, result = self.validator.validate_phone_number(phone)
                if is_valid:
                    validated_data['phones'].append(result)
            
            # 팩스번호 검증
            for fax in extracted_data.get('faxes', []):
                is_valid, result = self.validator.validate_fax_number(fax)
                if is_valid:
                    validated_data['faxes'].append(result)
            
            # 이메일은 기본 검증만
            validated_data['emails'] = extracted_data.get('emails', [])
            validated_data['addresses'] = extracted_data.get('addresses', [])
            
            self.logger.info(f"Validator 검증 완료: {len(validated_data['phones'])}개 유효 전화번호, "
                           f"{len(validated_data['faxes'])}개 유효 팩스번호")
            
            return validated_data
            
        except Exception as e:
            self.logger.error(f"Validator 검증 오류: {e}")
            return extracted_data

    async def enhance_with_ai(self, parsed_data: Dict[str, Any], source_url: str) -> Dict[str, List]:
        """AI를 이용한 추가 추출"""
        if not self.use_ai or not self.ai_manager:
            return {}
        
        try:
            self.logger.info(f"🤖 AI 추가 추출 시작: {source_url}")
            self.stats['api_calls_made'] += 1
            
            # AI용 텍스트 준비 (길이 제한)
            all_text = parsed_data.get('all_text', '')
            footer_text = parsed_data.get('footer_text', '')
            contact_sections = ' '.join(parsed_data.get('contact_sections', []))
            
            # 중요 섹션 우선 조합
            ai_text_parts = []
            if footer_text:
                ai_text_parts.append(f"=== Footer 정보 ===\n{footer_text[:1500]}")
            if contact_sections:
                ai_text_parts.append(f"=== 연락처 섹션 ===\n{contact_sections[:1500]}")
            if all_text:
                ai_text_parts.append(f"=== 기타 내용 ===\n{all_text[:2000]}")
            
            ai_text = '\n\n'.join(ai_text_parts)
            
            # 텍스트 길이 제한 (최대 5000자)
            if len(ai_text) > 5000:
                ai_text = ai_text[:5000]
            
            # AI 프롬프트 생성
            prompt = f"""
다음 웹사이트에서 연락처 정보를 정확하게 추출해주세요.

**추출할 정보:**
- 전화번호: 한국 형식 (02-1234-5678, 031-123-4567, 010-1234-5678)
- 팩스번호: 한국 형식 (02-1234-5679)
- 이메일: 유효한 형식 (info@example.com)
- 주소: 완전한 주소

**응답 형식:**
```markdown
**전화번호:** [발견된 번호 또는 "없음"]
**팩스번호:** [발견된 번호 또는 "없음"]  
**이메일:** [발견된 이메일 또는 "없음"]
**주소:** [발견된 주소 또는 "없음"]
```

**분석할 텍스트:**
{ai_text}
"""
            
            # AI 호출
            ai_response = await self.ai_manager.extract_with_gemini(ai_text, prompt)
            
            if ai_response:
                ai_extracted = self.parse_ai_response(ai_response)
                self.logger.info(f"✅ AI 추출 완료")
                return ai_extracted
            else:
                self.logger.warning(f"⚠️ AI 응답 없음")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ AI 추출 오류: {e}")
            return {}

    def parse_ai_response(self, ai_response: str) -> Dict[str, List]:
        """AI 응답을 파싱하여 구조화"""
        try:
            result = {
                'phones': [],
                'faxes': [],
                'emails': [],
                'addresses': []
            }
            
            # 마크다운 형식 파싱
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line and ('**' in line or '*' in line):
                    # 마크다운 볼드 제거
                    line = line.replace('**', '').replace('*', '')
                    
                    try:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if value and value not in ["없음", "정보없음", "확인안됨", "-"]:
                            if '전화번호' in key or 'phone' in key:
                                if self._is_valid_phone_format(value):
                                    result['phones'].append(value)
                            elif '팩스' in key or 'fax' in key:
                                if self._is_valid_phone_format(value):
                                    result['faxes'].append(value)
                            elif '이메일' in key or 'email' in key:
                                if self._is_valid_email_format(value):
                                    result['emails'].append(value)
                            elif '주소' in key or 'address' in key:
                                if len(value) > 10:
                                    result['addresses'].append(value)
                    except ValueError:
                        continue
            
            return result
            
        except Exception as e:
            self.logger.error(f"AI 응답 파싱 오류: {e}")
            return {}

    def _is_valid_phone_format(self, phone: str) -> bool:
        """전화번호 형식 검증"""
        phone_pattern = r'^\d{2,3}-\d{3,4}-\d{4}$'
        return bool(re.match(phone_pattern, phone))
    
    def _is_valid_email_format(self, email: str) -> bool:
        """이메일 형식 검증"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def merge_extraction_results(self, validated_result: Dict, ai_result: Dict) -> Dict:
        """추출 결과 병합"""
        merged = {
            'phone': '',
            'fax': '',
            'email': '',
            'address': ''
        }
        
        # AI 결과 우선, 검증된 결과로 보완
        field_mappings = [
            ('phones', 'phone'),
            ('faxes', 'fax'),
            ('emails', 'email'),
            ('addresses', 'address')
        ]
        
        for source_field, target_field in field_mappings:
            # AI 결과 우선
            if ai_result.get(source_field):
                merged[target_field] = ai_result[source_field][0]
            # 검증된 결과로 보완
            elif validated_result.get(source_field):
                merged[target_field] = validated_result[source_field][0]
        
        return merged

# ==================== GoogleContactSearcher 클래스 추가 ====================

class GoogleContactSearcher:
    """구글 검색을 통한 연락처 정보 직접 검색 - advcrawler.py에서 이식"""
    
    def __init__(self):
        try:
            self.session = requests.Session()
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
            ]
            self.current_ua_index = 0
            self.setup_session()
            
        except Exception as e:
            raise Exception(f"GoogleContactSearcher 초기화 실패: {e}")
    
    def setup_session(self):
        """세션 설정"""
        ua = self.user_agents[self.current_ua_index % len(self.user_agents)]
        self.current_ua_index += 1
        
        self.session.headers.clear()
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    async def search_organization_contacts(self, organization_name: str) -> Dict[str, List]:
        """기관명으로 연락처 정보 검색"""
        all_contacts = {
            'phones': [],
            'faxes': [],
            'emails': [],
            'addresses': []
        }
        
        try:
            # 다양한 검색 쿼리
            search_queries = [
                f'"{organization_name}" 전화번호',
                f'"{organization_name}" 연락처',
                f'{organization_name} contact'
            ]
            
            # 각 쿼리로 검색 (최대 2개만)
            for i, query in enumerate(search_queries[:2]):
                try:
                    # 구글 검색
                    html_content = self.search_google_with_retry(query)
                    
                    if html_content:
                        # 연락처 추출
                        extracted = self.extract_contacts_from_search_results(html_content, organization_name)
                        
                        # 결과 병합
                        for contact_type, contact_list in extracted.items():
                            for contact in contact_list:
                                if contact not in all_contacts[contact_type]:
                                    all_contacts[contact_type].append(contact)
                    
                    # 검색 간격
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    continue
        
        except Exception as e:
            pass
        
        return all_contacts
    
    def search_google_with_retry(self, query: str, max_retries: int = 2) -> Optional[str]:
        """재시도 로직이 포함된 구글 검색"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.setup_session()
                
                search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=ko&num=5"
                
                response = self.session.get(search_url, timeout=10, verify=False)
                
                if response.status_code == 200:
                    if not self.is_blocked_response(response.text):
                        return response.text
                
            except Exception as e:
                continue
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def is_blocked_response(self, html: str) -> bool:
        """구글 차단 응답 감지"""
        if not html:
            return True
            
        block_indicators = ['unusual traffic', 'automated queries', 'captcha', 'blocked']
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in block_indicators)
    
    def extract_contacts_from_search_results(self, html: str, organization_name: str) -> Dict[str, List]:
        """구글 검색 결과에서 연락처 정보 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            all_text = soup.get_text()
            
            contacts = {
                'phones': [],
                'faxes': [],
                'emails': [],
                'addresses': []
            }
            
            # 전화번호 패턴 (한국)
            phone_patterns = [
                r'\b0\d{1,2}-\d{3,4}-\d{4}\b',      # 02-1234-5678
                r'\b010-\d{4}-\d{4}\b',             # 010-1234-5678
            ]
            
            # 이메일 패턴
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            
            # 전화번호 추출
            for pattern in phone_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    clean_phone = re.sub(r'[^\d-]', '', match)
                    if len(clean_phone) >= 9 and clean_phone not in contacts['phones']:
                        contacts['phones'].append(clean_phone)
            
            # 이메일 추출
            email_matches = re.findall(email_pattern, all_text)
            for email in email_matches:
                if email not in contacts['emails']:
                    contacts['emails'].append(email)
            
            return contacts
            
        except Exception as e:
            return {'phones': [], 'faxes': [], 'emails': [], 'addresses': []}

# 편의 함수들
async def crawl_from_file(input_file: str, options: Dict = None) -> List[Dict]:
    """파일에서 데이터를 로드하여 크롤링"""
    try:
        # 파일 로드
        data = FileUtils.load_json(input_file)
        if not data:
            raise ValueError(f"파일을 로드할 수 없습니다: {input_file}")
        
        # 크롤러 생성 및 실행
        crawler = UnifiedCrawler()
        results = await crawler.process_organizations(data, options)
        
        return results
        
    except Exception as e:
        logging.error(f"파일 크롤링 실패: {e}")
        return []

async def crawl_latest_file(options: Dict = None) -> List[Dict]:
    """최신 입력 파일을 자동으로 찾아서 크롤링"""
    try:
        latest_file = get_latest_input_file()
        if not latest_file:
            raise ValueError("입력 파일을 찾을 수 없습니다.")
        
        print(f"📂 최신 파일 사용: {latest_file}")
        return await crawl_from_file(str(latest_file), options)
        
    except Exception as e:
        logging.error(f"최신 파일 크롤링 실패: {e}")
        return []

# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    print("🚀 통합 크롤링 시스템 시작")
    print("="*60)
    
    try:
        # 프로젝트 초기화
        initialize_project()
        
        # 최신 파일로 크롤링 실행
        results = await crawl_latest_file()
        
        if results:
            print(f"\n✅ 크롤링 완료: {len(results)}개 조직 처리")
        else:
            print("\n❌ 크롤링 실패")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
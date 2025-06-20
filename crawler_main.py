#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 크롤링 엔진
기존 advcrawler.py + enhanced_detail_extractor.py 통합
config.py 설정 활용
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 프로젝트 설정 import
from settings import *
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from utils.phone_utils import PhoneUtils
from ai_helpers import AIModelManager

class UnifiedCrawler:
    """통합 크롤링 엔진"""
    
    def __init__(self, config_override=None):
        """초기화"""
        self.config = config_override or CRAWLING_CONFIG
        self.logger = LoggerUtils.setup_crawler_logger()
        self.ai_manager = AIModelManager()
        self.phone_utils = PhoneUtils()
        
        # 통계 정보
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
        
        self.logger.info("🚀 통합 크롤러 초기화 완료")
    
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
        """홈페이지에서 상세 정보 추출"""
        try:
            self.logger.debug(f"🌐 홈페이지 분석: {homepage_url}")
            
            # TODO: 실제 웹 크롤링 및 AI 분석 로직 구현
            # 현재는 빈 딕셔너리 반환
            extracted_data = {
                "extraction_method": "homepage_crawling",
                "extraction_timestamp": datetime.now().isoformat(),
                "source_url": homepage_url
            }
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"홈페이지 분석 실패: {e}")
            return {}
    
    async def search_missing_info(self, org_name: str, missing_fields: List[str]) -> Dict:
        """구글 검색으로 누락 정보 검색"""
        try:
            self.logger.debug(f"🔍 누락 정보 검색: {org_name} - {missing_fields}")
            
            results = {}
            
            for field in missing_fields:
                if field == "phone":
                    search_query = f"{org_name} 전화번호"
                elif field == "fax":
                    search_query = f"{org_name} 팩스번호"
                elif field == "email":
                    search_query = f"{org_name} 이메일"
                elif field == "address":
                    search_query = f"{org_name} 주소"
                else:
                    continue
                
                # TODO: 실제 구글 검색 로직 구현
                # 현재는 빈 값 반환
                
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
        """최종 통계 출력"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*60)
        print("📊 크롤링 완료 통계")
        print("="*60)
        print(f"📋 총 처리: {self.stats['total_processed']}개")
        print(f"✅ 성공: {self.stats['successful']}개")
        print(f"❌ 실패: {self.stats['failed']}개")
        print(f"📈 성공률: {(self.stats['successful']/self.stats['total_processed']*100):.1f}%")
        print(f"⏱️ 소요시간: {duration}")
        print(f"🚀 평균 처리시간: {duration.total_seconds()/self.stats['total_processed']:.2f}초/개")
        print("="*60)

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
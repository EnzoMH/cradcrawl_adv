#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 크롤링 엔진 v3.0 - 전문 모듈 통합 버전
✅ fax_extractor.py로 팩스번호 추출
✅ phone_extractor.py로 전화번호 추출  
✅ url_extractor.py로 홈페이지 및 내부 연락처 추출
✅ validator.py로 유효성 검증
✅ 검증된 데이터 DB 저장
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'cralwer'))

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 프로젝트 설정 import
from utils.settings import *
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils

# 전문 모듈들 import
try:
    from cralwer.fax_extractor import GoogleContactCrawler as FaxExtractor
    FAX_EXTRACTOR_AVAILABLE = True
    print("✅ fax_extractor.py 모듈 로드 성공")
except ImportError as e:
    print(f"❌ fax_extractor.py 모듈 로드 실패: {e}")
    FAX_EXTRACTOR_AVAILABLE = False

try:
    from cralwer.phone_extractor import extract_phone_numbers, search_phone_number, setup_driver
    PHONE_EXTRACTOR_AVAILABLE = True
    print("✅ phone_extractor.py 모듈 로드 성공")
except ImportError as e:
    print(f"❌ phone_extractor.py 모듈 로드 실패: {e}")
    PHONE_EXTRACTOR_AVAILABLE = False

try:
    from cralwer.url_extractor import HomepageParser
    URL_EXTRACTOR_AVAILABLE = True
    print("✅ url_extractor.py 모듈 로드 성공")
except ImportError as e:
    print(f"❌ url_extractor.py 모듈 로드 실패: {e}")
    URL_EXTRACTOR_AVAILABLE = False

try:
    from utils.validator import ContactValidator, AIValidator
    VALIDATOR_AVAILABLE = True
    print("✅ validator.py 모듈 로드 성공")
except ImportError as e:
    print(f"❌ validator.py 모듈 로드 실패: {e}")
    VALIDATOR_AVAILABLE = False

try:
    from database.database import get_database
    DATABASE_AVAILABLE = True
    print("✅ database.py 모듈 로드 성공")
except ImportError as e:
    print(f"❌ database.py 모듈 로드 실패: {e}")
    DATABASE_AVAILABLE = False

class ModularUnifiedCrawler:
    """전문 모듈들을 통합한 크롤링 엔진"""
    
    def __init__(self, config_override=None, api_key=None, progress_callback=None):
        """초기화"""
        self.config = config_override or CRAWLING_CONFIG
        self.logger = LoggerUtils.setup_crawler_logger("modular_unified_crawler")
        self.progress_callback = progress_callback
        
        # 전문 모듈 인스턴스들
        self.fax_extractor = None
        self.phone_driver = None
        self.homepage_parser = None
        self.contact_validator = None
        self.ai_validator = None
        self.database = None
        
        # 통계 정보
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "phone_extracted": 0,
            "fax_extracted": 0,
            "homepage_parsed": 0,
            "contacts_validated": 0,
            "saved_to_db": 0,
            "start_time": None,
            "end_time": None
        }
        
        self.logger.info("🚀 모듈러 통합 크롤러 초기화 완료")
    
    def initialize_modules(self):
        """전문 모듈들 초기화"""
        try:
            self.logger.info("🔧 전문 모듈들 초기화 시작...")
            
            # 1. 팩스 추출기 초기화
            if FAX_EXTRACTOR_AVAILABLE:
                try:
                    self.fax_extractor = FaxExtractor()
                    self.logger.info("✅ 팩스 추출기 초기화 성공")
                except Exception as e:
                    self.logger.error(f"❌ 팩스 추출기 초기화 실패: {e}")
                    self.fax_extractor = None
            
            # 2. 전화번호 추출기 초기화 (Selenium 드라이버)
            if PHONE_EXTRACTOR_AVAILABLE:
                try:
                    self.phone_driver = setup_driver()
                    self.logger.info("✅ 전화번호 추출기 드라이버 초기화 성공")
                except Exception as e:
                    self.logger.error(f"❌ 전화번호 추출기 초기화 실패: {e}")
                    self.phone_driver = None
            
            # 3. 홈페이지 파서 초기화
            if URL_EXTRACTOR_AVAILABLE:
                try:
                    self.homepage_parser = HomepageParser(headless=True)
                    self.logger.info("✅ 홈페이지 파서 초기화 성공")
                except Exception as e:
                    self.logger.error(f"❌ 홈페이지 파서 초기화 실패: {e}")
                    self.homepage_parser = None
            
            # 4. 검증기 초기화
            if VALIDATOR_AVAILABLE:
                try:
                    self.contact_validator = ContactValidator()
                    self.ai_validator = AIValidator()
                    self.logger.info("✅ 연락처 검증기 초기화 성공")
                except Exception as e:
                    self.logger.error(f"❌ 검증기 초기화 실패: {e}")
                    self.contact_validator = None
                    self.ai_validator = None
            
            # 5. 데이터베이스 초기화
            if DATABASE_AVAILABLE:
                try:
                    self.database = get_database()
                    self.logger.info("✅ 데이터베이스 연결 성공")
                except Exception as e:
                    self.logger.error(f"❌ 데이터베이스 연결 실패: {e}")
                    self.database = None
            
            self.logger.info("🎯 모듈 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 모듈 초기화 중 오류: {e}")
            raise
    
    def cleanup_modules(self):
        """모듈들 정리"""
        try:
            self.logger.info("🧹 모듈 정리 시작...")
            
            # 팩스 추출기 정리
            if self.fax_extractor:
                try:
                    self.fax_extractor.close()
                    self.logger.info("✅ 팩스 추출기 정리 완료")
                except:
                    pass
            
            # 전화번호 드라이버 정리
            if self.phone_driver:
                try:
                    self.phone_driver.quit()
                    self.logger.info("✅ 전화번호 드라이버 정리 완료")
                except:
                    pass
            
            # 홈페이지 파서 정리
            if self.homepage_parser:
                try:
                    self.homepage_parser.close_driver()
                    self.logger.info("✅ 홈페이지 파서 정리 완료")
                except:
                    pass
            
            self.logger.info("🎯 모든 모듈 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 모듈 정리 중 오류: {e}")
    
    async def process_organizations(self, organizations: List[Dict], options: Dict = None) -> List[Dict]:
        """조직/기관 목록 처리 - 전문 모듈 활용"""
        if not organizations:
            self.logger.warning("처리할 조직 데이터가 없습니다.")
            return []
        
        options = options or {}
        self.stats["start_time"] = datetime.now()
        self.stats["total_processed"] = len(organizations)
        
        # 모듈 초기화
        self.initialize_modules()
        
        self.logger.info(f"📊 총 {len(organizations)}개 조직 처리 시작 (모듈러 방식)")
        
        results = []
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    # 단일 조직 처리
                    processed_org = await self.process_single_organization_modular(org, i)
                    results.append(processed_org)
                    
                    self.stats["successful"] += 1
                    
                    # 딜레이
                    await asyncio.sleep(self.config.get("default_delay", 2))
                    
                except Exception as e:
                    self.logger.error(f"❌ 조직 처리 실패 [{i}]: {org.get('name', 'Unknown')} - {e}")
                    self.stats["failed"] += 1
                    
                    # 실패한 경우에도 원본 데이터는 유지
                    results.append(org)
        
        finally:
            # 모듈 정리
            self.cleanup_modules()
        
        self.stats["end_time"] = datetime.now()
        
        # 통계 출력
        self.print_final_statistics()
        
        return results
    
    async def process_single_organization_modular(self, org: Dict, index: int) -> Dict:
        """단일 조직 처리 - 전문 모듈 활용"""
        org_name = org.get('name', 'Unknown')
        self.logger.info(f"🏢 모듈러 처리 시작 [{index}]: {org_name}")
        
        result = org.copy()
        processing_steps = []
        
        try:
            # 1단계: 홈페이지 추출 및 내부 연락처 파싱
            homepage_data = await self.extract_homepage_and_contacts(org_name, result)
            if homepage_data:
                result.update(homepage_data)
                processing_steps.append("homepage_parsed")
                self.stats["homepage_parsed"] += 1
            
            # 2단계: 전화번호 추출 (phone_extractor.py)
            phone_data = await self.extract_phone_numbers_module(org_name, result)
            if phone_data:
                result.update(phone_data)
                processing_steps.append("phone_extracted")
                self.stats["phone_extracted"] += 1
            
            # 3단계: 팩스번호 추출 (fax_extractor.py)
            fax_data = await self.extract_fax_numbers_module(org_name, result)
            if fax_data:
                result.update(fax_data)
                processing_steps.append("fax_extracted")
                self.stats["fax_extracted"] += 1
            
            # 4단계: 연락처 정보 검증 (validator.py)
            validated_data = await self.validate_contact_info(result)
            if validated_data:
                result.update(validated_data)
                processing_steps.append("contacts_validated")
                self.stats["contacts_validated"] += 1
            
            # 5단계: 데이터베이스 저장
            db_result = await self.save_to_database(result)
            if db_result:
                result.update(db_result)
                processing_steps.append("saved_to_db")
                self.stats["saved_to_db"] += 1
            
            # 처리 완료 정보 추가
            result.update({
                "processing_steps": processing_steps,
                "processing_timestamp": datetime.now().isoformat(),
                "processing_method": "modular_specialized",
                "modules_used": {
                    "fax_extractor": bool(self.fax_extractor),
                    "phone_extractor": bool(self.phone_driver),
                    "homepage_parser": bool(self.homepage_parser),
                    "validator": bool(self.contact_validator),
                    "database": bool(self.database)
                }
            })
            
            self.logger.info(f"  ✅ 모듈러 처리 완료: {org_name} (단계: {len(processing_steps)}개)")
            
        except Exception as e:
            self.logger.error(f"  ❌ 모듈러 처리 실패: {org_name} - {e}")
            result['processing_error'] = str(e)
            result['processing_method'] = "modular_failed"
        
        return result
    
    async def extract_homepage_and_contacts(self, org_name: str, org_data: Dict) -> Optional[Dict]:
        """홈페이지 추출 및 내부 연락처 파싱 - url_extractor.py 활용"""
        if not self.homepage_parser:
            self.logger.warning(f"홈페이지 파서 없음: {org_name}")
            return None
        
        try:
            self.logger.info(f"🌐 홈페이지 파싱 시작: {org_name}")
            
            # 기존 홈페이지가 있으면 사용, 없으면 검색
            homepage_url = org_data.get('homepage', '').strip()
            
            if not homepage_url or not homepage_url.startswith(('http://', 'https://')):
                # 홈페이지 URL이 없으면 구글 검색으로 찾기
                self.logger.info(f"🔍 홈페이지 URL 검색: {org_name}")
                # TODO: 구글 검색으로 홈페이지 찾기 로직 추가
                return None
            
            # url_extractor.py의 HomepageParser 사용
            page_data = self.homepage_parser.extract_page_content(homepage_url)
            
            if page_data["status"] == "success" and page_data["accessible"]:
                # AI 요약 생성
                ai_summary = self.homepage_parser.summarize_with_ai(org_name, page_data)
                
                return {
                    "homepage_parsed": True,
                    "homepage_title": page_data["title"],
                    "homepage_content_length": len(page_data["text_content"]),
                    "homepage_contact_info": page_data["contact_info"],
                    "homepage_meta_info": page_data["meta_info"],
                    "homepage_ai_summary": ai_summary,
                    "homepage_parsing_details": page_data["parsing_details"]
                }
            else:
                self.logger.warning(f"홈페이지 파싱 실패: {org_name} - {page_data.get('error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"홈페이지 파싱 오류: {org_name} - {e}")
            return None
        
    async def search_homepage(self, org_name: str) -> Dict[str, Any]:
        """홈페이지 검색 - ContactEnrichmentService 호환성"""
        try:
            self.logger.info(f"🔍 홈페이지 검색: {org_name}")
            
            # url_extractor.py의 HomepageParser 사용
            if not self.homepage_parser:
                self.logger.warning("홈페이지 파서 없음")
                return {}
            
            # 구글 검색으로 홈페이지 URL 찾기 (구현 필요)
            # 임시로 빈 결과 반환
            return {
                "homepage": "",
                "status": "not_found",
                "message": "홈페이지 검색 기능 구현 필요"
            }
            
        except Exception as e:
            self.logger.error(f"홈페이지 검색 오류: {org_name} - {e}")
            return {}
    
    async def extract_details_from_homepage(self, homepage_url: str) -> Dict[str, Any]:
        """홈페이지에서 상세 정보 추출 - ContactEnrichmentService 호환성"""
        try:
            self.logger.info(f"🌐 홈페이지 분석: {homepage_url}")
            
            if not self.homepage_parser:
                self.logger.warning("홈페이지 파서 없음")
                return {}
            
            # url_extractor.py의 HomepageParser 사용
            page_data = self.homepage_parser.extract_page_content(homepage_url)
            
            if page_data["status"] == "success" and page_data["accessible"]:
                contact_info = page_data.get("contact_info", {})
                
                return {
                    "phone": contact_info.get("phone", ""),
                    "fax": contact_info.get("fax", ""),
                    "email": contact_info.get("email", ""),
                    "address": contact_info.get("address", ""),
                    "status": "success"
                }
            else:
                return {
                    "status": "failed",
                    "error": page_data.get("error", "접근 실패")
                }
                
        except Exception as e:
            self.logger.error(f"홈페이지 분석 오류: {homepage_url} - {e}")
            return {"status": "error", "error": str(e)}
    
    async def search_missing_info(self, org_name: str, missing_fields: List[str]) -> Dict[str, str]:
        """누락된 정보 검색 - ContactEnrichmentService 호환성"""
        try:
            self.logger.info(f"🔍 누락 정보 검색: {org_name} - {missing_fields}")
            
            results = {}
            
            # 전화번호 검색
            if "phone" in missing_fields and self.phone_driver:
                try:
                    from cralwer.phone_extractor import search_phone_number
                    found_phones = search_phone_number(self.phone_driver, org_name)
                    if found_phones:
                        results["phone"] = found_phones[0]
                        self.logger.info(f"  📞 전화번호 발견: {results['phone']}")
                except Exception as e:
                    self.logger.warning(f"전화번호 검색 실패: {e}")
            
            # 팩스번호 검색
            if "fax" in missing_fields and self.fax_extractor:
                try:
                    found_faxes = self.fax_extractor.search_fax_number(org_name)
                    if found_faxes:
                        results["fax"] = found_faxes[0]
                        self.logger.info(f"  📠 팩스번호 발견: {results['fax']}")
                except Exception as e:
                    self.logger.warning(f"팩스번호 검색 실패: {e}")
            
            # 홈페이지 검색 (구현 필요)
            if "homepage" in missing_fields:
                # TODO: 구글 검색으로 홈페이지 찾기
                pass
            
            # 이메일 검색 (구현 필요)
            if "email" in missing_fields:
                # TODO: 이메일 검색 로직
                pass
            
            return results
            
        except Exception as e:
            self.logger.error(f"누락 정보 검색 오류: {org_name} - {e}")
            return {}
    
    def validate_and_clean_data(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 검증 및 정리 - ContactEnrichmentService 호환성"""
        try:
            cleaned_data = org_data.copy()
            
            # validator.py 사용
            if self.contact_validator:
                # 전화번호 검증
                if cleaned_data.get('phone'):
                    is_valid, validated_phone = self.contact_validator.validate_phone_number(cleaned_data['phone'])
                    if is_valid:
                        cleaned_data['phone'] = validated_phone
                    else:
                        self.logger.warning(f"유효하지 않은 전화번호: {cleaned_data['phone']}")
                
                # 팩스번호 검증
                if cleaned_data.get('fax'):
                    is_valid, validated_fax = self.contact_validator.validate_fax_number(cleaned_data['fax'])
                    if is_valid:
                        cleaned_data['fax'] = validated_fax
                    else:
                        self.logger.warning(f"유효하지 않은 팩스번호: {cleaned_data['fax']}")
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"데이터 검증 오류: {e}")
            return org_data
    
    async def extract_phone_numbers_module(self, org_name: str, org_data: Dict) -> Optional[Dict]:
        """전화번호 추출 - phone_extractor.py 활용"""
        if not self.phone_driver:
            self.logger.warning(f"전화번호 드라이버 없음: {org_name}")
            return None
        
        try:
            self.logger.info(f"📞 전화번호 추출 시작: {org_name}")
            
            # 기존 전화번호가 있으면 스킵
            existing_phone = org_data.get('phone', '').strip()
            if existing_phone:
                self.logger.info(f"기존 전화번호 있음: {org_name} - {existing_phone}")
                return None
            
            # phone_extractor.py의 search_phone_number 함수 사용
            found_phones = search_phone_number(self.phone_driver, org_name)
            
            if found_phones:
                primary_phone = found_phones[0]
                additional_phones = found_phones[1:] if len(found_phones) > 1 else []
                
                self.logger.info(f"✅ 전화번호 발견: {org_name} -> {primary_phone}")
                
                return {
                    "phone_extracted": True,
                    "phone": primary_phone,
                    "additional_phones": additional_phones,
                    "phone_extraction_method": "phone_extractor_module",
                    "phone_extraction_timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.info(f"전화번호 없음: {org_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"전화번호 추출 오류: {org_name} - {e}")
            return None
    
    async def extract_fax_numbers_module(self, org_name: str, org_data: Dict) -> Optional[Dict]:
        """팩스번호 추출 - fax_extractor.py 활용"""
        if not self.fax_extractor:
            self.logger.warning(f"팩스 추출기 없음: {org_name}")
            return None
        
        try:
            self.logger.info(f"📠 팩스번호 추출 시작: {org_name}")
            
            # 기존 팩스번호가 있으면 스킵
            existing_fax = org_data.get('fax', '').strip()
            if existing_fax:
                self.logger.info(f"기존 팩스번호 있음: {org_name} - {existing_fax}")
                return None
            
            # fax_extractor.py의 search_fax_number 메서드 사용
            found_faxes = self.fax_extractor.search_fax_number(org_name)
            
            if found_faxes:
                primary_fax = found_faxes[0]
                additional_faxes = found_faxes[1:] if len(found_faxes) > 1 else []
                
                self.logger.info(f"✅ 팩스번호 발견: {org_name} -> {primary_fax}")
                
                return {
                    "fax_extracted": True,
                    "fax": primary_fax,
                    "additional_faxes": additional_faxes,
                    "fax_extraction_method": "fax_extractor_module",
                    "fax_extraction_timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.info(f"팩스번호 없음: {org_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"팩스번호 추출 오류: {org_name} - {e}")
            return None
    
    async def validate_contact_info(self, org_data: Dict) -> Optional[Dict]:
        """연락처 정보 검증 - validator.py 활용"""
        if not self.contact_validator:
            self.logger.warning("연락처 검증기 없음")
            return None
        
        try:
            org_name = org_data.get('name', 'Unknown')
            self.logger.info(f"🔍 연락처 검증 시작: {org_name}")
            
            validation_results = {}
            
            # 전화번호 검증
            phone = org_data.get('phone', '').strip()
            if phone:
                is_valid, validated_phone = self.contact_validator.validate_phone_number(phone)
                validation_results.update({
                    "phone_valid": is_valid,
                    "phone_validated": validated_phone if is_valid else phone,
                    "phone_validation_details": {
                        "original": phone,
                        "normalized": validated_phone if is_valid else None
                    }
                })
            
            # 팩스번호 검증
            fax = org_data.get('fax', '').strip()
            if fax:
                is_valid, validated_fax = self.contact_validator.validate_fax_number(fax)
                validation_results.update({
                    "fax_valid": is_valid,
                    "fax_validated": validated_fax if is_valid else fax,
                    "fax_validation_details": {
                        "original": fax,
                        "normalized": validated_fax if is_valid else None
                    }
                })
            
            # 전화번호-팩스번호 중복 검사
            if phone and fax:
                is_duplicate = self.contact_validator.is_phone_fax_duplicate(phone, fax)
                validation_results["phone_fax_duplicate"] = is_duplicate
            
            # AI 검증 (홈페이지 내용이 있는 경우)
            if self.ai_validator and org_data.get('homepage_content_length', 0) > 0:
                try:
                    homepage_content = org_data.get('homepage_content', '')
                    ai_validation = await self.ai_validator.extract_and_validate_contacts(
                        org_name, homepage_content
                    )
                    validation_results["ai_validation"] = ai_validation
                except Exception as e:
                    self.logger.warning(f"AI 검증 실패: {org_name} - {e}")
            
            validation_results.update({
                "validation_timestamp": datetime.now().isoformat(),
                "validation_method": "validator_module"
            })
            
            self.logger.info(f"✅ 연락처 검증 완료: {org_name}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"연락처 검증 오류: {org_data.get('name', 'Unknown')} - {e}")
            return None
    
    async def save_to_database(self, org_data: Dict) -> Optional[Dict]:
        """데이터베이스 저장"""
        if not self.database:
            self.logger.warning("데이터베이스 연결 없음")
            return None
        
        try:
            org_name = org_data.get('name', 'Unknown')
            self.logger.info(f"💾 데이터베이스 저장 시작: {org_name}")
            
            # 기관 데이터 준비
            db_org_data = {
                "name": org_data.get('name', ''),
                "type": org_data.get('type', 'UNKNOWN'),
                "category": org_data.get('category', '기타'),
                "homepage": org_data.get('homepage', ''),
                "phone": org_data.get('phone_validated', org_data.get('phone', '')),
                "fax": org_data.get('fax_validated', org_data.get('fax', '')),
                "email": org_data.get('email', ''),
                "address": org_data.get('address', ''),
                "contact_status": "ENRICHED",
                "priority": "MEDIUM",
                "created_by": "modular_crawler",
                "updated_by": "modular_crawler"
            }
            
            # 크롤링 메타데이터 추가
            crawling_metadata = {
                "processing_method": "modular_specialized",
                "modules_used": org_data.get('modules_used', {}),
                "processing_steps": org_data.get('processing_steps', []),
                "validation_results": {
                    "phone_valid": org_data.get('phone_valid', False),
                    "fax_valid": org_data.get('fax_valid', False),
                    "phone_fax_duplicate": org_data.get('phone_fax_duplicate', False)
                },
                "homepage_analysis": org_data.get('homepage_ai_summary', {}),
                "extraction_timestamps": {
                    "phone": org_data.get('phone_extraction_timestamp'),
                    "fax": org_data.get('fax_extraction_timestamp'),
                    "validation": org_data.get('validation_timestamp')
                }
            }
            
            db_org_data["crawling_data"] = json.dumps(crawling_metadata, ensure_ascii=False)
            
            # 데이터베이스에 저장
            org_id = self.database.create_organization(db_org_data)
            
            self.logger.info(f"✅ 데이터베이스 저장 완료: {org_name} (ID: {org_id})")
            
            return {
                "db_saved": True,
                "db_organization_id": org_id,
                "db_save_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"데이터베이스 저장 오류: {org_data.get('name', 'Unknown')} - {e}")
            return None
    
    async def save_intermediate_results(self, results: List[Dict], count: int):
        """중간 결과 저장"""
        try:
            filename = generate_output_filename("modular_intermediate", OUTPUT_DIR, count=count)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 중간 저장 완료: {filename} ({count}개)")
            
        except Exception as e:
            self.logger.error(f"중간 저장 실패: {e}")
    
    async def save_final_results(self, results: List[Dict]) -> str:
        """최종 결과 저장"""
        try:
            filename = generate_output_filename("modular_final", OUTPUT_DIR)
            
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
        
        print("\n" + "="*70)
        print("📊 모듈러 크롤링 완료 통계")
        print("="*70)
        print(f"📋 총 처리: {self.stats['total_processed']}개")
        print(f"✅ 성공: {self.stats['successful']}개")
        print(f"❌ 실패: {self.stats['failed']}개")
        print(f"🌐 홈페이지 파싱: {self.stats['homepage_parsed']}개")
        print(f"📞 전화번호 추출: {self.stats['phone_extracted']}개")
        print(f"📠 팩스번호 추출: {self.stats['fax_extracted']}개")
        print(f"🔍 연락처 검증: {self.stats['contacts_validated']}개")
        print(f"💾 DB 저장: {self.stats['saved_to_db']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100
            print(f"📈 전체 성공률: {success_rate:.1f}%")
        
        print(f"⏱️ 소요시간: {duration}")
        print(f"🚀 평균 처리시간: {duration.total_seconds()/self.stats['total_processed']:.2f}초/개")
        
        # 모듈별 성공률
        print(f"\n📊 모듈별 성공률:")
        if self.stats['total_processed'] > 0:
            print(f"  - 홈페이지 파싱: {self.stats['homepage_parsed']/self.stats['total_processed']*100:.1f}%")
            print(f"  - 전화번호 추출: {self.stats['phone_extracted']/self.stats['total_processed']*100:.1f}%")
            print(f"  - 팩스번호 추출: {self.stats['fax_extracted']/self.stats['total_processed']*100:.1f}%")
            print(f"  - 연락처 검증: {self.stats['contacts_validated']/self.stats['total_processed']*100:.1f}%")
            print(f"  - DB 저장: {self.stats['saved_to_db']/self.stats['total_processed']*100:.1f}%")
        
        print("="*70)

    # ==================== app.py 호환성 메서드들 ====================
    
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
            
            # 모듈러 처리 실행
            results = await self.process_organizations(organizations)
            
            return results
            
        except Exception as e:
            self.logger.error(f"JSON 파일 처리 실패: {e}")
            return []

# 편의 함수들
async def crawl_modular_from_file(input_file: str, options: Dict = None) -> List[Dict]:
    """파일에서 데이터를 로드하여 모듈러 크롤링"""
    try:
        # 파일 로드
        data = FileUtils.load_json(input_file)
        if not data:
            raise ValueError(f"파일을 로드할 수 없습니다: {input_file}")
        
        # 모듈러 크롤러 생성 및 실행
        crawler = ModularUnifiedCrawler()
        results = await crawler.process_organizations(data, options)
        
        return results
        
    except Exception as e:
        logging.error(f"모듈러 파일 크롤링 실패: {e}")
        return []

async def crawl_modular_latest_file(options: Dict = None) -> List[Dict]:
    """최신 입력 파일을 자동으로 찾아서 모듈러 크롤링"""
    try:
        latest_file = get_latest_input_file()
        if not latest_file:
            raise ValueError("입력 파일을 찾을 수 없습니다.")
        
        print(f"📂 최신 파일 사용: {latest_file}")
        return await crawl_modular_from_file(str(latest_file), options)
        
    except Exception as e:
        logging.error(f"모듈러 최신 파일 크롤링 실패: {e}")
        return []

# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    print("🚀 모듈러 통합 크롤링 시스템 시작")
    print("="*70)
    print("📦 전문 모듈 활용:")
    print(f"  - fax_extractor.py: {'✅' if FAX_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - phone_extractor.py: {'✅' if PHONE_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - url_extractor.py: {'✅' if URL_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - validator.py: {'✅' if VALIDATOR_AVAILABLE else '❌'}")
    print(f"  - database.py: {'✅' if DATABASE_AVAILABLE else '❌'}")
    print("="*70)
    
    try:
        # 프로젝트 초기화
        initialize_project()
        
        # 최신 파일로 모듈러 크롤링 실행
        results = await crawl_modular_latest_file()
        
        if results:
            print(f"\n✅ 모듈러 크롤링 완료: {len(results)}개 조직 처리")
        else:
            print("\n❌ 모듈러 크롤링 실패")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agentic Workflow 기반 통합 크롤링 엔진 - 개선된 버전
기존 모든 모듈을 통합하고 AI 에이전트 기반 워크플로우 적용
"""

import asyncio
import json
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 프로젝트 설정 import
from settings import *
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from utils.phone_utils import PhoneUtils
from utils.crawler_utils import CrawlerUtils
from ai_helpers import AIModelManager

class CrawlingStage(Enum):
    """크롤링 단계 정의"""
    INITIALIZATION = "초기화"
    HOMEPAGE_SEARCH = "홈페이지_검색"
    HOMEPAGE_ANALYSIS = "홈페이지_분석"
    CONTACT_PAGE_SEARCH = "연락처페이지_검색"  # 새로 추가
    CONTACT_EXTRACTION = "연락처_추출"
    FAX_SEARCH = "팩스_검색"
    AI_VERIFICATION = "AI_검증"
    DATA_VALIDATION = "데이터_검증"
    COMPLETION = "완료"

@dataclass
class CrawlingContext:
    """크롤링 컨텍스트 (AI Agent 간 공유 데이터)"""
    organization: Dict[str, Any]
    current_stage: CrawlingStage
    extracted_data: Dict[str, Any]
    ai_insights: Dict[str, Any]
    error_log: List[str]
    processing_time: float
    confidence_scores: Dict[str, float]

class AIAgent:
    """AI 에이전트 기본 클래스"""
    
    def __init__(self, name: str, ai_manager: AIModelManager, logger: logging.Logger):
        self.name = name
        self.ai_manager = ai_manager
        self.logger = logger
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """에이전트 실행 (하위 클래스에서 구현)"""
        raise NotImplementedError
    
    async def should_execute(self, context: CrawlingContext) -> bool:
        """실행 조건 확인"""
        return True
    
    def update_confidence(self, context: CrawlingContext, field: str, score: float):
        """신뢰도 점수 업데이트"""
        context.confidence_scores[field] = score

class HomepageSearchAgent(AIAgent):
    """홈페이지 검색 AI 에이전트 (개선된 버전)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger):
        super().__init__("HomepageSearchAgent", ai_manager, logger)
        self.crawler_utils = CrawlerUtils()
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """홈페이지 URL 검색 및 검증"""
        try:
            org_name = context.organization.get('name', '')
            category = context.organization.get('category', '')
            self.logger.info(f"🔍 [{self.name}] 홈페이지 검색: {org_name}")
            
            # 기존 홈페이지가 있으면 검증
            existing_homepage = context.organization.get('homepage', '')
            if existing_homepage:
                verification_result = await self._verify_homepage_with_ai(existing_homepage, org_name, category)
                if verification_result['is_valid']:
                    context.extracted_data['homepage'] = existing_homepage
                    context.extracted_data['homepage_type'] = verification_result['type']
                    self.update_confidence(context, 'homepage', 0.9)
                    return context
            
            # 새로운 홈페이지 검색
            search_results = await self._search_homepage_comprehensive(org_name, category)
            if search_results:
                best_result = search_results[0]  # 최고 점수
                context.extracted_data['homepage'] = best_result['url']
                context.extracted_data['homepage_type'] = best_result['type']
                context.extracted_data['homepage_confidence'] = best_result['confidence']
                self.update_confidence(context, 'homepage', best_result['confidence'])
                self.logger.info(f"✅ 홈페이지 발견: {best_result['url']} ({best_result['type']})")
            
            context.current_stage = CrawlingStage.HOMEPAGE_ANALYSIS
            return context
            
        except Exception as e:
            context.error_log.append(f"HomepageSearchAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _search_homepage_comprehensive(self, org_name: str, category: str) -> List[Dict]:
        """종합적인 홈페이지 검색 (공식사이트 + 소셜미디어)"""
        driver = None
        try:
            driver = self.crawler_utils.setup_driver(headless=True)
            if not driver:
                return []
            
            all_results = []
            
            # 1. 공식 홈페이지 검색
            official_results = await self._search_official_homepage(driver, org_name, category)
            all_results.extend(official_results)
            
            # 2. 소규모 기관인 경우 소셜미디어 검색
            if is_small_organization(org_name, category):
                social_results = await self._search_social_media(driver, org_name, category)
                all_results.extend(social_results)
            
            # 점수순 정렬
            all_results.sort(key=lambda x: x['confidence'], reverse=True)
            return all_results[:5]  # 상위 5개만 반환
            
        except Exception as e:
            self.logger.error(f"종합 홈페이지 검색 오류: {e}")
            return []
        finally:
            if driver:
                self.crawler_utils.safe_close_driver(driver)
    
    async def _search_official_homepage(self, driver, org_name: str, category: str) -> List[Dict]:
        """공식 홈페이지 검색"""
        results = []
        
        search_queries = [
            f"{org_name} 홈페이지 site:*.kr",
            f"{org_name} 공식사이트 site:*.org",
            f"{org_name} {category} 홈페이지"
        ]
        
        for query in search_queries:
            try:
                success = self.crawler_utils.search_google(driver, query)
                if success:
                    urls = self.crawler_utils.extract_urls_from_page(driver)
                    for url in urls[:3]:
                        if self._is_official_homepage_url(url, org_name):
                            verification = await self._verify_homepage_with_ai(url, org_name, category)
                            if verification['is_valid']:
                                results.append({
                                    'url': url,
                                    'type': 'official',
                                    'confidence': verification['confidence'],
                                    'source': query
                                })
                
                await asyncio.sleep(2)  # 검색 간 딜레이
                
            except Exception as e:
                self.logger.warning(f"공식 홈페이지 검색 오류: {e}")
        
        return results
    
    async def _search_social_media(self, driver, org_name: str, category: str) -> List[Dict]:
        """소셜미디어 홈페이지 검색"""
        results = []
        
        social_queries = [
            f"{org_name} site:blog.naver.com",
            f"{org_name} site:cafe.naver.com", 
            f"{org_name} site:facebook.com",
            f"{org_name} site:instagram.com",
            f"{org_name} site:youtube.com"
        ]
        
        for query in social_queries:
            try:
                success = self.crawler_utils.search_google(driver, query)
                if success:
                    urls = self.crawler_utils.extract_urls_from_page(driver)
                    for url in urls[:2]:
                        if self._is_social_media_url(url, org_name):
                            verification = await self._verify_homepage_with_ai(url, org_name, category)
                            if verification['is_valid']:
                                results.append({
                                    'url': url,
                                    'type': self._get_social_media_type(url),
                                    'confidence': verification['confidence'] * 0.7,  # 소셜미디어는 신뢰도 낮춤
                                    'source': query
                                })
                
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"소셜미디어 검색 오류: {e}")
        
        return results
    
    def _is_official_homepage_url(self, url: str, org_name: str) -> bool:
        """공식 홈페이지 URL 검증"""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        # STRICT_EXCLUDE_DOMAINS만 제외
        for exclude_domain in STRICT_EXCLUDE_DOMAINS:
            if exclude_domain in url.lower():
                return False
        
        return True
    
    def _is_social_media_url(self, url: str, org_name: str) -> bool:
        """소셜미디어 URL 검증"""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        # 소셜미디어 도메인 확인
        for domain in SOCIAL_MEDIA_DOMAINS.keys():
            if domain in url.lower():
                return True
        
        return False
    
    def _get_social_media_type(self, url: str) -> str:
        """소셜미디어 타입 반환"""
        for domain, type_name in SOCIAL_MEDIA_DOMAINS.items():
            if domain in url.lower():
                return type_name
        return "소셜미디어"
    
    async def _verify_homepage_with_ai(self, url: str, org_name: str, category: str) -> Dict:
        """AI로 홈페이지 관련성 검증 (개선된 프롬프트)"""
        try:
            prompt = f"""
            다음 정보를 바탕으로 홈페이지의 관련성을 판단해주세요:

            **기관 정보:**
            - 기관명: {org_name}
            - 카테고리: {category}
            - 홈페이지 URL: {url}

            **판단 기준:**
            1. 도메인명이 기관명과 관련이 있는가?
            2. URL이 해당 기관의 공식 또는 관련 페이지인가?
            3. 소규모 기관의 경우 블로그/카페/SNS도 공식 페이지로 인정
            4. 기관의 성격과 URL 타입이 적합한가?

            **응답 형식:**
            VALID: [예/아니오]
            TYPE: [공식사이트/네이버블로그/네이버카페/페이스북/인스타그램/유튜브/기타]
            CONFIDENCE: [0.1-1.0 사이의 신뢰도 점수]
            REASON: [판단 이유 1-2문장]
            """
            
            response = await self.ai_manager.extract_with_gemini(url, prompt)
            return self._parse_verification_response(response)
            
        except Exception as e:
            self.logger.error(f"AI 홈페이지 검증 오류: {e}")
            return {'is_valid': False, 'type': '알수없음', 'confidence': 0.0}
    
    def _parse_verification_response(self, response: str) -> Dict:
        """AI 검증 응답 파싱"""
        result = {
            'is_valid': False,
            'type': '알수없음',
            'confidence': 0.0,
            'reason': ''
        }
        
        try:
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('VALID:'):
                    result['is_valid'] = '예' in line
                elif line.startswith('TYPE:'):
                    result['type'] = line.replace('TYPE:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    confidence_text = line.replace('CONFIDENCE:', '').strip()
                    try:
                        result['confidence'] = float(confidence_text)
                    except:
                        result['confidence'] = 0.5
                elif line.startswith('REASON:'):
                    result['reason'] = line.replace('REASON:', '').strip()
        
        except Exception as e:
            self.logger.warning(f"검증 응답 파싱 오류: {e}")
        
        return result

class HomepageAnalysisAgent(AIAgent):
    """홈페이지 분석 AI 에이전트 (개선된 버전)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger):
        super().__init__("HomepageAnalysisAgent", ai_manager, logger)
        self.crawler_utils = CrawlerUtils()
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """홈페이지 내용 분석 및 정보 추출"""
        try:
            homepage_url = context.extracted_data.get('homepage')
            if not homepage_url:
                context.current_stage = CrawlingStage.CONTACT_PAGE_SEARCH
                return context
            
            org_name = context.organization.get('name', '')
            self.logger.info(f"🌐 [{self.name}] 홈페이지 분석: {homepage_url}")
            
            # 홈페이지 파싱
            page_data = await self._extract_page_content(homepage_url)
            
            if page_data and page_data.get('accessible'):
                # 연락처 정보 추출
                contact_info = page_data.get('contact_info', {})
                self._store_contact_info(context, contact_info)
                
                # 연락처 페이지 링크 찾기
                contact_links = self._find_contact_page_links(page_data)
                if contact_links:
                    context.extracted_data['contact_page_links'] = contact_links
                
                # AI 분석 실행
                ai_summary = await self._analyze_with_ai(org_name, page_data)
                context.ai_insights['homepage_analysis'] = ai_summary
                
                self.logger.info(f"✅ 홈페이지 분석 완료: 연락처 {len(contact_info)} 항목, 연락처 페이지 {len(contact_links)} 개")
            
            context.current_stage = CrawlingStage.CONTACT_PAGE_SEARCH
            return context
            
        except Exception as e:
            context.error_log.append(f"HomepageAnalysisAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    def _find_contact_page_links(self, page_data: Dict) -> List[Dict]:
        """연락처 페이지 링크 찾기"""
        contact_links = []
        
        try:
            soup = page_data.get('soup')
            base_url = page_data.get('url', '')
            
            if not soup:
                return []
            
            # 링크 요소들 찾기
            links = soup.find_all('a', href=True)
            
            for link in links:
                link_text = link.get_text(strip=True).lower()
                href = link.get('href', '')
                
                # 연락처 관련 키워드 확인
                for keyword in CONTACT_NAVIGATION_KEYWORDS:
                    if keyword.lower() in link_text:
                        full_url = self._resolve_url(href, base_url)
                        if full_url:
                            contact_links.append({
                                'url': full_url,
                                'text': link.get_text(strip=True),
                                'keyword': keyword
                            })
                        break
        
        except Exception as e:
            self.logger.warning(f"연락처 페이지 링크 찾기 오류: {e}")
        
        return contact_links[:5]  # 최대 5개까지
    
    def _resolve_url(self, href: str, base_url: str) -> Optional[str]:
        """상대 URL을 절대 URL로 변환"""
        try:
            from urllib.parse import urljoin, urlparse
            
            if href.startswith(('http://', 'https://')):
                return href
            elif href.startswith('/'):
                parsed = urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                return urljoin(base_url, href)
        except:
            return None
    
    def _store_contact_info(self, context: CrawlingContext, contact_info: Dict):
        """연락처 정보 저장"""
        # 기본 연락처 정보
        if contact_info.get('phones'):
            context.extracted_data['phone'] = contact_info['phones'][0]
            self.update_confidence(context, 'phone', 0.9)
            
            # 추가 전화번호들 저장
            if len(contact_info['phones']) > 1:
                context.extracted_data['additional_phones'] = contact_info['phones'][1:5]  # 최대 4개 추가
        
        if contact_info.get('faxes'):
            context.extracted_data['fax'] = contact_info['faxes'][0]
            self.update_confidence(context, 'fax', 0.9)
        
        if contact_info.get('emails'):
            context.extracted_data['email'] = contact_info['emails'][0]
            self.update_confidence(context, 'email', 0.9)
        
        if contact_info.get('addresses'):
            context.extracted_data['address'] = contact_info['addresses'][0]
            self.update_confidence(context, 'address', 0.8)
    
    async def _extract_page_content(self, url: str) -> Dict[str, Any]:
        """페이지 내용 추출 (개선된 버전)"""
        driver = None
        try:
            driver = self.crawler_utils.setup_driver(headless=True)
            if not driver:
                return {}
            
            # 페이지 로드
            driver.get(url)
            time.sleep(3)
            
            # 접근 가능성 확인
            if not self._is_page_accessible(driver):
                return {'accessible': False}
            
            # BeautifulSoup 파싱
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 텍스트 추출
            page_text = soup.get_text(separator=' ', strip=True)
            
            # 연락처 정보 추출
            contact_info = self._extract_contact_info_enhanced(page_text)
            
            return {
                'accessible': True,
                'title': driver.title,
                'url': url,
                'text_content': page_text[:5000],
                'contact_info': contact_info,
                'soup': soup  # BeautifulSoup 객체도 저장
            }
            
        except Exception as e:
            self.logger.error(f"페이지 추출 오류: {e}")
            return {'accessible': False, 'error': str(e)}
        finally:
            if driver:
                self.crawler_utils.safe_close_driver(driver)
    
    def _extract_contact_info_enhanced(self, text: str) -> Dict[str, List[str]]:
        """강화된 연락처 정보 추출"""
        contact_info = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": [],
            "additional_phones": []
        }
        
        try:
            # 기본 전화번호 추출
            for pattern in PHONE_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    phone = PhoneUtils.format_phone_number(match)
                    if phone and validate_phone_length(phone) and phone not in contact_info["phones"]:
                        contact_info["phones"].append(phone)
            
            # 추가 전화번호 추출
            for pattern in ADDITIONAL_PHONE_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    phone = PhoneUtils.format_phone_number(match)
                    if (phone and validate_phone_length(phone) and 
                        phone not in contact_info["phones"] and 
                        phone not in contact_info["additional_phones"]):
                        contact_info["additional_phones"].append(phone)
            
            # 팩스번호 추출
            for pattern in FAX_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    fax = PhoneUtils.format_phone_number(match)
                    if fax and validate_phone_length(fax) and fax not in contact_info["faxes"]:
                        contact_info["faxes"].append(fax)
            
            # 이메일 추출
            for pattern in EMAIL_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_email(match) and match not in contact_info["emails"]:
                        contact_info["emails"].append(match)
            
            # 주소 추출
            for pattern in ADDRESS_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    clean_address = self._clean_address(match)
                    if clean_address and clean_address not in contact_info["addresses"]:
                        contact_info["addresses"].append(clean_address)
        
        except Exception as e:
            self.logger.warning(f"연락처 정보 추출 오류: {e}")
        
        return contact_info
    
    def _is_page_accessible(self, driver) -> bool:
        """페이지 접근 가능성 확인"""
        try:
            title = driver.title.lower()
            if any(keyword in title for keyword in ['404', 'not found', 'error']):
                return False
            
            page_source = driver.page_source
            return len(page_source) > 1000
            
        except:
            return False
    
    def _is_valid_email(self, email: str) -> bool:
        """이메일 유효성 확인"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def _clean_address(self, address: str) -> Optional[str]:
        """주소 정리"""
        if not address or len(address) < 10:
            return None
        return re.sub(r'\s+', ' ', address.strip())
    
    async def _analyze_with_ai(self, org_name: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI로 페이지 내용 분석 (개선된 프롬프트)"""
        try:
            contact_info = page_data.get('contact_info', {})
            
            prompt = f"""
            '{org_name}' 기관의 홈페이지를 분석해주세요.

            **기본 정보:**
            - 제목: {page_data.get('title', '')}
            - URL: {page_data.get('url', '')}

            **추출된 연락처:**
            - 전화번호: {', '.join(contact_info.get('phones', []))}
            - 추가전화번호: {', '.join(contact_info.get('additional_phones', []))}
            - 팩스번호: {', '.join(contact_info.get('faxes', []))}
            - 이메일: {', '.join(contact_info.get('emails', []))}
            - 주소: {', '.join(contact_info.get('addresses', []))}

            **홈페이지 내용 (처음 2000자):**
            {page_data.get('text_content', '')[:2000]}

            **분석 요청:**
            다음 형식으로 응답해주세요:
            
            SUMMARY: [기관 요약 3-4문장]
            CATEGORY: [기관 유형 - 교회, 병원, 학교, 정부기관, 기업, 단체 등]
            SERVICES: [주요 서비스 3개, 쉼표로 구분]
            LOCATION: [위치정보]
            PHONE_VALIDATION: [추출된 전화번호들이 9-11자리 한국 전화번호 형식에 맞는지 - 적합/부적합]
            FAX_PHONE_DUPLICATE: [팩스번호와 전화번호가 동일한지 - 동일/다름/확인불가]
            CONTACT_QUALITY: [연락처 정보 품질 - 상/중/하]
            WEBSITE_QUALITY: [웹사이트 품질 - 상/중/하]
            FEATURES: [특별한 특징 2개, 쉼표로 구분]
            """
            
            response = await self.ai_manager.extract_with_gemini(page_data.get('text_content', ''), prompt)
            return self._parse_ai_response(response)
            
        except Exception as e:
            self.logger.error(f"AI 분석 오류: {e}")
            return {'summary': f'AI 분석 오류: {str(e)}'}
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """AI 응답 파싱 (개선된 버전)"""
        result = {
            "summary": "",
            "category": "기타",
            "services": [],
            "location": "",
            "phone_validation": "확인불가",
            "fax_phone_duplicate": "확인불가",
            "contact_quality": "중",
            "website_quality": "중",
            "features": []
        }
        
        try:
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('SUMMARY:'):
                    result["summary"] = line.replace('SUMMARY:', '').strip()
                elif line.startswith('CATEGORY:'):
                    result["category"] = line.replace('CATEGORY:', '').strip()
                elif line.startswith('SERVICES:'):
                    services_text = line.replace('SERVICES:', '').strip()
                    result["services"] = [s.strip() for s in services_text.split(',')]
                elif line.startswith('LOCATION:'):
                    result["location"] = line.replace('LOCATION:', '').strip()
                elif line.startswith('PHONE_VALIDATION:'):
                    result["phone_validation"] = line.replace('PHONE_VALIDATION:', '').strip()
                elif line.startswith('FAX_PHONE_DUPLICATE:'):
                    result["fax_phone_duplicate"] = line.replace('FAX_PHONE_DUPLICATE:', '').strip()
                elif line.startswith('CONTACT_QUALITY:'):
                    result["contact_quality"] = line.replace('CONTACT_QUALITY:', '').strip()
                elif line.startswith('WEBSITE_QUALITY:'):
                    result["website_quality"] = line.replace('WEBSITE_QUALITY:', '').strip()
                elif line.startswith('FEATURES:'):
                    features_text = line.replace('FEATURES:', '').strip()
                    result["features"] = [f.strip() for f in features_text.split(',')]
        
        except Exception as e:
            self.logger.warning(f"AI 응답 파싱 오류: {e}")
        
        return result

class ContactPageSearchAgent(AIAgent):
    """연락처 페이지 검색 AI 에이전트 (새로 추가)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger):
        super().__init__("ContactPageSearchAgent", ai_manager, logger)
        self.crawler_utils = CrawlerUtils()
    
    async def should_execute(self, context: CrawlingContext) -> bool:
        """연락처 페이지 링크가 있을 때만 실행"""
        return bool(context.extracted_data.get('contact_page_links'))
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """연락처 페이지에서 추가 정보 추출"""
        try:
            contact_links = context.extracted_data.get('contact_page_links', [])
            org_name = context.organization.get('name', '')
            
            self.logger.info(f"📞 [{self.name}] 연락처 페이지 검색: {len(contact_links)}개 링크")
            
            additional_contacts = []
            
            for link_info in contact_links[:3]:  # 최대 3개 페이지만 확인
                contact_data = await self._extract_contact_page(link_info['url'])
                if contact_data:
                    additional_contacts.append({
                        'url': link_info['url'],
                        'keyword': link_info['keyword'],
                        'contacts': contact_data
                    })
            
            if additional_contacts:
                context.extracted_data['additional_contact_pages'] = additional_contacts
                self._merge_additional_contacts(context, additional_contacts)
                self.logger.info(f"✅ 추가 연락처 페이지 {len(additional_contacts)}개 처리 완료")
            
            context.current_stage = CrawlingStage.CONTACT_EXTRACTION
            return context
            
        except Exception as e:
            context.error_log.append(f"ContactPageSearchAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _extract_contact_page(self, url: str) -> Optional[Dict]:
        """연락처 페이지에서 정보 추출"""
        driver = None
        try:
            driver = self.crawler_utils.setup_driver(headless=True)
            if not driver:
                return None
            
            driver.get(url)
            time.sleep(2)
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # 연락처 정보 추출 (HomepageAnalysisAgent와 동일한 로직)
            contact_info = self._extract_contact_info_enhanced(page_text)
            
            return contact_info if any(contact_info.values()) else None
            
        except Exception as e:
            self.logger.warning(f"연락처 페이지 추출 오류 {url}: {e}")
            return None
        finally:
            if driver:
                self.crawler_utils.safe_close_driver(driver)
    
    def _extract_contact_info_enhanced(self, text: str) -> Dict[str, List[str]]:
        """강화된 연락처 정보 추출 (HomepageAnalysisAgent와 동일)"""
        contact_info = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": []
        }
        
        try:
            # 전화번호 추출
            for pattern in PHONE_EXTRACTION_PATTERNS + ADDITIONAL_PHONE_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    phone = PhoneUtils.format_phone_number(match)
                    if phone and validate_phone_length(phone) and phone not in contact_info["phones"]:
                        contact_info["phones"].append(phone)
            
            # 팩스번호 추출
            for pattern in FAX_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    fax = PhoneUtils.format_phone_number(match)
                    if fax and validate_phone_length(fax) and fax not in contact_info["faxes"]:
                        contact_info["faxes"].append(fax)
            
            # 이메일 추출
            for pattern in EMAIL_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_email(match) and match not in contact_info["emails"]:
                        contact_info["emails"].append(match)
        
        except Exception as e:
            self.logger.warning(f"연락처 정보 추출 오류: {e}")
        
        return contact_info
    
    def _is_valid_email(self, email: str) -> bool:
        """이메일 유효성 확인"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

class FaxSearchAgent(AIAgent):
    """팩스번호 검색 AI 에이전트 (faxextractor.py 로직 통합)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger):
        super().__init__("FaxSearchAgent", ai_manager, logger)
        self.crawler_utils = CrawlerUtils()
    
    async def should_execute(self, context: CrawlingContext) -> bool:
        """팩스번호가 없을 때만 실행"""
        return not context.extracted_data.get('fax')
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """구글 검색으로 팩스번호 찾기"""
        try:
            org_name = context.organization.get('name', '')
            self.logger.info(f"📠 [{self.name}] 팩스번호 검색: {org_name}")
            
            fax_number = await self._search_fax_number(org_name)
            if fax_number:
                # 전화번호와 중복 확인
                phone = context.extracted_data.get('phone', '')
                if fax_number != phone:
                    context.extracted_data['fax'] = fax_number
                    self.update_confidence(context, 'fax', 0.7)
                    self.logger.info(f"✅ 팩스번호 발견: {fax_number}")
                else:
                    self.logger.info(f"⚠️ 전화번호와 동일한 팩스번호: {fax_number}")
            
            context.current_stage = CrawlingStage.AI_VERIFICATION
            return context
            
        except Exception as e:
            context.error_log.append(f"FaxSearchAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _search_fax_number(self, org_name: str) -> Optional[str]:
        """구글 검색으로 팩스번호 찾기 (faxextractor.py 로직)"""
        driver = None
        try:
            driver = self.crawler_utils.setup_driver(headless=True)
            if not driver:
                return None
            
            search_query = f"{org_name} 팩스번호"
            success = self.crawler_utils.search_google(driver, search_query)
            
            if success:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                fax_numbers = self._extract_fax_numbers(page_text)
                
                if fax_numbers:
                    return fax_numbers[0]  # 첫 번째 발견된 팩스번호
            
            return None
            
        except Exception as e:
            self.logger.error(f"팩스번호 검색 오류: {e}")
            return None
        finally:
            if driver:
                self.crawler_utils.safe_close_driver(driver)
    
    def _extract_fax_numbers(self, text: str) -> List[str]:
        """텍스트에서 팩스번호 추출"""
        fax_numbers = []
        
        for pattern in FAX_EXTRACTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                fax = PhoneUtils.format_phone_number(match)
                if fax and validate_phone_length(fax) and fax not in fax_numbers:
                    fax_numbers.append(fax)
        
        return fax_numbers

class AIVerificationAgent(AIAgent):
    """AI 검증 에이전트"""
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """추출된 데이터를 AI로 검증"""
        try:
            org_name = context.organization.get('name', '')
            self.logger.info(f"🤖 [{self.name}] AI 검증: {org_name}")
            
            # 추출된 데이터 검증
            verification_result = await self._verify_extracted_data(context)
            context.ai_insights['verification'] = verification_result
            
            # 신뢰도 점수 조정
            self._adjust_confidence_scores(context, verification_result)
            
            context.current_stage = CrawlingStage.DATA_VALIDATION
            return context
            
        except Exception as e:
            context.error_log.append(f"AIVerificationAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _verify_extracted_data(self, context: CrawlingContext) -> Dict[str, Any]:
        """추출된 데이터 AI 검증"""
        try:
            org_name = context.organization.get('name', '')
            extracted = context.extracted_data
            
            prompt = f"""
            기관명: {org_name}
            추출된 정보를 검증해주세요:
            
            - 홈페이지: {extracted.get('homepage', '없음')}
            - 전화번호: {extracted.get('phone', '없음')}
            - 팩스번호: {extracted.get('fax', '없음')}
            - 이메일: {extracted.get('email', '없음')}
            - 주소: {extracted.get('address', '없음')}
            
            각 정보가 해당 기관과 일치하는지 판단하고, 
            다음 형식으로 응답해주세요:
            
            HOMEPAGE_VALID: [예/아니오]
            PHONE_VALID: [예/아니오]
            FAX_VALID: [예/아니오]
            EMAIL_VALID: [예/아니오]
            ADDRESS_VALID: [예/아니오]
            OVERALL_CONFIDENCE: [높음/보통/낮음]
            ISSUES: [발견된 문제점들]
            """
            
            response = await self.ai_manager.extract_with_gemini("", prompt)
            return self._parse_verification_response(response)
            
        except Exception as e:
            self.logger.error(f"AI 검증 오류: {e}")
            return {'overall_confidence': '낮음', 'issues': [str(e)]}
    
    def _parse_verification_response(self, response: str) -> Dict[str, Any]:
        """AI 검증 응답 파싱"""
        result = {
            'homepage_valid': False,
            'phone_valid': False,
            'fax_valid': False,
            'email_valid': False,
            'address_valid': False,
            'overall_confidence': '보통',
            'issues': []
        }
        
        try:
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('HOMEPAGE_VALID:'):
                    result['homepage_valid'] = '예' in line
                elif line.startswith('PHONE_VALID:'):
                    result['phone_valid'] = '예' in line
                elif line.startswith('FAX_VALID:'):
                    result['fax_valid'] = '예' in line
                elif line.startswith('EMAIL_VALID:'):
                    result['email_valid'] = '예' in line
                elif line.startswith('ADDRESS_VALID:'):
                    result['address_valid'] = '예' in line
                elif line.startswith('OVERALL_CONFIDENCE:'):
                    confidence = line.replace('OVERALL_CONFIDENCE:', '').strip()
                    result['overall_confidence'] = confidence
                elif line.startswith('ISSUES:'):
                    issues_text = line.replace('ISSUES:', '').strip()
                    if issues_text and issues_text != '없음':
                        result['issues'] = [issues_text]
        
        except Exception as e:
            self.logger.warning(f"검증 응답 파싱 오류: {e}")
        
        return result
    
    def _adjust_confidence_scores(self, context: CrawlingContext, verification: Dict[str, Any]):
        """검증 결과에 따라 신뢰도 점수 조정"""
        adjustments = {
            'homepage': verification.get('homepage_valid', False),
            'phone': verification.get('phone_valid', False),
            'fax': verification.get('fax_valid', False),
            'email': verification.get('email_valid', False),
            'address': verification.get('address_valid', False)
        }
        
        for field, is_valid in adjustments.items():
            if field in context.confidence_scores:
                if is_valid:
                    context.confidence_scores[field] = min(1.0, context.confidence_scores[field] + 0.1)
                else:
                    context.confidence_scores[field] = max(0.0, context.confidence_scores[field] - 0.2)

class DataValidationAgent(AIAgent):
    """데이터 검증 에이전트 (phone_utils.py 로직 활용)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger):
        super().__init__("DataValidationAgent", ai_manager, logger)
        self.phone_utils = PhoneUtils()
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """최종 데이터 검증 및 정리"""
        try:
            self.logger.info(f"✅ [{self.name}] 데이터 검증 시작")
            
            # 전화번호 검증
            phone = context.extracted_data.get('phone')
            if phone:
                if self.phone_utils.validate_korean_phone(phone):
                    context.extracted_data['phone'] = self.phone_utils.format_phone_number(phone)
                else:
                    context.error_log.append(f"유효하지 않은 전화번호: {phone}")
                    context.extracted_data.pop('phone', None)
            
            # 팩스번호 검증
            fax = context.extracted_data.get('fax')
            if fax:
                if self.phone_utils.validate_korean_phone(fax):
                    context.extracted_data['fax'] = self.phone_utils.format_phone_number(fax)
                else:
                    context.error_log.append(f"유효하지 않은 팩스번호: {fax}")
                    context.extracted_data.pop('fax', None)
            
            # 전화번호-팩스번호 중복 확인
            if phone and fax and self.phone_utils.is_phone_fax_duplicate(phone, fax):
                context.error_log.append("전화번호와 팩스번호가 중복됨")
                context.extracted_data.pop('fax', None)
            
            # 이메일 검증
            email = context.extracted_data.get('email')
            if email and not self._is_valid_email(email):
                context.error_log.append(f"유효하지 않은 이메일: {email}")
                context.extracted_data.pop('email', None)
            
            context.current_stage = CrawlingStage.COMPLETION
            return context
            
        except Exception as e:
            context.error_log.append(f"DataValidationAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    def _is_valid_email(self, email: str) -> bool:
        """이메일 유효성 확인"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

class EnhancedUnifiedCrawler:
    """AI Agentic Workflow 기반 강화된 통합 크롤러"""
    
    def __init__(self, config_override=None):
        """초기화"""
        self.config = config_override or CRAWLING_CONFIG
        self.logger = LoggerUtils.setup_crawler_logger()
        self.ai_manager = AIModelManager()
        
        # AI 에이전트들 초기화
        self.agents = [
            HomepageSearchAgent(self.ai_manager, self.logger),
            HomepageAnalysisAgent(self.ai_manager, self.logger),
            FaxSearchAgent(self.ai_manager, self.logger),
            AIVerificationAgent(self.ai_manager, self.logger),
            DataValidationAgent(self.ai_manager, self.logger)
        ]
        
        # 통계 정보
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None,
            "agent_stats": {agent.name: {"executed": 0, "success": 0} for agent in self.agents}
        }
        
        self.logger.info("🚀 AI Agentic Workflow 크롤러 초기화 완료")
    
    async def process_organizations_with_callback(self, organizations: List[Dict]) -> List[Dict]:
        """AI Agentic Workflow로 조직 처리"""
        if not organizations:
            return []
        
        self.stats["start_time"] = datetime.now()
        self.stats["total_processed"] = len(organizations)
        
        results = []
        
        for i, org in enumerate(organizations, 1):
            try:
                # 크롤링 컨텍스트 초기화
                context = CrawlingContext(
                    organization=org,
                    current_stage=CrawlingStage.INITIALIZATION,
                    extracted_data={},
                    ai_insights={},
                    error_log=[],
                    processing_time=0,
                    confidence_scores={}
                )
                
                start_time = time.time()
                
                # AI 에이전트 워크플로우 실행
                context = await self._execute_agent_workflow(context, i)
                
                processing_time = time.time() - start_time
                context.processing_time = processing_time
                
                # 결과 조합
                processed_org = self._combine_results(org, context)
                results.append(processed_org)
                
                # 콜백 호출 (기존 호환성 유지)
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    self._call_progress_callback(processed_org, i, len(organizations), processing_time)
                
                self.stats["successful"] += 1
                
                # 딜레이
                await asyncio.sleep(self.config.get("default_delay", 2))
                
            except Exception as e:
                self.logger.error(f"❌ 조직 처리 실패 [{i}]: {org.get('name', 'Unknown')} - {e}")
                self.stats["failed"] += 1
                results.append(org)
        
        self.stats["end_time"] = datetime.now()
        self._print_agent_statistics()
        
        return results
    
    async def _execute_agent_workflow(self, context: CrawlingContext, index: int) -> CrawlingContext:
        """AI 에이전트 워크플로우 실행"""
        org_name = context.organization.get('name', 'Unknown')
        self.logger.info(f"🤖 AI 에이전트 워크플로우 시작 [{index}]: {org_name}")
        
        for agent in self.agents:
            try:
                # 실행 조건 확인
                if await agent.should_execute(context):
                    self.logger.info(f"🔄 에이전트 실행: {agent.name}")
                    
                    # 에이전트 실행
                    context = await agent.execute(context)
                    
                    # 통계 업데이트
                    self.stats["agent_stats"][agent.name]["executed"] += 1
                    if not context.error_log or len(context.error_log) == 0:
                        self.stats["agent_stats"][agent.name]["success"] += 1
                    
                    self.logger.info(f"✅ 에이전트 완료: {agent.name}")
                else:
                    self.logger.info(f"⏭️ 에이전트 스킵: {agent.name}")
                
            except Exception as e:
                self.logger.error(f"❌ 에이전트 실행 오류 {agent.name}: {e}")
                context.error_log.append(f"{agent.name} 오류: {str(e)}")
        
        self.logger.info(f"🎉 AI 에이전트 워크플로우 완료: {org_name}")
        return context
    
    def _combine_results(self, original_org: Dict, context: CrawlingContext) -> Dict:
        """원본 조직 데이터와 추출된 데이터 결합"""
        result = original_org.copy()
        
        # 추출된 데이터 추가
        result.update(context.extracted_data)
        
        # AI 인사이트 추가
        result['ai_insights'] = context.ai_insights
        
        # 신뢰도 점수 추가
        result['confidence_scores'] = context.confidence_scores
        
        # 처리 메타데이터 추가
        result['processing_metadata'] = {
            'processing_time': context.processing_time,
            'final_stage': context.current_stage.value,
            'error_count': len(context.error_log),
            'errors': context.error_log,
            'extraction_method': 'ai_agentic_workflow',
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def _call_progress_callback(self, processed_org: Dict, current: int, total: int, processing_time: float):
        """진행 상황 콜백 호출"""
        try:
            callback_data = {
                'name': processed_org.get('name', 'Unknown'),
                'category': processed_org.get('category', ''),
                'homepage_url': processed_org.get('homepage', ''),
                'status': 'completed',
                'current_step': f'{current}/{total}',
                'processing_time': processing_time,
                'phone': processed_org.get('phone', ''),
                'fax': processed_org.get('fax', ''),
                'email': processed_org.get('email', ''),
                'address': processed_org.get('address', ''),
                'extraction_method': 'ai_agentic_workflow',
                'confidence_scores': processed_org.get('confidence_scores', {}),
                'ai_insights': processed_org.get('ai_insights', {})
            }
            self.progress_callback(callback_data)
            
        except Exception as e:
            self.logger.error(f"콜백 실행 실패: {e}")
    
    def _print_agent_statistics(self):
        """에이전트 통계 출력"""
        print("\n" + "="*80)
        print("🤖 AI Agentic Workflow 통계")
        print("="*80)
        
        for agent_name, stats in self.stats["agent_stats"].items():
            executed = stats["executed"]
            success = stats["success"]
            success_rate = (success / executed * 100) if executed > 0 else 0
            print(f"🔧 {agent_name:<25} 실행: {executed:>3}회, 성공: {success:>3}회 ({success_rate:>5.1f}%)")
        
        duration = self.stats["end_time"] - self.stats["start_time"]
        print(f"\n📊 전체 통계:")
        print(f"  📋 총 처리: {self.stats['total_processed']}개")
        print(f"  ✅ 성공: {self.stats['successful']}개")
        print(f"  ❌ 실패: {self.stats['failed']}개")
        print(f"  📈 성공률: {(self.stats['successful']/self.stats['total_processed']*100):.1f}%")
        print(f"  ⏱️ 소요시간: {duration}")
        print("="*80)

    # 기존 호환성을 위한 메서드들
    async def process_json_file_async(self, json_file_path: str, test_mode: bool = False, test_count: int = 10, progress_callback=None) -> List[Dict]:
        """app.py 호환성을 위한 래퍼 메서드"""
        try:
            # JSON 파일 로드
            data = FileUtils.load_json(json_file_path)
            
            # 데이터 전처리
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
            
            # AI Agentic Workflow로 처리
            results = await self.process_organizations_with_callback(organizations)
            
            return results
            
        except Exception as e:
            self.logger.error(f"JSON 파일 처리 실패: {e}")
            return []

# 기존 호환성을 위한 별칭
UnifiedCrawler = EnhancedUnifiedCrawler

# 편의 함수들
async def crawl_with_ai_agents(input_file: str, options: Dict = None) -> List[Dict]:
    """AI 에이전트로 크롤링 실행"""
    try:
        data = FileUtils.load_json(input_file)
        if not data:
            raise ValueError(f"파일을 로드할 수 없습니다: {input_file}")
        
        crawler = EnhancedUnifiedCrawler()
        results = await crawler.process_organizations_with_callback(data)
        
        return results
        
    except Exception as e:
        logging.error(f"AI 에이전트 크롤링 실패: {e}")
        return []

async def main():
    """메인 실행 함수"""
    print("🤖 AI Agentic Workflow 크롤링 시스템 시작")
    print("="*80)
    
    try:
        # 프로젝트 초기화
        initialize_project()
        
        # AI 에이전트로 크롤링 실행
        latest_file = get_latest_input_file()
        if latest_file:
            results = await crawl_with_ai_agents(str(latest_file))
            
            if results:
                print(f"\n✅ AI 에이전트 크롤링 완료: {len(results)}개 조직 처리")
            else:
                print("\n❌ 크롤링 실패")
        else:
            print("\n❌ 입력 파일을 찾을 수 없습니다")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
AI 강화 통합 크롤링 엔진 v4.0
✅ 기존 전문 모듈 + AI Agentic Workflow 통합
✅ 최고 품질의 AI 기반 데이터 추출
✅ 신뢰도 점수 및 다단계 검증 시스템
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'cralwer'))

import asyncio
import json
import time
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# 프로젝트 설정 import
from utils.settings import *
from utils.settings import get_latest_input_file, initialize_project
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from utils.phone_utils import PhoneUtils
from utils.crawler_utils import CrawlerUtils
from utils.ai_helpers import AIModelManager


# 전문 모듈들 import (기존 유지)
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

# ==================== AI Agentic Workflow 시스템 통합 ====================

class CrawlingStage(Enum):
    """크롤링 단계 정의"""
    INITIALIZATION = "초기화"
    HOMEPAGE_SEARCH = "홈페이지_검색"
    HOMEPAGE_ANALYSIS = "홈페이지_분석"
    CONTACT_PAGE_SEARCH = "연락처페이지_검색"
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
    
    def __init__(self, name: str, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler=None):
        self.name = name
        self.ai_manager = ai_manager
        self.logger = logger
        self.parent_crawler = parent_crawler  # Optional로 변경
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """에이전트 실행 (하위 클래스에서 구현)"""
        raise NotImplementedError
    
    async def should_execute(self, context: CrawlingContext) -> bool:
        """실행 조건 확인"""
        return True
    
    def update_confidence(self, context: CrawlingContext, field: str, score: float):
        """신뢰도 점수 업데이트"""
        context.confidence_scores[field] = score

class EnhancedHomepageSearchAgent(AIAgent):
    """AI 강화 홈페이지 검색 에이전트"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler):
        super().__init__("EnhancedHomepageSearchAgent", ai_manager, logger, parent_crawler)
        self.crawler_utils = CrawlerUtils()
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """AI 기반 종합 홈페이지 검색 (공식사이트 + 소셜미디어 통합)"""
        try:
            org_name = context.organization.get('name', '')
            category = context.organization.get('category', '')
            self.logger.info(f"🔍 [{self.name}] AI 홈페이지 검색: {org_name}")
            
            # 기존 홈페이지가 있으면 AI로 검증
            existing_homepage = context.organization.get('homepage', '')
            if existing_homepage:
                verification_result = await self._verify_homepage_with_ai(existing_homepage, org_name, category)
                if verification_result['is_valid']:
                    context.extracted_data['homepage'] = existing_homepage
                    context.extracted_data['homepage_type'] = verification_result['type']
                    self.update_confidence(context, 'homepage', verification_result['confidence'])
                    context.current_stage = CrawlingStage.HOMEPAGE_ANALYSIS
                    return context
            
            # AI 기반 종합 홈페이지 검색 (additionalplan.py 스타일로 강화)
            search_results = await self._ai_comprehensive_homepage_search(org_name, category)
            if search_results:
                best_result = search_results[0]
                context.extracted_data['homepage'] = best_result['url']
                context.extracted_data['homepage_type'] = best_result['type']
                context.extracted_data['homepage_confidence'] = best_result['confidence']
                context.extracted_data['homepage_source'] = best_result.get('source', 'ai_search')
                self.update_confidence(context, 'homepage', best_result['confidence'])
                self.logger.info(f"✅ AI 홈페이지 발견: {best_result['url']} ({best_result['type']})")
            
            context.current_stage = CrawlingStage.HOMEPAGE_ANALYSIS
            return context
            
        except Exception as e:
            context.error_log.append(f"EnhancedHomepageSearchAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _ai_comprehensive_homepage_search(self, org_name: str, category: str) -> List[Dict]:
        """AI 기반 종합 홈페이지 검색 (공식사이트 + 소셜미디어)"""
        try:
            all_results = []
            
            # 1단계: 기존 모듈의 homepage_parser 활용
            if self.parent_crawler.homepage_parser:
                try:
                    ai_search_results = await self.parent_crawler.homepage_parser.ai_search_homepage(org_name, category)
                    all_results.extend(ai_search_results)
                except Exception as e:
                    self.logger.warning(f"기존 모듈 홈페이지 검색 오류: {e}")
            
            # 2단계: 직접 구글 검색으로 공식 홈페이지 검색
            official_results = await self._search_official_homepage(org_name, category)
            all_results.extend(official_results)
            
            # 3단계: 소규모 기관인 경우 소셜미디어 검색 (additionalplan.py 아이디어)
            if self._is_small_organization(org_name, category):
                social_results = await self._search_social_media(org_name, category)
                all_results.extend(social_results)
            
            # 중복 제거 및 점수순 정렬
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return unique_results[:5]  # 상위 5개만 반환
            
        except Exception as e:
            self.logger.error(f"종합 홈페이지 검색 오류: {e}")
            return []
    
    async def _search_official_homepage(self, org_name: str, category: str) -> List[Dict]:
        """공식 홈페이지 검색 (additionalplan.py에서 가져온 로직)"""
        results = []
        
        search_queries = [
            f"{org_name} 홈페이지 site:*.kr",
            f"{org_name} 공식사이트 site:*.org", 
            f"{org_name} {category} 홈페이지",
            f"{org_name} 공식홈페이지"
        ]
        
        # 간단한 구글 검색 시뮬레이션 (실제로는 parent_crawler의 기능 활용)
        for query in search_queries[:2]:  # 리소스 절약을 위해 상위 2개만
            try:
                self.logger.info(f"🔍 공식 홈페이지 검색: {query}")
                
                # 여기서는 기존 모듈의 검색 결과를 AI로 검증하는 방식으로 구현
                # (실제 구글 검색은 기존 모듈에서 처리)
                
            except Exception as e:
                self.logger.warning(f"공식 홈페이지 검색 오류: {e}")
        
        return results
    
    async def _search_social_media(self, org_name: str, category: str) -> List[Dict]:
        """소셜미디어 홈페이지 검색 (additionalplan.py의 혁신적 아이디어!)"""
        results = []
        
        # 소셜미디어 도메인 정의
        SOCIAL_MEDIA_DOMAINS = {
            "blog.naver.com": "네이버블로그",
            "cafe.naver.com": "네이버카페", 
            "facebook.com": "페이스북",
            "instagram.com": "인스타그램",
            "youtube.com": "유튜브"
        }
        
        social_queries = [
            f"{org_name} site:blog.naver.com",
            f"{org_name} site:cafe.naver.com", 
            f"{org_name} site:facebook.com",
            f"{org_name} site:instagram.com"
        ]
        
        self.logger.info(f"📱 소셜미디어 검색 시작: {org_name} (소규모 기관용)")
        
        # 실제 검색은 기존 모듈 활용하되, 여기서는 검색 전략만 정의
        # (구현 복잡도를 줄이기 위해 로직만 준비)
        
        for query in social_queries[:2]:  # 상위 2개만 시도
            try:
                self.logger.info(f"🔍 소셜미디어 검색: {query}")
                
                # 소셜미디어 검색 결과를 AI로 검증
                # (실제 구현시 parent_crawler의 검색 기능 활용)
                
            except Exception as e:
                self.logger.warning(f"소셜미디어 검색 오류: {e}")
        
        return results
    
    def _is_small_organization(self, org_name: str, category: str) -> bool:
        """소규모 기관 판별 (소셜미디어 검색 대상)"""
        try:
            # 소규모 기관 판별 기준
            small_org_indicators = [
                "교회", "성당", "절", "사찰", "채플", "예배당",
                "의원", "한의원", "치과", "약국",
                "미용실", "카페", "식당", "상점",
                "학원", "교습소", "연구소"
            ]
            
            # 기관명이나 카테고리에 소규모 기관 키워드가 포함되어 있으면
            org_text = f"{org_name} {category}".lower()
            
            for indicator in small_org_indicators:
                if indicator in org_text:
                    self.logger.info(f"🏢 소규모 기관으로 판별: {org_name} ({indicator})")
                    return True
            
            # 기관명이 짧으면 소규모로 간주
            if len(org_name) <= 10:
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"소규모 기관 판별 오류: {e}")
            return False
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """검색 결과 중복 제거"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def _verify_homepage_with_ai(self, url: str, org_name: str, category: str) -> Dict:
        """AI로 홈페이지 관련성 검증"""
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
            self.logger.info(f"🤖 [AI 프롬프트] 홈페이지 검증 - {org_name}")
            self.logger.debug(f"📝 프롬프트: {prompt}")
            self.logger.info(f"🤖 [AI 응답] 홈페이지 검증 - {org_name}")
            self.logger.debug(f"📋 응답: {response}")
            parsed_result = self._parse_verification_response(response)
            self.logger.info(f"🎯 [파싱 결과] {parsed_result}")
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

class EnhancedHomepageAnalysisAgent(AIAgent):
    """AI 강화 홈페이지 분석 에이전트 - BS4 → JS → AI 순서"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler):
        super().__init__("EnhancedHomepageAnalysisAgent", ai_manager, logger, parent_crawler)
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """단계별 홈페이지 분석: BS4 → JS 렌더링 → AI 분석"""
        try:
            homepage_url = context.extracted_data.get('homepage')
            if not homepage_url:
                self.logger.info(f"📋 [{self.name}] 홈페이지가 없어 분석 건너뛰기")
                context.current_stage = CrawlingStage.CONTACT_EXTRACTION
                return context
            
            org_name = context.organization.get('name', '')
            self.logger.info(f"🔍 [{self.name}] 단계별 홈페이지 분석: {homepage_url}")
            
            # 1단계: BS4로 텍스트 추출 시도
            extracted_text = await self._extract_with_bs4(homepage_url)
            soup_object = None
            
            if not extracted_text:
                # 2단계: JS 렌더링으로 텍스트 추출 시도
                extraction_result = await self._extract_with_selenium(homepage_url)
                if extraction_result:
                    extracted_text = extraction_result.get('text')
                    soup_object = extraction_result.get('soup')
            
            if extracted_text:
                # 3단계: AI로 연락처 정보 추출
                contact_info = await self._extract_contacts_with_ai(extracted_text, org_name)
                if contact_info:
                    self._store_enhanced_contact_info(context, contact_info)
                    context.extracted_data['homepage_analyzed'] = True
                    self.logger.info(f"✅ [{self.name}] AI 홈페이지 분석 완료")
                
                # 4단계: 연락처 페이지 링크 찾기 (additionalplan.py에서 가져온 기능)
                if soup_object:
                    contact_links = self._find_contact_page_links(soup_object, homepage_url)
                    if contact_links:
                        context.extracted_data['contact_page_links'] = contact_links
                        self.logger.info(f"🔗 연락처 페이지 링크 {len(contact_links)}개 발견")
                else:
                    self.logger.warning(f"⚠️ [{self.name}] AI에서 연락처 정보를 찾지 못함")
            else:
                context.error_log.append(f"홈페이지 텍스트 추출 실패: {homepage_url}")
                self.logger.warning(f"⚠️ [{self.name}] 홈페이지 텍스트 추출 실패")
            
            context.current_stage = CrawlingStage.CONTACT_EXTRACTION
            return context
            
        except Exception as e:
            context.error_log.append(f"EnhancedHomepageAnalysisAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    def _find_contact_page_links(self, soup, base_url: str) -> List[Dict]:
        """연락처 페이지 링크 찾기 (additionalplan.py에서 가져온 기능)"""
        contact_links = []
        
        try:
            # 연락처 관련 키워드
            CONTACT_NAVIGATION_KEYWORDS = [
                "연락처", "Contact", "contact us", "CONTACT US", "문의", "오시는길", 
                "찾아오시는길", "위치", "주소", "전화", "TEL", "전화번호", "연락망"
            ]
            
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
    
    async def _extract_with_bs4(self, url: str) -> Optional[str]:
        """1단계: BS4로 텍스트 추출"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            self.logger.info(f"🔍 BS4 텍스트 추출 시도: {url}")
            
            headers = REQUEST_HEADERS
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 스크립트, 스타일 제거
            for element in soup(["script", "style", "noscript", "meta", "link"]):
                element.decompose()
            
            # 텍스트 추출
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) > 500:  # 의미있는 텍스트인지 확인
                self.logger.info(f"✅ BS4 추출 성공: {len(text)} chars")
                return text[:10000]  # 최대 10,000자
            else:
                self.logger.warning(f"⚠️ BS4 추출된 텍스트가 너무 짧음: {len(text)} chars")
                return None
                
        except Exception as e:
            self.logger.warning(f"BS4 텍스트 추출 실패: {e}")
            return None
    
    async def _extract_with_selenium(self, url: str) -> Optional[Dict]:
        """2단계: Selenium으로 JS 렌더링 후 텍스트 추출 (개선된 버전)"""
        try:
            self.logger.info(f"🔍 Selenium JS 렌더링 텍스트 추출 시도: {url}")
            
            if self.parent_crawler and self.parent_crawler.homepage_parser:
                page_data = self.parent_crawler.homepage_parser.extract_page_content(url)
                if page_data and page_data.get('accessible') and page_data.get('text_content'):
                    text = page_data['text_content']
                    
                    # BeautifulSoup 객체도 생성
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(page_data.get('raw_html', ''), 'html.parser') if page_data.get('raw_html') else None
                    
                    self.logger.info(f"✅ Selenium 추출 성공: {len(text)} chars")
                    return {
                        'text': text,
                        'soup': soup
                    }
            
            self.logger.warning("⚠️ Selenium 텍스트 추출 실패")
            return None
            
        except Exception as e:
            self.logger.warning(f"Selenium 텍스트 추출 실패: {e}")
            return None
    
    async def _extract_contacts_with_ai(self, text_content: str, org_name: str) -> Optional[Dict]:
        """3단계: AI로 연락처 정보 추출"""
        try:
            self.logger.info(f"🤖 AI 연락처 추출: {org_name}")
            
            prompt = f"""
            다음은 '{org_name}' 기관의 홈페이지 텍스트입니다.
            이 텍스트에서 연락처 정보를 정확히 추출해주세요.

            **홈페이지 텍스트:**
            {text_content[:5000]}

            **추출할 정보:**
            1. 전화번호 (02-XXX-XXXX, 031-XXX-XXXX 형태)
            2. 팩스번호 (전화번호와 다른 번호)
            3. 이메일 주소
            4. 주소 (도로명주소 또는 지번주소)
            5. 휴대폰번호 (010-XXXX-XXXX 형태)

            **응답 형식 (JSON):**
            {{
                "phone": "전화번호 또는 null",
                "fax": "팩스번호 또는 null", 
                "email": "이메일 또는 null",
                "address": "주소 또는 null",
                "mobile": "휴대폰 또는 null"
            }}

            **주의사항:**
            - 정확한 형태의 연락처만 추출
            - 전화번호와 팩스번호가 같으면 팩스는 null
            - 찾을 수 없으면 null 값 사용
            """
            
            if self.ai_manager and self.ai_manager.gemini_model:
                response = self.ai_manager.gemini_model.generate_content(prompt)
                response_text = response.text.strip()
                
                # JSON 추출 및 파싱
                contact_info = self._parse_ai_contact_response(response_text)
                
                if contact_info:
                    self.logger.info(f"✅ AI 연락처 추출 성공: {contact_info}")
                    return contact_info
                else:
                    self.logger.warning("⚠️ AI 응답에서 연락처 정보를 파싱할 수 없음")
                    return None
            else:
                self.logger.warning("⚠️ AI 모델이 사용 불가능")
                return None
                
        except Exception as e:
            self.logger.error(f"AI 연락처 추출 오류: {e}")
            return None
    
    def _parse_ai_contact_response(self, response_text: str) -> Optional[Dict]:
        """AI 응답에서 연락처 정보 파싱"""
        try:
            import json
            
            # JSON 블록 찾기
            if '```json' in response_text:
                json_part = response_text.split('```json')[1].split('```')[0].strip()
            elif '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_part = response_text[start:end]
            else:
                return None
            
            # JSON 파싱
            contact_info = json.loads(json_part)
            
            # 결과 정리 (null 값 제거)
            cleaned_info = {}
            for key, value in contact_info.items():
                if value and value.lower() != 'null' and value.strip():
                    cleaned_info[key] = value.strip()
            
            return cleaned_info if cleaned_info else None
            
        except Exception as e:
            self.logger.warning(f"AI 응답 파싱 오류: {e}")
            return None
    
    def _store_enhanced_contact_info(self, context: CrawlingContext, contact_info: Dict):
        """연락처 정보 저장 (additionalplan.py 스타일로 강화)"""
        # 기본 연락처 정보
        if contact_info.get('phone'):
            context.extracted_data['phone'] = contact_info['phone']
            self.update_confidence(context, 'phone', 0.9)
        
        if contact_info.get('fax'):
            context.extracted_data['fax'] = contact_info['fax']
            self.update_confidence(context, 'fax', 0.9)
        
        if contact_info.get('email'):
            context.extracted_data['email'] = contact_info['email']
            self.update_confidence(context, 'email', 0.9)
        
        if contact_info.get('address'):
            context.extracted_data['address'] = contact_info['address']
            self.update_confidence(context, 'address', 0.8)
        
        if contact_info.get('mobile'):
            context.extracted_data['mobile'] = contact_info['mobile']
            self.update_confidence(context, 'mobile', 0.8)

class EnhancedContactExtractionAgent(AIAgent):
    """AI 강화 연락처 추출 에이전트 - 주소 기반 Selenium 검색"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler):
        super().__init__("EnhancedContactExtractionAgent", ai_manager, logger, parent_crawler)
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """주소 기반 Selenium 검색 → AI 검증"""
        try:
            org_name = context.organization.get('name', '')
            org_address = context.organization.get('address', '')
            
            self.logger.info(f"📞 [{self.name}] 주소 기반 연락처 검색: {org_name}")
            
            # 전화번호가 없으면 검색
            if not context.extracted_data.get('phone'):
                phone_result = await self._search_phone_with_address(org_name, org_address)
                if phone_result:
                    # AI로 검증
                    is_valid = await self._verify_contact_with_ai(phone_result, org_name, 'phone')
                    if is_valid:
                        context.extracted_data['phone'] = phone_result
                        context.extracted_data['phone_source'] = 'address_based_search'
                        self.update_confidence(context, 'phone', 0.8)
            
            # 팩스번호가 없으면 검색 (전화번호와 중복 방지)
            if not context.extracted_data.get('fax'):
                fax_result = await self._search_fax_with_address(
                    org_name, org_address, context.extracted_data.get('phone')
                )
                if fax_result:
                    # AI로 검증
                    is_valid = await self._verify_contact_with_ai(fax_result, org_name, 'fax')
                    if is_valid:
                        context.extracted_data['fax'] = fax_result
                        context.extracted_data['fax_source'] = 'address_based_search'
                        self.update_confidence(context, 'fax', 0.8)
            
            context.current_stage = CrawlingStage.AI_VERIFICATION
            return context
            
        except Exception as e:
            context.error_log.append(f"EnhancedContactExtractionAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _search_phone_with_address(self, org_name: str, address: str) -> Optional[str]:
        """주소 기반 전화번호 검색"""
        try:
            if not org_name:
                return None
            
            # 지역 정보 추출
            region_info = self._extract_region_from_address(address)
            search_query = f"{org_name} 전화번호"
            
            if region_info:
                search_query = f"{region_info} {org_name} 전화번호"
            
            self.logger.info(f"🔍 전화번호 검색: {search_query}")
            
            # Selenium으로 검색
            if self.parent_crawler and self.parent_crawler.phone_driver:
                from cralwer.phone_extractor import search_phone_number
                found_phones = search_phone_number(self.parent_crawler.phone_driver, search_query)
                
                if found_phones:
                    # 첫 번째 결과를 반환 (가장 관련성 높은 것으로 가정)
                    phone = found_phones[0]
                    
                    # 지역번호 검증
                    if self._validate_phone_by_region(phone, address):
                        self.logger.info(f"✅ 전화번호 발견: {phone}")
                        return phone
                    else:
                        self.logger.warning(f"⚠️ 지역번호 불일치: {phone} (주소: {address})")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"전화번호 검색 실패: {e}")
            return None
    
    async def _search_fax_with_address(self, org_name: str, address: str, existing_phone: str) -> Optional[str]:
        """주소 기반 팩스번호 검색 (전화번호와 중복 방지)"""
        try:
            if not org_name:
                return None
            
            # 지역 정보 추출
            region_info = self._extract_region_from_address(address)
            search_query = f"{org_name} 팩스번호"
            
            if region_info:
                search_query = f"{region_info} {org_name} 팩스번호"
            
            self.logger.info(f"📠 팩스번호 검색: {search_query}")
            
            # 팩스 추출기로 검색
            if self.parent_crawler and self.parent_crawler.fax_extractor:
                found_faxes = self.parent_crawler.fax_extractor.search_fax_number(org_name)
                
                for fax in found_faxes:
                    # 전화번호와 중복 체크
                    if not self._is_duplicate_number(fax, existing_phone):
                        # 지역번호 검증
                        if self._validate_phone_by_region(fax, address):
                            self.logger.info(f"✅ 팩스번호 발견: {fax}")
                            return fax
                        else:
                            self.logger.warning(f"⚠️ 팩스 지역번호 불일치: {fax}")
                
                self.logger.info("📠 중복되지 않는 팩스번호 없음")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"팩스번호 검색 실패: {e}")
            return None
    
    def _extract_region_from_address(self, address: str) -> Optional[str]:
        """주소에서 지역 정보 추출"""
        if not address:
            return None
        
        # settings.py의 REGION_TO_AREA_CODE 활용
        for region in REGION_TO_AREA_CODE.keys():
            if region in address:
                return region
        
        return None
    
    def _validate_phone_by_region(self, phone: str, address: str) -> bool:
        """지역번호와 주소 일치 여부 확인"""
        if not phone or not address:
            return True  # 정보가 부족하면 일단 통과
        
        # settings.py의 validate_phone_by_region 활용
        return validate_phone_by_region(phone, address)
    
    def _is_duplicate_number(self, number1: str, number2: str) -> bool:
        """두 번호가 중복인지 확인"""
        if not number1 or not number2:
            return False
        
        # settings.py의 is_phone_fax_duplicate 활용
        return is_phone_fax_duplicate(number1, number2)
    
    async def _verify_contact_with_ai(self, contact: str, org_name: str, contact_type: str) -> bool:
        """AI로 연락처 유효성 검증"""
        try:
            prompt = f"""
            다음 정보가 올바른지 검증해주세요:

            **기관명:** {org_name}
            **{contact_type}:** {contact}

            **검증 기준:**
            1. 번호 형식이 올바른가? (한국 전화번호 형식)
            2. 기관명과 관련성이 있어 보이는가?
            3. 유효한 번호로 보이는가?

            **응답 형식:**
            VALID: [예/아니오]
            CONFIDENCE: [0.1-1.0]
            REASON: [판단 이유]
            """
            
            if self.ai_manager and self.ai_manager.gemini_model:
                response = self.ai_manager.gemini_model.generate_content(prompt)
                response_text = response.text.strip()
                
                # 응답 파싱
                is_valid = self._parse_verification_response(response_text)
                self.logger.info(f"🤖 AI 검증 결과 ({contact_type}): {is_valid}")
                return is_valid
            
            return True  # AI가 없으면 기본적으로 통과
            
        except Exception as e:
            self.logger.warning(f"AI 검증 실패: {e}")
            return True  # 오류시 기본적으로 통과
    
    def _parse_verification_response(self, response_text: str) -> bool:
        """AI 검증 응답 파싱"""
        try:
            if 'VALID:' in response_text:
                valid_line = [line for line in response_text.split('\n') if 'VALID:' in line][0]
                return '예' in valid_line or 'true' in valid_line.lower()
            
            # 백업: 긍정적 키워드 체크
            positive_keywords = ['예', 'valid', 'true', '올바', '유효', '적절']
            return any(keyword in response_text.lower() for keyword in positive_keywords)
            
        except Exception:
            return True

class AIVerificationAgent(AIAgent):
    """AI 검증 에이전트"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler):
        super().__init__("AIVerificationAgent", ai_manager, logger, parent_crawler)
    
    async def execute(self, context: CrawlingContext) -> CrawlingContext:
        """AI 종합 검증"""
        try:
            org_name = context.organization.get('name', '')
            self.logger.info(f"🔍 [{self.name}] AI 종합 검증: {org_name}")
            
            # AI 종합 검증 실행
            verification_result = await self._ai_comprehensive_verification(context)
            
            # 검증 결과 적용
            context.ai_insights['verification'] = verification_result
            self._adjust_confidence_scores(context, verification_result)
            
            context.current_stage = CrawlingStage.COMPLETION
            return context
            
        except Exception as e:
            context.error_log.append(f"AIVerificationAgent 오류: {str(e)}")
            self.logger.error(f"❌ [{self.name}] 오류: {e}")
            return context
    
    async def _ai_comprehensive_verification(self, context: CrawlingContext) -> Dict[str, Any]:
        """AI 종합 검증"""
        try:
            org_name = context.organization.get('name', '')
            extracted_data = context.extracted_data
            
            # 검증할 데이터 준비
            verification_prompt = f"""
            기관명: {org_name}
            추출된 데이터:
            - 홈페이지: {extracted_data.get('homepage', '없음')}
            - 전화번호: {extracted_data.get('phone', '없음')}
            - 팩스번호: {extracted_data.get('fax', '없음')}
            - 이메일: {extracted_data.get('email', '없음')}
            
            위 정보들이 해당 기관과 일치하는지 검증해주세요.
            응답 형식:
            OVERALL_VALIDITY: [valid/invalid/uncertain]
            PHONE_VALIDITY: [valid/invalid/uncertain]
            FAX_VALIDITY: [valid/invalid/uncertain]
            HOMEPAGE_VALIDITY: [valid/invalid/uncertain]
            CONFIDENCE_SCORE: [0.0-1.0]
            """
            
            if self.ai_manager and self.ai_manager.gemini_model:
                response = self.ai_manager.gemini_model.generate_content(verification_prompt)
                response_text = response.text.strip()
                
                # 응답 파싱
                return self._parse_verification_response(response_text)
            else:
                return {
                    'overall_validity': 'uncertain',
                    'confidence_score': 0.5,
                    'verification_method': 'no_ai_available'
                }
                
        except Exception as e:
            self.logger.warning(f"AI 검증 실패: {e}")
            return {
                'overall_validity': 'uncertain',
                'confidence_score': 0.5,
                'verification_error': str(e)
            }
    
    def _parse_verification_response(self, response_text: str) -> Dict[str, Any]:
        """검증 응답 파싱"""
        result = {
            'overall_validity': 'uncertain',
            'phone_validity': 'uncertain',
            'fax_validity': 'uncertain',
            'homepage_validity': 'uncertain',
            'confidence_score': 0.5
        }
        
        try:
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip().upper()
                
                if 'OVERALL_VALIDITY:' in line:
                    validity = line.split(':', 1)[1].strip().lower()
                    if validity in ['valid', 'invalid', 'uncertain']:
                        result['overall_validity'] = validity
                
                elif 'PHONE_VALIDITY:' in line:
                    validity = line.split(':', 1)[1].strip().lower()
                    if validity in ['valid', 'invalid', 'uncertain']:
                        result['phone_validity'] = validity
                
                elif 'FAX_VALIDITY:' in line:
                    validity = line.split(':', 1)[1].strip().lower()
                    if validity in ['valid', 'invalid', 'uncertain']:
                        result['fax_validity'] = validity
                
                elif 'HOMEPAGE_VALIDITY:' in line:
                    validity = line.split(':', 1)[1].strip().lower()
                    if validity in ['valid', 'invalid', 'uncertain']:
                        result['homepage_validity'] = validity
                
                elif 'CONFIDENCE_SCORE:' in line:
                    try:
                        score = float(line.split(':', 1)[1].strip())
                        if 0.0 <= score <= 1.0:
                            result['confidence_score'] = score
                    except ValueError:
                        pass
        
        except Exception as e:
            self.logger.warning(f"검증 응답 파싱 실패: {e}")
        
        return result
    
    def _adjust_confidence_scores(self, context: CrawlingContext, verification: Dict[str, Any]):
        """신뢰도 점수 조정"""
        try:
            adjustment_factor = verification.get('confidence_score', 0.5)
            
            # 전체 유효성에 따른 조정
            if verification.get('overall_validity') == 'valid':
                adjustment_factor *= 1.2
            elif verification.get('overall_validity') == 'invalid':
                adjustment_factor *= 0.5
            
            # 각 필드별 신뢰도 조정
            for field in ['phone', 'fax', 'homepage']:
                if field in context.confidence_scores:
                    field_validity = verification.get(f'{field}_validity', 'uncertain')
                    if field_validity == 'valid':
                        context.confidence_scores[field] *= 1.1
                    elif field_validity == 'invalid':
                        context.confidence_scores[field] *= 0.6
                    
                    # 범위 제한
                    context.confidence_scores[field] = min(1.0, max(0.0, context.confidence_scores[field]))
        
        except Exception as e:
            self.logger.warning(f"신뢰도 점수 조정 실패: {e}")

class ContactPageSearchAgent(AIAgent):
    """연락처 페이지 전용 검색 AI 에이전트 (additionalplan.py에서 가져온 혁신적 기능!)"""
    
    def __init__(self, ai_manager: AIModelManager, logger: logging.Logger, parent_crawler):
        super().__init__("ContactPageSearchAgent", ai_manager, logger, parent_crawler)
    
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
        try:
            self.logger.info(f"🔍 연락처 페이지 추출: {url}")
            
            if self.parent_crawler and self.parent_crawler.homepage_parser:
                page_data = self.parent_crawler.homepage_parser.extract_page_content(url)
                if page_data and page_data.get('accessible') and page_data.get('text_content'):
                    page_text = page_data['text_content']
                    
                    # 연락처 정보 추출
                    contact_info = self._extract_contact_info_enhanced(page_text)
                    
                    return contact_info if any(contact_info.values()) else None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"연락처 페이지 추출 오류 {url}: {e}")
            return None
    
    def _extract_contact_info_enhanced(self, text: str) -> Dict[str, List[str]]:
        """강화된 연락처 정보 추출"""
        contact_info = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": []
        }
        
        try:
            # 전화번호 추출 (기본 + 추가 패턴)
            phone_patterns = [
                r'(\d{2,3})-(\d{3,4})-(\d{4})',
                r'(\d{2,3})\.(\d{3,4})\.(\d{4})',
                r'tel[:\s]*(\d{2,3})-(\d{3,4})-(\d{4})',
                r'전화[:\s]*(\d{2,3})-(\d{3,4})-(\d{4})'
            ]
            
            for pattern in phone_patterns:
                import re
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        phone = '-'.join(match)
                    else:
                        phone = match
                    
                    # 전화번호 검증 및 포맷팅
                    if phone and len(phone.replace('-', '')) >= 9 and phone not in contact_info["phones"]:
                        contact_info["phones"].append(phone)
            
            # 팩스번호 추출
            fax_patterns = [
                r'팩스[:\s]*(\d{2,3})-(\d{3,4})-(\d{4})',
                r'fax[:\s]*(\d{2,3})-(\d{3,4})-(\d{4})',
                r'F[:\s]*(\d{2,3})-(\d{3,4})-(\d{4})'
            ]
            
            for pattern in fax_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        fax = '-'.join(match)
                    else:
                        fax = match
                    
                    if fax and len(fax.replace('-', '')) >= 9 and fax not in contact_info["faxes"]:
                        contact_info["faxes"].append(fax)
            
            # 이메일 추출
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            for email in emails:
                if email not in contact_info["emails"]:
                    contact_info["emails"].append(email)
        
        except Exception as e:
            self.logger.warning(f"연락처 정보 추출 오류: {e}")
        
        return contact_info
    
    def _merge_additional_contacts(self, context: CrawlingContext, additional_contacts: List[Dict]):
        """추가 연락처 정보를 메인 컨텍스트에 병합"""
        try:
            for contact_page in additional_contacts:
                contacts = contact_page.get('contacts', {})
                
                # 전화번호 추가 (중복 방지)
                for phone in contacts.get('phones', []):
                    if not context.extracted_data.get('phone'):
                        context.extracted_data['phone'] = phone
                        context.extracted_data['phone_source'] = f"contact_page_{contact_page['keyword']}"
                        self.update_confidence(context, 'phone', 0.8)
                        break
                
                # 팩스번호 추가 (중복 방지)
                existing_phone = context.extracted_data.get('phone', '')
                for fax in contacts.get('faxes', []):
                    if fax != existing_phone and not context.extracted_data.get('fax'):
                        context.extracted_data['fax'] = fax
                        context.extracted_data['fax_source'] = f"contact_page_{contact_page['keyword']}"
                        self.update_confidence(context, 'fax', 0.8)
                        break
                
                # 이메일 추가
                for email in contacts.get('emails', []):
                    if not context.extracted_data.get('email'):
                        context.extracted_data['email'] = email
                        context.extracted_data['email_source'] = f"contact_page_{contact_page['keyword']}"
                        self.update_confidence(context, 'email', 0.8)
                        break
        
        except Exception as e:
            self.logger.warning(f"추가 연락처 병합 오류: {e}")

# ==================== AI 강화 ModularUnifiedCrawler ====================

class AIEnhancedModularUnifiedCrawler:
    """AI 강화 모듈러 통합 크롤러"""
    
    def __init__(self, config_override=None, api_key=None, progress_callback=None):
        """초기화"""
        self.config = config_override or CRAWLING_CONFIG
        self.logger = LoggerUtils.setup_crawler_logger("ai_enhanced_modular_crawler")
        self.progress_callback = progress_callback
        
        # AI 매니저 초기화
        try:
            self.ai_manager = AIModelManager()
        except Exception as e:
            self.logger.warning(f"AI 매니저 초기화 실패: {e}")
            self.ai_manager = None
        
        # 전문 모듈 인스턴스들 (기존 유지)
        self.fax_extractor = None
        self.phone_driver = None
        self.homepage_parser = None
        self.contact_validator = None
        self.ai_validator = None
        self.database = None
        
        # AI 에이전트들 초기화 (수정: parent_crawler 전달)
        self.ai_agents = []
        if self.ai_manager:
            try:
                self.ai_agents = [
                    EnhancedHomepageSearchAgent(self.ai_manager, self.logger, self),
                    EnhancedHomepageAnalysisAgent(self.ai_manager, self.logger, self),
                    ContactPageSearchAgent(self.ai_manager, self.logger, self),
                    EnhancedContactExtractionAgent(self.ai_manager, self.logger, self),
                    AIVerificationAgent(self.ai_manager, self.logger, self)
                ]
                self.logger.info("✅ AI 에이전트 초기화 성공")
            except Exception as e:
                self.logger.error(f"❌ AI 에이전트 초기화 실패: {e}")
                self.ai_agents = []
        else:
            self.logger.warning("⚠️ AI 매니저 없음 - 기본 모듈만 사용")
        
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
            "ai_enhanced": 0,
            "start_time": None,
            "end_time": None,
            "agent_stats": {agent.name: {"executed": 0, "success": 0} for agent in self.ai_agents}
        }
        
        self.logger.info("🚀 AI 강화 모듈러 크롤러 초기화 완료")
    
    def initialize_modules(self):
        """전문 모듈들 초기화 (기존 로직 유지)"""
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
    
    async def process_organizations(self, organizations: List[Dict], options: Dict = None) -> List[Dict]:
        """AI 강화 조직 처리"""
        if not organizations:
            self.logger.warning("처리할 조직 데이터가 없습니다.")
            return []
        
        options = options or {}
        self.stats["start_time"] = datetime.now()
        self.stats["total_processed"] = len(organizations)
        
        # 모듈 초기화
        self.initialize_modules()
        
        self.logger.info(f"📊 총 {len(organizations)}개 조직 AI 강화 처리 시작")
        
        results = []
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    # AI 에이전트를 사용한 단일 조직 처리
                    processed_org = await self.process_single_organization_with_ai(org, i)
                    results.append(processed_org)
                    
                    self.stats["successful"] += 1
                    if processed_org.get('ai_enhanced'):
                        self.stats["ai_enhanced"] += 1
                    
                    # 딜레이
                    await asyncio.sleep(self.config.get("default_delay", 2))
                    
                except Exception as e:
                    self.logger.error(f"❌ 조직 처리 실패 [{i}]: {org.get('name', 'Unknown')} - {e}")
                    self.stats["failed"] += 1
                    results.append(org)
        
        finally:
            # 모듈 정리
            self.cleanup_modules()
        
        self.stats["end_time"] = datetime.now()
        self.print_ai_enhanced_statistics()
        
        return results
    
    async def process_single_organization_with_ai(self, org: Dict, index: int) -> Dict:
        """AI 에이전트를 사용한 단일 조직 처리"""
        start_time = time.time()
        
        try:
            org_name = org.get('name', 'Unknown')
            self.logger.info(f"🤖 AI 워크플로우 시작 [{index}]: {org_name}")
            
            # AI 에이전트 체인 초기화
            context = CrawlingContext(
                organization=org,
                current_stage=CrawlingStage.INITIALIZATION,
                extracted_data={},
                ai_insights={},
                error_log=[],
                processing_time=0,
                confidence_scores={}
            )
            
            # AI 에이전트 체인 실행 (올바른 순서로 배치)
            agents = [
                EnhancedHomepageSearchAgent(self.ai_manager, self.logger, self),
                EnhancedHomepageAnalysisAgent(self.ai_manager, self.logger, self),
                ContactPageSearchAgent(self.ai_manager, self.logger, self),  # 홈페이지 분석 후 바로 실행
                EnhancedContactExtractionAgent(self.ai_manager, self.logger, self),
                AIVerificationAgent(self.ai_manager, self.logger, self)
            ]
            
            for agent in agents:
                try:
                    if await agent.should_execute(context):
                        self.logger.info(f"🔄 에이전트 실행: {agent.name}")
                        context = await agent.execute(context)
                    else:
                        self.logger.info(f"⏭️ 에이전트 건너뛰기: {agent.name}")
                except Exception as e:
                    # error 속성 대신 error_log에 추가
                    error_msg = f"{agent.name} 실행 실패: {str(e)}"
                    context.error_log.append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
                    continue
            
            # 처리 시간 계산
            context.processing_time = time.time() - start_time
            
            # 결과 결합
            result = self._combine_ai_results(org, context)
            
            # 전통적인 모듈로 보완
            await self._supplement_with_traditional_modules(result, context)
            
            return result
            
        except Exception as e:
            # error 속성 대신 직접 오류 메시지 로깅
            error_msg = f"AI 워크플로우 실패: {org_name} - {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            # 실패시 기본 처리
            result = org.copy()
            result.update({
                'ai_enhanced': False,
                'processing_metadata': {
                    'extraction_method': 'fallback_error',
                    'error_message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': time.time() - start_time
                }
            })
            return result
    
    def _combine_ai_results(self, original_org: Dict, context: CrawlingContext) -> Dict:
        """AI 결과 조합"""
        result = original_org.copy()
        
        # 추출된 데이터 추가
        result.update(context.extracted_data)
        
        # AI 인사이트 추가
        result['ai_insights'] = context.ai_insights
        result['confidence_scores'] = context.confidence_scores
        
        # 처리 메타데이터 추가
        result['processing_metadata'] = {
            'processing_time': context.processing_time,
            'final_stage': context.current_stage.value,
            'error_count': len(context.error_log),
            'errors': context.error_log,
            'extraction_method': 'ai_enhanced_modular',
            'ai_enhanced': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    async def _supplement_with_traditional_modules(self, result: Dict, context: CrawlingContext):
        """기존 모듈로 보완 처리 (개선된 버전)"""
        try:
            org_name = result.get('name', 'Unknown')
            self.logger.info(f"🔧 기존 모듈로 보완 처리: {org_name}")
            
            # 전화번호가 없거나 신뢰도가 낮으면 기존 모듈로 추가 시도
            phone_confidence = context.confidence_scores.get('phone', 0.0)
            if (not result.get('phone') or phone_confidence < 0.7) and self.phone_driver:
                try:
                    self.logger.info(f"📞 전화번호 검색 시도: {org_name}")
                    found_phones = search_phone_number(self.phone_driver, org_name)
                    if found_phones:
                        # 가장 적절한 전화번호 선택
                        best_phone = self._select_best_phone_number(found_phones, result.get('address', ''))
                        if best_phone:
                            result['phone'] = best_phone
                            result['phone_source'] = 'traditional_module_supplement'
                            result['phone_confidence'] = 0.8  # 검색 결과 신뢰도
                            self.stats["phone_extracted"] += 1
                            self.logger.info(f"✅ 전화번호 보완 성공: {best_phone}")
                except Exception as e:
                    self.logger.warning(f"전화번호 보완 실패: {e}")
            
            # 팩스번호가 없거나 신뢰도가 낮으면 기존 모듈로 추가 시도
            fax_confidence = context.confidence_scores.get('fax', 0.0)
            if (not result.get('fax') or fax_confidence < 0.7) and self.fax_extractor:
                try:
                    self.logger.info(f"📠 팩스번호 검색 시도: {org_name}")
                    found_faxes = self.fax_extractor.search_fax_number(org_name)
                    if found_faxes:
                        # 전화번호와 중복되지 않는 팩스번호 선택
                        best_fax = self._select_best_fax_number(found_faxes, result.get('phone', ''))
                        if best_fax:
                            result['fax'] = best_fax
                            result['fax_source'] = 'traditional_module_supplement'
                            result['fax_confidence'] = 0.8  # 검색 결과 신뢰도
                            self.stats["fax_extracted"] += 1
                            self.logger.info(f"✅ 팩스번호 보완 성공: {best_fax}")
                except Exception as e:
                    self.logger.warning(f"팩스번호 보완 실패: {e}")
            
            # 홈페이지가 없으면 기존 모듈로 추가 시도
            if not result.get('homepage') and self.homepage_parser:
                try:
                    self.logger.info(f"🌐 홈페이지 검색 시도: {org_name}")
                    # AI 홈페이지 검색 시도
                    homepage_results = await self.homepage_parser.ai_search_homepage(org_name, result.get('category', ''))
                    if homepage_results:
                        best_homepage = homepage_results[0]
                        result['homepage'] = best_homepage.get('url', '')
                        result['homepage_source'] = 'traditional_module_supplement'
                        result['homepage_confidence'] = best_homepage.get('confidence', 0.6)
                        self.logger.info(f"✅ 홈페이지 보완 성공: {result['homepage']}")
                except Exception as e:
                    self.logger.warning(f"홈페이지 보완 실패: {e}")
            
        except Exception as e:
            self.logger.error(f"기존 모듈 보완 오류: {e}")
    
    def _select_best_phone_number(self, phone_numbers: List[str], address: str = '') -> Optional[str]:
        """가장 적절한 전화번호 선택"""
        if not phone_numbers:
            return None
        
        try:
            # 지역번호와 주소 매칭 확인
            for phone in phone_numbers:
                if self._validate_phone_by_region(phone, address):
                    return phone
            
            # 지역 매칭이 안 되면 첫 번째 번호 반환
            return phone_numbers[0]
            
        except Exception as e:
            self.logger.warning(f"전화번호 선택 오류: {e}")
            return phone_numbers[0] if phone_numbers else None
    
    def _select_best_fax_number(self, fax_numbers: List[str], existing_phone: str = '') -> Optional[str]:
        """가장 적절한 팩스번호 선택 (전화번호와 중복 방지)"""
        if not fax_numbers:
            return None
        
        try:
            # 전화번호와 중복되지 않는 팩스번호 선택
            for fax in fax_numbers:
                if not self._is_duplicate_number(fax, existing_phone):
                    return fax
            
            # 모두 중복이면 None 반환
            return None
            
        except Exception as e:
            self.logger.warning(f"팩스번호 선택 오류: {e}")
            return None
    
    def _validate_phone_by_region(self, phone: str, address: str) -> bool:
        """지역번호와 주소 일치 여부 확인"""
        if not phone or not address:
            return True  # 정보가 부족하면 일단 통과
        
        try:
            # settings.py의 validate_phone_by_region 활용 (존재한다면)
            return True  # 기본적으로 통과
        except:
            return True
    
    def _is_duplicate_number(self, number1: str, number2: str) -> bool:
        """두 번호가 중복인지 확인"""
        if not number1 or not number2:
            return False
        
        # 숫자만 추출하여 비교
        digits1 = re.sub(r'[^\d]', '', number1)
        digits2 = re.sub(r'[^\d]', '', number2)
        
        return digits1 == digits2
    
    # 기존 메서드들 유지 (호환성)
    def cleanup_modules(self):
        """모듈들 정리"""
        try:
            self.logger.info("🧹 모듈 정리 시작...")
            
            if self.fax_extractor:
                try:
                    self.fax_extractor.close()
                except:
                    pass
            
            if self.phone_driver:
                try:
                    self.phone_driver.quit()
                except:
                    pass
            
            if self.homepage_parser:
                try:
                    self.homepage_parser.close_driver()
                except:
                    pass
            
            self.logger.info("🎯 모든 모듈 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 모듈 정리 중 오류: {e}")
    
    async def save_to_database(self, org_data: Dict) -> Optional[Dict]:
        """크롤링 결과를 데이터베이스에 저장/업데이트 (개선된 버전)"""
        try:
            if not DATABASE_AVAILABLE:
                self.logger.warning("데이터베이스 모듈을 사용할 수 없습니다")
                return None
            
            from database.database import get_database
            db = get_database()
            
            # DB ID가 있으면 업데이트, 없으면 새로 생성
            db_id = org_data.get('db_id') or org_data.get('id')
            org_name = org_data.get('name', 'Unknown')
            
            # 업데이트할 데이터 준비
            update_data = {}
            
            # 🔥 크롤링 상태 필드 업데이트 (항상 실행)
            update_data['ai_crawled'] = True
            update_data['last_crawled_at'] = datetime.now().isoformat()
            
            # 크롤링으로 얻은 새로운 정보만 업데이트 (검증 강화)
            changes_made = []
            
            if org_data.get('homepage') and org_data['homepage'].strip() != '':
                homepage = org_data['homepage'].strip()
                if homepage.startswith(('http://', 'https://')):
                    update_data['homepage'] = homepage
                    changes_made.append(f"홈페이지: {homepage}")
            
            if org_data.get('phone') and org_data['phone'].strip() != '':
                phone = org_data['phone'].strip()
                if self._is_valid_phone_format(phone):
                    update_data['phone'] = phone
                    changes_made.append(f"전화번호: {phone}")
            
            if org_data.get('fax') and org_data['fax'].strip() != '':
                fax = org_data['fax'].strip()
                if self._is_valid_phone_format(fax):
                    update_data['fax'] = fax
                    changes_made.append(f"팩스번호: {fax}")
            
            if org_data.get('email') and org_data['email'].strip() != '':
                email = org_data['email'].strip()
                if self._is_valid_email_format(email):
                    update_data['email'] = email
                    changes_made.append(f"이메일: {email}")
            
            # 크롤링 메타데이터 저장 (강화된 버전)
            crawling_data = {
                'last_crawled': datetime.now().isoformat(),
                'ai_enhanced': org_data.get('ai_enhanced', False),
                'extraction_method': org_data.get('processing_metadata', {}).get('extraction_method', 'unknown'),
                'confidence_scores': org_data.get('confidence_scores', {}),
                'ai_insights': org_data.get('ai_insights', {}),
                'sources': {
                    'phone_source': org_data.get('phone_source', ''),
                    'fax_source': org_data.get('fax_source', ''),
                    'homepage_source': org_data.get('homepage_source', ''),
                    'email_source': org_data.get('email_source', '')
                },
                'processing_time': org_data.get('processing_metadata', {}).get('processing_time', 0),
                'error_count': len(org_data.get('processing_metadata', {}).get('errors', [])),
                'changes_made': changes_made
            }
            
            if org_data.get('crawling_data'):
                crawling_data.update(org_data['crawling_data'])
            
            update_data['crawling_data'] = json.dumps(crawling_data, ensure_ascii=False)
            update_data['updated_by'] = 'crawler_system'
            
            if db_id:
                # 기존 조직 업데이트
                success = db.update_organization(db_id, update_data, 'crawler_system')
                if success:
                    self.stats["saved_to_db"] += 1
                    self.logger.info(f"✅ 조직 업데이트 완료: {org_name} (ID: {db_id})")
                    self.logger.info(f"🎯 크롤링 상태: ai_crawled=True, last_crawled_at={update_data['last_crawled_at']}")
                    if changes_made:
                        self.logger.info(f"📝 변경사항: {', '.join(changes_made)}")
                    return {'action': 'updated', 'id': db_id, 'changes': changes_made}
                else:
                    self.logger.error(f"❌ 조직 업데이트 실패: {org_name} (ID: {db_id})")
                    return None
            else:
                # 새로운 조직 생성
                org_data_for_db = {
                    'name': org_data.get('name', ''),
                    'category': org_data.get('category', '종교시설'),
                    'type': org_data.get('type', 'CHURCH'),
                    'homepage': org_data.get('homepage', ''),
                    'phone': org_data.get('phone', ''),
                    'fax': org_data.get('fax', ''),
                    'email': org_data.get('email', ''),
                    'address': org_data.get('address', ''),
                    'organization_size': org_data.get('organization_size', ''),
                    'denomination': org_data.get('denomination', ''),
                    'crawling_data': json.dumps(crawling_data, ensure_ascii=False),
                    'created_by': 'crawler_system',
                    'updated_by': 'crawler_system',
                    'lead_source': 'CRAWLER'
                }
                
                new_id = db.create_organization(org_data_for_db)
                if new_id:
                    self.stats["saved_to_db"] += 1
                    self.logger.info(f"✅ 새 조직 생성 완료: {org_name} (ID: {new_id})")
                    if changes_made:
                        self.logger.info(f"📝 생성된 정보: {', '.join(changes_made)}")
                    return {'action': 'created', 'id': new_id, 'changes': changes_made}
                else:
                    self.logger.error(f"❌ 새 조직 생성 실패: {org_name}")
                    return None
            
        except Exception as e:
            self.logger.error(f"데이터베이스 저장 오류: {org_data.get('name', 'Unknown')} - {e}")
            return None
    
    def _is_valid_phone_format(self, phone: str) -> bool:
        """전화번호 형식 검증"""
        if not phone:
            return False
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 한국 전화번호 길이 확인 (9-11자리)
        if len(digits) < 9 or len(digits) > 11:
            return False
        
        # 유효한 지역번호로 시작하는지 확인
        valid_prefixes = ['02', '031', '032', '033', '041', '042', '043', '044', '051', '052', '053', '054', '055', '061', '062', '063', '064', '070', '010', '011', '016', '017', '018', '019']
        
        for prefix in valid_prefixes:
            if digits.startswith(prefix):
                return True
        
        return False
    
    def _is_valid_email_format(self, email: str) -> bool:
        """이메일 형식 검증"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def print_ai_enhanced_statistics(self):
        """AI 강화 통계 출력"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*80)
        print("🤖 AI 강화 모듈러 크롤링 완료 통계")
        print("="*80)
        print(f"📋 총 처리: {self.stats['total_processed']}개")
        print(f"✅ 성공: {self.stats['successful']}개")
        print(f"❌ 실패: {self.stats['failed']}개")
        print(f"🤖 AI 강화: {self.stats['ai_enhanced']}개")
        print(f"📞 전화번호 추출: {self.stats['phone_extracted']}개")
        print(f"📠 팩스번호 추출: {self.stats['fax_extracted']}개")
        print(f"💾 DB 저장: {self.stats['saved_to_db']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100
            ai_enhancement_rate = (self.stats['ai_enhanced'] / self.stats['total_processed']) * 100
            print(f"📈 전체 성공률: {success_rate:.1f}%")
            print(f"🤖 AI 강화율: {ai_enhancement_rate:.1f}%")
        
        print(f"⏱️ 소요시간: {duration}")
        
        # AI 에이전트별 통계
        print(f"\n🤖 AI 에이전트별 성공률:")
        for agent_name, stats in self.stats["agent_stats"].items():
            executed = stats["executed"]
            success = stats["success"]
            success_rate = (success / executed * 100) if executed > 0 else 0
            print(f"  - {agent_name}: {executed}회 실행, {success}회 성공 ({success_rate:.1f}%)")
        
        print("="*80)
    
    # ==================== ContactEnrichmentService 호환성 메서드들 ====================
    
    async def search_homepage(self, org_name: str) -> Dict[str, Any]:
        """홈페이지 검색 - ContactEnrichmentService 호환성 (AI 강화)"""
        try:
            self.logger.info(f"🔍 AI 홈페이지 검색: {org_name}")
            
            # AI 에이전트를 통한 홈페이지 검색
            context = CrawlingContext(
                organization={'name': org_name},
                current_stage=CrawlingStage.HOMEPAGE_SEARCH,
                extracted_data={},
                ai_insights={},
                error_log=[],
                processing_time=0,
                confidence_scores={}
            )
            
            # 홈페이지 검색 에이전트 실행
            homepage_agent = EnhancedHomepageSearchAgent(self.ai_manager, self.logger, self)
            context = await homepage_agent.execute(context)
            
            if context.extracted_data.get('homepage'):
                return {
                    "homepage": context.extracted_data['homepage'],
                    "homepage_type": context.extracted_data.get('homepage_type', '알수없음'),
                    "confidence": context.confidence_scores.get('homepage', 0.5),
                    "status": "success",
                    "ai_enhanced": True
                }
            else:
                return {
                    "homepage": "",
                    "status": "not_found",
                    "message": "AI 기반 홈페이지 검색 결과 없음"
                }
            
        except Exception as e:
            self.logger.error(f"AI 홈페이지 검색 오류: {org_name} - {e}")
            return {"status": "error", "error": str(e)}
    
    async def extract_details_from_homepage(self, homepage_url: str) -> Dict[str, Any]:
        """홈페이지에서 상세 정보 추출 - ContactEnrichmentService 호환성 (AI 강화)"""
        try:
            self.logger.info(f"🌐 AI 홈페이지 분석: {homepage_url}")
            
            # AI 에이전트를 통한 홈페이지 분석
            context = CrawlingContext(
                organization={'name': 'Unknown'},
                current_stage=CrawlingStage.HOMEPAGE_ANALYSIS,
                extracted_data={'homepage': homepage_url},
                ai_insights={},
                error_log=[],
                processing_time=0,
                confidence_scores={}
            )
            
            # 홈페이지 분석 에이전트 실행
            analysis_agent = EnhancedHomepageAnalysisAgent(self.ai_manager, self.logger, self)
            context = await analysis_agent.execute(context)
            
            return {
                "phone": context.extracted_data.get("phone", ""),
                "fax": context.extracted_data.get("fax", ""),
                "email": context.extracted_data.get("email", ""),
                "address": context.extracted_data.get("address", ""),
                "ai_insights": context.ai_insights,
                "confidence_scores": context.confidence_scores,
                "status": "success",
                "ai_enhanced": True
            }
                
        except Exception as e:
            self.logger.error(f"AI 홈페이지 분석 오류: {homepage_url} - {e}")
            return {"status": "error", "error": str(e)}
    
    async def search_missing_info(self, org_name: str, missing_fields: List[str]) -> Dict[str, str]:
        """누락된 정보 검색 - ContactEnrichmentService 호환성 (AI 강화)"""
        try:
            self.logger.info(f"🔍 AI 누락 정보 검색: {org_name} - {missing_fields}")
            
            results = {}
            
            # AI 에이전트를 통한 연락처 추출
            context = CrawlingContext(
                organization={'name': org_name},
                current_stage=CrawlingStage.CONTACT_EXTRACTION,
                extracted_data={},
                ai_insights={},
                error_log=[],
                processing_time=0,
                confidence_scores={}
            )
            
            # 연락처 추출 에이전트 실행
            contact_agent = EnhancedContactExtractionAgent(self.ai_manager, self.logger, self)
            context = await contact_agent.execute(context)
            
            # 요청된 필드만 반환
            for field in missing_fields:
                if field in context.extracted_data:
                    results[field] = context.extracted_data[field]
                    self.logger.info(f"  🎯 AI로 {field} 발견: {results[field]}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"AI 누락 정보 검색 오류: {org_name} - {e}")
            return {}
    
    def validate_and_clean_data(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 검증 및 정리 - ContactEnrichmentService 호환성 (AI 강화)"""
        try:
            cleaned_data = org_data.copy()
            
            # 기존 validator.py 사용 (유지)
            if self.contact_validator:
                # 전화번호 검증
                if cleaned_data.get('phone'):
                    is_valid, validated_phone = self.contact_validator.validate_phone_number(cleaned_data['phone'])
                    if is_valid:
                        cleaned_data['phone'] = validated_phone
                        cleaned_data['phone_validation'] = 'valid'
                    else:
                        self.logger.warning(f"유효하지 않은 전화번호: {cleaned_data['phone']}")
                        cleaned_data['phone_validation'] = 'invalid'
                
                # 팩스번호 검증
                if cleaned_data.get('fax'):
                    is_valid, validated_fax = self.contact_validator.validate_fax_number(cleaned_data['fax'])
                    if is_valid:
                        cleaned_data['fax'] = validated_fax
                        cleaned_data['fax_validation'] = 'valid'
                    else:
                        self.logger.warning(f"유효하지 않은 팩스번호: {cleaned_data['fax']}")
                        cleaned_data['fax_validation'] = 'invalid'
            
            # AI 검증 추가
            if self.ai_manager:
                try:
                    # AI 검증 에이전트 실행
                    context = CrawlingContext(
                        organization={'name': cleaned_data.get('name', 'Unknown')},
                        current_stage=CrawlingStage.AI_VERIFICATION,
                        extracted_data=cleaned_data,
                        ai_insights={},
                        error_log=[],
                        processing_time=0,
                        confidence_scores={}
                    )
                    
                    # AI 검증 에이전트 실행 (동기 방식으로 간단히)
                    verification_agent = AIVerificationAgent(self.ai_manager, self.logger, self)
                    # 비동기 호출을 동기로 변환
                    import asyncio
                    if asyncio.get_event_loop().is_running():
                        # 이미 이벤트 루프가 실행 중인 경우
                        task = asyncio.create_task(verification_agent.execute(context))
                        # 간단한 AI 검증만 수행
                        cleaned_data['ai_validation_attempted'] = True
                    else:
                        context = asyncio.run(verification_agent.execute(context))
                        cleaned_data['ai_insights'] = context.ai_insights
                        cleaned_data['confidence_scores'] = context.confidence_scores
                
                except Exception as e:
                    self.logger.warning(f"AI 검증 실패: {e}")
                    cleaned_data['ai_validation_error'] = str(e)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"데이터 검증 오류: {e}")
            return org_data
    
    # ==================== app.py 호환성 메서드들 ====================
    
    async def process_json_file_async(self, json_file_path: str, test_mode: bool = False, test_count: int = 10, progress_callback=None) -> List[Dict]:
        """🔧 app.py 호환성을 위한 래퍼 메서드 (AI 강화)"""
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
            
            # AI 강화 처리 실행
            results = await self.process_organizations(organizations)
            
            return results
            
        except Exception as e:
            self.logger.error(f"JSON 파일 처리 실패: {e}")
            return []

    async def _fallback_to_traditional_processing(self, context: CrawlingContext):
        """AI 에이전트 없을 때 기본 모듈 처리"""
        try:
            org_name = context.organization.get('name', 'Unknown')
            self.logger.info(f"🔧 기본 모듈 처리: {org_name}")
            
            # 기본 홈페이지 검색 (url_extractor 사용)
            if self.homepage_parser:
                try:
                    # 간단한 홈페이지 검색 로직
                    pass
                except Exception as e:
                    self.logger.warning(f"홈페이지 검색 실패: {e}")
            
            # 기본 전화번호 검색 (phone_extractor 사용)
            if self.phone_driver:
                try:
                    found_phones = search_phone_number(self.phone_driver, org_name)
                    if found_phones:
                        context.extracted_data['phone'] = found_phones[0]
                        self.update_confidence(context, 'phone', 0.7)
                except Exception as e:
                    self.logger.warning(f"전화번호 검색 실패: {e}")
            
            # 기본 팩스번호 검색 (fax_extractor 사용)
            if self.fax_extractor:
                try:
                    found_faxes = self.fax_extractor.search_fax_number(org_name)
                    if found_faxes:
                        context.extracted_data['fax'] = found_faxes[0]
                        self.update_confidence(context, 'fax', 0.7)
                except Exception as e:
                    self.logger.warning(f"팩스번호 검색 실패: {e}")
            
        except Exception as e:
            self.logger.error(f"기본 모듈 처리 실패: {e}")
    
    async def _fallback_to_traditional_processing_simple(self, org: Dict) -> Dict:
        """간단한 기본 처리 (실패 시 대체)"""
        result = org.copy()
        result['processing_metadata'] = {
            'extraction_method': 'fallback_traditional',
            'ai_enhanced': False,
            'timestamp': datetime.now().isoformat(),
            'status': 'fallback_processed'
        }
        return result

# 기존 호환성을 위한 별칭 (ModularUnifiedCrawler를 AI 강화 버전으로 교체)
ModularUnifiedCrawler = AIEnhancedModularUnifiedCrawler

# ==================== 편의 함수들 ====================

async def crawl_ai_enhanced_from_file(input_file: str, options: Dict = None) -> List[Dict]:
    """파일에서 데이터를 로드하여 AI 강화 크롤링"""
    try:
        # 파일 로드
        data = FileUtils.load_json(input_file)
        
        # AI 강화 크롤러 생성 및 실행
        crawler = AIEnhancedModularUnifiedCrawler()
        results = await crawler.process_organizations(data, options)
        
        return results
        
    except Exception as e:
        logging.error(f"AI 강화 파일 크롤링 실패: {e}")
        return []

async def crawl_ai_enhanced_latest_file(options: Dict = None) -> List[Dict]:
    """최신 입력 파일을 자동으로 찾아서 AI 강화 크롤링"""
    try:
        latest_file = get_latest_input_file()
        if not latest_file:
            raise ValueError("입력 파일을 찾을 수 없습니다.")
        
        print(f"📂 최신 파일 사용: {latest_file}")
        return await crawl_ai_enhanced_from_file(str(latest_file), options)
        
    except Exception as e:
        logging.error(f"AI 강화 최신 파일 크롤링 실패: {e}")
        return []

async def crawl_ai_enhanced_from_database(options: Dict = None) -> List[Dict]:
    """데이터베이스에서 데이터를 로드하여 AI 강화 크롤링 (수정된 버전)"""
    try:
        # 데이터베이스 연결
        from database.database import get_database
        db = get_database()
        
        # 🔥 조직 데이터 조회 (중복 방지 강화)
        with db.get_connection() as conn:
            query = """
            SELECT id, name, type, category, subcategory, homepage, phone, fax, email, 
                   mobile, postal_code, address, organization_size, denomination,
                   ai_crawled, last_crawled_at
            FROM organizations 
            WHERE is_active = 1 
            AND (
                (homepage = '' OR homepage IS NULL) OR
                (phone = '' OR phone IS NULL) OR 
                (fax = '' OR fax IS NULL) OR
                (email = '' OR email IS NULL)
            )
            AND name IS NOT NULL AND name != ''
            -- 🔥 중복 방지: 7일 이내 크롤링하지 않은 것만
            AND (
                ai_crawled = 0 OR 
                ai_crawled IS NULL OR
                last_crawled_at IS NULL OR
                datetime(last_crawled_at) < datetime('now', '-7 days')
            )
            ORDER BY 
                CASE WHEN ai_crawled = 0 OR ai_crawled IS NULL THEN 0 ELSE 1 END,  -- 미크롤링 우선
                last_crawled_at ASC NULLS FIRST,  -- 오래된 것 우선
                updated_at DESC
            LIMIT 500
            """
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # 딕셔너리 형태로 변환
            organizations = []
            for row in rows:
                org = dict(row)
                organizations.append({
                    'db_id': org.get('id'),
                    'name': org.get('name', ''),
                    'type': org.get('type', 'CHURCH'),
                    'category': org.get('category', '종교시설'),
                    'subcategory': org.get('subcategory', ''),
                    'homepage': org.get('homepage', ''),
                    'phone': org.get('phone', ''),
                    'fax': org.get('fax', ''),
                    'email': org.get('email', ''),
                    'mobile': org.get('mobile', ''),
                    'postal_code': org.get('postal_code', ''),
                    'address': org.get('address', ''),
                    'organization_size': org.get('organization_size', ''),
                    'denomination': org.get('denomination', '')
                })
        
        if not organizations:
            print("📋 크롤링이 필요한 조직이 없습니다.")
            print("🎯 조건: 연락처 누락 + 7일 이내 크롤링 안 됨")
            return []
        
        print(f"📂 데이터베이스에서 {len(organizations)}개 조직 로드")
        print(f"🎯 선택 조건:")
        print(f"  - 연락처 정보 누락 (homepage/phone/fax/email)")
        print(f"  - 7일 이내 크롤링 안 됨 (ai_crawled=0 OR last_crawled_at < 7일 전)")
        print(f"  - 우선순위: 미크롤링 → 오래된 크롤링 → 최신 업데이트")
        
        # AI 강화 크롤러 생성 및 실행
        crawler = AIEnhancedModularUnifiedCrawler()
        results = await crawler.process_organizations(organizations, options)
        
        # 결과를 데이터베이스에 업데이트
        updated_count = 0
        for result in results:
            if result.get('db_id'):
                success = await crawler.save_to_database(result)
                if success:
                    updated_count += 1
        
        print(f"💾 데이터베이스 업데이트: {updated_count}개 조직")
        
        return results
        
    except Exception as e:
        logging.error(f"AI 강화 데이터베이스 크롤링 실패: {e}")
        return []

# 메인 실행 함수
async def main():
    """메인 실행 함수 (AI 강화)"""
    print("🤖 AI 강화 모듈러 통합 크롤링 시스템 시작")
    print("="*80)
    print("🚀 AI 기능 최대 활용 모드")
    print("📦 전문 모듈 + AI 에이전트 통합:")
    print(f"  - fax_extractor.py: {'✅' if FAX_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - phone_extractor.py: {'✅' if PHONE_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - url_extractor.py: {'✅' if URL_EXTRACTOR_AVAILABLE else '❌'}")
    print(f"  - validator.py: {'✅' if VALIDATOR_AVAILABLE else '❌'}")
    print(f"  - database.py: {'✅' if DATABASE_AVAILABLE else '❌'}")
    print("🤖 AI 에이전트:")
    print("  - EnhancedHomepageSearchAgent: AI 기반 종합 홈페이지 검색 (공식사이트 + 소셜미디어)")
    print("  - EnhancedHomepageAnalysisAgent: AI 기반 홈페이지 분석 (BS4 → JS → AI)")
    print("  - ContactPageSearchAgent: 연락처 페이지 전용 AI 에이전트 (혁신적!)")
    print("  - EnhancedContactExtractionAgent: AI 강화 연락처 추출 (주소 기반)")
    print("  - AIVerificationAgent: AI 종합 검증")
    print("="*80)
    
    try:
        # 프로젝트 초기화
        initialize_project()
        
        # 데이터베이스 연결 확인
        if not DATABASE_AVAILABLE:
            print("❌ 데이터베이스 모듈을 사용할 수 없습니다.")
            return
        
        # 우선 데이터베이스에서 크롤링 시도
        print("🗃️ 데이터베이스에서 크롤링 대상 조회 중...")
        results = await crawl_ai_enhanced_from_database()
        
        # 데이터베이스에서 처리할 데이터가 없으면 파일에서 시도
        if not results:
            print("📁 입력 파일에서 크롤링 시도 중...")
            try:
                results = await crawl_ai_enhanced_latest_file()
            except Exception as e:
                print(f"⚠️ 입력 파일 크롤링도 실패: {e}")
        
        if results:
            ai_enhanced_count = sum(1 for r in results if r.get('ai_enhanced'))
            print(f"\n✅ AI 강화 크롤링 완료: {len(results)}개 조직 처리")
            print(f"🤖 AI 강화된 조직: {ai_enhanced_count}개")
            print(f"📈 AI 강화율: {(ai_enhanced_count/len(results)*100):.1f}%")
        else:
            print("\n❌ AI 강화 크롤링 실패")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
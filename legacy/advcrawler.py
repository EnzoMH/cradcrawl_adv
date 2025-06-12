#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 교회/기관/공부방 /기관/공부방 연락처 크롤러
홈페이지를 크롤링하고 AI를 활용하여 연락처 정보를 정확하게 추출합니다.
"""

import json
import requests
import asyncio
import re
import time
import random
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import logging

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경변수 로드
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않음. pip install python-dotenv 실행 필요")
    print("💡 수동으로 환경변수 설정을 시도합니다...")
    
    # .env 파일 수동 로드
    try:
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')  # 따옴표 제거
                        os.environ[key] = value
            print("✅ .env 파일 수동 로드 완료")
        else:
            print("❌ .env 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ .env 파일 로드 실패: {e}")

from bs4 import BeautifulSoup
from parser import WebPageParser
from validator import ContactValidator, AIValidator
from ai_helpers import AIModelManager
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedChurchCrawler:
    def __init__(self):
        """초기화"""
        self.setup_logger()
        
        # API 키 확인
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            print(f"🔑 GEMINI_API_KEY 로드 성공: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
            print("💡 .env 파일에 GEMINI_API_KEY='your_api_key' 형식으로 저장했는지 확인하세요.")
        
        # 컴포넌트 초기화
        self.web_parser = WebPageParser()
        self.validator = ContactValidator()
        
        # AI 매니저 초기화
        self.ai_manager = None
        self.use_ai = False
        
        try:
            if api_key:
                self.ai_manager = AIModelManager()
                self.use_ai = True
                print("🤖 AI 모델 매니저 초기화 성공")
            else:
                print("🔧 AI 기능 비활성화 (API 키 없음)")
        except Exception as e:
            print(f"❌ AI 모델 매니저 초기화 실패: {e}")
            self.ai_manager = None
            self.use_ai = False
        
        # 구글 검색 기반 연락처 검색기 (지연 초기화)
        self.google_searcher = None
        
        # URL 추출기 추가
        try:
            from legacy.url_extractor_enhanced import URLExtractorEnhanced
            self.url_extractor = URLExtractorEnhanced(headless=False)
            print("🔍 URL 추출기 초기화 성공")
        except ImportError:
            print("⚠️ URL 추출기 import 실패")
            self.url_extractor = None
        
        # 크롤링 설정
        self.timeout = 15  # 타임아웃 증가
        self.max_retries = 3
        self.delay_range = (2, 5)  # 딜레이 증가
        
        # 통계 (구글 검색 통계 추가)
        self.stats = {
            'total_processed': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'ai_enhanced': 0,
            'contacts_found': 0,
            'api_calls_made': 0,
            'ai_failures': 0,
            'google_searches_performed': 0,  # 새 통계
            'google_contacts_found': 0       # 새 통계
        }
        
        # 세션 설정 (기존 유지)
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
        
        # AI 검증기
        try:
            from validator import AIValidator
            self.ai_validator = AIValidator()
            print("🔍 AI URL/연락처 검증기 초기화 성공")
        except ImportError:
            print("⚠️ AI 검증기 import 실패")
            self.ai_validator = None
        except Exception as e:
            print(f"❌ AI 검증기 초기화 실패: {e}")
            self.ai_validator = None
        
        print("🚀 고급 크롤러 초기화 완료 - 구글 검색 기능 포함")

    def setup_logger(self):
        """로거 설정"""
        self.logger = logging.getLogger('adv_crawler')
        self.logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter('%(asctime)s - [고급크롤러] - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def load_json_data(self, filepath: str) -> List[Dict]:
        """JSON 파일 로드"""
        try:
            print(f"📂 JSON 파일 로딩: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                print(f"✅ {len(data)}개 교회/기관/공부방  데이터 로드 완료")
                return data
            else:
                print("❌ 지원하지 않는 JSON 형식입니다.")
                return []
                
        except Exception as e:
            print(f"❌ JSON 파일 로딩 실패: {e}")
            return []
    
    def fetch_webpage(self, url: str) -> Optional[str]:
        """웹페이지 내용 가져오기"""
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        try:
            self.logger.info(f"웹페이지 요청: {url}")
            
            response = self.session.get(
                url, 
                timeout=self.timeout, 
                verify=False,
                allow_redirects=True
            )
            
            # 인코딩 설정
            response.encoding = response.apparent_encoding or 'utf-8'
            
            if response.status_code == 200:
                self.logger.info(f"웹페이지 가져오기 성공: {url}")
                return response.text
            else:
                self.logger.warning(f"HTTP 오류 {response.status_code}: {url}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.warning(f"타임아웃: {url}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"요청 실패: {url} - {e}")
            return None
        except Exception as e:
            self.logger.error(f"예상치 못한 오류: {url} - {e}")
            return None
    
    def fetch_webpage_enhanced(self, url: str, max_retries: int = 3) -> Optional[str]:
        """강화된 웹페이지 가져오기 (차단 우회)"""
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
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
                'Cache-Control': 'max-age=0'
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
                
                # 요청 파라미터
                request_params = {
                    'timeout': (10, 30),  # (연결, 읽기) 타임아웃
                    'verify': False,
                    'allow_redirects': True,
                    'stream': False
                }
                
                # 리퍼러 설정 (2번째 시도부터)
                if attempt > 0:
                    parsed_url = urlparse(url)
                    referer = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    self.session.headers['Referer'] = referer
                
                response = self.session.get(url, **request_params)
                
                # 응답 상태 확인
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
                            self.logger.info(f"{delay:.1f}초 대기 후 재시도...")
                            time.sleep(delay)
                            continue
                        else:
                            return None
                    
                    self.logger.info(f"웹페이지 가져오기 성공: {url}")
                    return content
                    
                elif response.status_code == 403:
                    self.logger.warning(f"접근 거부 (403) - 시도 {attempt + 1}: {url}")
                    
                    if attempt < max_retries - 1:
                        # 더 긴 대기
                        delay = random.uniform(10, 20)
                        time.sleep(delay)
                        continue
                        
                elif response.status_code == 429:
                    self.logger.warning(f"요청 제한 (429) - 시도 {attempt + 1}: {url}")
                    
                    if attempt < max_retries - 1:
                        # 매우 긴 대기
                        delay = random.uniform(30, 60)
                        self.logger.info(f"요청 제한으로 인한 {delay:.1f}초 대기...")
                        time.sleep(delay)
                        continue
                        
                else:
                    self.logger.warning(f"HTTP 오류 {response.status_code} (시도 {attempt + 1}): {url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"타임아웃 (시도 {attempt + 1}): {url}")
                
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}): {url}")
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}): {url} - {e}")
                
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
            'access denied',
            'forbidden',
            'blocked',
            '접근이 거부',
            '차단된',
            'cloudflare',
            'checking your browser',
            'ddos protection',
            'security check',
            'captcha'
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
            
            # 연락처 관련 섹션 추출 (수정된 부분)
            contact_keywords = ['연락처', 'contact', '전화', 'phone', '팩스', 'fax', '이메일', 'email']
            # text= 대신 string= 사용
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
            
            # 이메일은 기본 검증만 (validator에 이메일 검증 함수가 없으므로)
            validated_data['emails'] = extracted_data.get('emails', [])
            validated_data['addresses'] = extracted_data.get('addresses', [])
            
            # 우편번호 추출 (주소에서)
            for address in validated_data['addresses']:
                postal_matches = re.findall(r'\b\d{5}\b', address)
                for postal in postal_matches:
                    if postal not in validated_data['postal_codes']:
                        validated_data['postal_codes'].append(postal)
            
            self.logger.info(f"Validator 검증 완료: {len(validated_data['phones'])}개 유효 전화번호, "
                           f"{len(validated_data['faxes'])}개 유효 팩스번호")
            
            return validated_data
            
        except Exception as e:
            self.logger.error(f"Validator 검증 오류: {e}")
            return extracted_data
    
    async def enhance_with_ai(self, parsed_data: Dict[str, Any], church_name: str) -> Dict[str, List]:
        """AI를 이용한 추가 추출"""
        if not self.use_ai or not self.ai_manager:
            print(f"  🔧 AI 기능 비활성화 - 기본 추출만 사용")
            return {}
        
        try:
            print(f"  🤖 AI 추가 추출 시작: {church_name}")
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
            prompt_template = """
'{church_name}' 교회/기관/공부방 의 연락처 정보를 정확하게 추출해주세요.

**교회/기관/공부방 명:** {church_name}

**추출할 정보:**
- 전화번호: 한국 형식 (02-1234-5678, 031-123-4567, 010-1234-5678)
- 팩스번호: 한국 형식 (02-1234-5679)
- 이메일: 유효한 형식 (info@church.com)
- 휴대폰: 010으로 시작하는 번호
- 우편번호: 5자리 숫자
- 주소: 완전한 주소

**응답 형식:** (정확히 지켜주세요)
```markdown
## 연락처 정보

**전화번호:** [발견된 번호 또는 "없음"]
**팩스번호:** [발견된 번호 또는 "없음"]  
**이메일:** [발견된 이메일 또는 "없음"]
**휴대폰:** [발견된 휴대폰 또는 "없음"]
**우편번호:** [발견된 우편번호 또는 "없음"]
**주소:** [발견된 주소 또는 "없음"]
```

**중요 규칙:**
1. {church_name}와 직접 관련된 연락처만 추출
2. 대표번호, 메인 연락처 우선
3. 대표번화와 팩스번호는 일치하지 않으니 이점 확실히 할 것
4. 확실하지 않으면 "없음"으로 표시

**분석할 텍스트:**
{{text_content}}
"""
            
            # 프롬프트에 교회/기관/공부방 명과 텍스트 삽입
            final_prompt = prompt_template.format(church_name=church_name)
            
            # AI 호출
            ai_response = await self.ai_manager.extract_with_gemini(ai_text, final_prompt)
            
            if ai_response:
                ai_extracted = self.parse_ai_response(ai_response)
                self.stats['ai_enhanced'] += 1
                print(f"  ✅ AI 추출 완료: {church_name}")
                return ai_extracted
            else:
                print(f"  ⚠️ AI 응답 없음: {church_name}")
                self.stats['ai_failures'] += 1
                return {}
                
        except Exception as e:
            print(f"  ❌ AI 추출 오류 ({church_name}): {e}")
            self.stats['ai_failures'] += 1
            self.logger.error(f"AI 추출 오류 ({church_name}): {e}")
            return {}
    
    def parse_ai_response(self, ai_response: str) -> Dict[str, List]:
        """AI 응답을 파싱하여 구조화"""
        try:
            result = {
                'phones': [],
                'faxes': [],
                'emails': [],
                'mobiles': [],
                'postal_codes': [],
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
                            elif '휴대폰' in key or 'mobile' in key:
                                if value.startswith('010') and self._is_valid_phone_format(value):
                                    result['mobiles'].append(value)
                            elif '우편번호' in key or 'postal' in key:
                                if re.match(r'^\d{5}$', value):
                                    result['postal_codes'].append(value)
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
    
    def merge_ai_and_parser_results(self, ai_result: Dict, parser_result: Dict) -> Dict:
        """AI 결과와 파서 결과 병합"""
        merged = {
            'phone': [],
            'fax': [],
            'email': [],
            'address': [],
            'postal_code': []
        }
        
        # AI 결과 우선, 파서 결과로 보완
        field_mappings = [
            ('phones', 'phone'),
            ('faxes', 'fax'),
            ('emails', 'email'),
            ('addresses', 'address'),
            ('postal_codes', 'postal_code')
        ]
        
        for ai_field, merged_field in field_mappings:
            # AI 결과
            ai_values = ai_result.get(ai_field, [])
            # 파서 결과
            parser_values = parser_result.get(ai_field, [])
            
            # 중복 제거하여 병합
            all_values = list(set(ai_values + parser_values))
            merged[merged_field] = all_values[0] if all_values else ""
        
        return merged
    
    async def process_single_church(self, church_data: Dict) -> Dict:
        """단일 교회/기관 처리 (URL 검색 + 연락처 추출 + 구글 검색)"""
        church_name = church_data.get('name', 'Unknown')
        homepage = church_data.get('homepage', '')
        
        print(f"\n🏢 처리 중: {church_name}")
        
        result = church_data.copy()
        extraction_summary = {
            'url_search_performed': False,
            'homepage_status': 'existing' if homepage else 'none',
            'parser_extracted': {},
            'validator_result': {},
            'ai_enhanced': {},
            'google_search_result': {},  # 구글 검색 결과 추가
            'final_merged': {},
            'extraction_timestamp': datetime.now().isoformat(),
            'ai_used': self.use_ai
        }
        
        self.stats['total_processed'] += 1
        
        # 구글 검색 기반 연락처 검색 초기화 (안전한 초기화)
        if not hasattr(self, 'google_searcher') or self.google_searcher is None:
            try:
                print("  🔧 구글 검색기 초기화 중...")
                self.google_searcher = GoogleContactSearcher()
                print("  ✅ 구글 검색기 초기화 성공")
            except Exception as e:
                print(f"  ❌ 구글 검색기 초기화 실패: {e}")
                self.google_searcher = None
        
        # 홈페이지가 없는 경우 URL 검색
        if not homepage and self.url_extractor:
            print(f"  🔍 홈페이지 URL 검색 중...")
            try:
                homepage = self.url_extractor.search_organization_homepage(church_name)
                if homepage:
                    result['homepage'] = homepage
                    extraction_summary['url_search_performed'] = True
                    extraction_summary['homepage_status'] = 'found'
                    print(f"  ✅ 홈페이지 발견: {homepage}")
                else:
                    print(f"  ❌ 홈페이지 검색 실패")
                    extraction_summary['homepage_status'] = 'not_found'
            except Exception as e:
                print(f"  ❌ 홈페이지 검색 오류: {e}")
                extraction_summary['homepage_status'] = 'search_error'
        
        # 1단계: 구글 검색으로 연락처 직접 검색 (우선 시도)
        google_contacts = {'phones': [], 'faxes': [], 'emails': [], 'addresses': []}
        
        if self.google_searcher is not None:
            try:
                print(f"  🔎 구글 검색으로 연락처 정보 검색...")
                google_contacts = await self.google_searcher.search_organization_contacts(church_name)
                extraction_summary['google_search_result'] = google_contacts
                self.stats['google_searches_performed'] += 1
                
                if sum(len(v) for v in google_contacts.values()) > 0:
                    self.stats['google_contacts_found'] += 1
            except Exception as e:
                print(f"  ❌ 구글 검색 오류: {e}")
                extraction_summary['google_search_result'] = {'error': str(e)}
        else:
            print(f"  ⚠️ 구글 검색기 사용 불가 - 건너뜀")
            extraction_summary['google_search_result'] = {'disabled': 'GoogleContactSearcher 초기화 실패'}
        
        # 구글 검색 결과가 충분한 경우 홈페이지 크롤링 생략
        google_contact_count = sum(len(v) for v in google_contacts.values())
        skip_homepage_crawl = google_contact_count >= 3
        
        if skip_homepage_crawl:
            print(f"  ⚡ 구글 검색에서 충분한 연락처 발견 ({google_contact_count}개), 홈페이지 크롤링 생략")
        
        # 2단계: 홈페이지가 있고 구글 검색이 불충분한 경우에만 크롤링
        parser_result = {}
        validator_result = {}
        ai_result = {}
        
        if homepage and not skip_homepage_crawl:
            try:
                # 웹페이지 가져오기 (강화된 버전 사용)
                print(f"  🌐 홈페이지 접속: {homepage}")
                html_content = self.fetch_webpage_enhanced(homepage)
                
                if html_content:
                    # BS4로 파싱
                    print(f"  📄 HTML 파싱 중...")
                    parsed_data = self.parse_with_bs4(html_content, homepage)
                    extraction_summary['homepage_status'] = 'parsed'
                    
                    # parser.py로 기본 추출
                    print(f"  🔍 기본 연락처 추출 중...")
                    parser_result = self.extract_with_parser(parsed_data)
                    extraction_summary['parser_extracted'] = parser_result
                    
                    # validator.py로 검증
                    print(f"  ✅ 연락처 검증 중...")
                    validator_result = self.validate_with_validator(parser_result)
                    extraction_summary['validator_result'] = validator_result
                    
                    # AI로 추가 추출
                    ai_result = await self.enhance_with_ai(parsed_data, church_name)
                    extraction_summary['ai_enhanced'] = ai_result
                    
                    extraction_summary['homepage_status'] = 'completed'
                    self.stats['successful_crawls'] += 1
                else:
                    print(f"  ❌ 홈페이지 접속 실패")
                    extraction_summary['homepage_status'] = 'fetch_failed'
                    self.stats['failed_crawls'] += 1
                    
            except Exception as e:
                print(f"  ❌ 홈페이지 처리 오류: {e}")
                extraction_summary['homepage_status'] = 'error'
                extraction_summary['error'] = str(e)
                self.stats['failed_crawls'] += 1
        
        # 3단계: 모든 결과 병합 (구글 검색 결과 포함)
        print(f"  🔄 결과 병합 중...")
        merged_result = self.merge_all_results(google_contacts, ai_result, parser_result)
        extraction_summary['final_merged'] = merged_result
        
        # 4단계: 기존 빈 값을 추출된 값으로 업데이트
        contact_fields = ['phone', 'fax', 'email', 'mobile', 'postal_code', 'address']
        updated_fields = []
        
        for field in contact_fields:
            if not result.get(field) and merged_result.get(field):
                result[field] = merged_result[field]
                updated_fields.append(field)
        
        if updated_fields:
            print(f"  ✨ 업데이트된 필드: {', '.join(updated_fields)}")
            self.stats['contacts_found'] += 1
        
        extraction_summary['updated_fields'] = updated_fields
        result['extraction_summary'] = extraction_summary
        
        print(f"  ✅ 처리 완료: {church_name}")
        return result

    def merge_all_results(self, google_result: Dict, ai_result: Dict, parser_result: Dict) -> Dict:
        """구글 검색, AI, 파서 결과를 모두 병합 (우선순위: 구글 > AI > 파서)"""
        merged = {
            'phone': '',
            'fax': '',
            'email': '',
            'address': '',
            'postal_code': ''
        }
        
        # 필드별 매핑
        field_mappings = {
            'phone': ['phones'],
            'fax': ['faxes'],
            'email': ['emails'],
            'address': ['addresses'],
            'postal_code': ['postal_codes']
        }
        
        for merged_field, source_fields in field_mappings.items():
            # 1순위: 구글 검색 결과
            for source_field in source_fields:
                if google_result.get(source_field):
                    merged[merged_field] = google_result[source_field][0]
                    break
            
            # 2순위: AI 결과 (구글에서 찾지 못한 경우)
            if not merged[merged_field]:
                for source_field in source_fields:
                    if ai_result.get(source_field):
                        merged[merged_field] = ai_result[source_field][0]
                        break
            
            # 3순위: 파서 결과 (둘 다 없는 경우)
            if not merged[merged_field]:
                for source_field in source_fields:
                    if parser_result.get(source_field):
                        merged[merged_field] = parser_result[source_field][0]
                        break
        
        return merged
    
    async def process_all_churches(self, churches_data: List[Dict]) -> List[Dict]:
        """모든 교회/기관/공부방  처리"""
        print(f"\n🚀 총 {len(churches_data)}개 교회/기관/공부방  처리 시작")
        
        results = []
        
        for i, church in enumerate(churches_data):
            print(f"\n📍 진행상황: {i+1}/{len(churches_data)}")
            
            # 교회/기관/공부방  처리
            result = await self.process_single_church(church)
            results.append(result)
            
            # 중간 저장 (50개마다)
            if (i + 1) % 50 == 0:
                await self.save_intermediate_results(results, i + 1)
            
            # 요청 간격 조절
            delay = random.uniform(*self.delay_range)
            await asyncio.sleep(delay)
        
        return results
    
    async def save_intermediate_results(self, results: List[Dict], count: int):
        """중간 결과 저장 (이전 파일 자동 삭제)"""
        try:
            # 이전 중간 파일 삭제 (현재 저장할 파일 제외)
            self.cleanup_previous_intermediate_files(count)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"churches_enhanced_intermediate_{count}_{timestamp}.json"
            
            # 실제 저장되는 데이터 개수 확인
            actual_count = len(results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 중간 저장 완료: {filename}")
            print(f"📊 저장된 데이터: {actual_count}개 (처리 진행률: {count}개)")
            
            # 데이터 개수 불일치 경고
            if actual_count != count:
                print(f"⚠️ 데이터 개수 불일치! 예상: {count}개, 실제: {actual_count}개")
            
        except Exception as e:
            print(f"❌ 중간 저장 실패: {e}")

    def cleanup_previous_intermediate_files(self, current_count: int):
        """이전 중간 파일들 삭제 (현재 저장할 파일 제외)"""
        try:
            # churches_enhanced_intermediate_*.json 패턴으로 파일 찾기
            intermediate_files = glob.glob("churches_enhanced_intermediate_*.json")
            
            if not intermediate_files:
                return
            
            deleted_count = 0
            for file in intermediate_files:
                try:
                    # 파일명에서 카운트 추출
                    # 패턴: churches_enhanced_intermediate_{count}_{timestamp}.json
                    parts = os.path.basename(file).split('_')
                    if len(parts) >= 4:
                        try:
                            file_count = int(parts[3])  # count 부분 추출
                            
                            # 현재 저장할 파일의 카운트보다 작은 경우에만 삭제
                            if file_count < current_count:
                                # 파일 크기 확인 (디버깅용)
                                file_size = os.path.getsize(file)
                                print(f"🗑️ 삭제할 파일: {file} (크기: {file_size:,} bytes)")
                                
                                os.remove(file)
                                deleted_count += 1
                        except ValueError:
                            print(f"⚠️ 파일명에서 카운트 추출 실패: {file}")
                            continue
                                
                except (OSError, IOError) as e:
                    print(f"⚠️ 파일 삭제 중 오류 ({file}): {e}")
                    continue
            
            if deleted_count > 0:
                print(f"✅ {deleted_count}개 이전 중간 파일 삭제 완료")
                
        except Exception as e:
            print(f"❌ 이전 파일 정리 중 오류: {e}")
    
    def save_final_results(self, results: List[Dict]) -> str:
        """최종 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"churches_enhanced_final_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 최종 결과 저장: {filename}")
            
            # 중간 파일들 정리
            print("🧹 중간 파일 정리 중...")
            self.cleanup_intermediate_files()
            
            return filename
            
        except Exception as e:
            print(f"❌ 최종 저장 실패: {e}")
            return ""
    
    def cleanup_intermediate_files(self):
        """모든 중간 파일 정리"""
        try:
            intermediate_files = glob.glob("churches_enhanced_intermediate_*.json")
            
            if not intermediate_files:
                print("📁 정리할 중간 파일이 없습니다.")
                return
            
            deleted_count = 0
            total_size = 0
            
            for file in intermediate_files:
                try:
                    file_size = os.path.getsize(file)
                    total_size += file_size
                    print(f"🗑️ 중간 파일 삭제: {file} (크기: {file_size:,} bytes)")
                    os.remove(file)
                    deleted_count += 1
                except OSError as e:
                    print(f"⚠️ 파일 삭제 실패 ({file}): {e}")
            
            if deleted_count > 0:
                print(f"✅ {deleted_count}개 중간 파일 정리 완료 (총 {total_size:,} bytes 절약)")
            
        except Exception as e:
            print(f"❌ 중간 파일 정리 중 오류: {e}")

    def save_final_results(self, results: List[Dict]) -> str:
        """최종 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"churches_enhanced_final_{timestamp}.json"
            
            # 실제 저장할 데이터 개수 확인
            actual_count = len(results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 파일 크기 확인
            file_size = os.path.getsize(filename)
            
            print(f"✅ 최종 결과 저장: {filename}")
            print(f"📊 저장된 데이터: {actual_count}개")
            print(f"📁 파일 크기: {file_size:,} bytes")
            
            # 중간 파일들 정리
            print("🧹 중간 파일 정리 중...")
            self.cleanup_intermediate_files()
            
            return filename
            
        except Exception as e:
            print(f"❌ 최종 저장 실패: {e}")
            return ""
        
    def validate_final_data(self, results: List[Dict], expected_count: int):
        """최종 데이터 검증"""
        actual_count = len(results)
        
        print(f"\n🔍 데이터 검증:")
        print(f"  예상 개수: {expected_count}개")
        print(f"  실제 개수: {actual_count}개")
        
        if actual_count != expected_count:
            print(f"⚠️ 데이터 개수 불일치!")
            
            # 중복 데이터 확인
            names = [item.get('name', '') for item in results]
            unique_names = set(names)
            duplicates = len(names) - len(unique_names)
            
            if duplicates > 0:
                print(f"🔍 중복된 기관명: {duplicates}개")
                
                # 중복 제거
                seen_names = set()
                unique_results = []
                
                for item in results:
                    name = item.get('name', '')
                    if name not in seen_names:
                        unique_results.append(item)
                        seen_names.add(name)
                    else:
                        print(f"  중복 제거: {name}")
                
                print(f"✅ 중복 제거 후: {len(unique_results)}개")
                return unique_results
        
        print(f"✅ 데이터 검증 완료")
        return results

    def print_final_statistics(self):
        """최종 통계 출력"""
        print(f"\n📊 크롤링 완료 통계:")
        print(f"  📋 총 처리: {self.stats['total_processed']}개")
        print(f"  ✅ 성공: {self.stats['successful_crawls']}개")
        print(f"  ❌ 실패: {self.stats['failed_crawls']}개")
        print(f"  🔍 구글 검색 수행: {self.stats['google_searches_performed']}개")
        print(f"  📞 구글에서 연락처 발견: {self.stats['google_contacts_found']}개")
        print(f"  🤖 AI 호출: {self.stats['api_calls_made']}회")
        print(f"  🎯 AI 성공: {self.stats['ai_enhanced']}개")
        print(f"  ⚠️ AI 실패: {self.stats['ai_failures']}개")
        print(f"  📞 총 연락처 발견: {self.stats['contacts_found']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_crawls'] / self.stats['total_processed']) * 100
            print(f"  📈 성공률: {success_rate:.1f}%")
        
        if self.stats['api_calls_made'] > 0:
            ai_success_rate = (self.stats['ai_enhanced'] / self.stats['api_calls_made']) * 100
            print(f"  🤖 AI 성공률: {ai_success_rate:.1f}%")
        
        if self.stats['google_searches_performed'] > 0:
            google_success_rate = (self.stats['google_contacts_found'] / self.stats['google_searches_performed']) * 100
            print(f"  🔍 구글 검색 성공률: {google_success_rate:.1f}%")

class GoogleContactSearcher:
    """구글 검색을 통한 연락처 정보 직접 검색"""
    
    def __init__(self):
        try:
            self.session = requests.Session()
            # 더 다양한 User-Agent 로테이션
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            self.current_ua_index = 0
            
            # 검색 통계
            self.search_stats = {
                'google_searches': 0,
                'successful_extractions': 0,
                'blocked_attempts': 0
            }
            
            # 세션 설정
            self.setup_session()
            
            print("🔍 GoogleContactSearcher 초기화 완료")
            
        except Exception as e:
            print(f"❌ GoogleContactSearcher 초기화 중 오류: {e}")
            raise
    
    def setup_session(self):
        """세션 설정 강화"""
        try:
            # User-Agent 로테이션
            ua = self.user_agents[self.current_ua_index % len(self.user_agents)]
            self.current_ua_index += 1
            
            self.session.headers.clear()
            self.session.headers.update({
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })
            
        except Exception as e:
            print(f"❌ 세션 설정 오류: {e}")
            # 기본 헤더라도 설정
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def search_google_with_retry(self, query: str, max_retries: int = 3) -> Optional[str]:
        """재시도 로직이 포함된 구글 검색"""
        for attempt in range(max_retries):
            try:
                # User-Agent 변경
                if attempt > 0:
                    self.setup_session()
                
                # 구글 검색 URL
                search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=ko&num=10"
                
                print(f"  🔍 구글 검색 시도 {attempt + 1}/{max_retries}: {query}")
                
                response = self.session.get(
                    search_url,
                    timeout=15,
                    verify=False
                )
                
                self.search_stats['google_searches'] += 1
                
                if response.status_code == 200:
                    # 차단 감지
                    if self.is_blocked_response(response.text):
                        print(f"  ⚠️ 구글 차단 감지 (시도 {attempt + 1})")
                        self.search_stats['blocked_attempts'] += 1
                        
                        if attempt < max_retries - 1:
                            delay = random.uniform(10, 20)  # 긴 대기
                            print(f"  ⏳ {delay:.1f}초 대기 후 재시도...")
                            time.sleep(delay)
                            continue
                        else:
                            return None
                    
                    return response.text
                else:
                    print(f"  ❌ HTTP 오류 {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 검색 오류 (시도 {attempt + 1}): {e}")
                
            # 재시도 전 대기
            if attempt < max_retries - 1:
                delay = random.uniform(5, 10)
                time.sleep(delay)
        
        return None
    
    def is_blocked_response(self, html: str) -> bool:
        """구글 차단 응답 감지"""
        if not html:
            return True
            
        block_indicators = [
            'unusual traffic',
            'automated queries',
            'captcha',
            'blocked',
            'suspicious activity',
            'Our systems have detected',
            '비정상적인 트래픽'
        ]
        
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in block_indicators)
    
    
    def extract_contacts_from_search_results(self, html: str, organization_name: str) -> Dict[str, List]:
        """구글 검색 결과에서 연락처 정보 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 모든 텍스트 추출
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
                r'\b\d{3}-\d{3,4}-\d{4}\b',         # 031-123-4567
                r'\b010-\d{4}-\d{4}\b',             # 010-1234-5678
                r'\b0\d{1,2}\.\d{3,4}\.\d{4}\b',    # 02.1234.5678
                r'\b\d{3}\.\d{3,4}\.\d{4}\b'        # 031.123.4567
            ]
            
            # 팩스 패턴 (FAX, 팩스 키워드 포함)
            fax_patterns = [
                r'(?:fax|팩스|팩시밀리)[:：\s]*(\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4})',
                r'(?:F|f)[:：\s]*(\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4})'
            ]
            
            # 이메일 패턴
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            
            # 전화번호 추출
            for pattern in phone_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    # 정규화
                    clean_phone = re.sub(r'[^\d-]', '', match)
                    if len(clean_phone) >= 9 and clean_phone not in contacts['phones']:
                        contacts['phones'].append(clean_phone)
            
            # 팩스 추출
            for pattern in fax_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                for match in matches:
                    clean_fax = re.sub(r'[^\d-]', '', match)
                    if len(clean_fax) >= 9 and clean_fax not in contacts['faxes']:
                        contacts['faxes'].append(clean_fax)
            
            # 이메일 추출
            email_matches = re.findall(email_pattern, all_text)
            for email in email_matches:
                if email not in contacts['emails']:
                    contacts['emails'].append(email)
            
            # 기관명과 연관성 필터링
            filtered_contacts = self.filter_relevant_contacts(contacts, organization_name, all_text)
            
            if any(len(v) > 0 for v in filtered_contacts.values()):
                self.search_stats['successful_extractions'] += 1
            
            return filtered_contacts
            
        except Exception as e:
            print(f"  ❌ 연락처 추출 오류: {e}")
            return {'phones': [], 'faxes': [], 'emails': [], 'addresses': []}
    
    def filter_relevant_contacts(self, contacts: Dict[str, List], org_name: str, context: str) -> Dict[str, List]:
        """기관명과 연관성이 높은 연락처만 필터링"""
        try:
            filtered = {key: [] for key in contacts.keys()}
            
            # 기관명 키워드 추출
            org_keywords = re.findall(r'[가-힣a-zA-Z]+', org_name.lower())
            
            for contact_type, contact_list in contacts.items():
                for contact in contact_list:
                    # 연락처 주변 텍스트 확인
                    contact_context = self.get_contact_context(contact, context, 100)
                    
                    # 기관명이 연락처 근처에 있는지 확인
                    relevance_score = 0
                    for keyword in org_keywords:
                        if len(keyword) > 2 and keyword in contact_context.lower():
                            relevance_score += 1
                    
                    # 연관성이 있거나 연락처가 적은 경우 포함
                    if relevance_score > 0 or len(contact_list) <= 2:
                        filtered[contact_type].append(contact)
            
            return filtered
        except Exception as e:
            print(f"  ❌ 연락처 필터링 오류: {e}")
            return contacts  # 필터링 실패시 원본 반환
    
    def get_contact_context(self, contact: str, full_text: str, window_size: int = 100) -> str:
        """연락처 주변 텍스트 추출"""
        try:
            index = full_text.find(contact)
            if index == -1:
                return ""
            
            start = max(0, index - window_size)
            end = min(len(full_text), index + len(contact) + window_size)
            
            return full_text[start:end]
        except:
            return ""
    
    async def search_organization_contacts(self, organization_name: str) -> Dict[str, List]:
        """기관명으로 연락처 정보 검색"""
        print(f"  📞 구글 검색으로 연락처 찾기: {organization_name}")
        
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
                f'"{organization_name}" 대표번호',
                f'"{organization_name}" 팩스번호',
                f'"{organization_name}" 이메일',
                f'{organization_name} tel phone',
                f'{organization_name} contact'
            ]
            
            # 각 쿼리로 검색
            for i, query in enumerate(search_queries):
                try:
                    print(f"  🔍 쿼리 {i+1}/{len(search_queries)}: {query}")
                    
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
                        
                        # 연락처를 충분히 찾았으면 중단
                        total_found = sum(len(v) for v in all_contacts.values())
                        if total_found >= 5:  # 충분한 연락처 발견
                            print(f"  ✅ 충분한 연락처 발견 ({total_found}개), 검색 중단")
                            break
                    
                    # 검색 간격
                    delay = random.uniform(2, 5)
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    print(f"  ❌ 쿼리 검색 오류: {e}")
                    continue
            
            total_found = sum(len(v) for v in all_contacts.values())
            print(f"  📊 총 {total_found}개 연락처 발견: "
                  f"전화 {len(all_contacts['phones'])}개, "
                  f"팩스 {len(all_contacts['faxes'])}개, "
                  f"이메일 {len(all_contacts['emails'])}개")
        
        except Exception as e:
            print(f"  ❌ 전체 검색 과정에서 오류: {e}")
        
        return all_contacts
    
async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 고급 교회/기관/공부방  연락처 크롤러 v2.0")
    print("=" * 60)
    
    # 환경변수 확인
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"🔑 API 키 확인: ...{api_key[-10:]}")
    else:
        print("⚠️ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("🔧 AI 기능 없이 기본 크롤링만 수행됩니다.")
    
    # 크롤러 인스턴스 생성
    crawler = AdvancedChurchCrawler()
    
    # 입력 파일 경로 설정 (사용자 지정)
    input_file = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\raw_data_with_homepages_20250609_134906.json"
    
    # 파일 존재 확인
    if not os.path.exists(input_file):
        print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
        
        # 현재 디렉토리에서 대체 파일 찾기
        alternative_files = glob.glob("raw_data_with_homepages_*.json")
        if alternative_files:
            latest_file = max(alternative_files, key=os.path.getctime)
            print(f"🔍 대신 사용할 파일을 찾았습니다: {latest_file}")
            input_file = latest_file
        else:
            print("❌ 대체 파일도 찾을 수 없습니다. 프로그램을 종료합니다.")
            return
    
    # JSON 파일 로드
    churches_data = crawler.load_json_data(input_file)
    
    if not churches_data:
        print("❌ 데이터 로드 실패. 프로그램을 종료합니다.")
        return
    
    print(f"📂 입력 파일: {input_file}")
    print(f"📊 처리할 교회/기관/공부방  수: {len(churches_data)}")
    
    # 원본 데이터 개수 저장
    original_count = len(churches_data)
    
    # 처리할 개수 제한 옵션 추가
    max_process = input(f"처리할 교회/기관/공부방  수 (전체: {len(churches_data)}개, 엔터=전체): ").strip()
    
    if max_process and max_process.isdigit():
        max_process = int(max_process)
        churches_data = churches_data[:max_process]
        print(f"📊 실제 처리할 교회/기관/공부방  수: {len(churches_data)}")
        original_count = len(churches_data)  # 실제 처리할 개수로 업데이트
    
    # 사용자 확인
    print(f"\n⚠️ {len(churches_data)}개 교회/기관/공부방 의 홈페이지를 크롤링합니다.")
    print("이 작업은 시간이 오래 걸릴 수 있습니다.")
    
    proceed = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("❌ 사용자에 의해 취소되었습니다.")
        return
    
    try:
        # 모든 교회/기관/공부방  처리
        enhanced_results = await crawler.process_all_churches(churches_data)
        
        # 데이터 검증
        validated_results = crawler.validate_final_data(enhanced_results, original_count)
        
        # 최종 결과 저장
        output_file = crawler.save_final_results(validated_results)
        
        # 통계 출력
        crawler.print_final_statistics()
        
        print(f"\n🎉 크롤링 완료!")
        print(f"📁 출력 파일: {output_file}")
        print(f"📊 최종 데이터 개수: {len(validated_results)}개")
        
        # Excel 변환 옵션
        excel_convert = input("\nExcel 파일로 변환하시겠습니까? (y/N): ").strip().lower()
        if excel_convert in ['y', 'yes']:
            print("📊 Excel 변환을 위해 jsontoexcel.py를 실행하세요.")
            print(f"💡 명령어: python jsontoexcel.py")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
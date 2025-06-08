#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 교회 연락처 크롤러
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
from validator import ContactValidator
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
        
        # AI 매니저 초기화 (개선)
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
        
        # 크롤링 설정
        self.timeout = 10
        self.max_retries = 3
        self.delay_range = (1, 3)
        
        # 통계
        self.stats = {
            'total_processed': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'ai_enhanced': 0,
            'contacts_found': 0,
            'api_calls_made': 0,
            'ai_failures': 0
        }
        
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
                print(f"✅ {len(data)}개 교회 데이터 로드 완료")
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
            contact_elements = soup.find_all(text=re.compile('|'.join(contact_keywords), re.I))
            
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
'{church_name}' 교회의 연락처 정보를 정확하게 추출해주세요.

**교회명:** {church_name}

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
3. 확실하지 않으면 "없음"으로 표시

**분석할 텍스트:**
{{text_content}}
"""
            
            # 프롬프트에 교회명과 텍스트 삽입
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
    
    def merge_extraction_results(self, parser_result: Dict, validator_result: Dict, ai_result: Dict) -> Dict:
        """모든 추출 결과를 병합"""
        merged = {
            'phone': [],
            'fax': [],
            'email': [],
            'mobile': [],
            'postal_code': [],
            'address': []
        }
        
        try:
            # 전화번호 병합 (검증된 것 우선)
            all_phones = validator_result.get('phones', []) + parser_result.get('phones', []) + ai_result.get('phones', [])
            merged['phone'] = list(dict.fromkeys(all_phones))  # 중복 제거
            
            # 팩스번호 병합
            all_faxes = validator_result.get('faxes', []) + parser_result.get('faxes', []) + ai_result.get('faxes', [])
            merged['fax'] = list(dict.fromkeys(all_faxes))
            
            # 이메일 병합
            all_emails = validator_result.get('emails', []) + parser_result.get('emails', []) + ai_result.get('emails', [])
            merged['email'] = list(dict.fromkeys(all_emails))
            
            # 휴대폰 병합 (AI 결과 우선)
            merged['mobile'] = list(dict.fromkeys(ai_result.get('mobiles', [])))
            
            # 우편번호 병합
            all_postals = validator_result.get('postal_codes', []) + ai_result.get('postal_codes', [])
            merged['postal_code'] = list(dict.fromkeys(all_postals))
            
            # 주소 병합
            all_addresses = validator_result.get('addresses', []) + parser_result.get('addresses', []) + ai_result.get('addresses', [])
            merged['address'] = list(dict.fromkeys(all_addresses))
            
            # 최대 1개씩만 유지 (가장 첫 번째 값)
            for key in merged:
                if merged[key]:
                    merged[key] = merged[key][0]  # 첫 번째 값만
                else:
                    merged[key] = ""  # 빈 문자열
            
            return merged
            
        except Exception as e:
            self.logger.error(f"결과 병합 오류: {e}")
            return merged
    
    async def process_single_church(self, church_data: Dict) -> Dict:
        """단일 교회 처리"""
        church_name = church_data.get('name', 'Unknown')
        homepage = church_data.get('homepage', '')
        
        print(f"\n🏢 처리 중: {church_name}")
        self.logger.info(f"교회 처리 시작: {church_name}")
        
        result = church_data.copy()  # 기존 데이터 복사
        
        # 추출된 연락처 정보 초기화
        extraction_summary = {
            'parser_extracted': {},
            'validator_result': {},
            'ai_enhanced': {},
            'final_merged': {},
            'extraction_timestamp': datetime.now().isoformat(),
            'homepage_status': 'not_processed',
            'ai_used': self.use_ai
        }
        
        self.stats['total_processed'] += 1
        
        # 홈페이지가 없는 경우
        if not homepage:
            print(f"  ⚠️ 홈페이지 URL 없음")
            extraction_summary['homepage_status'] = 'no_url'
            result['extraction_summary'] = extraction_summary
            return result
        
        try:
            # 1단계: 웹페이지 가져오기
            print(f"  🌐 홈페이지 접속: {homepage}")
            html_content = self.fetch_webpage(homepage)
            
            if not html_content:
                print(f"  ❌ 홈페이지 접속 실패")
                extraction_summary['homepage_status'] = 'fetch_failed'
                self.stats['failed_crawls'] += 1
                result['extraction_summary'] = extraction_summary
                return result
            
            # 2단계: BS4로 파싱
            print(f"  📄 HTML 파싱 중...")
            parsed_data = self.parse_with_bs4(html_content, homepage)
            extraction_summary['homepage_status'] = 'parsed'
            
            # 3단계: parser.py로 기본 추출
            print(f"  🔍 기본 연락처 추출 중...")
            parser_result = self.extract_with_parser(parsed_data)
            extraction_summary['parser_extracted'] = parser_result
            
            # 4단계: validator.py로 검증
            print(f"  ✅ 연락처 검증 중...")
            validator_result = self.validate_with_validator(parser_result)
            extraction_summary['validator_result'] = validator_result
            
            # 5단계: AI로 추가 추출
            ai_result = await self.enhance_with_ai(parsed_data, church_name)
            extraction_summary['ai_enhanced'] = ai_result
            
            # 6단계: 결과 병합
            print(f"  🔄 결과 병합 중...")
            merged_result = self.merge_extraction_results(parser_result, validator_result, ai_result)
            extraction_summary['final_merged'] = merged_result
            
            # 7단계: 기존 빈 값을 추출된 값으로 업데이트
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
            extraction_summary['homepage_status'] = 'completed'
            self.stats['successful_crawls'] += 1
            
            print(f"  ✅ 처리 완료: {church_name}")
            
        except Exception as e:
            print(f"  ❌ 처리 오류: {e}")
            extraction_summary['homepage_status'] = 'error'
            extraction_summary['error'] = str(e)
            self.stats['failed_crawls'] += 1
            self.logger.error(f"교회 처리 오류 ({church_name}): {e}")
        
        result['extraction_summary'] = extraction_summary
        return result
    
    async def process_all_churches(self, churches_data: List[Dict]) -> List[Dict]:
        """모든 교회 처리"""
        print(f"\n🚀 총 {len(churches_data)}개 교회 처리 시작")
        
        results = []
        
        for i, church in enumerate(churches_data):
            print(f"\n📍 진행상황: {i+1}/{len(churches_data)}")
            
            # 교회 처리
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
        """중간 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"churches_enhanced_intermediate_{count}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 중간 저장 완료: {filename} ({count}개 처리됨)")
            
        except Exception as e:
            print(f"❌ 중간 저장 실패: {e}")
    
    def cleanup_intermediate_files(self):
        """중간 결과 파일들 일괄 삭제"""
        try:
            # churches_enhanced_intermediate_*.json 패턴으로 파일 찾기
            intermediate_files = glob.glob("churches_enhanced_intermediate_*.json")
            
            if not intermediate_files:
                print("🗂️ 삭제할 중간 파일이 없습니다.")
                return
            
            deleted_count = 0
            for file in intermediate_files:
                try:
                    os.remove(file)
                    print(f"🗑️ 삭제됨: {file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 파일 삭제 실패 ({file}): {e}")
            
            print(f"✅ 중간 파일 정리 완료: {deleted_count}개 파일 삭제")
            
        except Exception as e:
            print(f"❌ 중간 파일 정리 실패: {e}")
    
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
    
    def print_final_statistics(self):
        """최종 통계 출력"""
        print(f"\n📊 크롤링 완료 통계:")
        print(f"  📋 총 처리: {self.stats['total_processed']}개")
        print(f"  ✅ 성공: {self.stats['successful_crawls']}개")
        print(f"  ❌ 실패: {self.stats['failed_crawls']}개")
        print(f"  🤖 AI 호출: {self.stats['api_calls_made']}회")
        print(f"  🎯 AI 성공: {self.stats['ai_enhanced']}개")
        print(f"  ⚠️ AI 실패: {self.stats['ai_failures']}개")
        print(f"  📞 연락처 발견: {self.stats['contacts_found']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_crawls'] / self.stats['total_processed']) * 100
            print(f"  📈 성공률: {success_rate:.1f}%")
        
        if self.stats['api_calls_made'] > 0:
            ai_success_rate = (self.stats['ai_enhanced'] / self.stats['api_calls_made']) * 100
            print(f"  🤖 AI 성공률: {ai_success_rate:.1f}%")

async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 고급 교회 연락처 크롤러 v2.0")
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
    
    # JSON 파일 로드
    input_file = "combined_20250605_131931.json"
    churches_data = crawler.load_json_data(input_file)
    
    if not churches_data:
        print("❌ 데이터 로드 실패. 프로그램을 종료합니다.")
        return
    
    print(f"📂 입력 파일: {input_file}")
    print(f"📊 처리할 교회 수: {len(churches_data)}")
    
    # 사용자 확인
    print(f"\n⚠️ {len(churches_data)}개 교회의 홈페이지를 크롤링합니다.")
    print("이 작업은 시간이 오래 걸릴 수 있습니다.")
    
    try:
        # 모든 교회 처리
        enhanced_results = await crawler.process_all_churches(churches_data)
        
        # 최종 결과 저장
        output_file = crawler.save_final_results(enhanced_results)
        
        # 통계 출력
        crawler.print_final_statistics()
        
        print(f"\n🎉 크롤링 완료!")
        print(f"📁 출력 파일: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
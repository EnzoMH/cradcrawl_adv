#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전화번호 및 팩스번호 검증 및 정제 모듈
더미 데이터 제거, 중복 검증, 형식 검증 등을 수행
"""

import re
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

class ContactValidator:
    def __init__(self):
        # 전화번호 정규식 패턴 (Finding_Church_Fax.py와 동일)
        self.phone_pattern = re.compile(
            r'(?:\+?82[-\s]?)?'  # 선택적 국가번호
            r'(0\d{1,2})'        # 지역번호 (0으로 시작, 1~2자리)
            r'[-\.\)\s]?'        # 구분자 (하이픈, 점, 오른쪽 괄호, 공백 등)
            r'(\d{3,4})'         # 중간 번호 (3~4자리)
            r'[-\.\s]?'          # 구분자
            r'(\d{4})',          # 마지막 번호 (4자리)
            re.IGNORECASE
        )
        
        # 더미 데이터 패턴들
        self.dummy_patterns = [
            r'033-333-3333',     # 033-333-3333
            r'02-222-2222',      # 02-222-2222
            r'031-111-1111',     # 031-111-1111
            r'(\d)\1{2}-\1{3}-\1{4}',  # 같은 숫자 반복 (예: 111-1111-1111)
            r'0\d{1,2}-000-0000',      # 끝자리가 모두 0
            r'0\d{1,2}-123-4567',      # 순차적 숫자
            r'0\d{1,2}-1234-5678',     # 순차적 숫자
            r'000-000-0000',           # 모두 0
            r'999-999-9999',           # 모두 9
        ]
        
        # 유효한 지역번호 목록
        self.valid_area_codes = [
            '02',   # 서울
            '031',  # 경기
            '032',  # 인천
            '033',  # 강원
            '041',  # 충남
            '042',  # 대전
            '043',  # 충북
            '044',  # 세종
            '051',  # 부산
            '052',  # 울산
            '053',  # 대구
            '054',  # 경북
            '055',  # 경남
            '061',  # 전남
            '062',  # 광주
            '063',  # 전북
            '064',  # 제주
            '070',  # 인터넷전화
            '010',  # 휴대폰
        ]
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('contact_validator')
        logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - [검증기] - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def normalize_phone_number(self, phone):
        """전화번호 정규화 (하이픈 추가, 공백 제거 등)"""
        if not phone:
            return ""
        
        # 숫자만 추출
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # 국가번호 제거 (+82, 82)
        if digits_only.startswith('82'):
            digits_only = '0' + digits_only[2:]
        
        # 길이 검증 (10-11자리)
        if len(digits_only) < 10 or len(digits_only) > 11:
            return ""
        
        # 지역번호별 포맷팅
        if digits_only.startswith('02'):
            # 서울 (02-XXXX-XXXX 또는 02-XXX-XXXX)
            if len(digits_only) == 10:
                return f"{digits_only[:2]}-{digits_only[2:5]}-{digits_only[5:]}"
            elif len(digits_only) == 9:
                return f"{digits_only[:2]}-{digits_only[2:5]}-{digits_only[5:]}"
        elif digits_only.startswith('0'):
            # 기타 지역 (0XX-XXXX-XXXX 또는 0XX-XXX-XXXX)
            if len(digits_only) == 11:
                return f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:]}"
            elif len(digits_only) == 10:
                return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
        
        return ""
    
    def is_dummy_data(self, phone):
        """더미 데이터 여부 검증"""
        if not phone:
            return True
        
        # 정규화된 번호로 검증
        normalized = self.normalize_phone_number(phone)
        if not normalized:
            return True
        
        # 더미 패턴 검사
        for pattern in self.dummy_patterns:
            if re.match(pattern, normalized):
                self.logger.info(f"더미 데이터 감지: {normalized} (패턴: {pattern})")
                print(f"🗑️ 더미 데이터 제거: {normalized}")
                return True
        
        return False
    
    def is_valid_area_code(self, phone):
        """유효한 지역번호 검증"""
        if not phone:
            return False
        
        normalized = self.normalize_phone_number(phone)
        if not normalized:
            return False
        
        # 지역번호 추출
        area_code = normalized.split('-')[0]
        
        if area_code in self.valid_area_codes:
            return True
        else:
            self.logger.warning(f"유효하지 않은 지역번호: {area_code} in {normalized}")
            print(f"⚠️ 유효하지 않은 지역번호: {normalized}")
            return False
    
    def validate_phone_number(self, phone):
        """전화번호 종합 검증"""
        if not phone:
            return False, "빈 값"
        
        # 1. 더미 데이터 검사
        if self.is_dummy_data(phone):
            return False, "더미 데이터"
        
        # 2. 정규화 가능 여부
        normalized = self.normalize_phone_number(phone)
        if not normalized:
            return False, "형식 오류"
        
        # 3. 지역번호 검증
        if not self.is_valid_area_code(normalized):
            return False, "유효하지 않은 지역번호"
        
        # 4. 정규식 패턴 매칭
        if not self.phone_pattern.match(normalized):
            return False, "패턴 불일치"
        
        self.logger.info(f"전화번호 검증 성공: {normalized}")
        print(f"✅ 유효한 전화번호: {normalized}")
        return True, normalized
    
    def validate_fax_number(self, fax):
        """팩스번호 검증 (전화번호와 동일한 로직)"""
        if not fax:
            return False, "빈 값"
        
        # 팩스번호도 전화번호와 동일한 형식을 사용
        return self.validate_phone_number(fax)
    
    def extract_area_and_exchange(self, phone):
        """지역번호와 국번 추출 (전화번호-팩스번호 비교용)"""
        if not phone:
            return None, None
        
        normalized = self.normalize_phone_number(phone)
        if not normalized:
            return None, None
        
        parts = normalized.split('-')
        if len(parts) >= 2:
            area_code = parts[0]      # 지역번호 (02, 031 등)
            exchange = parts[1]       # 국번 (3~4자리)
            return area_code, exchange
        
        return None, None
    
    def is_phone_fax_duplicate(self, phone, fax):
        """전화번호와 팩스번호 중복 검증"""
        if not phone or not fax:
            return False
        
        # 정규화
        phone_normalized = self.normalize_phone_number(phone)
        fax_normalized = self.normalize_phone_number(fax)
        
        if not phone_normalized or not fax_normalized:
            return False
        
        # 완전 동일한 경우
        if phone_normalized == fax_normalized:
            self.logger.warning(f"전화번호-팩스번호 완전 중복: {phone_normalized}")
            print(f"🔄 전화번호-팩스번호 중복: {phone_normalized}")
            return True
        
        # 지역번호+국번이 동일한 경우 (일반적으로 같은 기관)
        phone_area, phone_exchange = self.extract_area_and_exchange(phone_normalized)
        fax_area, fax_exchange = self.extract_area_and_exchange(fax_normalized)
        
        if (phone_area == fax_area and phone_exchange == fax_exchange and 
            phone_area and phone_exchange):
            self.logger.info(f"전화번호-팩스번호 부분 중복 (지역번호+국번): {phone_area}-{phone_exchange}")
            print(f"📞📠 같은 기관 번호 (지역번호+국번 동일): {phone_area}-{phone_exchange}")
            return False  # 이 경우는 중복으로 보지 않음 (같은 기관의 다른 번호)
        
        return False
    
    def clean_contact_data(self, phone, fax):
        """연락처 데이터 정제 (메인 메서드)"""
        result = {
            "phone": "",
            "fax": "",
            "phone_valid": False,
            "fax_valid": False,
            "is_duplicate": False,
            "messages": []
        }
        
        print(f"🔍 연락처 검증 시작: 전화번호={phone}, 팩스번호={fax}")
        
        # 1. 전화번호 검증
        if phone:
            phone_valid, phone_result = self.validate_phone_number(phone)
            if phone_valid:
                result["phone"] = phone_result
                result["phone_valid"] = True
                result["messages"].append(f"전화번호 검증 성공: {phone_result}")
            else:
                result["messages"].append(f"전화번호 검증 실패: {phone_result}")
        
        # 2. 팩스번호 검증
        if fax:
            fax_valid, fax_result = self.validate_fax_number(fax)
            if fax_valid:
                result["fax"] = fax_result
                result["fax_valid"] = True
                result["messages"].append(f"팩스번호 검증 성공: {fax_result}")
            else:
                result["messages"].append(f"팩스번호 검증 실패: {fax_result}")
        
        # 3. 중복 검사 (둘 다 유효한 경우만)
        if result["phone_valid"] and result["fax_valid"]:
            if self.is_phone_fax_duplicate(result["phone"], result["fax"]):
                result["is_duplicate"] = True
                result["fax"] = ""  # 중복인 경우 팩스번호 제거
                result["fax_valid"] = False
                result["messages"].append("전화번호-팩스번호 중복으로 팩스번호 제거")
                print(f"🗑️ 중복으로 팩스번호 제거: {fax}")
        
        # 결과 출력
        print(f"📋 검증 결과:")
        print(f"  📞 전화번호: {result['phone']} ({'✅' if result['phone_valid'] else '❌'})")
        print(f"  📠 팩스번호: {result['fax']} ({'✅' if result['fax_valid'] else '❌'})")
        if result["is_duplicate"]:
            print(f"  🔄 중복 처리됨")
        
        return result

from ai_helpers import AIModelManager
import os
from dotenv import load_dotenv

import os
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from ai_helpers import AIModelManager
from legacy.constants import *

class AIValidator:
    """AI를 활용한 고급 검증 시스템"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # API 키 확인
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            print(f"🔑 GEMINI_API_KEY 로드 성공: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
        
        # AI 매니저 초기화
        self.ai_manager = None
        self.use_ai = False
        
        try:
            if api_key:
                self.ai_manager = AIModelManager()
                self.use_ai = True
                print("🤖 AI 검증 시스템 활성화")
            else:
                print("🔧 AI 기능 비활성화 (API 키 없음)")
        except Exception as e:
            print(f"❌ AI 모델 매니저 초기화 실패: {e}")
            self.ai_manager = None
            self.use_ai = False
    
    def _setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('AIValidator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - [AI검증] - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # =================================================================
    # 1. URL 적합성 검증 (가장 급한 것)
    # =================================================================
    
    async def validate_homepage_url_relevance(self, organization_name: str, url: str, 
                                            page_content: str = "", source: str = "unknown") -> Dict[str, Any]:
        """
        홈페이지 URL이 해당 기관과 관련성이 있는지 AI로 검증
        
        Args:
            organization_name: 기관명
            url: 검증할 URL
            page_content: 페이지 내용 (선택사항)
            source: 검색 소스 (naver, google 등)
        
        Returns:
            Dict with relevance score, confidence, reasoning
        """
        if not self.use_ai:
            return {"is_relevant": True, "confidence": 0.5, "reasoning": "AI 비활성화"}
        
        try:
            prompt = self._get_url_validation_prompt()
            
            # 페이지 내용이 있다면 앞부분만 사용 (토큰 제한)
            content_preview = ""
            if page_content:
                content_preview = page_content[:2000]
            
            final_prompt = prompt.format(
                organization_name=organization_name,
                url=url,
                source=source,
                content_preview=content_preview
            )
            
            self.logger.info(f"URL 관련성 검증 중: {organization_name} -> {url}")
            
            ai_response = await self.ai_manager.extract_with_gemini(
                f"기관명: {organization_name}\nURL: {url}\n페이지내용: {content_preview}",
                final_prompt
            )
            
            if ai_response:
                return self._parse_url_validation_response(ai_response)
            else:
                return {"is_relevant": True, "confidence": 0.5, "reasoning": "AI 응답 없음"}
                
        except Exception as e:
            self.logger.error(f"URL 검증 중 오류: {e}")
            return {"is_relevant": True, "confidence": 0.5, "reasoning": f"검증 오류: {e}"}
    
    def _get_url_validation_prompt(self) -> str:
        """URL 검증용 프롬프트"""
        return """
다음 URL이 해당 기관의 공식 홈페이지인지 검증해주세요.

**기관명:** {organization_name}
**URL:** {url}
**검색소스:** {source}
**페이지내용 미리보기:** 
{content_preview}

**검증 기준:**
1. 도메인명이 기관명과 관련성이 있는가?
2. 페이지 내용이 해당 기관 정보를 포함하는가?
3. 공식 홈페이지 형태인가? (블로그, 카페, 게시판 제외)
4. 도메인 신뢰도 (.or.kr, .go.kr, .ac.kr 등 공식 도메인 우대)

**응답 형식:**
```json
{{
    "is_relevant": true/false,
    "confidence": 0.0~1.0,
    "reasoning": "판단 근거 설명",
    "domain_score": 0~10,
    "content_score": 0~10,
    "official_score": 0~10
}}
```

**중요사항:**
- 확실하지 않으면 confidence를 낮게 설정
- 블로그, 카페, 뉴스기사는 is_relevant를 false로 설정
- 공식 도메인(.or.kr, .go.kr 등)은 높은 점수 부여
"""
    
    def _parse_url_validation_response(self, response: str) -> Dict[str, Any]:
        """URL 검증 응답 파싱"""
        try:
            # JSON 형태로 응답이 올 경우
            import json
            if '```json' in response:
                json_part = response.split('```json')[1].split('```')[0].strip()
                return json.loads(json_part)
            elif '{' in response and '}' in response:
                # JSON 부분만 추출
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            
            # 텍스트 파싱 fallback
            is_relevant = "true" in response.lower() and "is_relevant" in response.lower()
            confidence = 0.7 if is_relevant else 0.3
            
            return {
                "is_relevant": is_relevant,
                "confidence": confidence,
                "reasoning": response[:200],
                "domain_score": 5,
                "content_score": 5,
                "official_score": 5
            }
            
        except Exception as e:
            self.logger.error(f"URL 검증 응답 파싱 오류: {e}")
            return {
                "is_relevant": True,
                "confidence": 0.5,
                "reasoning": "파싱 오류",
                "domain_score": 5,
                "content_score": 5,
                "official_score": 5
            }
    
    # =================================================================
    # 2. 연락처 정보 추출 및 검증
    # =================================================================
    
    async def extract_and_validate_contacts(self, organization_name: str, 
                                          page_content: str) -> Dict[str, Any]:
        """
        페이지에서 연락처 정보를 추출하고 검증
        
        Args:
            organization_name: 기관명
            page_content: 페이지 내용
        
        Returns:
            Dict with extracted and validated contact information
        """
        if not self.use_ai:
            return self._fallback_contact_extraction(page_content)
        
        try:
            prompt = self._get_contact_extraction_prompt()
            
            # 내용 길이 제한
            content = page_content[:5000] if len(page_content) > 5000 else page_content
            
            final_prompt = prompt.format(
                organization_name=organization_name,
                content=content
            )
            
            self.logger.info(f"연락처 정보 AI 추출 중: {organization_name}")
            
            ai_response = await self.ai_manager.extract_with_gemini(content, final_prompt)
            
            if ai_response:
                extracted_data = self._parse_contact_response(ai_response)
                # AI 추출 결과를 constants.py 패턴으로 검증
                validated_data = self._validate_extracted_contacts(extracted_data)
                return validated_data
            else:
                return self._fallback_contact_extraction(page_content)
                
        except Exception as e:
            self.logger.error(f"연락처 추출 중 오류: {e}")
            return self._fallback_contact_extraction(page_content)
    
    def _get_contact_extraction_prompt(self) -> str:
        """연락처 추출용 프롬프트"""
        return """
'{organization_name}' 기관의 연락처 정보를 정확하게 추출해주세요.

**추출할 정보:**
1. **전화번호**: 한국 전화번호 형식 (02-1234-5678, 031-123-4567, 010-1234-5678)
2. **팩스번호**: 한국 팩스번호 형식 (전화번호와 구분)
3. **이메일**: 유효한 이메일 주소
4. **주소**: 완전한 주소 (우편번호 포함 선호)
5. **우편번호**: 5자리 숫자

**한국 전화번호 패턴:**
- 서울: 02-XXXX-XXXX
- 지역: 0XX-XXX(X)-XXXX
- 휴대폰: 010-XXXX-XXXX
- 대표번호와 팩스번호는 보통 다름

**응답 형식:**
```json
{{
    "phones": ["02-1234-5678"],
    "faxes": ["02-1234-5679"],
    "emails": ["info@example.org"],
    "addresses": ["서울시 강남구 테헤란로 123"],
    "postal_codes": ["12345"],
    "confidence": {{
        "phones": 0.9,
        "faxes": 0.8,
        "emails": 0.9,
        "addresses": 0.7,
        "postal_codes": 0.8
    }}
}}
```

**검증 규칙:**
- {organization_name}과 직접 관련된 연락처만 추출
- 광고, 배너의 연락처는 제외
- 대표번호 우선, 부서별 번호는 부차적
- 확실하지 않은 정보는 confidence를 낮게 설정

**분석할 내용:**
{content}
"""
    
    def _parse_contact_response(self, response: str) -> Dict[str, Any]:
        """연락처 추출 응답 파싱"""
        try:
            import json
            
            # JSON 형태 응답 처리
            if '```json' in response:
                json_part = response.split('```json')[1].split('```')[0].strip()
                return json.loads(json_part)
            elif '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            
            # 텍스트 파싱 fallback
            return self._text_parse_contacts(response)
            
        except Exception as e:
            self.logger.error(f"연락처 응답 파싱 오류: {e}")
            return self._text_parse_contacts(response)
    
    def _text_parse_contacts(self, text: str) -> Dict[str, Any]:
        """텍스트에서 연락처 정보 파싱"""
        result = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": [],
            "postal_codes": [],
            "confidence": {}
        }
        
        try:
            # constants.py의 패턴 활용
            for pattern in PHONE_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    if match and match not in result["phones"]:
                        result["phones"].append(match.strip())
            
            for pattern in FAX_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    if match and match not in result["faxes"]:
                        result["faxes"].append(match.strip())
            
            for pattern in EMAIL_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    if match and match not in result["emails"]:
                        result["emails"].append(match.strip())
            
            # 우편번호 추출
            postal_matches = re.findall(r'\b\d{5}\b', text)
            result["postal_codes"] = list(set(postal_matches))
            
            # 주소 추출 (간단한 패턴)
            address_matches = re.findall(r'[가-힣]+(?:시|군|구)\s+[가-힣\s\d\-]+(?:로|길|동)', text)
            result["addresses"] = list(set(address_matches))
            
        except Exception as e:
            self.logger.error(f"텍스트 파싱 오류: {e}")
        
        return result
    
    def _validate_extracted_contacts(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """추출된 연락처 정보를 constants.py 규칙으로 검증"""
        validated = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": [],
            "postal_codes": [],
            "validation_summary": {}
        }
        
        try:
            # 전화번호 검증
            for phone in extracted_data.get("phones", []):
                if self._validate_phone_with_constants(phone):
                    validated["phones"].append(phone)
            
            # 팩스번호 검증
            for fax in extracted_data.get("faxes", []):
                if self._validate_phone_with_constants(fax):
                    validated["faxes"].append(fax)
            
            # 이메일 검증
            for email in extracted_data.get("emails", []):
                if re.match(EMAIL_PATTERN, email):
                    validated["emails"].append(email)
            
            # 주소는 그대로 (기본 필터링만)
            validated["addresses"] = [addr for addr in extracted_data.get("addresses", []) if len(addr) > 10]
            
            # 우편번호 검증 (5자리 숫자)
            for postal in extracted_data.get("postal_codes", []):
                if re.match(r'^\d{5}$', postal):
                    validated["postal_codes"].append(postal)
            
            # 검증 요약
            validated["validation_summary"] = {
                "phones_validated": len(validated["phones"]),
                "faxes_validated": len(validated["faxes"]),
                "emails_validated": len(validated["emails"]),
                "addresses_found": len(validated["addresses"]),
                "postal_codes_found": len(validated["postal_codes"])
            }
            
        except Exception as e:
            self.logger.error(f"연락처 검증 오류: {e}")
        
        return validated
    
    def _validate_phone_with_constants(self, phone: str) -> bool:
        """constants.py 규칙으로 전화번호 검증"""
        try:
            # 숫자만 추출
            digits = re.sub(r'[^\d]', '', phone)
            
            # 최소 길이 체크
            if len(digits) < 9 or len(digits) > 11:
                return False
            
            # 지역번호 체크
            area_code = extract_phone_area_code(phone)
            if not area_code or not is_valid_area_code(area_code):
                return False
            
            # 더미 패턴 체크
            for pattern in DUMMY_PHONE_PATTERNS:
                if re.match(pattern, phone):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _fallback_contact_extraction(self, content: str) -> Dict[str, Any]:
        """AI 없을 때 기본 추출"""
        return {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": [],
            "postal_codes": [],
            "validation_summary": {"fallback": True}
        }
    
def main():
    """테스트 함수"""
    validator = ContactValidator()
    
    # 테스트 케이스들
    test_cases = [
        ("02-123-4567", "02-123-4568"),  # 정상 케이스
        ("033-333-3333", "033-444-4444"),  # 더미 데이터 포함
        ("02-123-4567", "02-123-4567"),  # 완전 중복
        ("031-123-4567", "031-123-5678"),  # 같은 기관 (지역번호+국번 동일)
        ("invalid", "02-123-4567"),  # 잘못된 형식
        ("", ""),  # 빈 값
    ]
    
    print("=" * 60)
    print("📋 연락처 검증기 테스트")
    print("=" * 60)
    
    for i, (phone, fax) in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 케이스 {i}: phone='{phone}', fax='{fax}'")
        result = validator.clean_contact_data(phone, fax)
        print("-" * 40)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전화번호 관련 유틸리티 통합
기존 4개 파일의 중복된 전화번호 검증/포맷팅 기능을 통합
"""

import re
import sys
import os

from typing import Optional, Tuple
from pathlib import Path

# 프로젝트 루트 디렉토리 동적 탐지
def find_project_root():
    """settings.py가 있는 프로젝트 루트 디렉토리를 찾습니다"""
    current_path = Path(__file__).resolve()
    
    # 상위 디렉토리들을 탐색하면서 settings.py 찾기
    for parent in current_path.parents:
        if (parent / 'settings.py').exists():
            return str(parent)
        # constants.py도 체크 (legacy 호환)
        elif (parent / 'constants.py').exists():
            return str(parent)
    
    # 찾지 못하면 현재 파일의 상위 디렉토리 반환
    return str(current_path.parent.parent)

# 프로젝트 루트를 sys.path에 추가
project_root = find_project_root()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# settings.py에서 필요한 함수들과 상수들 import
try:
    from .settings import (
        KOREAN_AREA_CODES,
        VALID_AREA_CODES, 
        AREA_CODE_LENGTH_RULES,
        PHONE_VALIDATION_PATTERN,
        # 함수들 import
        is_valid_area_code,
        extract_phone_area_code,
        format_phone_number as settings_format_phone_number
    )
    print("✅ settings.py에서 전화번호 유틸리티 import 성공")
except ImportError as e:
    print(f"Warning: settings.py import 실패 - {e}")
    # 기본값 사용...
    KOREAN_AREA_CODES = {
        "02": "서울", "031": "경기", "032": "인천", "033": "강원",
        "041": "충남", "042": "대전", "043": "충북", "044": "세종",
        "051": "부산", "052": "울산", "053": "대구", "054": "경북", 
        "055": "경남", "061": "전남", "062": "광주", "063": "전북", "064": "제주",
        "070": "인터넷전화", "010": "핸드폰", "017": "핸드폰"
    }
    VALID_AREA_CODES = list(KOREAN_AREA_CODES.keys())
    
    # 기본 함수들 정의
    def is_valid_area_code(area_code: str) -> bool:
        """유효한 지역번호인지 확인"""
        return area_code in VALID_AREA_CODES
    
    def extract_phone_area_code(phone: str) -> str:
        """전화번호에서 지역코드 추출"""
        if not phone:
            return None
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 지역코드 매칭
        for code in KOREAN_AREA_CODES.keys():
            if digits.startswith(code):
                return code
        
        return None
    
    def settings_format_phone_number(digits: str, area_code: str) -> str:
        """전화번호 포맷팅"""
        if area_code == "02":
            if len(digits) == 9:
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
            else:
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        elif area_code in ["010", "017", "070"]:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        else:
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    # 기본 PHONE_VALIDATION_PATTERN 정의
    PHONE_VALIDATION_PATTERN = re.compile(
        r'(?:\+?82[-\s]?)?'     # 선택적 국가번호
        r'(0\d{1,2})'                 # 지역번호 (0으로 시작, 1~2자리)
        r'[-\.\)\s]?'                 # 구분자 (하이픈, 점, 오른쪽 괄호, 공백 등)
        r'(\d{3,4})'                   # 중간 번호 (3~4자리)
        r'[-\.\s]?'                     # 구분자
        r'(\d{4})',                     # 마지막 번호 (4자리)
        re.IGNORECASE
    )

class PhoneUtils:
    """전화번호 관련 유틸리티 클래스 - 중복 제거"""
    
    @staticmethod
    def validate_korean_phone(phone: str) -> bool:
        """
        한국 전화번호 유효성 검증 (통합)
        data_statistics.py + fax_crawler.py + parser.py + validator.py 통합
        """
        if not phone:
            return False
        
        # 숫자만 추출
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # 국가번호 제거 (+82, 82)
        if digits_only.startswith('82'):
            digits_only = '0' + digits_only[2:]
        
        # 길이 검증 (9-11자리)
        if len(digits_only) < 9 or len(digits_only) > 11:
            return False
        
        # 지역번호 검증
        area_code = PhoneUtils.extract_area_code(digits_only)
        if not area_code or not is_valid_area_code(area_code):
            return False
        
        # 길이 규칙 검증 (AREA_CODE_LENGTH_RULES가 있을 때만)
        if 'AREA_CODE_LENGTH_RULES' in globals():
            length_rules = AREA_CODE_LENGTH_RULES.get(area_code, {})
            min_length = length_rules.get('min_length', 9)
            max_length = length_rules.get('max_length', 11)
            
            if not (min_length <= len(digits_only) <= max_length):
                return False
        
        # 정규식 패턴 검증
        formatted = PhoneUtils.format_phone_number(digits_only)
        if not formatted:
            return False
        
        return PHONE_VALIDATION_PATTERN.match(formatted) is not None
    
    @staticmethod
    def format_phone_number(phone: str) -> Optional[str]:
        """
        전화번호 포맷팅 (통합)
        4개 파일의 포맷팅 로직 통합
        """
        if not phone:
            return None
        
        # 숫자만 추출
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # 국가번호 제거
        if digits_only.startswith('82'):
            digits_only = '0' + digits_only[2:]
        
        # 길이 검증 (9-11자리)
        if len(digits_only) < 9 or len(digits_only) > 11:
            return None
        
        # 지역번호 추출
        area_code = PhoneUtils.extract_area_code(digits_only)
        if not area_code:
            return None
        
        # settings.py의 포맷팅 함수 활용
        try:
            return settings_format_phone_number(digits_only, area_code)
        except Exception as e:
            # fallback 포맷팅
            return PhoneUtils._fallback_format(digits_only, area_code)
    
    @staticmethod
    def _fallback_format(digits: str, area_code: str) -> str:
        """포맷팅 fallback 함수"""
        if area_code == "02":
            if len(digits) == 9:
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
            else:
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        elif area_code in ["010", "017", "070"]:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        else:
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    @staticmethod
    def extract_area_code(phone: str) -> Optional[str]:
        """
        지역번호 추출 (통합)
        settings.py 함수 활용
        """
        return extract_phone_area_code(phone)
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """
        전화번호 정규화 (validator.py에서 가져옴)
        하이픈 추가, 공백 제거 등
        """
        formatted = PhoneUtils.format_phone_number(phone)
        return formatted if formatted else ""
    
    @staticmethod
    def extract_area_and_exchange(phone: str) -> Tuple[Optional[str], Optional[str]]:
        """
        지역번호와 국번 추출 (validator.py에서 가져옴)
        전화번호-팩스번호 비교용
        """
        if not phone:
            return None, None
        
        normalized = PhoneUtils.normalize_phone_number(phone)
        if not normalized:
            return None, None
        
        parts = normalized.split('-')
        if len(parts) >= 2:
            area_code = parts[0]      # 지역번호 (02, 031 등)
            exchange = parts[1]       # 국번 (3~4자리)
            return area_code, exchange
        
        return None, None
    
    @staticmethod
    def is_phone_fax_duplicate(phone: str, fax: str) -> bool:
        """
        전화번호와 팩스번호 중복 검증 (validator.py에서 가져옴)
        """
        if not phone or not fax:
            return False
        
        # 정규화
        phone_normalized = PhoneUtils.normalize_phone_number(phone)
        fax_normalized = PhoneUtils.normalize_phone_number(fax)
        
        if not phone_normalized or not fax_normalized:
            return False
        
        # 완전 동일한 경우
        if phone_normalized == fax_normalized:
            return True
        
        # 지역번호+국번이 동일한 경우는 중복으로 보지 않음 (같은 기관의 다른 번호)
        phone_area, phone_exchange = PhoneUtils.extract_area_and_exchange(phone_normalized)
        fax_area, fax_exchange = PhoneUtils.extract_area_and_exchange(fax_normalized)
        
        return False  # 부분 중복은 허용
    
    @staticmethod
    def get_area_name(area_code: str) -> str:
        """지역번호에 해당하는 지역명 반환"""
        return KOREAN_AREA_CODES.get(area_code, "알 수 없음")
    
    @staticmethod
    def is_valid_area_code(area_code: str) -> bool:
        """유효한 지역번호인지 확인"""
        return is_valid_area_code(area_code)

# 테스트 함수
def test_phone_utils():
    """전화번호 유틸리티 테스트"""
    test_phones = [
        "02-123-4567",
        "031-1234-5678", 
        "010-1234-5678",
        "070-1234-5678",
        "02 123 4567",
        "0212345678",
        "82-2-123-4567"
    ]
    
    print("=" * 50)
    print("📞 전화번호 유틸리티 테스트")
    print("=" * 50)
    
    for phone in test_phones:
        print(f"\n🔍 테스트: {phone}")
        
        # 유효성 검증
        is_valid = PhoneUtils.validate_korean_phone(phone)
        print(f"  ✅ 유효성: {is_valid}")
        
        # 포맷팅
        formatted = PhoneUtils.format_phone_number(phone)
        print(f"  📝 포맷팅: {formatted}")
        
        # 지역번호 추출
        area_code = PhoneUtils.extract_area_code(phone)
        if area_code:
            area_name = PhoneUtils.get_area_name(area_code)
            print(f"  🌍 지역: {area_code} ({area_name})")
        
        # 지역번호+국번 추출
        area, exchange = PhoneUtils.extract_area_and_exchange(phone)
        if area and exchange:
            print(f"  🔢 지역번호-국번: {area}-{exchange}")

if __name__ == "__main__":
    test_phone_utils()
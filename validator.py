#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전화번호 및 팩스번호 검증 및 정제 모듈
더미 데이터 제거, 중복 검증, 형식 검증 등을 수행
"""

import re
import logging

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

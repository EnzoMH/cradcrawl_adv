#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 도우미 함수들
공통으로 사용되는 유틸리티 함수들과 헬퍼 클래스
"""

import re
import json
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from pathlib import Path
import asyncio
import time
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    normalized_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

class AgentHelpers:
    """AI 에이전트 시스템 도우미 클래스"""
    
    # 정규식 패턴들
    PHONE_PATTERNS = [
        r'(\d{2,3})-(\d{3,4})-(\d{4})',           # 02-1234-5678
        r'(\d{3})-(\d{4})-(\d{4})',               # 010-1234-5678
        r'(\d{2,3})\.(\d{3,4})\.(\d{4})',         # 02.1234.5678
        r'(\d{2,3})\s(\d{3,4})\s(\d{4})',         # 02 1234 5678
        r'(\d{2,3})(\d{3,4})(\d{4})',             # 0212345678
        r'\+82-(\d{1,2})-(\d{3,4})-(\d{4})',      # +82-2-1234-5678
    ]
    
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    URL_PATTERN = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    
    FAX_PATTERNS = [
        r'(?:팩스|fax|FAX)[\s:]*(\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4})',
        r'(?:F|f)[\s:]*(\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4})',
    ]
    
    # 주소 키워드
    ADDRESS_KEYWORDS = [
        '시', '군', '구', '동', '읍', '면', '리', '로', '길', '번지', '번', '호',
        '아파트', '빌딩', '타워', '센터', '오피스텔', '상가', '층'
    ]
    
    # 조직 유형 키워드
    ORGANIZATION_TYPES = {
        '의료': ['병원', '의원', '클리닉', '보건소', '약국', '한의원'],
        '교육': ['학교', '대학교', '대학원', '유치원', '어린이집', '학원', '교육청'],
        '공공': ['청', '구청', '시청', '군청', '동사무소', '주민센터', '관공서'],
        '문화': ['박물관', '미술관', '도서관', '문화센터', '체육관', '공연장'],
        '종교': ['교회', '성당', '절', '사찰', '성전', '교당'],
        '기업': ['회사', '기업', '법인', '상사', '그룹', '코퍼레이션'],
        '금융': ['은행', '신용금고', '보험', '증권', '카드', '캐피탈'],
        '음식': ['식당', '카페', '레스토랑', '베이커리', '주점', '술집'],
        '쇼핑': ['마트', '백화점', '쇼핑몰', '상점', '매장', '편의점'],
        '서비스': ['미용실', '세탁소', '수리점', '정비소', '부동산', '여행사']
    }
    
    @staticmethod
    def normalize_phone_number(phone: str) -> Optional[str]:
        """전화번호 정규화"""
        if not phone:
            return None
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 국가 코드 제거
        if digits.startswith('82'):
            digits = '0' + digits[2:]
        
        # 길이 검증
        if len(digits) < 9 or len(digits) > 11:
            return None
        
        # 형식 정규화
        if len(digits) == 9:  # 지역번호 2자리
            return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
        elif len(digits) == 10:  # 지역번호 3자리 또는 휴대폰
            if digits.startswith('02'):
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11:  # 휴대폰
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return None
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """텍스트에서 전화번호 추출"""
        phones = []
        
        for pattern in AgentHelpers.PHONE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = match
                
                normalized = AgentHelpers.normalize_phone_number(phone)
                if normalized and normalized not in phones:
                    phones.append(normalized)
        
        return phones
    
    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """텍스트에서 이메일 주소 추출"""
        emails = re.findall(AgentHelpers.EMAIL_PATTERN, text, re.IGNORECASE)
        return list(set(email.lower() for email in emails))
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """텍스트에서 URL 추출"""
        urls = re.findall(AgentHelpers.URL_PATTERN, text, re.IGNORECASE)
        return list(set(urls))
    
    @staticmethod
    def extract_fax_numbers(text: str) -> List[str]:
        """텍스트에서 팩스 번호 추출"""
        fax_numbers = []
        
        for pattern in AgentHelpers.FAX_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                normalized = AgentHelpers.normalize_phone_number(match)
                if normalized and normalized not in fax_numbers:
                    fax_numbers.append(normalized)
        
        return fax_numbers
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """이메일 주소 검증"""
        errors = []
        warnings = []
        
        if not email:
            errors.append("이메일 주소가 비어있습니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # 기본 형식 검증
        if not re.match(AgentHelpers.EMAIL_PATTERN, email):
            errors.append("올바르지 않은 이메일 형식입니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # 도메인 검증
        domain = email.split('@')[1]
        if '.' not in domain:
            errors.append("도메인에 최상위 도메인이 없습니다")
            return ValidationResult(False, 0.1, errors, warnings)
        
        # 일반적인 도메인 확인
        common_domains = ['gmail.com', 'naver.com', 'daum.net', 'hanmail.net', 'yahoo.com']
        if domain.lower() in common_domains:
            confidence = 0.9
        else:
            confidence = 0.7
            warnings.append("일반적이지 않은 도메인입니다")
        
        return ValidationResult(True, confidence, errors, warnings, email.lower())
    
    @staticmethod
    def validate_phone_number(phone: str) -> ValidationResult:
        """전화번호 검증"""
        errors = []
        warnings = []
        
        if not phone:
            errors.append("전화번호가 비어있습니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        normalized = AgentHelpers.normalize_phone_number(phone)
        if not normalized:
            errors.append("올바르지 않은 전화번호 형식입니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # 번호 유형 판별
        digits = re.sub(r'[^\d]', '', normalized)
        confidence = 0.8
        
        if digits.startswith('010') or digits.startswith('011') or digits.startswith('016'):
            # 휴대폰 번호
            confidence = 0.9
        elif digits.startswith('02'):
            # 서울 지역번호
            confidence = 0.9
        elif digits.startswith('0'):
            # 기타 지역번호
            confidence = 0.8
        else:
            warnings.append("알 수 없는 번호 유형입니다")
            confidence = 0.6
        
        return ValidationResult(True, confidence, errors, warnings, normalized)
    
    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """URL 검증"""
        errors = []
        warnings = []
        
        if not url:
            errors.append("URL이 비어있습니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # 기본 형식 검증
        if not re.match(AgentHelpers.URL_PATTERN, url):
            errors.append("올바르지 않은 URL 형식입니다")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # URL 파싱
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                errors.append("도메인이 없습니다")
                return ValidationResult(False, 0.1, errors, warnings)
        except Exception as e:
            errors.append(f"URL 파싱 오류: {str(e)}")
            return ValidationResult(False, 0.0, errors, warnings)
        
        # HTTPS 확인
        confidence = 0.8
        if url.startswith('https://'):
            confidence = 0.9
        elif url.startswith('http://'):
            warnings.append("HTTP 프로토콜을 사용합니다 (보안 취약)")
            confidence = 0.7
        
        return ValidationResult(True, confidence, errors, warnings, url)
    
    @staticmethod
    def extract_addresses(text: str) -> List[str]:
        """텍스트에서 주소 추출"""
        addresses = []
        
        # 주소 패턴 찾기
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 주소 키워드 포함 여부 확인
            keyword_count = sum(1 for keyword in AgentHelpers.ADDRESS_KEYWORDS if keyword in line)
            
            if keyword_count >= 2:  # 최소 2개 이상의 주소 키워드 포함
                addresses.append(line)
        
        return addresses
    
    @staticmethod
    def classify_organization_type(name: str, description: str = "") -> str:
        """조직 유형 분류"""
        text = f"{name} {description}".lower()
        
        scores = defaultdict(int)
        
        for org_type, keywords in AgentHelpers.ORGANIZATION_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    scores[org_type] += 1
        
        if scores:
            return max(scores, key=scores.get)
        
        return "기타"
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣.-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, List[str]]:
        """텍스트에서 모든 연락처 정보 추출"""
        return {
            'phone_numbers': AgentHelpers.extract_phone_numbers(text),
            'email_addresses': AgentHelpers.extract_email_addresses(text),
            'fax_numbers': AgentHelpers.extract_fax_numbers(text),
            'urls': AgentHelpers.extract_urls(text),
            'addresses': AgentHelpers.extract_addresses(text)
        }
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """텍스트 유사도 계산 (간단한 단어 기반)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    @staticmethod
    def generate_hash(data: Union[str, Dict, List]) -> str:
        """데이터 해시 생성"""
        if isinstance(data, (dict, list)):
            data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def format_confidence(confidence: float) -> str:
        """신뢰도 형식화"""
        if confidence >= 0.9:
            return f"매우 높음 ({confidence:.1%})"
        elif confidence >= 0.7:
            return f"높음 ({confidence:.1%})"
        elif confidence >= 0.5:
            return f"보통 ({confidence:.1%})"
        elif confidence >= 0.3:
            return f"낮음 ({confidence:.1%})"
        else:
            return f"매우 낮음 ({confidence:.1%})"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """시간 형식화"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes:.0f}분 {remaining_seconds:.0f}초"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours:.0f}시간 {remaining_minutes:.0f}분"
    
    @staticmethod
    def create_task_id(prefix: str = "task") -> str:
        """작업 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}_{int(time.time() * 1000) % 10000}"
    
    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
        """재시도 데코레이터"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"시도 {attempt + 1}/{max_retries} 실패: {str(e)}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay * (2 ** attempt))  # 지수 백오프
                
                raise last_exception
            
            return wrapper
        return decorator
    
    @staticmethod
    def merge_contact_data(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """여러 연락처 데이터 병합"""
        merged = {
            'phone_numbers': [],
            'email_addresses': [],
            'fax_numbers': [],
            'urls': [],
            'addresses': []
        }
        
        for data in data_list:
            for key in merged.keys():
                if key in data:
                    merged[key].extend(data[key])
        
        # 중복 제거
        for key in merged.keys():
            merged[key] = list(set(merged[key]))
        
        return merged
    
    @staticmethod
    def validate_contact_data(data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """연락처 데이터 검증"""
        results = {}
        
        # 전화번호 검증
        if 'phone_numbers' in data:
            results['phone_numbers'] = []
            for phone in data['phone_numbers']:
                results['phone_numbers'].append(
                    AgentHelpers.validate_phone_number(phone)
                )
        
        # 이메일 검증
        if 'email_addresses' in data:
            results['email_addresses'] = []
            for email in data['email_addresses']:
                results['email_addresses'].append(
                    AgentHelpers.validate_email(email)
                )
        
        # URL 검증
        if 'urls' in data:
            results['urls'] = []
            for url in data['urls']:
                results['urls'].append(
                    AgentHelpers.validate_url(url)
                )
        
        return results
    
    @staticmethod
    def calculate_overall_confidence(validations: Dict[str, List[ValidationResult]]) -> float:
        """전체 신뢰도 계산"""
        total_confidence = 0.0
        total_count = 0
        
        for validation_list in validations.values():
            for validation in validation_list:
                if validation.is_valid:
                    total_confidence += validation.confidence
                total_count += 1
        
        if total_count == 0:
            return 0.0
        
        return total_confidence / total_count
    
    @staticmethod
    def create_summary_report(data: Dict[str, Any], validations: Dict[str, List[ValidationResult]]) -> str:
        """요약 리포트 생성"""
        report = []
        report.append("📊 연락처 정보 요약")
        report.append("=" * 40)
        
        # 데이터 개수
        for key, items in data.items():
            if items:
                count = len(items)
                report.append(f"{key}: {count}개")
        
        # 검증 결과
        report.append("\n🔍 검증 결과:")
        overall_confidence = AgentHelpers.calculate_overall_confidence(validations)
        report.append(f"전체 신뢰도: {AgentHelpers.format_confidence(overall_confidence)}")
        
        # 오류 및 경고
        total_errors = sum(len([v for v in vlist if v.errors]) for vlist in validations.values())
        total_warnings = sum(len([v for v in vlist if v.warnings]) for vlist in validations.values())
        
        if total_errors > 0:
            report.append(f"⚠️ 오류: {total_errors}개")
        if total_warnings > 0:
            report.append(f"📝 경고: {total_warnings}개")
        
        return "\n".join(report)

# 편의 함수들
def extract_all_contacts(text: str) -> Dict[str, List[str]]:
    """모든 연락처 정보 추출 (편의 함수)"""
    return AgentHelpers.extract_contact_info(text)

def validate_all_contacts(data: Dict[str, Any]) -> Dict[str, List[ValidationResult]]:
    """모든 연락처 정보 검증 (편의 함수)"""
    return AgentHelpers.validate_contact_data(data)

def create_contact_report(text: str) -> str:
    """연락처 정보 리포트 생성 (편의 함수)"""
    contacts = extract_all_contacts(text)
    validations = validate_all_contacts(contacts)
    return AgentHelpers.create_summary_report(contacts, validations)

if __name__ == "__main__":
    # 테스트 실행
    test_text = """
    서울시립어린이병원
    주소: 서울특별시 중구 소공로 120
    전화: 02-570-8000
    팩스: 02-570-8001
    이메일: info@childhosp.go.kr
    웹사이트: https://www.childhosp.go.kr
    """
    
    print("🧪 AgentHelpers 테스트")
    print("=" * 40)
    
    # 연락처 추출 테스트
    contacts = extract_all_contacts(test_text)
    print("📞 추출된 연락처:")
    for key, items in contacts.items():
        if items:
            print(f"  {key}: {items}")
    
    # 검증 테스트
    validations = validate_all_contacts(contacts)
    print("\n🔍 검증 결과:")
    for key, validation_list in validations.items():
        for i, validation in enumerate(validation_list):
            print(f"  {key}[{i}]: {validation.is_valid} (신뢰도: {validation.confidence:.1%})")
    
    # 리포트 생성
    print("\n" + create_contact_report(test_text))
    
    print("\n✅ 테스트 완료") 
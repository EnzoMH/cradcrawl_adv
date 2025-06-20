#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Crawling 프로젝트 통합 설정 관리
모든 상수, 설정, 경로를 중앙에서 관리하여 일관성과 유지보수성을 향상시킴

통합된 파일들:
- constants.py (기본 상수 및 패턴)
- constants_extended.py (확장 설정)
- config.py (경로 및 API 설정)
"""

import re
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# ===== 기본 경로 설정 =====
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json"
EXCEL_DIR = DATA_DIR / "excel"
CSV_DIR = DATA_DIR / "csv"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
LEGACY_DIR = BASE_DIR / "legacy"
UTILS_DIR = BASE_DIR / "utils"
TEMPLATES_DIR = BASE_DIR / "templates"

# ===== API 설정 =====
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL_TEXT = "gemini-1.5-flash"
GEMINI_MODEL_VISION = "gemini-1.5-flash"

# AI 관련 설정
AI_MODEL_CONFIG = {
    'temperature': 0.1,
    'top_p': 0.8,
    'top_k': 10,
    'max_output_tokens': 1000,
}

TPM_LIMITS = {
    'requests_per_minute': 6,
    'max_wait_time': 30
}

# ===== 파일 패턴 관리 =====
INPUT_FILE_PATTERNS = [
    "raw_data_*.json",
    "church_data_*.json", 
    "churches_enhanced_*.json",
    "undefined_converted_*.json",
    "combined_*.json"
]

OUTPUT_FILE_PATTERNS = {
    "enhanced_final": "churches_enhanced_final_{timestamp}.json",
    "intermediate": "churches_enhanced_intermediate_{count}_{timestamp}.json",
    "excel_filtered": "church_data_filtered_{timestamp}.xlsx",
    "excel_enhanced": "church_data_enhanced_{timestamp}.xlsx",
    "converted_json": "church_data_converted_{timestamp}.json",
    "statistics": "crawling_statistics_{timestamp}.json"
}

# ===== 크롤링 설정 =====
CRAWLING_CONFIG = {
    "default_delay": 2,
    "max_retries": 3,
    "timeout": 30,
    "headless_mode": True,
    "max_concurrent": 5,
    "save_interval": 50,
    "chunk_size_large": 3000,
    "chunk_size_medium": 2000,
    "overlap": 300,
    "max_chunks": 5,
    "max_text_length": 10000,
    "async_timeout": 120
}

SELENIUM_CONFIG = {
    "implicit_wait": 10,
    "page_load_timeout": 30,
    "script_timeout": 30,
    "window_size": (1920, 1080),
    "headless_mode": True,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# ===== 웹 애플리케이션 설정 =====
WEB_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True,
    "reload": True,
    "title": "향상된 크롤링 제어 시스템",
    "description": "FastAPI 기반 크롤링 제어 및 모니터링 시스템"
}

STATIC_PATHS = {
    "css": "templates/css",
    "js": "templates/js", 
    "html": "templates/html",
    "files": "static"
}

# ===== 데이터 처리 설정 =====
CONVERSION_CONFIG = {
    "exclude_fields": [
        "processing_error", "validation_errors", "extraction_timestamp",
        "source_url", "extraction_method", "merge_status", "phone_validation_error",
        "email_validation_error", "ai_analysis", "search_results", "homepage", "extraction_summary"
    ],
    "priority_columns": [
        "name", "category", "homepage", "phone", "fax", "email", 
        "mobile", "postal_code", "address"
    ],
    "max_preview_rows": 5,
    "encoding": "utf-8",
    "save_interval": 50
}

VALIDATION_CONFIG = {
    "required_fields": ["name", "category"],
    "optional_fields": ["phone", "fax", "email", "address", "postal_code", "mobile", "homepage"],
    "min_name_length": 2,
    "max_name_length": 100,
    "phone_validation": True,
    "email_validation": True
}

# ===== 한국 지역번호 관련 상수 =====

# 한국 지역번호 매핑 (코드 -> 지역명)
KOREAN_AREA_CODES = {
    "02": "서울", 
    "031": "경기", 
    "032": "인천", 
    "033": "강원",
    "041": "충남", 
    "042": "대전", 
    "043": "충북", 
    "044": "세종",
    "051": "부산", 
    "052": "울산", 
    "053": "대구", 
    "054": "경북", 
    "055": "경남",
    "061": "전남", 
    "062": "광주", 
    "063": "전북", 
    "064": "제주",
    "070": "인터넷전화", 
    "010": "핸드폰", 
    "017": "핸드폰"
}

# 유효한 지역번호 목록 (리스트 형태)
VALID_AREA_CODES = list(KOREAN_AREA_CODES.keys())

# 지역번호별 전화번호 길이 규칙
AREA_CODE_LENGTH_RULES = {
    "02": {"min_length": 9, "max_length": 10},       # 서울
    "031": {"min_length": 10, "max_length": 11},   # 경기
    "032": {"min_length": 10, "max_length": 11},   # 인천
    "033": {"min_length": 10, "max_length": 11},   # 강원
    "041": {"min_length": 10, "max_length": 11},   # 충남
    "042": {"min_length": 10, "max_length": 11},   # 대전
    "043": {"min_length": 10, "max_length": 11},   # 충북
    "044": {"min_length": 10, "max_length": 11},   # 세종
    "051": {"min_length": 10, "max_length": 11},   # 부산
    "052": {"min_length": 10, "max_length": 11},   # 울산
    "053": {"min_length": 10, "max_length": 11},   # 대구
    "054": {"min_length": 10, "max_length": 11},   # 경북
    "055": {"min_length": 10, "max_length": 11},   # 경남
    "061": {"min_length": 10, "max_length": 11},   # 전남
    "062": {"min_length": 10, "max_length": 11},   # 광주
    "063": {"min_length": 10, "max_length": 11},   # 전북
    "064": {"min_length": 10, "max_length": 11},   # 제주
    "070": {"min_length": 11, "max_length": 11},   # 인터넷전화
    "010": {"min_length": 11, "max_length": 11},   # 핸드폰
    "017": {"min_length": 11, "max_length": 11}    # 핸드폰
}

# ===== 정규식 패턴 상수들 =====

# 전화번호 추출 패턴들
PHONE_EXTRACTION_PATTERNS = [
    # 기본 패턴들
    r'(?:전화|TEL|Tel|tel|T\.|전화번호|연락처|대표번호)[\s*:?]*([0-9\-\.\(\)\s]{8,20})',
    r'(?:☎|=번호)[\s]*([0-9\-\.\(\)\s]{8,20})',
    r'(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    
    # 추가 패턴들
    r'전화[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'Tel[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'TEL[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'T[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'대표번호[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*전화',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*[Tt]el',
    r'(?:Phone|phone|PHONE)[\s:]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})'
]

# 팩스번호 추출 패턴들
FAX_EXTRACTION_PATTERNS = [
    # 기본 패턴들
    r'(?:팩스|FAX|Fax|fax|F\.|팩스번호)[\s*:?]*([0-9\-\.\(\)\s]{8,20})',
    r'(?:=팩스)[\s]*([0-9\-\.\(\)\s]{8,20})',
    
    # 추가 패턴들
    r'팩스[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'Fax[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'FAX[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'F[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'팩[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*팩스',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*[Ff]ax'
]

# 이메일 추출 패턴들
EMAIL_EXTRACTION_PATTERNS = [
    r'(?:이메일|EMAIL|Email|email|E-mail|e-mail|메일|mail)[\s*:?]*([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    r'([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
]

# 이메일 패턴 (일반 패턴)
EMAIL_PATTERN = r'[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# 주소 추출 패턴들
ADDRESS_EXTRACTION_PATTERNS = [
    r'(?:주소|ADDRESS|Address|address|소재지|위치)[\s*:?]*([가-힣\s\d\-\(\)]+(?:시|군|구|동|로|길)[가-힣\s\d\-\(\)]*)',
    r'([가-힣]+(?:특별시|광역시|시|군|도)\s+[가-힣\s\d\-\(\)]+(?:시|군|구|동|로|길)[가-힣\s\d\-\(\)]*)',
    r'(?:주소|Address|address|ADDRESS)[\s:]*([^\n]+(?:시|군|구|동|로|길)[^\n]*)',
    r'(\d{5}\s*[^\n]+(?:시|군|구|동|로|길)[^\n]*)'     # 우편번호 포함
]

# 웹사이트/홈페이지 추출 패턴들
WEBSITE_EXTRACTION_PATTERNS = [
    r'(?:홈페이지|웹사이트|Website|website|Homepage|homepage)[\s:]*([^\s\n]+)',
    r'(https?://[^\s\n]+)',
    r'(www\.[^\s\n]+)'
]

# ===== 전화번호 검증 관련 상수 =====

# 전화번호 검증 패턴 (엄격한 검증용)
PHONE_VALIDATION_PATTERN = re.compile(
    r'(?:\+?82[-\s]?)?'     # 선택적 국가번호
    r'(0\d{1,2})'                 # 지역번호 (0으로 시작, 1~2자리)
    r'[-\.\)\s]?'                 # 구분자 (하이픈, 점, 오른쪽 괄호, 공백 등)
    r'(\d{3,4})'                   # 중간 번호 (3~4자리)
    r'[-\.\s]?'                     # 구분자
    r'(\d{4})',                     # 마지막 번호 (4자리)
    re.IGNORECASE
)

# 한국 전화번호 기본 패턴들 (검증용)
KOREAN_PHONE_VALIDATION_PATTERNS = [
    r'^0\d{1,2}-\d{3,4}-\d{4}$',     # 지역번호-국번-번호
    r'^01\d-\d{3,4}-\d{4}$',             # 휴대폰
    r'^\d{2,3}-\d{3,4}-\d{4}$'         # 서울 지역번호 생략
]

# ===== 더미 데이터 패턴 상수 =====

# 더미/가짜 전화번호 패턴들
DUMMY_PHONE_PATTERNS = [
    r'033-333-3333',                               # 033-333-3333
    r'02-222-2222',                                 # 02-222-2222
    r'031-111-1111',                               # 031-111-1111
    r'(\d)\1{2}-\1{3}-\1{4}',             # 같은 숫자 반복 (예: 111-1111-1111)
    r'0\d{1,2}-000-0000',                     # 끝자리가 모두 0
    r'0\d{1,2}-123-4567',                     # 순차적 숫자
    r'0\d{1,2}-1234-5678',                   # 순차적 숫자
    r'000-000-0000',                               # 모두 0
    r'999-999-9999'                                # 모두 9
]

# ===== URL 크롤링 관련 상수 (개선) =====

# 완전 제외할 도메인 목록 (검색엔진, 쇼핑몰 등)
STRICT_EXCLUDE_DOMAINS = [
    # 검색 엔진들
    "google.com", "yahoo.com", "bing.com",
    
    # 쇼핑몰/마켓
    "11st.co.kr", "gmarket.co.kr", "auction.co.kr", 
    "coupang.com", "bunjang.co.kr", "joongna.com",
    
    # 뉴스/언론
    "chosun.com", "donga.com", "joins.com", "hani.co.kr",
    "khan.co.kr", "pressian.com", "ytn.co.kr",
    
    # 위키 사이트들
    "namu.wiki", "wiki.namu.wiki", "wikipedia.org", 
    "en.wikipedia.org", "ko.wikipedia.org",
    
    # 기타
    "114.co.kr", "findall.co.kr", "cyworld.com", "me2day.net"
]

# 소규모 기관용 허용 소셜미디어 도메인 (파싱하되 별도 표시)
SOCIAL_MEDIA_DOMAINS = {
    "blog.naver.com": "네이버블로그",
    "cafe.naver.com": "네이버카페", 
    "post.naver.com": "네이버포스트",
    "facebook.com": "페이스북",
    "instagram.com": "인스타그램",
    "youtube.com": "유튜브",
    "tistory.com": "티스토리",
    "blog.daum.net": "다음블로그",
    "blogspot.com": "블로그스팟",
    "modoo.at": "모두닷컴"
}

# 기존 EXCLUDE_DOMAINS를 STRICT_EXCLUDE_DOMAINS로 변경
EXCLUDE_DOMAINS = STRICT_EXCLUDE_DOMAINS

# 소규모 기관 판별 키워드
SMALL_ORGANIZATION_KEYWORDS = [
    "교회", "성당", "절", "사찰", "교회당", "예배당",
    "학원", "교습소", "과외", "학습지", "공부방",
    "의원", "치과", "한의원", "약국", "요양원",
    "미용실", "헤어샵", "네일샵", "마사지",
    "카페", "음식점", "식당", "베이커리", "제과점",
    "부동산", "공인중개사", "세무사", "회계사",
    "마을", "동네", "지역", "소규모", "개인"
]

# 연락처 추출 개선된 패턴들
CONTACT_NAVIGATION_KEYWORDS = [
    # 한국어
    "오시는길", "오시는 길", "찾아오시는길", "찾아오시는 길", 
    "연락처", "연락처정보", "연락처 정보", "문의", "문의하기",
    "위치", "위치정보", "위치 정보", "주소", "지도",
    "전화", "전화번호", "연락", "상담", "예약",
    
    # 영어
    "contact", "contact us", "contact info", "contact information",
    "location", "directions", "find us", "visit us", "get directions",
    "phone", "call", "reach us", "about us", "info",
    
    # 혼합
    "Contact", "Location", "About", "Info"
]

# 추가 전화번호 저장을 위한 패턴
ADDITIONAL_PHONE_PATTERNS = [
    r'(?:담당자|책임자|관리자|상담원)[\s]*:?[\s]*(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    r'(?:직통|내선|분관)[\s]*:?[\s]*(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    r'(?:사무실|사무소|본점|지점)[\s]*:?[\s]*(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    r'(?:예약|접수|상담)[\s]*:?[\s]*(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    r'(?:핸드폰|휴대폰|모바일|Mobile|mobile|HP|hp)[\s]*:?[\s]*(\d{3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})'
]

# 지역별 지역번호 매핑 (주소 기반 검증용)
REGION_TO_AREA_CODE = {
    # 서울
    "서울": ["02"],
    "서울시": ["02"],
    "서울특별시": ["02"],
    
    # 경기도
    "경기": ["031"],
    "경기도": ["031"],
    "수원": ["031"], "성남": ["031"], "안양": ["031"], "안산": ["031"],
    "고양": ["031"], "용인": ["031"], "부천": ["031"], "의정부": ["031"],
    
    # 인천
    "인천": ["032"],
    "인천시": ["032"],
    "인천광역시": ["032"],
    
    # 강원도
    "강원": ["033"],
    "강원도": ["033"],
    "춘천": ["033"], "원주": ["033"], "강릉": ["033"],
    
    # 충청남도
    "충남": ["041"],
    "충청남도": ["041"],
    "천안": ["041"], "아산": ["041"], "서산": ["041"],
    
    # 대전
    "대전": ["042"],
    "대전시": ["042"],
    "대전광역시": ["042"],
    
    # 충청북도
    "충북": ["043"],
    "충청북도": ["043"],
    "청주": ["043"], "충주": ["043"],
    
    # 세종
    "세종": ["044"],
    "세종시": ["044"],
    "세종특별자치시": ["044"],
    
    # 부산
    "부산": ["051"],
    "부산시": ["051"],
    "부산광역시": ["051"],
    
    # 울산
    "울산": ["052"],
    "울산시": ["052"],
    "울산광역시": ["052"],
    
    # 대구
    "대구": ["053"],
    "대구시": ["053"],
    "대구광역시": ["053"],
    
    # 경상북도
    "경북": ["054"],
    "경상북도": ["054"],
    "포항": ["054"], "경주": ["054"], "안동": ["054"],
    
    # 경상남도
    "경남": ["055"],
    "경상남도": ["055"],
    "창원": ["055"], "진주": ["055"], "통영": ["055"],
    
    # 전라남도
    "전남": ["061"],
    "전라남도": ["061"],
    "목포": ["061"], "여수": ["061"], "순천": ["061"],
    
    # 광주
    "광주": ["062"],
    "광주시": ["062"],
    "광주광역시": ["062"],
    
    # 전라북도
    "전북": ["063"],
    "전라북도": ["063"],
    "전주": ["063"], "익산": ["063"], "군산": ["063"],
    
    # 제주
    "제주": ["064"],
    "제주도": ["064"],
    "제주특별자치도": ["064"]
}

# 전화번호 검증 강화 함수들
def validate_phone_length(phone: str) -> bool:
    """전화번호 길이 검증 (9-11자리)"""
    digits = re.sub(r'[^\d]', '', phone)
    return 9 <= len(digits) <= 11

def validate_phone_by_region(phone: str, address: str) -> bool:
    """주소 기반 지역번호 검증"""
    if not phone or not address:
        return True  # 주소가 없으면 기본 검증만
    
    area_code = extract_phone_area_code(phone)
    if not area_code:
        return False
    
    # 주소에서 지역 추출
    for region, codes in REGION_TO_AREA_CODE.items():
        if region in address:
            return area_code in codes
    
    return True  # 매칭되는 지역이 없으면 통과

def is_phone_fax_duplicate(phone: str, fax: str) -> bool:
    """전화번호와 팩스번호 중복 확인"""
    if not phone or not fax:
        return False
    
    # 숫자만 추출해서 비교
    phone_digits = re.sub(r'[^\d]', '', phone)
    fax_digits = re.sub(r'[^\d]', '', fax)
    
    return phone_digits == fax_digits

def is_small_organization(org_name: str, category: str = "") -> bool:
    """소규모 기관 여부 판별"""
    text = f"{org_name} {category}".lower()
    return any(keyword in text for keyword in SMALL_ORGANIZATION_KEYWORDS)

# ===== 이메일 도메인 관련 상수 =====

# 이메일 도메인 분류용 리스트들
PORTAL_EMAIL_DOMAINS = [
    "naver.com", "gmail.com", "daum.net", "hanmail.net", 
    "yahoo.com", "hotmail.com"
]

GOVERNMENT_EMAIL_SUFFIXES = [".go.kr", ".gov.kr"]
EDUCATION_EMAIL_SUFFIXES = [".ac.kr", ".edu"]
BUSINESS_EMAIL_SUFFIXES = [".co.kr", ".com"]
RELIGIOUS_EMAIL_KEYWORDS = ["church", "temple", "cathedral"]

# ===== 로깅 관련 상수 =====

# 로그 출력 포맷터
LOG_FORMAT = "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"

# 모듈별 로거 이름
LOGGER_NAMES = {
    "app": "app",
    "url_extractor": "url_extractor", 
    "parser": "web_parser",
    "fax_crawler": "fax_crawler",
    "naver_map": "naver_map_crawler",
    "validator": "contact_validator",
    "statistics": "data_statistics",
    "ai_helpers": "ai_helpers",
    "detail_extractor": "detail_extractor",
    "enhanced_detail": "enhanced_detail",
    "gemini_ai": "gemini_ai_responses",
    "crawler_main": "crawler_main",
    "data_processor": "data_processor"
}

# URL 크롤링 관련 상수
HOMEPAGE_KEYWORDS = [
    "home", "index", "main", "www", "homepage", "홈페이지", 
    "메인", "대문", "official", "church", "교회"
]

# ===== 유틸리티 함수들 =====

def get_area_name(area_code: str) -> str:
    """지역번호를 지역명 반환"""
    return KOREAN_AREA_CODES.get(area_code, "알 수 없음")

def is_valid_area_code(area_code: str) -> bool:
    """유효한 지역번호인지 확인"""
    return area_code in VALID_AREA_CODES

def get_length_rules(area_code: str) -> dict:
    """지역번호별 길이 규칙 반환"""
    return AREA_CODE_LENGTH_RULES.get(area_code, {"min_length": 10, "max_length": 11})

def format_phone_number(digits: str, area_code: str) -> str:
    """전화번호 포맷팅 (공통 로직)"""
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

def extract_phone_area_code(phone: str) -> str:
    """전화번호에서 지역코드 추출 (공통 로직)"""
    if not phone:
        return None
    
    # 숫자만 추출
    digits = re.sub(r'[^\d]', '', phone)
    
    # 지역코드 매칭
    for code in KOREAN_AREA_CODES.keys():
        if digits.startswith(code):
            return code
    
    return None

def ensure_directories():
    """필요한 디렉토리들을 생성"""
    directories = [
        DATA_DIR, JSON_DIR, EXCEL_DIR, CSV_DIR,
        OUTPUT_DIR, LOG_DIR, TEMP_DIR,
        TEMPLATES_DIR / "html",
        TEMPLATES_DIR / "css", 
        TEMPLATES_DIR / "js",
        Path("static")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
    print(f"📁 필요한 디렉토리들이 생성되었습니다.")

def get_latest_input_file(search_dirs=None):
    """가장 최신 입력 파일을 찾아 반환"""
    if search_dirs is None:
        search_dirs = [BASE_DIR, JSON_DIR]
    
    latest_file = None
    latest_time = 0
    
    for search_dir in search_dirs:
        for pattern in INPUT_FILE_PATTERNS:
            files = list(Path(search_dir).glob(pattern))
            for file in files:
                if file.stat().st_mtime > latest_time:
                    latest_time = file.stat().st_mtime
                    latest_file = file
    
    return latest_file

def generate_output_filename(prefix, output_dir, extension=None, count=None):
    """출력 파일명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if count:
        filename = f"{prefix}_{timestamp}_{count}"
    else:
        filename = f"{prefix}_{timestamp}"
    
    if extension:
        filename += f".{extension}"
    elif prefix.startswith("excel"):
        filename += ".xlsx"
    else:
        filename += ".json"
    
    return Path(output_dir) / filename

def get_file_paths():
    """주요 파일 경로들을 반환"""
    return {
        "base_dir": BASE_DIR,
        "data_dir": DATA_DIR,
        "json_dir": JSON_DIR,
        "excel_dir": EXCEL_DIR,
        "csv_dir": CSV_DIR,
        "output_dir": OUTPUT_DIR,
        "log_dir": LOG_DIR,
        "temp_dir": TEMP_DIR,
        "legacy_dir": LEGACY_DIR,
        "utils_dir": UTILS_DIR,
        "templates_dir": TEMPLATES_DIR
    }

def validate_config():
    """설정 유효성 검사"""
    issues = []
    
    # API 키 확인
    if not GEMINI_API_KEY:
        issues.append("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    # 필수 디렉토리 확인
    if not BASE_DIR.exists():
        issues.append(f"기본 디렉토리가 존재하지 않습니다: {BASE_DIR}")
    
    # 크롤링 설정 검증
    if CRAWLING_CONFIG.get("max_concurrent", 5) > 10:
        issues.append("동시 처리 수가 너무 높습니다 (권장: 10 이하)")
    
    if issues:
        print("⚠️ 설정 검증 문제:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 설정 검증 완료")
        return True

def get_runtime_info():
    """런타임 정보 반환"""
    return {
        "base_dir": str(BASE_DIR),
        "python_version": os.sys.version,
        "platform": os.name,
        "api_key_configured": bool(GEMINI_API_KEY),
        "directories_exist": {
            "data": DATA_DIR.exists(),
            "json": JSON_DIR.exists(),
            "excel": EXCEL_DIR.exists(),
            "csv": CSV_DIR.exists(),
            "output": OUTPUT_DIR.exists(), 
            "logs": LOG_DIR.exists(),
            "templates": TEMPLATES_DIR.exists()
        },
        "latest_input_file": str(get_latest_input_file()) if get_latest_input_file() else None
    }

def initialize_project():
    """프로젝트 초기화"""
    print("🚀 프로젝트 초기화 시작...")
    
    # 디렉토리 생성
    ensure_directories()
    
    # 설정 검증
    validate_config()
    
    # 런타임 정보 출력
    runtime_info = get_runtime_info()
    print(f"📊 런타임 정보:")
    print(f"  - 기본 디렉토리: {runtime_info['base_dir']}")
    print(f"  - API 키 설정: {'✅' if runtime_info['api_key_configured'] else '❌'}")
    print(f"  - 최신 입력 파일: {runtime_info['latest_input_file'] or '없음'}")
    
    print("✅ 프로젝트 초기화 완료")

if __name__ == "__main__":
    initialize_project() 
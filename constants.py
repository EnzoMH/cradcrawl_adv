#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Crawling 프로젝트 전체 상수 정의 모듈
모든 중복 상수들을 통합하여 일관성과 유지보수성을 향상시킴
"""

import re

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

# 전화번호 추출 패턴들 (detailextractor.py, fax_crawler.py, parser.py에서 사용)
PHONE_EXTRACTION_PATTERNS = [
    # 기본 패턴들
    r'(?:전화|TEL|Tel|tel|T\.|전화번호|연락처|대표번호)[\s*:?]*([0-9\-\.\(\)\s]{8,20})',
    r'(?:☎|=번호)[\s]*([0-9\-\.\(\)\s]{8,20})',
    r'(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})',
    
    # 추가 패턴들 (fax_crawler.py에서)
    r'전화[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'Tel[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'TEL[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'T[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'대표번호[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*전화',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*[Tt]el',
    
    # parser.py 추가 패턴들
    r'(?:전화|Tel|TEL|T|대표번호|연락처|☎|=번호)[\s:]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})(?:\s*(?:전화|Tel|TEL))',
    r'(?:Phone|phone|PHONE)[\s:]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})'
]

# 팩스번호 추출 패턴들 (detailextractor.py, fax_crawler.py, parser.py에서 사용)
FAX_EXTRACTION_PATTERNS = [
    # 기본 패턴들
    r'(?:팩스|FAX|Fax|fax|F\.|팩스번호)[\s*:?]*([0-9\-\.\(\)\s]{8,20})',
    r'(?:=팩스)[\s]*([0-9\-\.\(\)\s]{8,20})',
    
    # 추가 패턴들 (fax_crawler.py에서)
    r'팩스[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'Fax[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'FAX[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'F[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'팩[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*팩스',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}).*[Ff]ax',
    
    # parser.py 추가 패턴들
    r'(?:팩스|Fax|FAX|F|팩|=팩스)[\s:]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',
    r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})(?:\s*(?:팩스|Fax|FAX))'
]

# 이메일 추출 패턴들 (detailextractor.py, parser.py에서 사용)
EMAIL_EXTRACTION_PATTERNS = [
    r'(?:이메일|EMAIL|Email|email|E-mail|e-mail|메일|mail)[\s*:?]*([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    r'([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
]

# 이메일 패턴 (일반 패턴, parser.py에서 사용)
EMAIL_PATTERN = r'[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# 주소 추출 패턴들 (detailextractor.py, parser.py에서 사용)
ADDRESS_EXTRACTION_PATTERNS = [
    # detailextractor.py 패턴들
    r'(?:주소|ADDRESS|Address|address|소재지|위치)[\s*:?]*([가-힣\s\d\-\(\)]+(?:시|군|구|동|로|길)[가-힣\s\d\-\(\)]*)',
    r'([가-힣]+(?:특별시|광역시|시|군|도)\s+[가-힣\s\d\-\(\)]+(?:시|군|구|동|로|길)[가-힣\s\d\-\(\)]*)',
    
    # parser.py 패턴들
    r'(?:주소|Address|address|ADDRESS)[\s:]*([^\n]+(?:시|군|구|동|로|길)[^\n]*)',
    r'(\d{5}\s*[^\n]+(?:시|군|구|동|로|길)[^\n]*)'     # 우편번호 포함
]

# 웹사이트/홈페이지 추출 패턴들 (parser.py에서)
WEBSITE_EXTRACTION_PATTERNS = [
    r'(?:홈페이지|웹사이트|Website|website|Homepage|homepage)[\s:]*([^\s\n]+)',
    r'(https?://[^\s\n]+)',
    r'(www\.[^\s\n]+)'
]

# ===== 전화번호 검증 관련 상수 =====

# 전화번호 검증 패턴 (엄격한 검증용, validator.py에서)
PHONE_VALIDATION_PATTERN = re.compile(
    r'(?:\+?82[-\s]?)?'     # 선택적 국가번호
    r'(0\d{1,2})'                 # 지역번호 (0으로 시작, 1~2자리)
    r'[-\.\)\s]?'                 # 구분자 (하이픈, 점, 오른쪽 괄호, 공백 등)
    r'(\d{3,4})'                   # 중간 번호 (3~4자리)
    r'[-\.\s]?'                     # 구분자
    r'(\d{4})',                     # 마지막 번호 (4자리)
    re.IGNORECASE
)

# 한국 전화번호 기본 패턴들 (검증용, naver_map_crawler.py에서)
KOREAN_PHONE_VALIDATION_PATTERNS = [
    r'^0\d{1,2}-\d{3,4}-\d{4}$',     # 지역번호-국번-번호
    r'^01\d-\d{3,4}-\d{4}$',             # 휴대폰
    r'^\d{2,3}-\d{3,4}-\d{4}$'         # 서울 지역번호 생략
]

# ===== 더미 데이터 패턴 상수 =====

# 더미/가짜 전화번호 패턴들 (validator.py에서)
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

# ===== URL 크롤링 관련 상수 =====

# 제외할 도메인 목록 (홈페이지 크롤링시, url_extractor.py에서)
EXCLUDE_DOMAINS = [
    # 검색 엔진들
    "naver.com", "daum.net", "google.com", "yahoo.com",
    
    # 소셜 미디어
    "facebook.com", "instagram.com", "twitter.com", "youtube.com",
    "linkedin.com", "pinterest.com", "tiktok.com",
    
    # 네이버 서비스들
    "blog.naver.com", "cafe.naver.com", "post.naver.com", 
    "news.naver.com", "shopping.naver.com", "map.naver.com",
    
    # 위키 사이트들 (개인홈페이지 아님)
    "namu.wiki", "wiki.namu.wiki", "wikipedia.org", 
    "en.wikipedia.org", "ko.wikipedia.org",
    
    # 블로그/개인서비스 플랫폼
    "tistory.com", "blog.daum.net", "blog.me", "modoo.at",
    "blogspot.com", "wordpress.com", "wix.com",
    
    # 쇼핑몰/마켓
    "11st.co.kr", "gmarket.co.kr", "auction.co.kr", 
    "coupang.com", "bunjang.co.kr", "joongna.com",
    "usedcarmarket.kr",     # 중고차 거래 관련 사이트
    
    # 뉴스/언론
    "chosun.com", "donga.com", "joins.com", "hani.co.kr",
    "khan.co.kr", "pressian.com", "ytn.co.kr",
    
    # 기타 비홈페이지 사이트들
    "114.co.kr",     # 전화번호부
    "findall.co.kr",     # 업체 검색
    "cyworld.com", "me2day.net",
    
    # 학원/교육 플랫폼 (개인홈페이지 아님)
    "learns.academy",     # 중고차 학원
    "academy21.co.kr", "hagwon.co.kr",
    
    # 지도/위치 서비스
    "cokmap.com",     # 중고차 거래 지도 서비스
    "mapquest.com", "here.com"
]

# 제외할 URL 패턴들 (정규식, url_extractor.py에서)
EXCLUDE_URL_PATTERNS = [
    r"namu\.wiki/w/",             # 나무위키 문서
    r"blog\.",                           # 네이버 블로그 서브도메인
    r"cafe\.",                           # 네이버 카페 서브도메인
    r"post\.",                           # 네이버 포스트 서브도메인
    r"news\.",                           # 네이버 뉴스 서브도메인
    r"wiki\.",                           # 네이버 위키 서브도메인
    r"/board/",                         # 게시판 URL
    r"/bbs/",                             # 게시판 URL
    r"/community/",                 # 커뮤니티 URL
    r"\.blogspot\.",               # 블로그스팟
    r"\.tistory\.",                 # 티스토리
    r"\.wordpress\."               # 워드프레스
]

# ===== 이메일 도메인 관련 상수 =====

# 이메일 도메인 분류용 리스트들 (data_statistics.py에서 사용)
PORTAL_EMAIL_DOMAINS = [
    "naver.com", "gmail.com", "daum.net", "hanmail.net", 
    "yahoo.com", "hotmail.com"
]

GOVERNMENT_EMAIL_SUFFIXES = [".go.kr", ".gov.kr"]
EDUCATION_EMAIL_SUFFIXES = [".ac.kr", ".edu"]
BUSINESS_EMAIL_SUFFIXES = [".co.kr", ".com"]
RELIGIOUS_EMAIL_KEYWORDS = ["church", "temple", "cathedral"]

# ===== JavaScript용 상수 (웹 인터페이스에서 사용) =====

# JavaScript용 지역번호 규칙 (main.js에서 사용)
JS_AREA_CODE_RULES = {
    code: {
        "area": name, 
        "minLength": AREA_CODE_LENGTH_RULES[code]["min_length"],
        "maxLength": AREA_CODE_LENGTH_RULES[code]["max_length"]
    }
    for code, name in KOREAN_AREA_CODES.items()
}

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
    "detail_extractor": "detail_extractor",                 # 추가
    "enhanced_detail": "enhanced_detail",                     # 추가  
    "gemini_ai": "gemini_ai_responses"                           # 추가
}

# URL 크롤링 관련 상수 (기본값들, 우선순위 키워드)
HOMEPAGE_KEYWORDS = [
    "home", "index", "main", "www", "homepage", "홈페이지", 
    "메인", "대문", "official", "church", "교회"
]

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

# 크롤링 설정
CRAWLING_CONFIG = {
    "timeout": 10,
    "chunk_size_large": 3000,
    "chunk_size_medium": 2000,
    "overlap": 300,
    "max_chunks": 5,
    "max_text_length": 10000,
    "async_timeout": 120
}

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
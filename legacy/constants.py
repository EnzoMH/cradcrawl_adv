#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Crawling 프로젝트 통합 상수 및 설정 관리
모든 상수, 설정, 경로를 중앙에서 관리하여 일관성과 유지보수성을 향상시킴
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

# ===== 크롤링 설정 확장 =====
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
    "exclude_fields": ["homepage", "extraction_summary"],
    "priority_columns": ["name", "category", "phone", "fax", "email", "address", "postal_code", "mobile"],
    "max_preview_rows": 5,
    "encoding": "utf-8"
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

# ===== 새로 추가된 유틸리티 함수들 =====

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

def generate_output_filename(file_type: str, output_dir=None, **kwargs):
    """출력 파일명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if file_type in OUTPUT_FILE_PATTERNS:
        filename = OUTPUT_FILE_PATTERNS[file_type].format(
            timestamp=timestamp,
            **kwargs
        )
    else:
        filename = f"{file_type}_{timestamp}.json"
    
    if output_dir:
        return Path(output_dir) / filename
    else:
        return filename

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

# ===== 초기화 함수 =====
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
 
 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Crawling 프로젝트 통합 상수 및 설정 관리
기존 constants.py를 확장하여 경로 관리, API 설정 등을 추가
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 기존 constants 모든 내용 import
from constants import *

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

if __name__ == "__main__":
    # 설정 테스트 및 초기화
    initialize_project()
    
    # 런타임 정보 출력
    import pprint
    print("\n📋 전체 설정 정보:")
    runtime_info = get_runtime_info()
    pprint.pprint(runtime_info) 
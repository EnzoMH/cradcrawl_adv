#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Crawling 프로젝트 통합 설정 관리
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 기본 경로 설정
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

# API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL_TEXT = "gemini-1.5-flash"

# 파일 패턴
INPUT_FILE_PATTERNS = [
    "raw_data_*.json",
    "church_data_*.json", 
    "churches_enhanced_*.json",
    "undefined_converted_*.json",
    "combined_*.json"
]

# 크롤링 설정
CRAWLING_CONFIG = {
    "default_delay": 2,
    "max_retries": 3,
    "timeout": 30,
    "headless_mode": True,
    "max_concurrent": 5
}

# 웹 설정
WEB_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# 데이터 변환 설정
CONVERSION_CONFIG = {
    "exclude_fields": [
        "processing_error", "validation_errors", "extraction_timestamp",
        "source_url", "extraction_method", "merge_status", "phone_validation_error",
        "email_validation_error", "ai_analysis", "search_results"
    ],
    "priority_columns": [
        "name", "category", "homepage", "phone", "fax", "email", 
        "mobile", "postal_code", "address"
    ],
    "save_interval": 50
}

def ensure_directories():
    """디렉토리 생성"""
    directories = [DATA_DIR, JSON_DIR, EXCEL_DIR, CSV_DIR, OUTPUT_DIR, LOG_DIR, TEMP_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    print("📁 디렉토리 생성 완료")

def get_latest_input_file():
    """최신 입력 파일 찾기"""
    latest_file = None
    latest_time = 0
    
    for search_dir in [BASE_DIR, JSON_DIR]:
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

def initialize_project():
    """프로젝트 초기화"""
    print("🚀 프로젝트 초기화 시작...")
    ensure_directories()
    
    latest_file = get_latest_input_file()
    print(f"📊 최신 입력 파일: {latest_file or '없음'}")
    print(f"🔑 API 키 설정: {'✅' if GEMINI_API_KEY else '❌'}")
    print("✅ 초기화 완료")

if __name__ == "__main__":
    initialize_project()

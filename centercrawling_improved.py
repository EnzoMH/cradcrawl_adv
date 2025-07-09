#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 아동센터 팩스번호 추출 시스템
- 전화번호 기반 지역 매핑
- 기관명 자동 정규화
- 8-16 워커 병렬 처리
- 엄격한 유효성 검사
"""

import os
import re
import time
import json
import logging
import pandas as pd
import smtplib
import traceback
import psutil
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from bs4 import BeautifulSoup

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
import random

# AI 관련
import google.generativeai as genai
from dotenv import load_dotenv

# 한국 지역번호 매핑 (하드코딩)
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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('centercrawling_improved.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# AI 모델 설정
AI_MODEL_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

class ImprovedCenterCrawlingBot:
    """개선된 아동센터 팩스번호 추출 봇"""
    
    def __init__(self, excel_path: str, use_ai: bool = True, send_email: bool = True):
        """
        초기화
        
        Args:
            excel_path: 원본 엑셀 파일 경로
            use_ai: AI 기능 사용 여부
            send_email: 이메일 전송 여부
        """
        self.excel_path = excel_path
        self.use_ai = use_ai
        self.send_email = send_email
        self.logger = logging.getLogger(__name__)
        
        # 환경 변수 로드
        load_dotenv()
        
        # AI 모델 초기화
        self.ai_model_manager = None
        if self.use_ai:
            self._initialize_ai()
        
        # 이메일 설정
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': os.getenv('SENDER_EMAIL', 'your_email@gmail.com'),
            'sender_password': os.getenv('SENDER_PASSWORD', 'your_app_password'),
            'recipient_email': 'isgs003@naver.com', 
            'recipient_email2': 'crad3981@naver.com'
        }
        
        # WebDriver 초기화
        self.driver = None
        self._initialize_webdriver()
        
        # 데이터 로드
        self.df = None
        self._load_data()
        
        # 결과 저장용
        self.results = []
        self.processed_count = 0
        self.success_count = 0
        self.invalid_count = 0
        self.start_time = datetime.now()
        
        # 시스템 모니터링용
        self.process = psutil.Process()
        self.monitoring_active = False
        self.monitoring_thread = None
        self.system_stats = {
            'cpu_percent': 0,
            'memory_mb': 0,
            'memory_percent': 0
        }
        
        # 🚀 멀티프로세싱 설정 (12개 워커로 최적화)
        # AMD Ryzen 5 3600 (6코어 12스레드) 환경에 최적화
        cpu_count = multiprocessing.cpu_count()
        self.max_workers = 12  # 12개 워커 고정 (하드웨어 사양에 최적화)
        
        # 청크 크기를 12개 워커에 맞게 조정
        self.chunk_size = 8  # 더 큰 청크로 효율성 향상
        
        # 요청 간격 설정 (초) - 12개 워커에 맞게 최적화
        self.request_delay_min = 1.0  # 최소 1초
        self.request_delay_max = 2.0  # 최대 2초
        
        # 에러 발생 시 대기 시간 (초) - 단축
        self.error_wait_time = 5
        
        # 팩스번호 정규식 패턴
        self.fax_patterns = [
            r'팩스[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'fax[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'F[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'전송[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}).*팩스',
            r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}).*fax',
        ]
        
        # 시스템 모니터링 시작
        self._start_system_monitoring()
        
        self.logger.info(f"🚀 ImprovedCenterCrawlingBot 초기화 완료 (워커: {self.max_workers}개)")
    
    class AIModelManager:
        """AI 모델 관리 클래스 - 4개의 Gemini API 키 지원"""
        
        def __init__(self):
            self.gemini_models = []
            self.gemini_config = None
            self.current_model_index = 0
            self.setup_models()
        
        def setup_models(self):
            """4개의 AI 모델 초기화"""
            try:
                # 첫 번째 API 키
                api_key_1 = os.getenv('GEMINI_API_KEY')
                # 두 번째 API 키
                api_key_2 = os.getenv('GEMINI_API_KEY_2')
                # 세 번째 API 키
                api_key_3 = os.getenv('GEMINI_API_KEY_3')
                # 네 번째 API 키
                api_key_4 = os.getenv('GEMINI_API_KEY_4')
                
                if not api_key_1 and not api_key_2 and not api_key_3 and not api_key_4:
                    raise ValueError("GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3, 또는 GEMINI_API_KEY_4 환경 변수가 설정되지 않았습니다.")
                
                self.gemini_config = AI_MODEL_CONFIG
                
                # 첫 번째 모델 설정
                if api_key_1:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key_1)
                        model_1 = genai.GenerativeModel(
                            "gemini-2.0-flash-lite-001",
                            generation_config=self.gemini_config
                        )
                        self.gemini_models.append({
                            'model': model_1,
                            'api_key': api_key_1[:10] + "...",
                            'name': 'GEMINI_1',
                            'failures': 0
                        })
                        logging.getLogger(__name__).info("🤖 Gemini AI 모델 1 초기화 성공")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Gemini 모델 1 초기화 실패: {e}")
                
                # 두 번째 모델 설정
                if api_key_2:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key_2)
                        model_2 = genai.GenerativeModel(
                            "gemini-2.0-flash-lite-001",
                            generation_config=self.gemini_config
                        )
                        self.gemini_models.append({
                            'model': model_2,
                            'api_key': api_key_2[:10] + "...",
                            'name': 'GEMINI_2',
                            'failures': 0
                        })
                        logging.getLogger(__name__).info("🤖 Gemini AI 모델 2 초기화 성공")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Gemini 모델 2 초기화 실패: {e}")
                
                # 세 번째 모델 설정
                if api_key_3:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key_3)
                        model_3 = genai.GenerativeModel(
                            "gemini-2.0-flash-lite-001",
                            generation_config=self.gemini_config
                        )
                        self.gemini_models.append({
                            'model': model_3,
                            'api_key': api_key_3[:10] + "...",
                            'name': 'GEMINI_3',
                            'failures': 0
                        })
                        logging.getLogger(__name__).info("🤖 Gemini AI 모델 3 초기화 성공")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Gemini 모델 3 초기화 실패: {e}")
                
                # 네 번째 모델 설정
                if api_key_4:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key_4)
                        model_4 = genai.GenerativeModel(
                            "gemini-2.0-flash-lite-001",
                            generation_config=self.gemini_config
                        )
                        self.gemini_models.append({
                            'model': model_4,
                            'api_key': api_key_4[:10] + "...",
                            'name': 'GEMINI_4',
                            'failures': 0
                        })
                        logging.getLogger(__name__).info("🤖 Gemini AI 모델 4 초기화 성공")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Gemini 모델 4 초기화 실패: {e}")
                
                if not self.gemini_models:
                    raise ValueError("사용 가능한 Gemini 모델이 없습니다.")
                
                logging.getLogger(__name__).info(f"🎉 총 {len(self.gemini_models)}개의 Gemini 모델 초기화 완료")
                
            except Exception as e:
                logging.getLogger(__name__).error(f"❌ AI 모델 초기화 실패: {e}")
                raise
        
        def get_next_model(self):
            """다음 사용 가능한 모델 선택"""
            if not self.gemini_models:
                return None
            
            # 실패 횟수가 적은 모델 우선 선택
            available_models = [m for m in self.gemini_models if m['failures'] < 3]
            if not available_models:
                # 모든 모델이 실패한 경우 실패 횟수 리셋
                for model in self.gemini_models:
                    model['failures'] = 0
                available_models = self.gemini_models
            
            # 라운드 로빈 방식으로 선택
            model = available_models[self.current_model_index % len(available_models)]
            self.current_model_index = (self.current_model_index + 1) % len(available_models)
            
            return model
        
        def extract_with_gemini(self, text_content: str, prompt_template: str) -> str:
            """Gemini API를 통한 정보 추출 (다중 모델 지원)"""
            if not self.gemini_models:
                return "오류: 사용 가능한 모델이 없습니다."
            
            # 모든 모델을 시도해볼 수 있도록 최대 시도 횟수 설정
            max_attempts = len(self.gemini_models)
            
            for attempt in range(max_attempts):
                current_model = self.get_next_model()
                if not current_model:
                    continue
                
                try:
                    # 텍스트 길이 제한
                    max_length = 32000
                    if len(text_content) > max_length:
                        front_portion = int(max_length * 0.67)
                        back_portion = max_length - front_portion
                        text_content = text_content[:front_portion] + "\n... (중략) ...\n" + text_content[-back_portion:]
                    
                    prompt = prompt_template.format(text_content=text_content)
                    
                    # 현재 모델로 API 호출
                    response = current_model['model'].generate_content(prompt)
                    result_text = response.text
                    
                    # 성공 시 로그 출력
                    logger = logging.getLogger(__name__)
                    logger.info(f"✅ {current_model['name']} API 성공 - 응답 (일부): {result_text[:200]}...")
                    
                    return result_text
                    
                except Exception as e:
                    # 실패 시 다음 모델로 시도
                    current_model['failures'] += 1
                    logger = logging.getLogger(__name__)
                    logger.warning(f"⚠️ {current_model['name']} API 실패 (시도 {attempt + 1}/{max_attempts}): {str(e)}")
                    
                    if attempt < max_attempts - 1:
                        logger.info(f"🔄 다음 모델로 재시도 중...")
                        continue
                    else:
                        logger.error(f"❌ 모든 Gemini 모델 실패")
                        return f"오류: 모든 API 호출 실패 - 마지막 오류: {str(e)}"
            
            return "오류: 모든 모델 시도 실패"
        
        def get_model_status(self) -> str:
            """모델 상태 정보 반환"""
            if not self.gemini_models:
                return "❌ 사용 가능한 모델 없음"
            
            status_info = []
            for model in self.gemini_models:
                status = "✅ 정상" if model['failures'] < 3 else "❌ 실패"
                status_info.append(f"{model['name']}: {status} (실패: {model['failures']}회)")
            
            return " | ".join(status_info)
    
    def _initialize_ai(self):
        """AI 모델 초기화"""
        try:
            self.ai_model_manager = self.AIModelManager()
            self.logger.info("🤖 AI 모델 관리자 초기화 완료")
            # 모델 상태 로그
            status = self.ai_model_manager.get_model_status()
            self.logger.info(f"🔍 AI 모델 상태: {status}")
        except Exception as e:
            self.logger.error(f"❌ AI 모델 초기화 실패: {e}")
            self.use_ai = False
    
    def _initialize_webdriver(self):
        """WebDriver 초기화"""
        try:
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--mute-audio')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            
            self.driver = uc.Chrome(options=chrome_options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            self.logger.info("🌐 WebDriver 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ WebDriver 초기화 실패: {e}")
            raise
    
    def _load_data(self):
        """엑셀 데이터 로드"""
        try:
            self.df = pd.read_excel(self.excel_path)
            self.logger.info(f"📊 데이터 로드 완료: {len(self.df)}개 기관")
            
            # 컬럼명 정규화
            column_mapping = {
                '기관명': 'name',
                '주소': 'address', 
                '전화번호': 'phone',
                '팩스번호': 'fax',
                '홈페이지': 'homepage'
            }
            
            self.df = self.df.rename(columns=column_mapping)
            
            # 누락된 컬럼 추가
            for col in ['name', 'address', 'phone', 'fax', 'homepage']:
                if col not in self.df.columns:
                    self.df[col] = ''
            
            # 🔍 기존 데이터 분석
            self._analyze_existing_data()
            
            self.logger.info(f"✅ 데이터 전처리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 로드 실패: {e}")
            raise
    
    def _analyze_existing_data(self):
        """기존 데이터 분석 (올바른/잘못된 팩스번호 분류)"""
        try:
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            
            # 잘못된 팩스번호 분석
            invalid_fax_count = 0
            for idx, row in self.df.iterrows():
                if pd.notna(row['fax']) and row['fax'].strip():
                    if not self._is_valid_fax_number_strict(row['fax'], row['phone'], row['address'], row['name']):
                        invalid_fax_count += 1
                        self.df.at[idx, 'fax'] = ''  # 잘못된 팩스번호 제거
            
            self.logger.info(f"📊 기존 데이터 분석:")
            self.logger.info(f"  - 전체 기관: {total_count}")
            self.logger.info(f"  - 기존 팩스번호: {fax_count}")
            self.logger.info(f"  - 잘못된 팩스번호 제거: {invalid_fax_count}")
            self.logger.info(f"  - 유효한 팩스번호: {fax_count - invalid_fax_count}")
            
        except Exception as e:
            self.logger.error(f"❌ 기존 데이터 분석 오류: {e}")
    
    def run_extraction(self):
        """전체 추출 프로세스 실행"""
        try:
            self.logger.info("🎯 개선된 팩스번호 추출 시작")
            self._log_system_stats("프로세스 시작")
            
            # 1단계: 병렬 팩스번호 추출
            self.logger.info(f"📞 1단계: 병렬 팩스번호 추출 ({self.max_workers}개 워커)")
            self._extract_fax_parallel()
            self._log_system_stats("1단계 완료")
            
            # 2단계: 홈페이지 직접 접속으로 추가 추출
            self.logger.info("🔍 2단계: 홈페이지 직접 접속으로 추가 추출")
            self._extract_fax_from_homepage()
            self._log_system_stats("2단계 완료")
            
            # 3단계: 결과 저장
            self.logger.info("💾 3단계: 결과 저장")
            result_path = self._save_results()
            self._log_system_stats("결과 저장 완료")
            
            # 4단계: 이메일 전송
            if self.send_email:
                self.logger.info("📧 4단계: 이메일 전송")
                self._send_completion_email(result_path)
            
            self.logger.info("🎉 전체 추출 프로세스 완료")
            
        except KeyboardInterrupt:
            self.logger.info("⚠️ 사용자 중단 요청 감지")
            self._save_intermediate_results("사용자중단저장")
            raise
        except Exception as e:
            self.logger.error(f"❌ 추출 프로세스 실패: {e}")
            self._save_intermediate_results("오류발생저장")
            if self.send_email:
                self._send_error_email(str(e))
            raise
        finally:
            self._cleanup()
    
    def _extract_fax_parallel(self):
        """병렬 팩스번호 추출"""
        # 팩스번호가 없는 행들만 필터링
        missing_fax_rows = self.df[
            (self.df['fax'].isna() | (self.df['fax'] == ''))
        ].copy()
        
        if len(missing_fax_rows) == 0:
            self.logger.info("📞 팩스번호 추출할 데이터가 없습니다.")
            return
        
        # 데이터를 워커 수만큼 분할
        chunks = self._split_dataframe(missing_fax_rows, self.max_workers)
        
        self.logger.info(f"📞 팩스번호 추출 시작: {len(missing_fax_rows)}개 데이터를 {len(chunks)}개 프로세스로 처리")
        
        # 멀티프로세싱으로 병렬 처리
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i, chunk in enumerate(chunks):
                future = executor.submit(
                    process_improved_fax_extraction,
                    chunk,
                    i,
                    self.fax_patterns,
                    KOREAN_AREA_CODES
                )
                futures.append(future)
            
            # 결과 수집
            for future in as_completed(futures):
                try:
                    results = future.result()
                    self._merge_extraction_results(results)
                except Exception as e:
                    self.logger.error(f"❌ 팩스번호 추출 프로세스 오류: {e}")
        
        # 중간 저장
        self._save_intermediate_results("병렬팩스추출_완료")
        self.logger.info("📞 병렬 팩스번호 추출 완료")
    
    def _split_dataframe(self, df: pd.DataFrame, num_chunks: int) -> List[pd.DataFrame]:
        """데이터프레임을 균등하게 분할"""
        chunk_size = max(1, len(df) // num_chunks)
        chunks = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            if i == num_chunks - 1:
                end_idx = len(df)
            else:
                end_idx = (i + 1) * chunk_size
            
            if start_idx < len(df):
                chunk = df.iloc[start_idx:end_idx].copy()
                chunks.append(chunk)
        
        return chunks
    
    def _merge_extraction_results(self, results: List[Dict]):
        """추출 결과를 메인 데이터프레임에 병합"""
        try:
            for result in results:
                idx = result['index']
                fax = result.get('fax', '')
                
                if fax and fax.strip():
                    self.df.at[idx, 'fax'] = fax
                    self.success_count += 1
                    self.logger.info(f"✅ 팩스번호 발견: {result.get('name', 'Unknown')} -> {fax}")
                else:
                    self.invalid_count += 1
                
                self.processed_count += 1
                
        except Exception as e:
            self.logger.error(f"❌ 결과 병합 오류: {e}")
    
    def _extract_fax_from_homepage(self):
        """홈페이지 직접 접속으로 팩스번호 추출"""
        # 팩스번호가 없고 홈페이지가 있는 행들
        missing_fax_rows = self.df[
            (self.df['fax'].isna() | (self.df['fax'] == '')) & 
            (self.df['homepage'].notna() & (self.df['homepage'] != ''))
        ]
        
        processed_in_this_step = 0
        
        for idx, row in missing_fax_rows.iterrows():
            name = row['name']
            homepage = row['homepage']
            phone = row['phone']
            address = row['address']
            
            try:
                self.logger.info(f"🔍 홈페이지 직접 접속: {name} -> {homepage}")
                
                # 홈페이지 크롤링
                page_data = self._crawl_homepage(homepage)
                
                if page_data:
                    # HTML에서 직접 팩스번호 추출
                    fax_numbers = self._extract_fax_from_html(page_data.get('html', ''))
                    self.logger.info(f"🔍 [{name}] HTML에서 추출된 팩스번호: {fax_numbers}")
                    
                    # 유효한 팩스번호 찾기
                    valid_fax = None
                    for fax_num in fax_numbers:
                        if self._is_valid_fax_number_strict(fax_num, phone, address, name):
                            valid_fax = fax_num
                            break
                    
                    if not valid_fax and self.use_ai and self.ai_model_manager:
                        # AI를 통한 팩스번호 추출
                        self.logger.info(f"🤖 [{name}] AI 팩스번호 추출 시도...")
                        ai_fax = self._extract_fax_with_ai(name, page_data)
                        self.logger.info(f"🤖 [{name}] AI 추출 결과: {ai_fax}")
                        
                        if ai_fax:
                            # 🎯 AI가 찾은 팩스번호에 대한 상세 유효성 검사
                            self.logger.info(f"🧪 [{name}] AI 팩스번호 유효성 검사 시작: {ai_fax}")
                            is_valid = self._is_valid_fax_number_strict(ai_fax, phone, address, name)
                            self.logger.info(f"🧪 [{name}] AI 팩스번호 유효성 검사 결과: {is_valid}")
                            
                            if is_valid:
                                valid_fax = ai_fax
                            else:
                                # 개선된 유효성 검사로 대부분의 경우 통과할 것으로 예상
                                self.logger.warning(f"⚠️ [{name}] AI 팩스번호 유효성 검사 실패: {ai_fax}")
                                # 형식만 맞으면 저장 (최후의 수단)
                                if self._is_valid_phone_format(ai_fax):
                                    self.logger.info(f"✅ [{name}] 형식 검사만 통과하여 저장: {ai_fax}")
                                    valid_fax = ai_fax
                    
                    if valid_fax:
                        self.df.at[idx, 'fax'] = valid_fax
                        self.success_count += 1
                        self.logger.info(f"✅ 홈페이지에서 팩스번호 추출: {name} -> {valid_fax}")
                    else:
                        self.logger.info(f"❌ 홈페이지에서 유효한 팩스번호 없음: {name}")
                
                processed_in_this_step += 1
                
                # 중간 저장 (10개마다)
                if processed_in_this_step % 10 == 0:
                    self._save_intermediate_results(f"홈페이지크롤링_중간저장_{processed_in_this_step}")
                    self._log_system_stats(f"홈페이지 크롤링 {processed_in_this_step}개 처리")
                
                time.sleep(2)  # 요청 간격 조절
                
            except KeyboardInterrupt:
                self.logger.info("⚠️ 사용자 중단 요청 감지 (홈페이지 크롤링)")
                self._save_intermediate_results(f"홈페이지크롤링_중단저장_{processed_in_this_step}")
                raise
            except Exception as e:
                self.logger.error(f"❌ 홈페이지 크롤링 오류: {name} - {e}")
                continue
    
    def _is_valid_fax_number_strict(self, fax_number: str, phone_number: str, address: str, org_name: str) -> bool:
        """엄격한 팩스번호 유효성 검증 (개선된 버전)"""
        try:
            if not fax_number or pd.isna(fax_number):
                self.logger.info(f"🚫 [{org_name}] 팩스번호 없음 또는 빈 값")
                return False
            
            normalized_fax = self._normalize_phone_number(fax_number)
            self.logger.info(f"🔍 [{org_name}] 팩스번호 유효성 검사 시작: {fax_number} -> {normalized_fax}")
            
            # 1. 형식 검증
            if not self._is_valid_phone_format(normalized_fax):
                self.logger.info(f"🚫 [{org_name}] 형식 검증 실패: {normalized_fax}")
                return False
            
            # 2. 전화번호와 비교 (완화된 검사) - 전화번호가 없거나 부정확한 경우 스킵
            if phone_number and not pd.isna(phone_number) and str(phone_number).strip():
                try:
                    normalized_phone = self._normalize_phone_number(str(phone_number))
                    self.logger.info(f"🔍 [{org_name}] 전화번호 비교: 팩스={normalized_fax}, 전화={normalized_phone}")
                    
                    # 전화번호 형식이 유효한 경우만 비교
                    if self._is_valid_phone_format(normalized_phone):
                        # 🎯 완전히 동일한 경우도 허용 (많은 기관에서 전화번호와 팩스번호가 같음)
                        if normalized_fax == normalized_phone:
                            self.logger.info(f"✅ [{org_name}] 팩스번호와 전화번호가 동일 (허용): {normalized_fax}")
                            # 동일한 번호도 유효한 팩스번호로 인정
                            return self._is_fax_area_match_address(normalized_fax, address, org_name)
                        
                        # 지역번호 일치성 검사
                        if not self._is_same_area_code(normalized_fax, normalized_phone):
                            fax_digits = re.sub(r'[^\d]', '', normalized_fax)
                            phone_digits = re.sub(r'[^\d]', '', normalized_phone)
                            fax_area = self._extract_area_code(fax_digits)
                            phone_area = self._extract_area_code(phone_digits)
                            self.logger.info(f"⚠️ [{org_name}] 지역번호 불일치하지만 허용: 팩스={fax_area}, 전화={phone_area}")
                            # 지역번호 불일치도 허용 (전화번호가 부정확할 수 있음)
                            pass
                        
                        # 유사성 검사 (완화)
                        if self._are_numbers_too_similar(normalized_fax, normalized_phone):
                            self.logger.info(f"⚠️ [{org_name}] 번호 유사성 검사 - 허용: 팩스={normalized_fax}, 전화={normalized_phone}")
                            # 유사한 번호도 허용 (예: 043-123-4567과 043-123-4568)
                            return self._is_fax_area_match_address(normalized_fax, address, org_name)
                    else:
                        self.logger.info(f"⚠️ [{org_name}] 전화번호 형식이 유효하지 않아 비교 스킵: {normalized_phone}")
                except Exception as e:
                    self.logger.warning(f"⚠️ [{org_name}] 전화번호 비교 중 오류 발생, 스킵: {e}")
            else:
                self.logger.info(f"🔍 [{org_name}] 전화번호 정보 없음 - 전화번호 비교 스킵")
            
            # 3. 주소와 지역 일치성 검사 (완화)
            if not self._is_fax_area_match_address(normalized_fax, address, org_name):
                self.logger.info(f"⚠️ [{org_name}] 주소-지역 일치성 검사 실패했지만 허용")
                # 주소-지역 불일치도 허용 (주소 정보가 부정확할 수 있음)
                pass
            
            self.logger.info(f"✅ [{org_name}] 팩스번호 유효성 검사 통과: {normalized_fax}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 팩스번호 유효성 검증 오류: {org_name} - {e}")
            return False
    
    def _normalize_phone_number(self, phone: str) -> str:
        """전화번호 정규화"""
        numbers = re.findall(r'\d+', phone)
        if not numbers:
            return phone
        
        if len(numbers) >= 3:
            return f"{numbers[0]}-{numbers[1]}-{numbers[2]}"
        elif len(numbers) == 2:
            return f"{numbers[0]}-{numbers[1]}"
        else:
            return numbers[0]
    
    def _is_valid_phone_format(self, phone: str) -> bool:
        """전화번호 형식 유효성 검사"""
        try:
            digits = re.sub(r'[^\d]', '', phone)
            if len(digits) < 8 or len(digits) > 11:
                return False
            
            valid_patterns = [
                r'^02\d{7,8}$',
                r'^0[3-6]\d{7,8}$',
                r'^070\d{7,8}$',
                r'^1[5-9]\d{6,7}$',
                r'^080\d{7,8}$',
            ]
            
            for pattern in valid_patterns:
                if re.match(pattern, digits):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_same_area_code(self, fax: str, phone: str) -> bool:
        """지역번호 일치성 검사"""
        try:
            fax_digits = re.sub(r'[^\d]', '', fax)
            phone_digits = re.sub(r'[^\d]', '', phone)
            
            fax_area = self._extract_area_code(fax_digits)
            phone_area = self._extract_area_code(phone_digits)
            
            return fax_area == phone_area
            
        except Exception:
            return False
    
    def _extract_area_code(self, phone_digits: str) -> str:
        """지역번호 추출"""
        if len(phone_digits) >= 10:
            if phone_digits.startswith('02'):
                return '02'
            else:
                return phone_digits[:3]
        elif len(phone_digits) >= 9:
            if phone_digits.startswith('02'):
                return '02'
            else:
                return phone_digits[:3]
        else:
            return phone_digits[:2]
    
    def _are_numbers_too_similar(self, fax: str, phone: str) -> bool:
        """번호 유사성 검사"""
        try:
            fax_digits = re.sub(r'[^\d]', '', fax)
            phone_digits = re.sub(r'[^\d]', '', phone)
            
            if len(fax_digits) != len(phone_digits) or len(fax_digits) < 8:
                return False
            
            fax_area = self._extract_area_code(fax_digits)
            phone_area = self._extract_area_code(phone_digits)
            
            if fax_area != phone_area:
                return False
            
            fax_suffix = fax_digits[len(fax_area):]
            phone_suffix = phone_digits[len(phone_area):]
            
            diff_count = sum(1 for i, (f, p) in enumerate(zip(fax_suffix, phone_suffix)) if f != p)
            
            return diff_count <= 1
            
        except Exception:
            return False
    
    def _is_fax_area_match_address(self, fax_number: str, address: str, org_name: str) -> bool:
        """팩스번호와 주소 지역 일치성 검사"""
        try:
            if not address or pd.isna(address):
                self.logger.info(f"🔍 [{org_name}] 주소 정보 없음 - 통과")
                return True
            
            fax_digits = re.sub(r'[^\d]', '', fax_number)
            area_code = self._extract_area_code(fax_digits)
            
            # 🎯 더 포괄적인 지역 매핑 (충북 지역 강화)
            area_mapping = {
                '02': ['서울', '서울특별시', '서울시'],
                '031': ['경기', '경기도', '인천', '인천광역시'],
                '032': ['인천', '인천광역시', '경기', '경기도'],
                '033': ['강원', '강원도', '강원특별자치도'],
                '041': ['충남', '충청남도', '세종', '세종특별자치시'],
                '042': ['대전', '대전광역시', '충남', '충청남도'],
                '043': ['충북', '충청북도', '충북도', '청주', '제천', '충주', '음성', '진천', '괴산', '증평', '영동', '옥천', '보은', '단양'],
                '044': ['세종', '세종특별자치시', '충남', '충청남도'],
                '051': ['부산', '부산광역시'],
                '052': ['울산', '울산광역시'],
                '053': ['대구', '대구광역시'],
                '054': ['경북', '경상북도', '대구', '대구광역시'],
                '055': ['경남', '경상남도', '부산', '부산광역시'],
                '061': ['전남', '전라남도', '광주', '광주광역시'],
                '062': ['광주', '광주광역시', '전남', '전라남도'],
                '063': ['전북', '전라북도', '전북도'],
                '064': ['제주', '제주도', '제주특별자치도'],
                '070': ['인터넷전화'],
            }
            
            if area_code == '070':
                self.logger.info(f"🔍 [{org_name}] 인터넷전화 (070) - 통과")
                return True
            
            expected_regions = area_mapping.get(area_code, [])
            if not expected_regions:
                self.logger.info(f"🔍 [{org_name}] 알 수 없는 지역번호 {area_code} - 통과")
                return True
            
            self.logger.info(f"🔍 [{org_name}] 지역 매핑 검사: 팩스지역={area_code}({expected_regions}), 주소={address}")
            
            for region in expected_regions:
                if region in address:
                    self.logger.info(f"✅ [{org_name}] 지역 일치: {region} in {address}")
                    return True
            
            # 🎯 추가 검사: 주소에 시/군/구 정보가 있는지 확인
            import re
            city_match = re.search(r'([가-힣]+시|[가-힣]+군|[가-힣]+구)', address)
            if city_match:
                city_name = city_match.group(1)
                self.logger.info(f"🔍 [{org_name}] 시/군/구 정보 발견: {city_name}")
                
                # 충북 지역 도시들 특별 검사
                if area_code == '043':
                    chungbuk_cities = ['청주시', '청주', '충주시', '충주', '제천시', '제천', '음성군', '음성', '진천군', '진천', '괴산군', '괴산', '증평군', '증평', '영동군', '영동', '옥천군', '옥천', '보은군', '보은', '단양군', '단양']
                    for city in chungbuk_cities:
                        if city in address:
                            self.logger.info(f"✅ [{org_name}] 충북 도시 일치: {city} in {address}")
                            return True
            
            self.logger.info(f"🚫 [{org_name}] 지역 불일치: 팩스={area_code}({expected_regions}) vs 주소={address}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ [{org_name}] 지역 일치성 검사 오류: {e}")
            return True  # 오류 발생 시 통과
    
    def _crawl_homepage(self, url: str) -> Optional[Dict[str, Any]]:
        """홈페이지 크롤링"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            time.sleep(3)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''
            
            return {
                'url': url,
                'html': page_source,
                'text_content': text_content,
                'title': title_text
            }
            
        except Exception as e:
            self.logger.error(f"❌ 홈페이지 크롤링 오류: {url} - {e}")
            return None
    
    def _extract_fax_from_html(self, html_content: str) -> List[str]:
        """HTML에서 팩스번호 추출"""
        try:
            fax_numbers = []
            for pattern in self.fax_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    normalized = self._normalize_phone_number(match)
                    if normalized and normalized not in fax_numbers:
                        fax_numbers.append(normalized)
            
            return fax_numbers
            
        except Exception as e:
            self.logger.error(f"❌ HTML 팩스번호 추출 오류: {e}")
            return []
    
    def _extract_fax_with_ai(self, org_name: str, page_data: Dict[str, Any]) -> Optional[str]:
        """AI를 통한 팩스번호 추출 (개선된 버전)"""
        if not self.use_ai or not self.ai_model_manager:
            return None
        
        try:
            prompt_template = """
'{org_name}' 기관의 홈페이지에서 팩스번호를 찾아주세요.

**홈페이지 정보:**
- 제목: {title}
- URL: {url}

**홈페이지 내용:**
{text_content}

**요청:**
이 기관의 팩스번호를 찾아서 다음 형식으로만 응답해주세요:
- 팩스번호가 있으면: 팩스번호만 (예: 02-1234-5678)
- 팩스번호가 없으면: "없음"

주의: 전화번호와 팩스번호가 다른 번호인지 확인해주세요.
팩스번호가 전화번호와 같아도 괜찮습니다.
""".format(
                org_name=org_name,
                title=page_data.get('title', ''),
                url=page_data.get('url', ''),
                text_content=page_data.get('text_content', '')[:3000]
            )
            
            response_text = self.ai_model_manager.extract_with_gemini(
                page_data.get('text_content', ''),
                prompt_template
            )
            
            self.logger.info(f"🤖 [{org_name}] AI 원본 응답: {response_text}")
            
            if response_text and response_text.strip():
                # "없음" 또는 오류 메시지 체크
                if any(keyword in response_text.lower() for keyword in ["없음", "오류:", "error", "찾을 수 없"]):
                    self.logger.info(f"🤖 [{org_name}] AI가 팩스번호 없음으로 응답")
                    return None
                
                # 🎯 더 포괄적인 팩스번호 추출 패턴
                fax_patterns = [
                    r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',  # 기본 패턴
                    r'팩스[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',  # 팩스: 043-123-4567
                    r'fax[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',  # fax: 043-123-4567
                    r'(\d{2,4})\D*(\d{3,4})\D*(\d{4})',  # 분리된 숫자들
                ]
                
                for pattern in fax_patterns:
                    matches = re.findall(pattern, response_text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            # 분리된 숫자들을 조합
                            if len(match) == 3:
                                fax_number = f"{match[0]}-{match[1]}-{match[2]}"
                            else:
                                fax_number = match[0] if match[0] else match[1]
                        else:
                            fax_number = match
                        
                        # 정규화
                        normalized_fax = self._normalize_phone_number(fax_number)
                        
                        # 기본 형식 검사
                        if self._is_valid_phone_format(normalized_fax):
                            self.logger.info(f"🤖 [{org_name}] AI 팩스번호 추출 성공: {fax_number} -> {normalized_fax}")
                            return normalized_fax
                        else:
                            self.logger.info(f"🤖 [{org_name}] AI 팩스번호 형식 검사 실패: {fax_number} -> {normalized_fax}")
                
                self.logger.info(f"🤖 [{org_name}] AI 응답에서 유효한 팩스번호를 찾지 못함")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ AI 팩스번호 추출 오류: {org_name} - {e}")
            return None
    
    def _save_results(self) -> str:
        """결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
            result_filename = f"{base_name}_개선된결과_{timestamp}.xlsx"
            result_path = os.path.join(os.path.dirname(self.excel_path), result_filename)
            
            self.df.to_excel(result_path, index=False)
            
            # 통계 정보
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            
            self.logger.info(f"💾 결과 저장 완료: {result_path}")
            self.logger.info(f"📊 최종 통계:")
            self.logger.info(f"  - 전체 기관 수: {total_count}")
            self.logger.info(f"  - 팩스번호 보유: {fax_count} ({fax_count/total_count*100:.1f}%)")
            self.logger.info(f"  - 처리된 기관 수: {self.processed_count}")
            self.logger.info(f"  - 성공 추출 수: {self.success_count}")
            self.logger.info(f"  - 무효 처리 수: {self.invalid_count}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"❌ 결과 저장 오류: {e}")
            raise
    
    def _send_completion_email(self, result_path: str):
        """완료 이메일 전송"""
        try:
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            
            subject = "🎉 개선된 아동센터 팩스번호 추출 완료"
            
            body = f"""
안녕하세요! 대표님! 신명호입니다.

개선된 아동센터 팩스번호 추출 작업이 완료되었습니다.

📊 **작업 결과 요약:**
- 전체 기관 수: {total_count:,}개
- 팩스번호 보유: {fax_count:,}개 ({fax_count/total_count*100:.1f}%)
- 처리된 기관 수: {self.processed_count:,}개
- 성공 추출 수: {self.success_count:,}개
- 무효 처리 수: {self.invalid_count:,}개

⏱️ **실행 시간:** {duration}
🚀 **사용 워커:** {self.max_workers}개

🔧 **개선 사항:**
- 전화번호 기반 지역 매핑
- 기관명 자동 정규화
- 엄격한 유효성 검사
- {self.max_workers}개 워커 병렬 처리

📁 **결과 파일:** {os.path.basename(result_path)}

감사합니다!
-신명호 드림-
"""
            
            self._send_email(subject, body, result_path)
            self.logger.info("📧 완료 이메일 전송 성공")
            
        except Exception as e:
            self.logger.error(f"❌ 완료 이메일 전송 실패: {e}")
    
    def _send_error_email(self, error_message: str):
        """오류 이메일 전송"""
        try:
            subject = "❌ 개선된 아동센터 팩스번호 추출 오류 발생"
            
            body = f"""
안녕하세요!

개선된 아동센터 팩스번호 추출 작업 중 오류가 발생했습니다.

❌ **오류 내용:**
{error_message}

📊 **진행 상황:**
- 처리된 기관 수: {self.processed_count:,}개
- 성공 추출 수: {self.success_count:,}개
- 무효 처리 수: {self.invalid_count:,}개

⏱️ **실행 시간:** {datetime.now() - self.start_time}

로그 파일을 확인해주세요.

ImprovedCenterCrawlingBot 🤖
"""
            
            self._send_email(subject, body)
            self.logger.info("📧 오류 이메일 전송 성공")
            
        except Exception as e:
            self.logger.error(f"❌ 오류 이메일 전송 실패: {e}")
    
    def _send_email(self, subject: str, body: str, attachment_path: str = None):
        """이메일 전송"""
        try:
            if not self.email_config['sender_email'] or not self.email_config['sender_password']:
                self.logger.warning("⚠️ 이메일 설정이 완료되지 않았습니다.")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], self.email_config['recipient_email'], text)
            server.quit()
            
            self.logger.info(f"📧 이메일 전송 완료: {self.email_config['recipient_email']}")
            
        except Exception as e:
            self.logger.error(f"❌ 이메일 전송 오류: {e}")
    
    def _start_system_monitoring(self):
        """시스템 모니터링 시작"""
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("📊 시스템 모니터링 시작")
        except Exception as e:
            self.logger.error(f"❌ 시스템 모니터링 시작 오류: {e}")
    
    def _monitor_system(self):
        """시스템 리소스 모니터링 (과부하 감지)"""
        overload_count = 0
        
        while self.monitoring_active:
            try:
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                system_memory = psutil.virtual_memory()
                memory_percent = (memory_info.rss / system_memory.total) * 100
                
                # 전체 시스템 리소스 확인
                system_cpu = psutil.cpu_percent(interval=1)
                system_memory_percent = system_memory.percent
                
                self.system_stats.update({
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_percent': memory_percent,
                    'system_cpu': system_cpu,
                    'system_memory': system_memory_percent
                })
                
                # 🚨 과부하 감지 (12개 워커에 맞게 조정)
                if system_cpu > 85 or system_memory_percent > 85:
                    overload_count += 1
                    if overload_count >= 3:  # 3번 연속 과부하 시
                        self.logger.warning(f"🚨 시스템 과부하 감지! CPU: {system_cpu:.1f}%, 메모리: {system_memory_percent:.1f}%")
                        self.logger.warning("⏳ 시스템 안정화를 위해 20초 대기...")
                        time.sleep(20)
                        overload_count = 0
                else:
                    overload_count = 0
                
                # 프로세스 과부하 체크 (12개 워커에 맞게 조정)
                if cpu_percent > 70 or memory_percent > 15:
                    self.logger.warning(f"⚠️ 프로세스 리소스 높음 - CPU: {cpu_percent:.1f}%, 메모리: {memory_percent:.1f}%")
                
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ 시스템 모니터링 오류: {e}")
                time.sleep(30)
    
    def _log_system_stats(self, stage: str):
        """시스템 통계 로깅"""
        try:
            stats = self.system_stats
            self.logger.info(f"📊 [{stage}] CPU: {stats['cpu_percent']:.1f}%, "
                           f"메모리: {stats['memory_mb']:.1f}MB ({stats['memory_percent']:.1f}%)")
        except Exception as e:
            self.logger.error(f"❌ 시스템 통계 로깅 오류: {e}")
    
    def _save_intermediate_results(self, suffix: str = "중간저장"):
        """중간 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
            result_filename = f"{base_name}_{suffix}_{timestamp}.xlsx"
            result_path = os.path.join(os.path.dirname(self.excel_path), result_filename)
            
            self.df.to_excel(result_path, index=False)
            
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            
            self.logger.info(f"💾 중간 저장 완료: {result_path}")
            self.logger.info(f"📊 현재 통계 - 전체: {total_count}, 팩스: {fax_count}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"❌ 중간 저장 오류: {e}")
            return None
    
    def _cleanup(self):
        """정리 작업"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=1)
            
            if self.driver:
                self.driver.quit()
                self.logger.info("🧹 WebDriver 정리 완료")
                
            self.logger.info("🧹 시스템 정리 완료")
        except Exception as e:
            self.logger.error(f"❌ 정리 작업 오류: {e}")


# ===== 병렬 처리 워커 함수들 =====

def create_improved_worker_driver(worker_id: int):
    """개선된 워커용 WebDriver 생성 (과부하 방지)"""
    try:
        import undetected_chromedriver as uc
        import random
        import time
        
        # 워커 간 시차 두기
        startup_delay = random.uniform(1.0, 3.0) * worker_id
        time.sleep(startup_delay)
        
        chrome_options = uc.ChromeOptions()
        
        # 기본 옵션
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1366,768')  # 더 작은 윈도우
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        
        # 🛡️ 리소스 절약 옵션 (12개 워커 최적화)
        chrome_options.add_argument('--disable-images')  # 이미지 로딩 비활성화
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        
        # 메모리 제한 (12개 워커에 맞게 조정)
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=256')  # 더 작은 메모리 할당
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--max-unused-resource-memory-usage-percentage=5')
        
        # 안전한 포트 설정 (9222 + worker_id * 10)
        debug_port = 9222 + (worker_id * 10)
        chrome_options.add_argument(f'--remote-debugging-port={debug_port}')
        
        # User-Agent 랜덤화
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # 드라이버 생성
        driver = uc.Chrome(options=chrome_options, version_main=None)
        
        # 타임아웃 설정 (12개 워커에 맞게 최적화)
        driver.implicitly_wait(10)  # 더 짧은 대기 시간
        driver.set_page_load_timeout(20)  # 더 짧은 페이지 로드 시간
        
        # 웹드라이버 감지 방지
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"🔧 워커 {worker_id}: WebDriver 생성 완료 (포트: {debug_port})")
        
        return driver
        
    except Exception as e:
        print(f"❌ 워커 {worker_id} WebDriver 생성 오류: {e}")
        return None

def get_region_from_phone(phone: str, address: str = None) -> str:
    """전화번호에서 지역 정보 추출"""
    try:
        if not phone or pd.isna(phone):
            return extract_region_from_address(address) if address else ""
        
        # 전화번호에서 지역번호 추출
        phone_digits = re.sub(r'[^\d]', '', str(phone))
        
        if len(phone_digits) >= 10:
            if phone_digits.startswith('02'):
                area_code = '02'
            else:
                area_code = phone_digits[:3]
        elif len(phone_digits) >= 9:
            if phone_digits.startswith('02'):
                area_code = '02'
            else:
                area_code = phone_digits[:3]
        else:
            area_code = phone_digits[:2]
        
        # 지역번호 -> 지역명 매핑
        region = KOREAN_AREA_CODES.get(area_code, "")
        
        # 핸드폰/인터넷전화인 경우 주소에서 추출
        if region in ["핸드폰", "인터넷전화", ""] and address:
            region = extract_region_from_address(address)
        
        return region
        
    except Exception as e:
        print(f"❌ 지역 추출 오류: {e}")
        return ""

def extract_region_from_address(address: str) -> str:
    """주소에서 지역 정보 추출"""
    if not address:
        return ""
    
    region_patterns = [
        r'(강원특별자치도|강원도)\s+(\S+시|\S+군)',
        r'(서울특별시|서울시|서울)\s+(\S+구)',
        r'(경기도|경기)\s+(\S+시|\S+군)',
        r'(인천광역시|인천시|인천)\s+(\S+구)',
        r'(충청남도|충남)\s+(\S+시|\S+군)',
        r'(충청북도|충북)\s+(\S+시|\S+군)',
        r'(전라남도|전남)\s+(\S+시|\S+군)',
        r'(전라북도|전북)\s+(\S+시|\S+군)',
        r'(경상남도|경남)\s+(\S+시|\S+군)',
        r'(경상북도|경북)\s+(\S+시|\S+군)',
        r'(부산광역시|부산시|부산)\s+(\S+구)',
        r'(대구광역시|대구시|대구)\s+(\S+구)',
        r'(광주광역시|광주시|광주)\s+(\S+구)',
        r'(대전광역시|대전시|대전)\s+(\S+구)',
        r'(울산광역시|울산시|울산)\s+(\S+구)',
        r'(제주특별자치도|제주도|제주)\s+(\S+시)',
        r'(세종특별자치시|세종시|세종)',
    ]
    
    for pattern in region_patterns:
        match = re.search(pattern, address)
        if match:
            return match.group(1)
    
    return ""

def normalize_org_name(name: str) -> str:
    """기관명 정규화 (지역아동센터 자동 추가)"""
    if not name or pd.isna(name):
        return name
    
    name = name.strip()
    
    # 이미 "지역아동센터"가 포함되어 있거나 "센터"로 끝나는 경우
    if "지역아동센터" in name or name.endswith("센터"):
        return name
    
    # 그렇지 않은 경우 "지역아동센터" 추가
    return f"{name} 지역아동센터"

def process_improved_fax_extraction(chunk_df: pd.DataFrame, worker_id: int, fax_patterns: List[str], area_codes: Dict) -> List[Dict]:
    """개선된 팩스번호 추출 청크 처리"""
    import pandas as pd
    import re
    import time
    import random
    
    results = []
    driver = None
    
    try:
        driver = create_improved_worker_driver(worker_id)
        if not driver:
            return results
        
        print(f"🔧 워커 {worker_id}: 개선된 팩스번호 추출 시작 ({len(chunk_df)}개)")
        
        for idx, row in chunk_df.iterrows():
            name = row['name']
            phone = row['phone']
            address = row.get('address', '')
            
            if not name or pd.isna(name):
                continue
            
            try:
                print(f"📞 워커 {worker_id}: 팩스번호 검색 - {name}")
                
                # 🎯 전화번호에서 지역 정보 추출
                region = get_region_from_phone(phone, address)
                
                # 🎯 기관명 정규화
                normalized_name = normalize_org_name(name)
                
                # 🎯 개선된 검색 쿼리 생성
                if region and region not in ["핸드폰", "인터넷전화"]:
                    search_query = f"{region} {normalized_name} 팩스번호"
                else:
                    search_query = f"{normalized_name} 팩스번호"
                
                print(f"🔍 워커 {worker_id}: 검색쿼리 - {search_query}")
                
                # 구글 검색
                fax_number = search_google_improved(driver, search_query, fax_patterns)
                
                # 유효성 검사
                if fax_number and is_valid_fax_improved(fax_number, phone, address, name):
                    results.append({
                        'index': idx,
                        'name': name,
                        'fax': fax_number
                    })
                    print(f"✅ 워커 {worker_id}: 팩스번호 발견 - {name} -> {fax_number}")
                else:
                    results.append({
                        'index': idx,
                        'name': name,
                        'fax': ''
                    })
                    if fax_number:
                        print(f"🚫 워커 {worker_id}: 팩스번호 유효성 검사 실패 - {name} -> {fax_number}")
                    else:
                        print(f"❌ 워커 {worker_id}: 팩스번호 없음 - {name}")
                
                # 🛡️ 안전한 랜덤 지연 (1-2초로 최적화)
                delay = random.uniform(1.0, 2.0)
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ 워커 {worker_id}: 팩스번호 검색 오류 - {name}: {e}")
                
                # 에러 발생 시 더 긴 대기 (단축)
                error_delay = random.uniform(3.0, 5.0)
                print(f"⏳ 워커 {worker_id}: 에러 발생으로 {error_delay:.1f}초 대기...")
                time.sleep(error_delay)
                
                results.append({
                    'index': idx,
                    'name': name,
                    'fax': ''
                })
                continue
        
        print(f"🎉 워커 {worker_id}: 팩스번호 추출 완료 ({len(results)}개)")
        
    except Exception as e:
        print(f"❌ 워커 {worker_id}: 팩스번호 추출 프로세스 오류: {e}")
    finally:
        if driver:
            driver.quit()
    
    return results

def search_google_improved(driver, query: str, fax_patterns: List[str]):
    """개선된 구글 검색 (과부하 방지)"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from bs4 import BeautifulSoup
        import time
        import random
        import re
        
        # 🛡️ 안전한 랜덤 지연 (1-3초로 조정)
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
        
        # 재시도 로직
        max_retries = 3
        for retry in range(max_retries):
            try:
                # 구글 검색 페이지로 이동
                driver.get('https://www.google.com')
                
                # 추가 대기 시간
                time.sleep(random.uniform(1.5, 2.5))
                
                # 검색창 찾기 (centercrawling.py와 동일한 방식)
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'q'))
                )
                
                # 검색어 입력 (천천히)
                search_box.clear()
                for char in query:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.03, 0.08))  # 더 천천히 입력
                
                # 검색 실행
                search_box.send_keys(Keys.RETURN)
                
                # 결과 페이지 로딩 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'search'))
                )
                
                # 추가 대기 시간
                time.sleep(random.uniform(1.0, 2.0))
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 팩스번호 추출
                for pattern in fax_patterns:
                    matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                    for match in matches:
                        normalized = normalize_phone_simple(match)
                        if is_valid_phone_format_simple(normalized):
                            return normalized
                
                # 검색 성공했지만 결과 없음
                return None
                
            except (TimeoutException, WebDriverException) as e:
                if retry < max_retries - 1:
                    wait_time = random.uniform(5, 10)  # 5-10초 대기
                    print(f"⚠️ 검색 실패 (재시도 {retry + 1}/{max_retries}), {wait_time:.1f}초 후 재시도: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        return None
        
    except Exception as e:
        print(f"❌ 구글 검색 오류: {e}")
        # 에러 발생 시 더 긴 대기
        time.sleep(random.uniform(5, 10))
        return None

def normalize_phone_simple(phone: str) -> str:
    """간단한 전화번호 정규화"""
    numbers = re.findall(r'\d+', phone)
    if not numbers:
        return phone
    
    if len(numbers) >= 3:
        return f"{numbers[0]}-{numbers[1]}-{numbers[2]}"
    elif len(numbers) == 2:
        return f"{numbers[0]}-{numbers[1]}"
    else:
        return numbers[0]

def is_valid_phone_format_simple(phone: str) -> bool:
    """간단한 전화번호 형식 검사"""
    try:
        digits = re.sub(r'[^\d]', '', phone)
        if len(digits) < 8 or len(digits) > 11:
            return False
        
        valid_patterns = [
            r'^02\d{7,8}$',
            r'^0[3-6]\d{7,8}$',
            r'^070\d{7,8}$',
            r'^1[5-9]\d{6,7}$',
            r'^080\d{7,8}$',
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, digits):
                return True
        
        return False
        
    except Exception:
        return False

def is_valid_fax_improved(fax_number: str, phone_number: str, address: str, org_name: str) -> bool:
    """개선된 팩스번호 유효성 검사"""
    try:
        import pandas as pd
        
        if not fax_number or pd.isna(fax_number):
            return False
        
        normalized_fax = normalize_phone_simple(fax_number)
        
        # 1. 형식 검증
        if not is_valid_phone_format_simple(normalized_fax):
            return False
        
        # 2. 전화번호와 비교
        if phone_number and not pd.isna(phone_number):
            normalized_phone = normalize_phone_simple(str(phone_number))
            
            # 완전히 동일한 경우 제외
            if normalized_fax == normalized_phone:
                return False
            
            # 지역번호 일치성 검사
            if not is_same_area_code_simple(normalized_fax, normalized_phone):
                return False
            
            # 유사성 검사
            if are_numbers_too_similar_simple(normalized_fax, normalized_phone):
                return False
        
        # 3. 주소와 지역 일치성 검사
        if not is_fax_area_match_address_simple(normalized_fax, address, org_name):
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 팩스번호 유효성 검사 오류: {org_name} - {e}")
        return False

def is_same_area_code_simple(fax: str, phone: str) -> bool:
    """간단한 지역번호 일치성 검사"""
    try:
        fax_digits = re.sub(r'[^\d]', '', fax)
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        fax_area = extract_area_code_simple(fax_digits)
        phone_area = extract_area_code_simple(phone_digits)
        
        return fax_area == phone_area
    except:
        return False

def extract_area_code_simple(phone_digits: str) -> str:
    """간단한 지역번호 추출"""
    if len(phone_digits) >= 10:
        if phone_digits.startswith('02'):
            return '02'
        else:
            return phone_digits[:3]
    elif len(phone_digits) >= 9:
        if phone_digits.startswith('02'):
            return '02'
        else:
            return phone_digits[:3]
    else:
        return phone_digits[:2]

def are_numbers_too_similar_simple(fax: str, phone: str) -> bool:
    """간단한 번호 유사성 검사"""
    try:
        fax_digits = re.sub(r'[^\d]', '', fax)
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        if len(fax_digits) != len(phone_digits) or len(fax_digits) < 8:
            return False
        
        fax_area = extract_area_code_simple(fax_digits)
        phone_area = extract_area_code_simple(phone_digits)
        
        if fax_area != phone_area:
            return False
        
        fax_suffix = fax_digits[len(fax_area):]
        phone_suffix = phone_digits[len(phone_area):]
        
        diff_count = sum(1 for i, (f, p) in enumerate(zip(fax_suffix, phone_suffix)) if f != p)
        
        return diff_count <= 1
    except:
        return False

def is_fax_area_match_address_simple(fax_number: str, address: str, org_name: str = None) -> bool:
    """간단한 지역 일치성 검사"""
    try:
        import pandas as pd
        
        if not address or pd.isna(address):
            return True
        
        fax_digits = re.sub(r'[^\d]', '', fax_number)
        area_code = extract_area_code_simple(fax_digits)
        
        area_mapping = {
            '02': ['서울', '서울특별시', '서울시'],
            '031': ['경기', '경기도', '인천', '인천광역시'],
            '032': ['인천', '인천광역시', '경기'],
            '033': ['강원', '강원도', '강원특별자치도'],
            '041': ['충남', '충청남도', '세종', '세종특별자치시'],
            '042': ['대전', '대전광역시', '충남', '충청남도'],
            '043': ['충북', '충청북도'],
            '044': ['세종', '세종특별자치시', '충남'],
            '051': ['부산', '부산광역시'],
            '052': ['울산', '울산광역시'],
            '053': ['대구', '대구광역시'],
            '054': ['경북', '경상북도', '대구'],
            '055': ['경남', '경상남도', '부산'],
            '061': ['전남', '전라남도', '광주'],
            '062': ['광주', '광주광역시', '전남'],
            '063': ['전북', '전라북도'],
            '064': ['제주', '제주도', '제주특별자치도'],
            '070': ['인터넷전화'],
        }
        
        if area_code == '070':
            return True
        
        expected_regions = area_mapping.get(area_code, [])
        if not expected_regions:
            return True
        
        for region in expected_regions:
            if region in address:
                return True
        
        print(f"🚫 지역 불일치: {org_name} - 팩스:{area_code}({expected_regions}) vs 주소:{address}")
        return False
        
    except:
        return True

def main():
    """메인 실행 함수"""
    try:
        print("🚀 개선된 아동센터 팩스번호 추출 시스템 시작")
        print("=" * 60)
        
        # 봇 초기화 및 실행
        bot = ImprovedCenterCrawlingBot("childcenter2.xlsx", use_ai=True, send_email=True)
        bot.run_extraction()
        
        print("=" * 60)
        print("✅ 팩스번호 추출 완료!")
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
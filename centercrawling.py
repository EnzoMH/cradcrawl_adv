#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아동센터 팩스번호 추출 시스템
Selenium WebDriver + BeautifulSoup + Gemini AI를 활용한 자동 팩스번호 추출
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

# AI 관련 (utils/ai_helpers.py 참고)
import google.generativeai as genai
from dotenv import load_dotenv

# 추가 import 필요
import undetected_chromedriver as uc
import random
from selenium.webdriver.common.action_chains import ActionChains

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('centercrawling.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# AI 모델 설정 (ai_helpers.py 스타일)
AI_MODEL_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

class CenterCrawlingBot:
    """아동센터 팩스번호 추출 봇"""
    
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
        
        # AI 모델 초기화 (ai_helpers.py 스타일)
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
            'recipient_email2': 'crad3981@naver.com'   # 테스트 이메일
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
        self.duplicate_count = 0  # 중복 제거된 팩스번호 개수
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
        
        # 멀티프로세싱 설정
        self.max_workers = 4  # 최대 4개 창
        self.chunk_size = 10  # 한 번에 처리할 데이터 크기
        
        # 팩스번호 정규식 패턴
        self.fax_patterns = [
            r'팩스[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'fax[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'F[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'전송[\s:：]*(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',
            r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}).*팩스',
            r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}).*fax',
        ]
        
        # 홈페이지 URL 정규식 패턴
        self.url_patterns = [
            r'https?://[^\s<>"\']+',
            r'www\.[^\s<>"\']+',
            r'[a-zA-Z0-9.-]+\.(com|co\.kr|or\.kr|go\.kr|net|org)[^\s<>"\']*'
        ]
        
        # 시스템 모니터링 시작
        self._start_system_monitoring()
        
        self.logger.info("🚀 CenterCrawlingBot 초기화 완료")
    
    class AIModelManager:
        """AI 모델 관리 클래스 (ai_helpers.py 스타일)"""
        
        def __init__(self):
            """초기화"""
            self.gemini_model = None
            self.gemini_config = None
            self.setup_models()
        
        def setup_models(self):
            """AI 모델 초기화"""
            try:
                # Gemini API 키 확인
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
                
                # Gemini 설정
                genai.configure(api_key=api_key)
                self.gemini_config = AI_MODEL_CONFIG
                self.gemini_model = genai.GenerativeModel(
                    "gemini-1.5-flash",
                    generation_config=self.gemini_config
                )
                
                logging.getLogger(__name__).info("🤖 Gemini AI 모델 초기화 성공")
                
            except Exception as e:
                logging.getLogger(__name__).error(f"❌ AI 모델 초기화 실패: {e}")
                logging.getLogger(__name__).debug(traceback.format_exc())
                raise
        
        def extract_with_gemini(self, text_content: str, prompt_template: str) -> str:
            """
            텍스트 콘텐츠를 Gemini API에 전달하여 정보 추출
            
            Args:
                text_content: 분석할 텍스트 콘텐츠
                prompt_template: 프롬프트 템플릿 문자열
                
            Returns:
                추출된 정보 문자열
            """
            try:
                # 텍스트 길이 제한
                max_length = 32000
                if len(text_content) > max_length:
                    front_portion = int(max_length * 0.67)
                    back_portion = max_length - front_portion
                    text_content = text_content[:front_portion] + "\n... (중략) ...\n" + text_content[-back_portion:]
                    logging.getLogger(__name__).warning(f"텍스트가 너무 길어 일부를 생략했습니다: {len(text_content)} -> {max_length}")
                
                # 프롬프트 구성
                prompt = prompt_template.format(text_content=text_content)
                
                # 응답 생성
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text
                
                # 결과 로깅 (첫 200자만)
                logging.getLogger(__name__).info(f"Gemini API 응답 (일부): {result_text[:200]}...")
                
                return result_text
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Gemini API 호출 중 오류: {str(e)}")
                logging.getLogger(__name__).debug(traceback.format_exc())
                return f"오류: {str(e)}"
    
    def _initialize_ai(self):
        """AI 모델 초기화"""
        try:
            self.ai_model_manager = self.AIModelManager()
            self.logger.info("🤖 AI 모델 관리자 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ AI 모델 초기화 실패: {e}")
            self.use_ai = False
    
    def _initialize_webdriver(self):
        """WebDriver 초기화 (undetected-chromedriver 사용)"""
        try:
            # 🤖 undetected-chromedriver 사용
            chrome_options = uc.ChromeOptions()
            
            # 기본 설정
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # 🔧 고급 봇 감지 우회 옵션들
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--mute-audio')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            
            # 🎭 프로필 설정
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # undetected-chromedriver 사용
            self.driver = uc.Chrome(options=chrome_options, version_main=None)
            
            # 🔧 추가 JavaScript 실행으로 봇 감지 우회
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")
            self.driver.execute_script("window.navigator.chrome = {runtime: {}};")
            self.driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => ({query: x => Promise.resolve({state: 'granted'})})});")
            
            self.driver.implicitly_wait(10)
            self.logger.info("🌐 WebDriver 초기화 완료 (undetected-chromedriver)")
            
        except Exception as e:
            self.logger.error(f"❌ undetected-chromedriver 초기화 실패: {e}")
            # fallback to regular webdriver
            self._initialize_regular_webdriver()
    
    def _initialize_regular_webdriver(self):
        """일반 WebDriver 초기화 (fallback)"""
        try:
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # User-Agent 랜덤화
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            selected_user_agent = random.choice(user_agents)
            chrome_options.add_argument(f'--user-agent={selected_user_agent}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.logger.info("🌐 일반 WebDriver 초기화 완료 (fallback)")
            
        except Exception as e:
            self.logger.error(f"❌ 일반 WebDriver 초기화 실패: {e}")
            raise
    
    def _load_data(self):
        """엑셀 데이터 로드"""
        try:
            self.df = pd.read_excel(self.excel_path)
            self.logger.info(f"📊 데이터 로드 완료: {len(self.df)}개 기관")
            self.logger.info(f"📋 컬럼: {list(self.df.columns)}")
            
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
            
            self.logger.info(f"✅ 데이터 전처리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 로드 실패: {e}")
            raise
    
    def run_extraction(self):
        """전체 추출 프로세스 실행"""
        try:
            self.logger.info("🎯 팩스번호 추출 시작")
            self._log_system_stats("프로세스 시작")
            
            # 1단계: 검색을 통한 팩스번호 추출 (병렬 처리)
            self.logger.info("📞 1단계: 검색을 통한 팩스번호 추출 (4개 창 병렬)")
            self._extract_fax_by_search_parallel()
            self._log_system_stats("1단계 완료")
            
            # 2단계: 검색을 통한 홈페이지 추출 (병렬 처리)
            self.logger.info("🌐 2단계: 검색을 통한 홈페이지 추출 (4개 창 병렬)")
            self._extract_homepage_by_search_parallel()
            self._log_system_stats("2단계 완료")
            
            # 3단계: 홈페이지 직접 접속으로 팩스번호 추출 (단일 처리)
            self.logger.info("🔍 3단계: 홈페이지 직접 접속으로 팩스번호 추출 (AI 검증)")
            self._extract_fax_from_homepage()
            self._log_system_stats("3단계 완료")
            
            # 4단계: 결과 저장
            self.logger.info("💾 4단계: 결과 저장")
            result_path = self._save_results()
            self._log_system_stats("결과 저장 완료")
            
            # 5단계: 이메일 전송
            if self.send_email:
                self.logger.info("📧 5단계: 이메일 전송")
                self._send_completion_email(result_path)
            
            self.logger.info("🎉 전체 추출 프로세스 완료")
            
        except KeyboardInterrupt:
            self.logger.info("⚠️ 사용자 중단 요청 감지")
            self._save_intermediate_results("사용자중단저장")
            raise
        except Exception as e:
            self.logger.error(f"❌ 추출 프로세스 실패: {e}")
            # 오류 발생 시에도 중간 결과 저장
            self._save_intermediate_results("오류발생저장")
            # 오류 발생 시에도 이메일 전송
            if self.send_email:
                self._send_error_email(str(e))
            raise
        finally:
            self._cleanup()
    
    def _search_with_multiple_engines(self, query: str, org_name: str, search_type: str = 'fax') -> Optional[str]:
        """다중 검색 엔진 사용 (구글만 사용)"""
        try:
            self.logger.info(f"🔍 구글 검색 시도: {query}")
            # 🐌 랜덤 지연 시간 추가
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # 구글 검색 페이지로 이동
            self.driver.get('https://www.google.com')
            
            # 🤖 사람처럼 행동하기 위한 추가 지연
            time.sleep(random.uniform(1, 3))
            
            # 페이지 스크롤 (사람처럼 행동)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색창 찾기
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )
            
            # 🎯 사람처럼 타이핑 (글자별 랜덤 지연)
            search_box.clear()
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            # 마우스 움직임 시뮬레이션
            ActionChains(self.driver).move_to_element(search_box).perform()
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색 실행
            search_box.send_keys(Keys.RETURN)
            
            # 결과 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search'))
            )
            
            # 🔍 페이지 소스에서 팩스번호 추출
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 검색 결과 텍스트에서 팩스번호 찾기
            for pattern in self.fax_patterns:
                matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                for match in matches:
                    fax_number = self._normalize_phone_number(match)
                    if self._is_valid_phone_format(fax_number):
                        return fax_number
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 팩스번호 검색 오류: {e}")
            return None
    
    def _search_for_homepage(self, query: str, org_name: str) -> Optional[str]:
        """구글 검색으로 홈페이지 찾기 (고급 봇 감지 우회)"""
        try:
            # 🐌 랜덤 지연 시간 추가
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # 구글 검색 페이지로 이동
            self.driver.get('https://www.google.com')
            
            # 🤖 사람처럼 행동하기 위한 추가 지연
            time.sleep(random.uniform(1, 3))
            
            # 페이지 스크롤 (사람처럼 행동)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색창 찾기
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )
            
            # �� 사람처럼 타이핑 (글자별 랜덤 지연)
            search_box.clear()
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            # 마우스 움직임 시뮬레이션
            ActionChains(self.driver).move_to_element(search_box).perform()
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색 실행
            search_box.send_keys(Keys.RETURN)
            
            # 결과 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search'))
            )
            
            # 🔍 검색 결과에서 URL 추출
            try:
                # 검색 결과 링크들 찾기
                links = self.driver.find_elements(By.CSS_SELECTOR, "h3 a, .yuRUbf a")
                
                for link in links[:5]:  # 상위 5개만 확인
                    href = link.get_attribute("href")
                    if href and self._is_valid_homepage_url(href, org_name):
                        return href
            except:
                # CSS 선택자가 안 되면 페이지 소스에서 직접 추출
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('/url?q='):
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                        if self._is_valid_homepage_url(actual_url, org_name):
                            return actual_url
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 홈페이지 검색 오류: {e}")
            return None
    
    def _extract_fax_by_search_parallel(self):
        """검색을 통한 팩스번호 추출 (병렬 처리)"""
        # 팩스번호가 없는 행들만 필터링
        missing_fax_rows = self.df[
            (self.df['fax'].isna() | (self.df['fax'] == ''))
        ].copy()
        
        if len(missing_fax_rows) == 0:
            self.logger.info("📞 팩스번호 추출할 데이터가 없습니다.")
            return
        
        # 데이터를 4개 청크로 분할
        chunks = self._split_dataframe(missing_fax_rows, self.max_workers)
        
        self.logger.info(f"📞 팩스번호 추출 시작: {len(missing_fax_rows)}개 데이터를 {len(chunks)}개 프로세스로 처리")
        
        # 멀티프로세싱으로 병렬 처리
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i, chunk in enumerate(chunks):
                future = executor.submit(
                    process_fax_extraction_chunk,
                    chunk,
                    i,
                    self.fax_patterns,
                    self.email_config
                )
                futures.append(future)
            
            # 결과 수집
            for future in as_completed(futures):
                try:
                    results = future.result()
                    self._merge_extraction_results(results, 'fax')
                except Exception as e:
                    self.logger.error(f"❌ 팩스번호 추출 프로세스 오류: {e}")
        
        # 중간 저장
        self._save_intermediate_results("팩스번호추출_완료")
        self.logger.info("📞 팩스번호 병렬 추출 완료")
    
    def _extract_homepage_by_search_parallel(self):
        """검색을 통한 홈페이지 추출 (병렬 처리)"""
        # 홈페이지가 없는 행들만 필터링
        missing_homepage_rows = self.df[
            (self.df['homepage'].isna() | (self.df['homepage'] == ''))
        ].copy()
        
        if len(missing_homepage_rows) == 0:
            self.logger.info("🌐 홈페이지 추출할 데이터가 없습니다.")
            return
        
        # 데이터를 4개 청크로 분할
        chunks = self._split_dataframe(missing_homepage_rows, self.max_workers)
        
        self.logger.info(f"🌐 홈페이지 추출 시작: {len(missing_homepage_rows)}개 데이터를 {len(chunks)}개 프로세스로 처리")
        
        # 멀티프로세싱으로 병렬 처리
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i, chunk in enumerate(chunks):
                future = executor.submit(
                    process_homepage_extraction_chunk,
                    chunk,
                    i,
                    self.url_patterns,
                    self.email_config
                )
                futures.append(future)
            
            # 결과 수집
            for future in as_completed(futures):
                try:
                    results = future.result()
                    self._merge_extraction_results(results, 'homepage')
                except Exception as e:
                    self.logger.error(f"❌ 홈페이지 추출 프로세스 오류: {e}")
        
        # 중간 저장
        self._save_intermediate_results("홈페이지추출_완료")
        self.logger.info("🌐 홈페이지 병렬 추출 완료")
    
    def _split_dataframe(self, df: pd.DataFrame, num_chunks: int) -> List[pd.DataFrame]:
        """데이터프레임을 균등하게 분할"""
        chunk_size = len(df) // num_chunks
        chunks = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            if i == num_chunks - 1:  # 마지막 청크는 남은 모든 데이터
                end_idx = len(df)
            else:
                end_idx = (i + 1) * chunk_size
            
            chunk = df.iloc[start_idx:end_idx].copy()
            chunks.append(chunk)
        
        return chunks
    
    def _merge_extraction_results(self, results: List[Dict], field_type: str):
        """추출 결과를 메인 데이터프레임에 병합"""
        try:
            for result in results:
                idx = result['index']
                value = result.get(field_type, '')
                
                if value and value.strip():
                    self.df.at[idx, field_type] = value
                    self.success_count += 1
                    self.logger.info(f"✅ {field_type} 발견: {result.get('name', 'Unknown')} -> {value}")
                
                self.processed_count += 1
                
        except Exception as e:
            self.logger.error(f"❌ 결과 병합 오류: {e}")
    
    def _extract_fax_by_search(self):
        """검색을 통한 팩스번호 추출 (기존 단일 처리 - 백업용)"""
        for idx, row in self.df.iterrows():
            if pd.notna(row['fax']) and row['fax'].strip():
                continue  # 이미 팩스번호가 있으면 스킵
            
            name = row['name']
            phone = row['phone']
            address = row.get('address', '')
            if not name or pd.isna(name):
                continue
            
            try:
                self.logger.info(f"📞 팩스번호 검색: {name}")
                
                # 🎯 지역 정보를 포함한 검색 쿼리 생성
                region_info = self._extract_region_from_address(address)
                if region_info:
                    search_query = f"{name} {region_info} 팩스번호"
                else:
                    search_query = f"{name} 팩스번호"
                
                fax_number = self._search_for_fax(search_query, name)
                
                if fax_number:
                    # 전화번호와 중복/유사성 체크
                    if self._is_valid_fax_number(fax_number, phone, name):
                        self.df.at[idx, 'fax'] = fax_number
                        self.success_count += 1
                        self.logger.info(f"✅ 팩스번호 발견: {name} -> {fax_number}")
                    else:
                        self.duplicate_count += 1
                        self.logger.info(f"🚫 팩스번호 중복/유사: {name} -> {fax_number} (전화번호: {phone})")
                else:
                    self.logger.info(f"❌ 팩스번호 없음: {name}")
                
                self.processed_count += 1
                time.sleep(2)  # 요청 간격 조절
                
            except Exception as e:
                self.logger.error(f"❌ 팩스번호 검색 오류: {name} - {e}")
                continue
    
    def _extract_region_from_address(self, address: str) -> str:
        """주소에서 지역 정보 추출 (메인 클래스용)"""
        if not address:
            return ""
        
        # 지역 패턴 추출 (시/도 + 시/군/구)
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
                if len(match.groups()) >= 2:
                    return f"{match.group(1)} {match.group(2)}"
                else:
                    return match.group(1)
        
        return ""
    
    def _extract_homepage_by_search(self):
        """검색을 통한 홈페이지 추출 (중간 저장 기능 추가)"""
        processed_in_this_step = 0
        
        for idx, row in self.df.iterrows():
            if pd.notna(row['homepage']) and row['homepage'].strip():
                continue  # 이미 홈페이지가 있으면 스킵
            
            name = row['name']
            if not name or pd.isna(name):
                continue
            
            try:
                self.logger.info(f"🌐 홈페이지 검색: {name}")
                
                # 검색어: 기관명 + 홈페이지
                search_query = f"{name} 홈페이지"
                homepage_url = self._search_for_homepage(search_query, name)
                
                if homepage_url:
                    self.df.at[idx, 'homepage'] = homepage_url
                    self.logger.info(f"✅ 홈페이지 발견: {name} -> {homepage_url}")
                else:
                    self.logger.info(f"❌ 홈페이지 없음: {name}")
                
                processed_in_this_step += 1
                
                # 🔥 중간 저장 (10개마다)
                if processed_in_this_step % 10 == 0:
                    self._save_intermediate_results(f"홈페이지추출_중간저장_{processed_in_this_step}")
                    self._log_system_stats(f"홈페이지 {processed_in_this_step}개 처리")
                
                time.sleep(2)  # 요청 간격 조절
                
            except KeyboardInterrupt:
                self.logger.info("⚠️ 사용자 중단 요청 감지 (홈페이지 추출)")
                self._save_intermediate_results(f"홈페이지추출_중단저장_{processed_in_this_step}")
                raise
            except Exception as e:
                self.logger.error(f"❌ 홈페이지 검색 오류: {name} - {e}")
                continue
    
    def _extract_fax_from_homepage(self):
        """홈페이지 직접 접속으로 팩스번호 추출 (중간 저장 기능 추가)"""
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
            
            try:
                self.logger.info(f"🔍 홈페이지 직접 접속: {name} -> {homepage}")
                
                # 홈페이지 크롤링
                page_data = self._crawl_homepage(homepage)
                
                if page_data:
                    # 1. HTML에서 직접 팩스번호 추출 시도
                    fax_numbers = self._extract_fax_from_html(page_data.get('html', ''))
                    
                    # 유효한 팩스번호 찾기
                    valid_fax = None
                    for fax_num in fax_numbers:
                        if self._is_valid_fax_number(fax_num, phone, name):
                            valid_fax = fax_num
                            break
                    
                    if not valid_fax and self.use_ai and self.ai_model_manager:
                        # 2. AI를 통한 팩스번호 추출
                        ai_fax = self._extract_fax_with_ai(name, page_data)
                        if ai_fax and self._is_valid_fax_number(ai_fax, phone, name):
                            valid_fax = ai_fax
                    
                    if valid_fax:
                        self.df.at[idx, 'fax'] = valid_fax
                        self.success_count += 1
                        self.logger.info(f"✅ 홈페이지에서 팩스번호 추출: {name} -> {valid_fax}")
                    else:
                        self.logger.info(f"❌ 홈페이지에서 유효한 팩스번호 없음: {name}")
                
                processed_in_this_step += 1
                
                # 🔥 중간 저장 (5개마다 - 홈페이지 크롤링은 더 무거워서)
                if processed_in_this_step % 5 == 0:
                    self._save_intermediate_results(f"홈페이지크롤링_중간저장_{processed_in_this_step}")
                    self._log_system_stats(f"홈페이지 크롤링 {processed_in_this_step}개 처리")
                
                time.sleep(3)  # 요청 간격 조절
                
            except KeyboardInterrupt:
                self.logger.info("⚠️ 사용자 중단 요청 감지 (홈페이지 크롤링)")
                self._save_intermediate_results(f"홈페이지크롤링_중단저장_{processed_in_this_step}")
                raise
            except Exception as e:
                self.logger.error(f"❌ 홈페이지 크롤링 오류: {name} - {e}")
                continue
    
    def _is_valid_fax_number(self, fax_number: str, phone_number: str, org_name: str) -> bool:
        """
        팩스번호 유효성 검증 (지역 일치성 검사 포함)
        
        Args:
            fax_number: 추출된 팩스번호
            phone_number: 기존 전화번호
            org_name: 기관명
            
        Returns:
            bool: 유효한 팩스번호인지 여부
        """
        try:
            if not fax_number or pd.isna(fax_number):
                return False
            
            # 팩스번호 정규화
            normalized_fax = self._normalize_phone_number(fax_number)
            
            # 1. 팩스번호 형식 검증
            if not self._is_valid_phone_format(normalized_fax):
                self.logger.info(f"🚫 잘못된 팩스번호 형식: {org_name} - {normalized_fax}")
                return False
            
            # 2. 전화번호가 있는 경우 비교
            if phone_number and not pd.isna(phone_number):
                normalized_phone = self._normalize_phone_number(str(phone_number))
                
                # 2-1. 완전히 동일한 경우 제외
                if normalized_fax == normalized_phone:
                    self.logger.info(f"🚫 팩스번호와 전화번호 동일: {org_name} - {normalized_fax}")
                    return False
                
                # 2-2. 지역번호 일치성 검사 (NEW!)
                if not self._is_same_area_code(normalized_fax, normalized_phone):
                    self.logger.info(f"🚫 팩스번호와 전화번호 지역번호 불일치: {org_name} - FAX:{normalized_fax} vs TEL:{normalized_phone}")
                    return False
                
                # 2-3. 유사성 검사 (더 엄격하게)
                if self._are_numbers_too_similar(normalized_fax, normalized_phone):
                    self.logger.info(f"🚫 팩스번호와 전화번호 유사: {org_name} - FAX:{normalized_fax} vs TEL:{normalized_phone}")
                    return False
            
            # 3. 기관 주소와 팩스번호 지역 일치성 검사 (NEW!)
            if hasattr(self, 'df') and org_name:
                org_row = self.df[self.df['name'] == org_name]
                if not org_row.empty:
                    org_address = org_row.iloc[0].get('address', '')
                    if not self._is_fax_area_match_address(normalized_fax, org_address, org_name):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 팩스번호 유효성 검증 오류: {org_name} - {e}")
            return False
    
    def _is_same_area_code(self, fax: str, phone: str) -> bool:
        """
        팩스번호와 전화번호의 지역번호가 같은지 확인
        
        Args:
            fax: 팩스번호
            phone: 전화번호
            
        Returns:
            bool: 같은 지역번호인지 여부
        """
        try:
            fax_digits = re.sub(r'[^\d]', '', fax)
            phone_digits = re.sub(r'[^\d]', '', phone)
            
            # 지역번호 추출
            fax_area = self._extract_area_code(fax_digits)
            phone_area = self._extract_area_code(phone_digits)
            
            return fax_area == phone_area
            
        except Exception as e:
            self.logger.error(f"❌ 지역번호 비교 오류: {e}")
            return False
    
    def _extract_area_code(self, phone_digits: str) -> str:
        """
        전화번호에서 지역번호 추출
        
        Args:
            phone_digits: 숫자만 있는 전화번호
            
        Returns:
            str: 지역번호
        """
        if len(phone_digits) >= 10:
            # 10자리 이상인 경우 (02-XXXX-XXXX, 031-XXX-XXXX 등)
            if phone_digits.startswith('02'):
                return '02'
            else:
                return phone_digits[:3]
        elif len(phone_digits) >= 9:
            # 9자리인 경우
            if phone_digits.startswith('02'):
                return '02'
            else:
                return phone_digits[:3]
        else:
            # 8자리인 경우
            return phone_digits[:2]
    
    def _is_fax_area_match_address(self, fax_number: str, address: str, org_name: str) -> bool:
        """
        팩스번호 지역번호와 기관 주소가 일치하는지 확인
        
        Args:
            fax_number: 팩스번호
            address: 기관 주소
            org_name: 기관명
            
        Returns:
            bool: 지역이 일치하는지 여부
        """
        try:
            if not address or pd.isna(address):
                return True  # 주소가 없으면 검증 스킵
            
            fax_digits = re.sub(r'[^\d]', '', fax_number)
            area_code = self._extract_area_code(fax_digits)
            
            # 지역번호별 지역 매핑
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
                '070': ['인터넷전화'],  # 인터넷전화는 지역 제한 없음
            }
            
            # 인터넷전화(070)는 지역 제한 없음
            if area_code == '070':
                return True
            
            expected_regions = area_mapping.get(area_code, [])
            if not expected_regions:
                self.logger.warning(f"⚠️ 알 수 없는 지역번호: {area_code} - {org_name}")
                return True  # 알 수 없는 지역번호는 통과
            
            # 주소에서 지역명 확인
            for region in expected_regions:
                if region in address:
                    return True
            
            self.logger.info(f"🚫 지역 불일치: {org_name} - 팩스:{area_code}({expected_regions}) vs 주소:{address}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 지역 일치성 검사 오류: {org_name} - {e}")
            return True  # 오류 시 통과
    
    def _are_numbers_too_similar(self, fax: str, phone: str) -> bool:
        """
        두 번호가 너무 유사한지 검사 (더 엄격하게)
        
        Args:
            fax: 팩스번호
            phone: 전화번호
            
        Returns:
            bool: 유사한 경우 True
        """
        try:
            # 숫자만 추출
            fax_digits = re.sub(r'[^\d]', '', fax)
            phone_digits = re.sub(r'[^\d]', '', phone)
            
            # 길이가 다르면 비교하지 않음
            if len(fax_digits) != len(phone_digits):
                return False
            
            # 같은 자리수끼리 비교
            if len(fax_digits) < 8:  # 너무 짧으면 비교하지 않음
                return False
            
            # 지역번호 추출
            fax_area = self._extract_area_code(fax_digits)
            phone_area = self._extract_area_code(phone_digits)
            
            # 지역번호가 다르면 유사하지 않음
            if fax_area != phone_area:
                return False
            
            # 지역번호가 같은 경우 뒷자리 비교
            fax_suffix = fax_digits[len(fax_area):]
            phone_suffix = phone_digits[len(phone_area):]
            
            # 뒷자리 차이 계산
            diff_count = sum(1 for i, (f, p) in enumerate(zip(fax_suffix, phone_suffix)) if f != p)
            
            # 1자리 이하 차이면 유사한 것으로 판단 (더 엄격하게)
            if diff_count <= 1:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 번호 유사성 검사 오류: {e}")
            return False
    
    def _is_valid_phone_format(self, phone: str) -> bool:
        """
        전화번호 형식 유효성 검사
        
        Args:
            phone: 전화번호
            
        Returns:
            bool: 유효한 형식인지 여부
        """
        try:
            # 숫자만 추출
            digits = re.sub(r'[^\d]', '', phone)
            
            # 길이 검사 (8자리 이상 11자리 이하)
            if len(digits) < 8 or len(digits) > 11:
                return False
            
            # 한국 전화번호 패턴 검사
            valid_patterns = [
                r'^02\d{7,8}$',      # 서울 (02-XXXX-XXXX)
                r'^0[3-6]\d{7,8}$',  # 지역번호 (031-XXX-XXXX)
                r'^070\d{7,8}$',     # 인터넷전화
                r'^1[5-9]\d{6,7}$',  # 특수번호
                r'^080\d{7,8}$',     # 무료전화
            ]
            
            for pattern in valid_patterns:
                if re.match(pattern, digits):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 전화번호 형식 검사 오류: {e}")
            return False
    
    def _search_for_fax(self, query: str, org_name: str) -> Optional[str]:
        """팩스번호 검색 (다중 검색 엔진 사용)"""
        return self._search_with_multiple_engines(query, org_name, 'fax')
    
    def _search_for_homepage(self, query: str, org_name: str) -> Optional[str]:
        """홈페이지 검색 (다중 검색 엔진 사용)"""
        return self._search_with_multiple_engines(query, org_name, 'homepage')
    
    def _search_with_multiple_engines(self, query: str, org_name: str, search_type: str = 'fax') -> Optional[str]:
        """구글 검색 사용"""
        try:
            self.logger.info(f"🔍 구글 검색 시도: {query}")
            
            # 🐌 랜덤 지연 시간 추가
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # 구글 검색 페이지로 이동
            self.driver.get('https://www.google.com')
            
            # 🤖 사람처럼 행동하기 위한 추가 지연
            time.sleep(random.uniform(1, 3))
            
            # 페이지 스크롤 (사람처럼 행동)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색창 찾기
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )
            
            # 🎯 사람처럼 타이핑 (글자별 랜덤 지연)
            search_box.clear()
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            # 마우스 움직임 시뮬레이션
            ActionChains(self.driver).move_to_element(search_box).perform()
            time.sleep(random.uniform(0.5, 1.5))
            
            # 검색 실행
            search_box.send_keys(Keys.RETURN)
            
            # 결과 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search'))
            )
            
            # 결과 처리
            if search_type == 'fax':
                result = self._extract_fax_from_search_results()
            else:
                result = self._extract_homepage_from_search_results(org_name)
            
            if result:
                self.logger.info(f"✅ 구글에서 결과 발견: {result}")
                return result
            else:
                self.logger.info(f"❌ 구글에서 결과 없음: {query}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 구글 검색 오류: {e}")
            return None
    
    def _extract_fax_from_search_results(self) -> Optional[str]:
        """검색 결과에서 팩스번호 추출"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 검색 결과 텍스트에서 팩스번호 찾기
            for pattern in self.fax_patterns:
                matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                for match in matches:
                    fax_number = self._normalize_phone_number(match)
                    if self._is_valid_phone_format(fax_number):
                        return fax_number
            
            return None
        except Exception as e:
            self.logger.error(f"❌ 검색 결과 팩스번호 추출 오류: {e}")
            return None
    
    def _extract_homepage_from_search_results(self, org_name: str) -> Optional[str]:
        """검색 결과에서 홈페이지 URL 추출"""
        try:
            # 검색 결과 링크들 찾기
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, "h3 a, .yuRUbf a")
                
                for link in links[:5]:  # 상위 5개만 확인
                    href = link.get_attribute("href")
                    if href and self._is_valid_homepage_url(href, org_name):
                        return href
            except:
                # CSS 선택자가 안 되면 페이지 소스에서 직접 추출
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('/url?q='):
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                        if self._is_valid_homepage_url(actual_url, org_name):
                            return actual_url
            
            return None
        except Exception as e:
            self.logger.error(f"❌ 검색 결과 홈페이지 추출 오류: {e}")
            return None
    
    def _crawl_homepage(self, url: str) -> Optional[Dict[str, Any]]:
        """홈페이지 크롤링"""
        try:
            # URL 정규화
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # 페이지 소스 가져오기
            page_source = self.driver.page_source
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 텍스트 추출
            text_content = soup.get_text(separator=' ', strip=True)
            
            # 메타 정보 추출
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_text = meta_desc.get('content', '') if meta_desc else ''
            
            return {
                'url': url,
                'html': page_source,
                'text_content': text_content,
                'title': title_text,
                'meta_description': meta_desc_text
            }
            
        except Exception as e:
            self.logger.error(f"❌ 홈페이지 크롤링 오류: {url} - {e}")
            return None
    
    def _extract_fax_from_html(self, html_content: str) -> List[str]:
        """HTML에서 팩스번호 추출 (여러 개 반환)"""
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
        """AI를 통한 팩스번호 추출"""
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

팩스번호는 다음과 같은 형태입니다:
- 팩스: 02-1234-5678
- FAX: 031-123-4567  
- F: 032-987-6543
- 전송: 042-555-1234

주의: 전화번호와 팩스번호가 다른 번호인지 확인해주세요.
""".format(
                org_name=org_name,
                title=page_data.get('title', ''),
                url=page_data.get('url', ''),
                text_content=page_data.get('text_content', '')[:3000]
            )
            
            # AI 모델 호출
            response_text = self.ai_model_manager.extract_with_gemini(
                page_data.get('text_content', ''),
                prompt_template
            )
            
            # AI 응답에서 팩스번호 추출
            if response_text and response_text != "없음" and "오류:" not in response_text:
                # 숫자와 하이픈만 추출
                fax_match = re.search(r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})', response_text)
                if fax_match:
                    return self._normalize_phone_number(fax_match.group(1))
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ AI 팩스번호 추출 오류: {org_name} - {e}")
            return None
    
    def _normalize_phone_number(self, phone: str) -> str:
        """전화번호 정규화"""
        # 숫자만 추출
        numbers = re.findall(r'\d+', phone)
        if not numbers:
            return phone
        
        # 하이픈으로 연결
        if len(numbers) >= 3:
            return f"{numbers[0]}-{numbers[1]}-{numbers[2]}"
        elif len(numbers) == 2:
            return f"{numbers[0]}-{numbers[1]}"
        else:
            return numbers[0]
    
    def _is_valid_homepage_url(self, url: str, org_name: str) -> bool:
        """유효한 홈페이지 URL인지 확인"""
        try:
            from urllib.parse import urlparse
            
            excluded_domains = [
                'google.com', 'naver.com', 'daum.net', 'youtube.com',
                'facebook.com', 'instagram.com', 'blog.naver.com'
            ]
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            for excluded in excluded_domains:
                if excluded in domain:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _save_results(self) -> str:
        """결과 저장"""
        try:
            # 타임스탬프 추가
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 결과 파일명
            base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
            result_filename = f"{base_name}_팩스추출결과_{timestamp}.xlsx"
            result_path = os.path.join(os.path.dirname(self.excel_path), result_filename)
            
            # 엑셀 저장
            self.df.to_excel(result_path, index=False)
            
            # 통계 정보
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            homepage_count = len(self.df[self.df['homepage'].notna() & (self.df['homepage'] != '')])
            
            self.logger.info(f"💾 결과 저장 완료: {result_path}")
            self.logger.info(f"📊 통계:")
            self.logger.info(f"  - 전체 기관 수: {total_count}")
            self.logger.info(f"  - 팩스번호 보유: {fax_count} ({fax_count/total_count*100:.1f}%)")
            self.logger.info(f"  - 홈페이지 보유: {homepage_count} ({homepage_count/total_count*100:.1f}%)")
            self.logger.info(f"  - 처리된 기관 수: {self.processed_count}")
            self.logger.info(f"  - 성공 추출 수: {self.success_count}")
            self.logger.info(f"  - 중복 제거 수: {self.duplicate_count}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"❌ 결과 저장 오류: {e}")
            raise
    
    def _send_completion_email(self, result_path: str):
        """완료 이메일 전송"""
        try:
            # 실행 시간 계산
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            # 통계 정보
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            homepage_count = len(self.df[self.df['homepage'].notna() & (self.df['homepage'] != '')])
            
            # 이메일 내용 구성
            subject = "🎉 아동센터 팩스번호 추출 완료"
            
            body = f"""
안녕하세요! 대표님! 신명호입니다. 

아동센터 팩스번호 추출 작업이 성공적으로 완료되었습니다.

📊 **작업 결과 요약:**
- 전체 기관 수: {total_count:,}개
- 팩스번호 보유: {fax_count:,}개 ({fax_count/total_count*100:.1f}%)
- 홈페이지 보유: {homepage_count:,}개 ({homepage_count/total_count*100:.1f}%)
- 처리된 기관 수: {self.processed_count:,}개
- 성공 추출 수: {self.success_count:,}개
- 중복 제거 수: {self.duplicate_count:,}개

⏱️ **실행 시간:** {duration}

📁 **결과 파일:** {os.path.basename(result_path)}

🤖 **사용된 기능:**
- Selenium WebDriver 검색 (브라우저 표시 모드)
- BeautifulSoup HTML 파싱
{"- Gemini AI 정보 추출" if self.use_ai else ""}
- 전화번호 중복/유사성 검증

작업이 완료되었습니다. 결과 파일을 확인해주세요.

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
            subject = "❌ 아동센터 팩스번호 추출 오류 발생"
            
            body = f"""
안녕하세요!

아동센터 팩스번호 추출 작업 중 오류가 발생했습니다.

❌ **오류 내용:**
{error_message}

📊 **진행 상황:**
- 처리된 기관 수: {self.processed_count:,}개
- 성공 추출 수: {self.success_count:,}개
- 중복 제거 수: {self.duplicate_count:,}개

⏱️ **실행 시간:** {datetime.now() - self.start_time}

로그 파일을 확인하여 자세한 오류 내용을 파악해주세요.

CenterCrawlingBot 🤖
"""
            
            self._send_email(subject, body)
            self.logger.info("📧 오류 이메일 전송 성공")
            
        except Exception as e:
            self.logger.error(f"❌ 오류 이메일 전송 실패: {e}")
    
    def _send_email(self, subject: str, body: str, attachment_path: str = None):
        """이메일 전송"""
        try:
            # 이메일 설정 확인
            if not self.email_config['sender_email'] or not self.email_config['sender_password']:
                self.logger.warning("⚠️ 이메일 설정이 완료되지 않았습니다. 이메일을 전송하지 않습니다.")
                return
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            # 본문 추가
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 첨부파일 추가
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
            
            # SMTP 서버 연결 및 전송
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
        """시스템 리소스 모니터링 (백그라운드 스레드)"""
        while self.monitoring_active:
            try:
                # CPU 사용률
                cpu_percent = self.process.cpu_percent()
                
                # 메모리 사용량
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # MB 단위
                
                # 시스템 메모리 대비 퍼센트
                system_memory = psutil.virtual_memory()
                memory_percent = (memory_info.rss / system_memory.total) * 100
                
                # 통계 업데이트
                self.system_stats.update({
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_percent': memory_percent
                })
                
                # 30초마다 모니터링
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ 시스템 모니터링 오류: {e}")
                break
    
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
            
            # 통계 정보
            total_count = len(self.df)
            fax_count = len(self.df[self.df['fax'].notna() & (self.df['fax'] != '')])
            homepage_count = len(self.df[self.df['homepage'].notna() & (self.df['homepage'] != '')])
            
            self.logger.info(f"💾 중간 저장 완료: {result_path}")
            self.logger.info(f"📊 현재 통계 - 전체: {total_count}, 팩스: {fax_count}, 홈페이지: {homepage_count}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"❌ 중간 저장 오류: {e}")
            return None
    
    def _cleanup(self):
        """정리 작업"""
        try:
            # 시스템 모니터링 중지
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=1)
            
            if self.driver:
                self.driver.quit()
                self.logger.info("🧹 WebDriver 정리 완료")
                
            self.logger.info("🧹 시스템 모니터링 정리 완료")
        except Exception as e:
            self.logger.error(f"❌ 정리 작업 오류: {e}")


# ===== 병렬 처리 워커 함수들 =====

def create_worker_driver(worker_id: int):
    """워커용 WebDriver 생성"""
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        import random
        import time
        
        # undetected-chromedriver 설정
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        
        # 각 워커마다 다른 포트 사용
        chrome_options.add_argument(f'--remote-debugging-port={9222 + worker_id}')
        
        driver = uc.Chrome(options=chrome_options, version_main=None)
        driver.implicitly_wait(10)
        
        # 봇 감지 우회 스크립트
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")
        
        return driver
        
    except Exception as e:
        print(f"❌ 워커 {worker_id} WebDriver 생성 오류: {e}")
        return None

def process_fax_extraction_chunk(chunk_df: pd.DataFrame, worker_id: int, fax_patterns: List[str], email_config: Dict) -> List[Dict]:
    """팩스번호 추출 청크 처리"""
    import pandas as pd
    import re
    results = []
    driver = None
    
    try:
        # 워커용 드라이버 생성
        driver = create_worker_driver(worker_id)
        if not driver:
            return results
        
        print(f"🔧 워커 {worker_id}: 팩스번호 추출 시작 ({len(chunk_df)}개)")
        
        for idx, row in chunk_df.iterrows():
            name = row['name']
            phone = row['phone']
            address = row.get('address', '')  # 주소 정보 추가
            
            if not name or pd.isna(name):
                continue
            
            try:
                print(f"📞 워커 {worker_id}: 팩스번호 검색 - {name}")
                
                # 🎯 지역 정보를 포함한 검색 쿼리 생성
                region_info = extract_region_from_address(address)
                if region_info:
                    search_query = f"{name} {region_info} 팩스번호"
                else:
                    search_query = f"{name} 팩스번호"
                
                fax_number = search_google_for_info(driver, search_query, fax_patterns, 'fax')
                
                # 유효성 검사 (주소 정보 포함)
                if fax_number and is_valid_fax_number_simple(fax_number, phone, address, name):
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
                
                # 랜덤 지연 (1-3초)
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"❌ 워커 {worker_id}: 팩스번호 검색 오류 - {name}: {e}")
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

def process_homepage_extraction_chunk(chunk_df: pd.DataFrame, worker_id: int, url_patterns: List[str], email_config: Dict) -> List[Dict]:
    """홈페이지 추출 청크 처리"""
    import pandas as pd
    import re
    results = []
    driver = None
    
    try:
        # 워커용 드라이버 생성
        driver = create_worker_driver(worker_id)
        if not driver:
            return results
        
        print(f"🔧 워커 {worker_id}: 홈페이지 추출 시작 ({len(chunk_df)}개)")
        
        for idx, row in chunk_df.iterrows():
            name = row['name']
            
            if not name or pd.isna(name):
                continue
            
            try:
                print(f"🌐 워커 {worker_id}: 홈페이지 검색 - {name}")
                
                # 구글 검색
                search_query = f"{name} 홈페이지"
                homepage_url = search_google_for_info(driver, search_query, url_patterns, 'homepage', name)
                
                if homepage_url:
                    results.append({
                        'index': idx,
                        'name': name,
                        'homepage': homepage_url
                    })
                    print(f"✅ 워커 {worker_id}: 홈페이지 발견 - {name} -> {homepage_url}")
                else:
                    results.append({
                        'index': idx,
                        'name': name,
                        'homepage': ''
                    })
                    print(f"❌ 워커 {worker_id}: 홈페이지 없음 - {name}")
                
                # 랜덤 지연 (1-3초)
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"❌ 워커 {worker_id}: 홈페이지 검색 오류 - {name}: {e}")
                results.append({
                    'index': idx,
                    'name': name,
                    'homepage': ''
                })
                continue
        
        print(f"🎉 워커 {worker_id}: 홈페이지 추출 완료 ({len(results)}개)")
        
    except Exception as e:
        print(f"❌ 워커 {worker_id}: 홈페이지 추출 프로세스 오류: {e}")
    finally:
        if driver:
            driver.quit()
    
    return results

def search_google_for_info(driver, query: str, patterns: List[str], search_type: str, org_name: str = None):
    """구글 검색으로 정보 추출"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse
        import random
        import time
        import re
        
        # 랜덤 지연
        time.sleep(random.uniform(1, 3))
        
        # 구글 검색 페이지로 이동
        driver.get('https://www.google.com')
        time.sleep(random.uniform(1, 2))
        
        # 검색창 찾기
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'q'))
        )
        
        # 검색어 입력
        search_box.clear()
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.02, 0.1))
        
        # 검색 실행
        search_box.send_keys(Keys.RETURN)
        
        # 결과 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search'))
        )
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        if search_type == 'fax':
            # 팩스번호 추출
            for pattern in patterns:
                matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                for match in matches:
                    normalized = normalize_phone_number(match)
                    if is_valid_phone_format(normalized):
                        return normalized
        
        elif search_type == 'homepage':
            # 홈페이지 URL 추출
            try:
                links = driver.find_elements(By.CSS_SELECTOR, "h3 a, .yuRUbf a")
                for link in links[:3]:  # 상위 3개만 확인
                    href = link.get_attribute("href")
                    if href and is_valid_homepage_url(href, org_name):
                        return href
            except:
                # 페이지 소스에서 직접 추출
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('/url?q='):
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                        if is_valid_homepage_url(actual_url, org_name):
                            return actual_url
        
        return None
        
    except Exception as e:
        print(f"❌ 구글 검색 오류: {e}")
        return None

def normalize_phone_number(phone: str) -> str:
    """전화번호 정규화"""
    import re
    numbers = re.findall(r'\d+', phone)
    if not numbers:
        return phone
    
    if len(numbers) >= 3:
        return f"{numbers[0]}-{numbers[1]}-{numbers[2]}"
    elif len(numbers) == 2:
        return f"{numbers[0]}-{numbers[1]}"
    else:
        return numbers[0]

def is_valid_phone_format(phone: str) -> bool:
    """전화번호 형식 유효성 검사"""
    import re
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

def is_valid_fax_number_simple(fax_number: str, phone_number: str, org_address: str = None, org_name: str = None) -> bool:
    """간단한 팩스번호 유효성 검사 (지역 일치성 포함)"""
    import pandas as pd
    import re
    
    if not fax_number or pd.isna(fax_number):
        return False
    
    normalized_fax = normalize_phone_number(fax_number)
    
    # 1. 형식 검증
    if not is_valid_phone_format(normalized_fax):
        return False
    
    # 2. 전화번호와 비교
    if phone_number and not pd.isna(phone_number):
        normalized_phone = normalize_phone_number(str(phone_number))
        
        # 2-1. 완전히 동일한 경우 제외
        if normalized_fax == normalized_phone:
            return False
        
        # 2-2. 지역번호 일치성 검사
        if not is_same_area_code_simple(normalized_fax, normalized_phone):
            return False
        
        # 2-3. 유사성 검사 (엄격하게)
        if are_numbers_too_similar_simple(normalized_fax, normalized_phone):
            return False
    
    # 3. 주소와 지역 일치성 검사
    if org_address and not is_fax_area_match_address_simple(normalized_fax, org_address, org_name):
        return False
    
    return True

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
        
        return diff_count <= 1  # 1자리 이하 차이면 유사
    except:
        return False

def is_fax_area_match_address_simple(fax_number: str, address: str, org_name: str = None) -> bool:
    """간단한 지역 일치성 검사"""
    try:
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
        
        if area_code == '070':  # 인터넷전화는 지역 제한 없음
            return True
        
        expected_regions = area_mapping.get(area_code, [])
        if not expected_regions:
            return True  # 알 수 없는 지역번호는 통과
        
        for region in expected_regions:
            if region in address:
                return True
        
        print(f"🚫 지역 불일치: {org_name} - 팩스:{area_code}({expected_regions}) vs 주소:{address}")
        return False
        
    except:
        return True  # 오류 시 통과

def extract_region_from_address(address: str) -> str:
    """주소에서 지역 정보 추출"""
    if not address:
        return ""
    
    # 지역 패턴 추출 (시/도 + 시/군/구)
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
            if len(match.groups()) >= 2:
                return f"{match.group(1)} {match.group(2)}"
            else:
                return match.group(1)
    
    return ""

def main():
    """메인 함수"""
    try:
        # 멀티프로세싱 시작 방법 설정 (Windows 호환)
        if __name__ == "__main__":
            multiprocessing.set_start_method('spawn', force=True)
        
        # 엑셀 파일 경로
        excel_path = r"C:\Users\MyoengHo Shin\pjt\advanced_crawling\childcenter.xlsx"
        
        # 파일 존재 확인
        if not os.path.exists(excel_path):
            print(f"❌ 파일을 찾을 수 없습니다: {excel_path}")
            return
        
        # 크롤링 봇 실행
        bot = CenterCrawlingBot(excel_path, use_ai=True, send_email=True)
        bot.run_extraction()
        
        print("🎉 팩스번호 추출 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

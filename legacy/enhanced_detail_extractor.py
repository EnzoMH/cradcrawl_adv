#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Detail Extractor Library
JSON 파일의 기존 정보를 최대한 활용하고, 필요시에만 홈페이지 크롤링을 수행하는 라이브러리
TPM 관리, 마크다운 파싱, 데이터 병합, 종합 리포트 기능 포함
"""

import json
import re
import time
import asyncio
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from urllib.parse import urljoin, urlparse
import warnings
warnings.filterwarnings('ignore')

import logging
import random

import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Selenium imports 추가
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# enhanced_detail_extractor.py에서 사용
from utils.phone_utils import PhoneUtils
from utils.file_utils import FileUtils
from utils.crawler_utils import CrawlerUtils
from utils.logger_utils import LoggerUtils

# constants.py에서 임포트
from constants import (
    PHONE_EXTRACTION_PATTERNS,
    FAX_EXTRACTION_PATTERNS,
    EMAIL_EXTRACTION_PATTERNS,
    ADDRESS_EXTRACTION_PATTERNS,
    LOGGER_NAMES,
    LOG_FORMAT,
    AI_MODEL_CONFIG,
    TPM_LIMITS,
    EXCLUDE_DOMAINS
)

from ai_helpers import AIModelManager, extract_with_gemini_text

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# validator.py의 ContactValidator 임포트
from validator import ContactValidator

# Gemini API 설정
import google.generativeai as genai

class TPMManager:
    """TPM(Tokens Per Minute) 관리 클래스"""
    
    def __init__(self, requests_per_minute=TPM_LIMITS["requests_per_minute"]):
        """TPM 관리자 초기화"""
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.max_wait_time = TPM_LIMITS["max_wait_time"]
    
    async def wait_if_needed(self):
        """개선된 TPM 제한 대기 (최대 대기시간 제한)"""
        now = datetime.now()
        
        # 1분 이내의 요청만 유지
        self.request_times = [t for t in self.request_times if now - t < timedelta(minutes=1)]
        
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]).total_seconds()
            # 최대 대기 시간 제한
            wait_time = min(wait_time, self.max_wait_time)
            
            if wait_time > 0:
                print(f"⏳ TPM 제한으로 {wait_time:.1f}초 대기 중...")
                await asyncio.sleep(wait_time)
        
        self.request_times.append(now)
        
        # 기본 대기 시간을 5초로 단축
        print(f"⏱️ API 호출 안전 대기: 5초")
        await asyncio.sleep(5)

    

class EnhancedDetailExtractor:
    """Gemini 1.5-flash 제약사항을 고려한 지능형 웹 분석 추출기"""
    
    def __init__(self, api_key=None, use_selenium=True, headless=False, progress_callback=None):
        """초기화 (AI 제약사항 고려)"""
        # 기존 초기화 코드...
        self.session = CrawlerUtils.setup_requests_session()
        self.validator = ContactValidator()
        
        # url_extractor.py의 설정 추가
        self.max_search_results = 5
        self.max_retries = 3
        self.delay_range = (3, 6)
        
        # 🔧 개선: constants.py의 TPM 설정 사용
        self.tpm_manager = TPMManager(requests_per_minute=TPM_LIMITS["requests_per_minute"])
        
        # 🔧 개선: ai_helpers.py의 AIModelManager 활용
        self.ai_model_manager = None
        if api_key or os.getenv('GEMINI_API_KEY'):
            try:
                self.ai_model_manager = AIModelManager()
                self.use_ai = True
                self.use_ai_web_analysis = True
                print("🤖 AI 모델 관리자 초기화 성공 (ai_helpers.py 기반)")
            except Exception as e:
                print(f"❌ AI 모델 관리자 초기화 실패: {e}")
                self.ai_model_manager = None
                self.use_ai = False
                self.use_ai_web_analysis = False
        else:
            self.use_ai = False
            self.use_ai_web_analysis = False
            print("🔧 정규식 전용 모드 (API 키 없음)")
        
        # 🆕 Gemini 1.5-flash 제약사항 고려한 설정
        self.max_input_tokens = 30000  # 32K 토큰 제한의 안전 마진
        self.max_html_chars = 60000    # 대략 30K 토큰에 해당 (한글 기준)
        self.max_text_chars = 15000    # 연락처 추출용 텍스트 제한
        
        # Selenium 관련 설정
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.exclude_domains = EXCLUDE_DOMAINS
        
        # 기존 통계 정보에 AI 관련 추가
        self.stats = {
            'total_processed': 0,
            'json_info_used': 0,
            'crawling_performed': 0,
            'url_search_performed': 0,
            'url_found': 0,
            'phone_found': 0,
            'fax_found': 0,
            'email_found': 0,
            'address_found': 0,
            'postal_code_found': 0,
            'ai_enhanced': 0,
            'duplicates_removed': 0,
            'api_calls_made': 0,
            'token_limit_exceeded': 0,  # 🆕 토큰 제한 초과 횟수
            'tpm_wait_count': 0,        # 🆕 TPM 대기 횟수
        }
        
        self.ai_logger = LoggerUtils.setup_ai_logger()
        self.patterns = {
            'phone': PHONE_EXTRACTION_PATTERNS,
            'fax': FAX_EXTRACTION_PATTERNS,
            'email': EMAIL_EXTRACTION_PATTERNS,
            'address': ADDRESS_EXTRACTION_PATTERNS
        }
        
        self.progress_callback = progress_callback
        
        self.merged_results = []

    # 🔧 개선: 토큰 수 계산 및 제한 함수
    def estimate_token_count(self, text: str) -> int:
        """🔧 개선된 토큰 수 추정 (보수적 계산)"""
        if not text:
            return 0
        
        try:
            # 더 보수적이고 정확한 토큰 계산
            korean_chars = len(re.findall(r'[가-힣]', text))
            chinese_chars = len(re.findall(r'[一-龯]', text))
            english_words = len(re.findall(r'[a-zA-Z]+', text))
            numbers = len(re.findall(r'\d+', text))
            special_chars = len(re.findall(r'[^\w\s가-힣一-龯]', text))
            
            # Gemini 기준 보수적 계산
            estimated_tokens = int(
                korean_chars * 2.0 +      # 한글: 2토큰 (보수적)
                chinese_chars * 2.0 +     # 한자: 2토큰
                english_words * 1.3 +     # 영단어: 1.3토큰 (서브워드 고려)
                numbers * 1.5 +           # 숫자: 1.5토큰
                special_chars * 1.2       # 특수문자: 1.2토큰
            )
            
            # 안전 마진 20% 추가
            return int(estimated_tokens * 1.2)
            
        except Exception as e:
            print(f"⚠️ 토큰 계산 오류: {e}")
            # 폴백: 매우 보수적 계산
            return len(text.split()) * 2

    def truncate_text_by_tokens(self, text: str, max_tokens: int = None) -> str:
        """🔧 개선된 토큰 기반 텍스트 절단"""
        if max_tokens is None:
            max_tokens = self.max_input_tokens
        
        current_tokens = self.estimate_token_count(text)
        
        if current_tokens <= max_tokens:
            return text
        
        try:
            # 🆕 연락처 우선 보존 절단
            return self._priority_aware_truncate(text, max_tokens, current_tokens)
            
        except Exception as e:
            print(f"⚠️ 우선순위 절단 실패, 기본 절단 사용: {e}")
            # 폴백: 기본 비율 절단
            ratio = (max_tokens * 0.9) / current_tokens
            target_length = int(len(text) * ratio)
            return text[:target_length]

    def _priority_aware_truncate(self, text, max_tokens, current_tokens):
        """🆕 우선순위 고려 절단"""
        # 연락처 패턴 위치 파악
        contact_patterns = [
            (r'(전화|tel|phone)[:\s]*\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}', 3),  # 전화번호 (우선순위 3)
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 2),        # 이메일 (우선순위 2)
            (r'\d{5}.*?(시|구|군)', 1),                                      # 주소 (우선순위 1)
        ]
        
        priority_sections = []
        
        for pattern, priority in contact_patterns:
            for match in re.finditer(pattern, text, re.I):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                section = text[start:end]
                priority_sections.append((section, priority, start, end))
        
        if priority_sections:
            # 우선순위별 정렬
            priority_sections.sort(key=lambda x: -x[1])
            
            # 높은 우선순위 섹션들부터 포함
            selected_text = ""
            included_ranges = []
            
            for section, priority, start, end in priority_sections:
                # 겹치지 않는 섹션만 추가
                if not any(start < e and end > s for s, e in included_ranges):
                    test_text = selected_text + "\n" + section
                    if self.estimate_token_count(test_text) <= max_tokens * 0.8:
                        selected_text = test_text
                        included_ranges.append((start, end))
                    else:
                        break
            
            if selected_text:
                self.stats['token_limit_exceeded'] += 1
                print(f"🎯 우선순위 기반 절단: {current_tokens} → {self.estimate_token_count(selected_text)} 토큰")
                return selected_text.strip()
        
        # 우선순위 섹션이 없으면 기본 절단
        ratio = (max_tokens * 0.9) / current_tokens
        target_length = int(len(text) * ratio)
        
        truncated = self._sentence_aware_truncate(text, target_length)
        
        self.stats['token_limit_exceeded'] += 1
        print(f"⚠️ 기본 절단: {current_tokens} → {self.estimate_token_count(truncated)} 토큰")
        
        return truncated

    # 🆕 URL 검색 관련 메서드들 추가
    def setup_selenium_driver(self):
        """Selenium WebDriver 설정"""
        if not self.use_selenium or self.driver:
            return
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"🌐 Chrome 드라이버 설정 완료 (headless: {self.headless})")
            
        except Exception as e:
            print(f"❌ 드라이버 설정 실패: {e}")
            self.use_selenium = False
    
    def close_selenium_driver(self):
        """Selenium WebDriver 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                print("🌐 드라이버 종료 완료")
            except:
                pass

    # 🆕 url_extractor.py의 정제 로직 완전 이식
    def clean_search_query_advanced(self, organization_name: str, location: str = "") -> str:
        """검색 쿼리 정제 (url_extractor.py와 동일한 로직)"""
        # 기본 정제
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', organization_name)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 지역 정보는 사용하지 않음 (검색 결과 제한 방지)
        
        # 키워드별 검색 전략
        if any(keyword in cleaned for keyword in ['교회', '성당', '절']):
            return f'{cleaned} 홈페이지'
        elif any(keyword in cleaned for keyword in ['센터', '관', '원']):
            return f'{cleaned} 공식홈페이지'
        else:
            return f'{cleaned} 홈페이지'

    # 🆕 url_extractor.py의 네이버 검색 로직 완전 이식
    def search_homepage_url_with_naver_advanced(self, organization_name: str) -> str:
        """기관 홈페이지 검색 (url_extractor.py 로직 완전 이식)"""
        if not self.use_selenium:
            print(f"⚠️ Selenium 비활성화됨: {organization_name}")
            return ""
        
        if not self.driver:
            self.setup_selenium_driver()
        
        if not self.driver:
            print(f"⚠️ 드라이버 초기화 실패: {organization_name}")
            return ""
        
        try:
            # url_extractor.py와 동일한 검색 쿼리들
            search_queries = [
                self.clean_search_query_advanced(organization_name),
                f'{organization_name} 홈페이지',
                f'{organization_name} 공식사이트',
                f'{organization_name} site:or.kr',
                f'{organization_name} site:org',
            ]
            
            for i, query in enumerate(search_queries, 1):
                print(f"🔍 네이버 검색 {i}/{len(search_queries)}: {query}")
                result = self._perform_naver_search_advanced(query, organization_name)
                if result:
                    self.stats['url_found'] += 1
                    return result
                
                # url_extractor.py와 동일한 지연
                self.add_delay_advanced()
            
            return ""
            
        except Exception as e:
            print(f"❌ 홈페이지 검색 실패 ({organization_name}): {e}")
            return ""

    # 🆕 url_extractor.py의 지연 로직 완전 이식
    def add_delay_advanced(self):
        """요청 간 지연 (url_extractor.py와 동일)"""
        delay = random.uniform(*self.delay_range)
        print(f"⏱️ 지연 시간: {delay:.1f}초")
        time.sleep(delay)

    # 🆕 url_extractor.py의 네이버 검색 로직 완전 이식
    def _perform_naver_search_advanced(self, query: str, organization_name: str) -> str:
        """실제 네이버 검색 수행 (url_extractor.py 로직 완전 이식)"""
        try:
            # 네이버 메인 페이지로 이동
            self.driver.get('https://www.naver.com')
            time.sleep(2)
            
            # 검색창 찾기 및 검색어 입력
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "query"))
            )
            
            # 검색창 클리어 후 검색어 입력
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # 검색 결과 로드 대기
            time.sleep(3)
            
            print(f"✅ 네이버 검색 실행: {query}")
            
            # 🔧 url_extractor.py와 동일한 선택자들 (더 정교함)
            link_selectors = [
                # 통합검색 결과
                'h3.title a[href*="http"]',
                '.total_wrap a[href*="http"]',
                '.result_area a[href*="http"]',
                '.data_area a[href*="http"]',
                
                # 웹문서 검색 결과
                '.web_page a[href*="http"]',
                '.site_area a[href*="http"]',
                
                # 일반 링크들
                'a[href*="http"]:not([href*="naver.com"])',
                '.info_area a[href*="http"]',
                '.source_area a[href*="http"]'
            ]
            
            found_urls = []
            
            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"📝 선택자 '{selector}'로 {len(elements)}개 요소 발견")
                    
                    for element in elements[:15]:  # 각 선택자당 15개씩
                        try:
                            href = element.get_attribute('href')
                            
                            if not href or href.startswith('#') or href.startswith('javascript:'):
                                continue
                            
                            # 네이버 내부 링크 필터링
                            if 'naver.com' in href and not self._extract_redirect_url_advanced(href):
                                continue
                            
                            # 리다이렉트 URL 처리
                            if 'naver.com' in href:
                                actual_url = self._extract_redirect_url_advanced(href)
                                if actual_url:
                                    url = actual_url
                                else:
                                    continue
                            else:
                                url = href
                            
                            # URL 유효성 검사 (url_extractor.py 로직)
                            if self.is_valid_homepage_url_advanced(url, organization_name):
                                found_urls.append(url)
                                print(f"📋 유효한 URL 발견: {url}")
                                
                                if len(found_urls) >= self.max_search_results:
                                    break
                                    
                        except Exception:
                            continue
                    
                    if found_urls:
                        break
                        
                except Exception as e:
                    print(f"⚠️ 선택자 '{selector}' 처리 중 오류: {e}")
                    continue
            
            # 🆕 url_extractor.py의 제목 텍스트 추가 검색
            if not found_urls:
                print(f"🔍 제목 텍스트 기반 추가 검색")
                found_urls = self._search_by_title_text_advanced(organization_name)
            
            # 가장 적합한 URL 선택 (url_extractor.py 로직)
            if found_urls:
                best_url = self.select_best_homepage_advanced(found_urls, organization_name)
                print(f"🎯 최종 선택된 URL: {best_url}")
                return best_url
            
            print(f"❌ '{query}' 검색에서 유효한 URL을 찾지 못했습니다")
            return ""
            
        except Exception as e:
            print(f"⚠️ 네이버 검색 실행 중 오류: {e}")
            return ""

    # 🆕 url_extractor.py의 리다이렉트 URL 처리 로직 완전 이식
    def _extract_redirect_url_advanced(self, naver_url: str) -> str:
        """네이버 리다이렉트 URL에서 실제 URL 추출 (url_extractor.py 로직)"""
        try:
            if 'url=' in naver_url:
                from urllib.parse import parse_qs, urlparse, unquote
                parsed_url = urlparse(naver_url)
                query_params = parse_qs(parsed_url.query)
                if 'url' in query_params:
                    actual_url = query_params['url'][0]
                    return unquote(actual_url)
            return ""
        except:
            return ""

    # 🆕 url_extractor.py의 제목 텍스트 검색 로직 완전 이식
    def _search_by_title_text_advanced(self, organization_name: str) -> list:
        """제목 텍스트로 추가 검색 (url_extractor.py 로직 완전 이식)"""
        found_urls = []
        try:
            # 홈페이지 관련 키워드가 포함된 링크 찾기
            homepage_keywords = ['홈페이지', '공식', 'official', 'home', 'www', '사이트']
            
            all_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="http"]')
            
            for link in all_links[:50]:
                try:
                    text = link.text.strip().lower()
                    href = link.get_attribute('href')
                    
                    # 링크 텍스트에 홈페이지 관련 키워드가 있는지 확인
                    if any(keyword in text for keyword in homepage_keywords):
                        if href and self.is_valid_homepage_url_advanced(href, organization_name):
                            found_urls.append(href)
                            print(f"📝 제목 텍스트로 발견: {href}")
                            
                            if len(found_urls) >= self.max_search_results:
                                break
                                
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"⚠️ 제목 텍스트 검색 중 오류: {e}")
            
        return found_urls

    # 🆕 url_extractor.py의 URL 유효성 검사 로직 완전 이식
    def is_valid_homepage_url_advanced(self, url: str, organization_name: str) -> bool:
        """유효한 홈페이지 URL인지 확인 (url_extractor.py 로직 완전 이식)"""
        try:
            if not url or len(url) < 10:
                return False
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            domain = parsed.netloc.lower()
            
            # 제외할 도메인 체크 (EXCLUDE_DOMAINS 사용)
            for exclude_domain in EXCLUDE_DOMAINS:
                if exclude_domain in domain:
                    return False
            
            # 추가 제외 패턴
            exclude_patterns = [
                r'\.pdf$', r'\.jpg$', r'\.png$', r'\.gif$',
                r'/board/', r'/bbs/', r'/community/',
                r'blog\.', r'cafe\.', r'post\.',
                r'search\.', r'maps\.', r'news\.'
            ]
            
            for pattern in exclude_patterns:
                if re.search(pattern, url.lower()):
                    return False
            
            # 너무 긴 URL 제외
            if len(url) > 200:
                return False
            
            # 공식 도메인 우선순위
            official_tlds = ['.or.kr', '.go.kr', '.ac.kr', '.org', '.church']
            if any(tld in domain for tld in official_tlds):
                print(f"🏛️ 공식 도메인 발견: {domain}")
                return True
            
            # 기관명이 도메인에 포함되어 있는지 확인
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    print(f"🎯 기관명이 도메인에 포함됨: {part} in {domain}")
                    return True
            
            return True
            
        except Exception:
            return False

    # 🆕 url_extractor.py의 점수 기반 URL 선택 로직 완전 이식
    def select_best_homepage_advanced(self, urls: list, organization_name: str) -> str:
        """가장 적합한 홈페이지 URL 선택 (url_extractor.py 로직 완전 이식)"""
        scored_urls = []
        
        for url in urls:
            score = 0
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 공식 도메인 높은 점수
            if any(tld in domain for tld in ['.or.kr', '.go.kr', '.ac.kr']):
                score += 10
            elif '.org' in domain:
                score += 8
            elif '.church' in domain:
                score += 7
            elif '.com' in domain:
                score += 3
            
            # 기관명 매칭 점수
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 1 and part in domain:
                    score += 5
            
            # 🔧 중요: url_extractor.py의 경로 점수 로직 추가
            path_depth = len(parsed.path.strip('/').split('/')) if parsed.path != '/' else 0
            score += max(0, 3 - path_depth)
            
            scored_urls.append((url, score))
        
        # 점수 순으로 정렬
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        
        best_url = scored_urls[0][0]
        print(f"🏆 최고 점수 URL 선택: {best_url} (점수: {scored_urls[0][1]})")
        
        return best_url

    # 🆕 url_extractor.py의 URL 검증 로직 완전 이식
    def verify_homepage_url_advanced(self, url: str) -> bool:
        """홈페이지 URL이 실제로 접근 가능한지 확인 (url_extractor.py 로직 완전 이식)"""
        try:
            original_window = self.driver.current_window_handle
            
            # 새 탭에서 URL 검증
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            self.driver.get(url)
            time.sleep(3)
            
            # 페이지 로드 성공 여부 확인
            is_accessible = "404" not in self.driver.title.lower() and \
                           "error" not in self.driver.title.lower() and \
                           len(self.driver.page_source) > 1000
            
            # 원래 창으로 돌아가기
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            if is_accessible:
                print(f"✅ URL 접근 성공: {url}")
            else:
                print(f"⚠️ URL 접근 실패: {url}")
            
            return is_accessible
            
        except Exception as e:
            print(f"❌ URL 검증 중 오류: {url} - {e}")
            try:
                # 오류 시 원래 창으로 돌아가기
                if self.driver and len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return False
    
    async def process_single_organization_enhanced(self, org_data):
        """완전히 개선된 단일 기관 처리 (실시간 진행 상황 콜백 포함)"""
        org_name = org_data.get('name', 'Unknown')
        homepage_url = org_data.get('homepage', '')
        
        # 🆕 추가: 초기 상태 콜백 호출
        if self.progress_callback:
            initial_result = {
                "name": org_name,
                "category": org_data.get('category', ''),
                "phone": org_data.get('phone', ''),
                "fax": org_data.get('fax', ''),
                "email": org_data.get('email', ''),
                "postal_code": org_data.get('postal_code', ''),
                "address": org_data.get('address', ''),
                "homepage_url": homepage_url,
                "status": "processing",
                "processed_at": datetime.now().isoformat(),
                "error_message": "",
                "current_step": "시작"
            }
            self.progress_callback(initial_result)
        
        try:
            start_time = time.time()
            
            # 🆕 1단계: 홈페이지 URL 확인/검색 시작 알림
            if self.progress_callback:
                step_result = initial_result.copy()
                step_result.update({
                    "current_step": "홈페이지 URL 검색 중...",
                    "status": "processing"
                })
                self.progress_callback(step_result)
            
            # 1. 홈페이지 URL 확인/검색 (url_extractor.py 로직 사용)
            if not homepage_url or homepage_url == '정보확인 안됨' or not homepage_url.startswith(('http://', 'https://')):
                print(f"🔍 고급 홈페이지 URL 검색: {org_name}")
                homepage_url = self.search_homepage_url_with_naver_advanced(org_name)
                self.stats['url_search_performed'] += 1
                
                if homepage_url:
                    # 🆕 URL 발견 시 콜백 호출
                    if self.progress_callback:
                        step_result = initial_result.copy()
                        step_result.update({
                            "homepage_url": homepage_url,
                            "current_step": "홈페이지 URL 검증 중...",
                            "status": "processing"
                        })
                        self.progress_callback(step_result)
                    
                    # 🆕 실제 접근성 검증 (url_extractor.py 핵심 기능)
                    if self.verify_homepage_url_advanced(homepage_url):
                        org_data['homepage'] = homepage_url
                        print(f"✅ 검증된 홈페이지 발견: {org_name} -> {homepage_url}")
                        
                        # 🆕 검증 완료 콜백
                        if self.progress_callback:
                            step_result = initial_result.copy()
                            step_result.update({
                                "homepage_url": homepage_url,
                                "current_step": "홈페이지 URL 검증 완료",
                                "status": "processing"
                            })
                            self.progress_callback(step_result)
                    else:
                        homepage_url = ""
                        print(f"❌ URL 접근 불가, 제외: {org_name}")
                        
                        # 🆕 검증 실패 콜백
                        if self.progress_callback:
                            step_result = initial_result.copy()
                            step_result.update({
                                "current_step": "홈페이지 URL 접근 불가",
                                "status": "processing"
                            })
                            self.progress_callback(step_result)
                else:
                    print(f"❌ 홈페이지를 찾을 수 없음: {org_name}")
                    
                    # 🆕 URL 찾기 실패 콜백
                    if self.progress_callback:
                        step_result = initial_result.copy()
                        step_result.update({
                            "current_step": "홈페이지 URL 찾기 실패",
                            "status": "processing"
                        })
                        self.progress_callback(step_result)
            else:
                print(f"📋 기존 홈페이지 사용: {org_name} -> {homepage_url}")
                
                # 🆕 기존 URL 사용 콜백
                if self.progress_callback:
                    step_result = initial_result.copy()
                    step_result.update({
                        "homepage_url": homepage_url,
                        "current_step": "기존 홈페이지 URL 사용",
                        "status": "processing"
                    })
                    self.progress_callback(step_result)
            
            # 🆕 2단계: JSON 데이터 추출 시작 알림
            if self.progress_callback:
                step_result = initial_result.copy()
                step_result.update({
                    "homepage_url": homepage_url,
                    "current_step": "JSON 데이터 추출 중...",
                    "status": "processing"
                })
                self.progress_callback(step_result)
            
            # 2. JSON 데이터 추출
            json_info = self.extract_from_json_data(org_data)
            
            # 🆕 JSON 추출 완료 콜백 (기본 연락처 정보 업데이트)
            if self.progress_callback:
                step_result = initial_result.copy()
                step_result.update({
                    "phone": json_info.get('전화번호', org_data.get('phone', '')),
                    "fax": json_info.get('팩스번호', org_data.get('fax', '')),
                    "email": json_info.get('이메일', org_data.get('email', '')),
                    "postal_code": json_info.get('우편번호', org_data.get('postal_code', '')),
                    "address": json_info.get('주소', org_data.get('address', '')),
                    "homepage_url": homepage_url,
                    "current_step": "JSON 데이터 추출 완료",
                    "status": "processing"
                })
                self.progress_callback(step_result)
            
            # 3. 홈페이지가 있으면 크롤링 수행
            ai_info = {}
            if homepage_url and homepage_url.startswith(('http://', 'https://')):
                if self.needs_additional_crawling(json_info):
                    # 🆕 3단계: 홈페이지 크롤링 시작 알림
                    if self.progress_callback:
                        step_result = initial_result.copy()
                        step_result.update({
                            "phone": json_info.get('전화번호', org_data.get('phone', '')),
                            "fax": json_info.get('팩스번호', org_data.get('fax', '')),
                            "email": json_info.get('이메일', org_data.get('email', '')),
                            "postal_code": json_info.get('우편번호', org_data.get('postal_code', '')),
                            "address": json_info.get('주소', org_data.get('address', '')),
                            "homepage_url": homepage_url,
                            "current_step": "홈페이지 크롤링 중...",
                            "status": "processing"
                        })
                        self.progress_callback(step_result)
                    
                    print(f"🌐 크롤링 수행: {org_name}")
                    
                    try:
                        ai_info = await asyncio.wait_for(
                            self.crawl_and_extract_async(org_data), 
                            timeout=120
                        )
                        
                        # 🆕 크롤링 완료 콜백
                        if self.progress_callback:
                            step_result = initial_result.copy()
                            step_result.update({
                                "phone": json_info.get('전화번호', org_data.get('phone', '')),
                                "fax": json_info.get('팩스번호', org_data.get('fax', '')),
                                "email": json_info.get('이메일', org_data.get('email', '')),
                                "postal_code": json_info.get('우편번호', org_data.get('postal_code', '')),
                                "address": json_info.get('주소', org_data.get('address', '')),
                                "homepage_url": homepage_url,
                                "current_step": "홈페이지 크롤링 완료",
                                "status": "processing"
                            })
                            self.progress_callback(step_result)
                            
                    except asyncio.TimeoutError:
                        print(f"⏰ 크롤링 시간 초과: {org_name}")
                        ai_info = {}
                        
                        # 🆕 크롤링 시간 초과 콜백
                        if self.progress_callback:
                            step_result = initial_result.copy()
                            step_result.update({
                                "phone": json_info.get('전화번호', org_data.get('phone', '')),
                                "fax": json_info.get('팩스번호', org_data.get('fax', '')),
                                "email": json_info.get('이메일', org_data.get('email', '')),
                                "postal_code": json_info.get('우편번호', org_data.get('postal_code', '')),
                                "address": json_info.get('주소', org_data.get('address', '')),
                                "homepage_url": homepage_url,
                                "current_step": "크롤링 시간 초과",
                                "status": "processing"
                            })
                            self.progress_callback(step_result)
                else:
                    print(f"📋 JSON 정보 충분: {org_name}")
                    
                    # 🆕 크롤링 스킵 콜백
                    if self.progress_callback:
                        step_result = initial_result.copy()
                        step_result.update({
                            "phone": json_info.get('전화번호', org_data.get('phone', '')),
                            "fax": json_info.get('팩스번호', org_data.get('fax', '')),
                            "email": json_info.get('이메일', org_data.get('email', '')),
                            "postal_code": json_info.get('우편번호', org_data.get('postal_code', '')),
                            "address": json_info.get('주소', org_data.get('address', '')),
                            "homepage_url": homepage_url,
                            "current_step": "JSON 정보 충분 (크롤링 스킵)",
                            "status": "processing"
                        })
                        self.progress_callback(step_result)
            
            # 🆕 4단계: 데이터 병합 시작 알림
            if self.progress_callback:
                step_result = initial_result.copy()
                step_result.update({
                    "current_step": "데이터 병합 중...",
                    "status": "processing"
                })
                self.progress_callback(step_result)
            
            # 4. 데이터 병합
            merged_data = self.merge_contact_data(json_info, ai_info)
            
            # 5. 최종 결과 포맷팅
            final_result = self.format_final_result(org_data, merged_data)
            final_result['추출방법'] = 'JSON+고급검색'  # 고급 검색 표시
            
            # 처리 시간 로깅
            elapsed_time = time.time() - start_time
            print(f"✅ 고급 처리 완료: {org_name} ({final_result['추출방법']}) - {elapsed_time:.1f}초")
            
            # 🆕 최종 완료 콜백 (모든 데이터 포함)
            if self.progress_callback:
                completion_result = {
                    "name": org_name,
                    "category": org_data.get('category', ''),
                    "phone": merged_data.get('전화번호', ''),
                    "fax": merged_data.get('팩스번호', ''),
                    "email": merged_data.get('이메일', ''),
                    "postal_code": merged_data.get('우편번호', ''),
                    "address": merged_data.get('주소', ''),
                    "homepage_url": homepage_url,
                    "status": "completed",
                    "processed_at": datetime.now().isoformat(),
                    "error_message": "",
                    "current_step": f"처리 완료 ({elapsed_time:.1f}초)",
                    "processing_time": f"{elapsed_time:.1f}초",
                    "extraction_method": final_result.get('추출방법', 'JSON+고급검색')
                }
                self.progress_callback(completion_result)
            
            return final_result
            
        except Exception as e:
            print(f"❌ 처리 실패 ({org_name}): {str(e)[:100]}...")
            
            # 🆕 에러 발생 시 콜백
            if self.progress_callback:
                error_result = {
                    "name": org_name,
                    "category": org_data.get('category', ''),
                    "phone": org_data.get('phone', ''),
                    "fax": org_data.get('fax', ''),
                    "email": org_data.get('email', ''),
                    "postal_code": org_data.get('postal_code', ''),
                    "address": org_data.get('address', ''),
                    "homepage_url": homepage_url,
                    "status": "failed",
                    "processed_at": datetime.now().isoformat(),
                    "error_message": str(e)[:200],  # 에러 메시지 제한
                    "current_step": "처리 실패",
                    "extraction_method": "실패"
                }
                self.progress_callback(error_result)
            
            return {
                '기관명': org_name,
                '홈페이지': homepage_url,
                '주소': '정보확인 안됨',
                '우편번호': '정보확인 안됨',
                '전화번호': '정보확인 안됨',
                '팩스번호': '정보확인 안됨',
                '이메일': '정보확인 안됨',
                '추출방법': '실패',
                '추출상태': '실패'
            }

    def validate_and_clean_contacts(self, phone_list, fax_list):
        """개선된 전화번호/팩스번호 검증 및 중복 제거"""
        cleaned_phones = []
        cleaned_faxes = []
        
        # ✅ 수정: PhoneUtils 활용
        # 전화번호 검증
        for phone in phone_list:
            if PhoneUtils.validate_korean_phone(phone):  # validator.validate_phone_number 대체
                formatted = PhoneUtils.format_phone_number(phone)
                if formatted and formatted not in cleaned_phones:
                    cleaned_phones.append(formatted)
        
        # 팩스번호 검증
        for fax in fax_list:
            if PhoneUtils.validate_korean_phone(fax):  # validator.validate_fax_number 대체
                formatted = PhoneUtils.format_phone_number(fax)
                if formatted and formatted not in cleaned_faxes:
                    cleaned_faxes.append(formatted)
        
        # 전화번호-팩스번호 중복 검사 개선
        final_phones = cleaned_phones.copy()
        final_faxes = []
        
        for fax in cleaned_faxes:
            # ✅ 수정: PhoneUtils 활용
            # 전화번호와 완전히 동일한 팩스번호는 제외
            if fax in final_phones:
                self.stats['duplicates_removed'] += 1
                print(f"🗑️ 중복 제거: {fax} (전화번호와 동일)")
                continue
            
            # 유사한 번호 검사 (더 정교한 로직)
            is_duplicate = False
            for phone in final_phones:
                if PhoneUtils.is_phone_fax_duplicate(phone, fax):  # validator 메서드 대체
                    is_duplicate = True
                    self.stats['duplicates_removed'] += 1
                    print(f"🗑️ 중복 제거: {fax} (전화번호 {phone}와 유사)")
                    break
            
            if not is_duplicate:
                final_faxes.append(fax)
        
        return final_phones, final_faxes
    
    def extract_from_json_data(self, org_data):
        """JSON 데이터에서 기존 정보 추출 (jsontocsv.py 로직 활용)"""
        result = {
            'phone': [],
            'fax': [],
            'email': [],
            'address': [],
            'postal_code': []
        }
        
        # 기본 필드에서 추출
        if org_data.get("phone"):
            result['phone'].append(org_data["phone"])
        if org_data.get("fax"):
            result['fax'].append(org_data["fax"])
        
        # 홈페이지 파싱 결과에서 추출
        homepage_content = org_data.get("homepage_content", {})
        if homepage_content:
            parsed_contact = homepage_content.get("parsed_contact", {})
            
            # 전화번호 추출 (파싱된 결과 우선)
            if parsed_contact.get("phones"):
                for phone in parsed_contact["phones"]:
                    if phone not in result['phone']:
                        result['phone'].append(phone)
            
            # 팩스번호 추출 (파싱된 결과 우선)
            if parsed_contact.get("faxes"):
                for fax in parsed_contact["faxes"]:
                    if fax not in result['fax']:
                        result['fax'].append(fax)
            
            # 이메일 추출
            if parsed_contact.get("emails"):
                for email in parsed_contact["emails"]:
                    if email not in result['email']:
                        result['email'].append(email)
            
            # 주소 추출
            if parsed_contact.get("addresses"):
                for address in parsed_contact["addresses"]:
                    if address not in result['address']:
                        result['address'].append(address)
            
            # contact_info에서도 추출 시도
            contact_info = homepage_content.get("contact_info", "")
            if contact_info:
                # 간단한 정규식으로 추가 정보 추출
                phone_matches = re.findall(r'전화[:\s]*([0-9\-\.\(\)\s]{8,20})', contact_info)
                fax_matches = re.findall(r'팩스[:\s]*([0-9\-\.\(\)\s]{8,20})', contact_info)
                email_matches = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', contact_info)
                postal_matches = re.findall(r'(\d{5})', contact_info)
                
                for phone in phone_matches:
                    clean_phone = phone.strip()
                    if clean_phone and clean_phone not in result['phone']:
                        result['phone'].append(clean_phone)
                
                for fax in fax_matches:
                    clean_fax = fax.strip()
                    if clean_fax and clean_fax not in result['fax']:
                        result['fax'].append(clean_fax)
                
                for email in email_matches:
                    clean_email = email.strip()
                    if clean_email and clean_email not in result['email']:
                        result['email'].append(clean_email)
                
                for postal in postal_matches:
                    clean_postal = postal.strip()
                    if clean_postal and clean_postal not in result['postal_code']:
                        result['postal_code'].append(clean_postal)
        
        return result
    
    def extract_with_regex(self, text, pattern_type):
        """정규식으로 정보 추출"""
        results = []
        if pattern_type in self.patterns:
            for pattern in self.patterns[pattern_type]:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    if match and len(match.strip()) > 3:
                        results.append(match.strip())
        
        # 중복 제거 및 정제
        unique_results = []
        for result in results:
            cleaned = re.sub(r'[^\w\s\-\.\@\(\)]', '', result)
            if cleaned and cleaned not in unique_results:
                unique_results.append(cleaned)
        
        return unique_results[:3]  # 최대 3개까지만
        
    def extract_contact_info_sync(self, text, organization_name):
        """연락처 정보 종합 추출"""
        result = {
            'phone': [],
            'fax': [],
            'email': [],
            'address': []
        }
        
        # 1. 정규식으로 1차 추출
        for info_type in result.keys():
            regex_results = self.extract_with_regex(text, info_type)
            result[info_type].extend(regex_results)
        
        # 2. AI로 2차 보완 (텍스트를 청크로 나누어 처리)
        if self.use_ai and text:
            chunk_size = 3000
            overlap = 300
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if len(chunk) < 100:  # 너무 짧은 청크는 스킵
                    continue
                
                ai_result = self.extract_with_ai(chunk, organization_name)
                
                # AI 결과 병합
                for info_type, values in ai_result.items():
                    if info_type in result and isinstance(values, list):
                        for value in values:
                            if value and value != "정보확인 안됨" and value not in result[info_type]:
                                result[info_type].append(value)
        
        # 3. 결과 정제 및 제한
        for info_type in result.keys():
            # 중복 제거 및 최대 개수 제한
            unique_items = []
            for item in result[info_type]:
                if item and item not in unique_items:
                    unique_items.append(item)
            result[info_type] = unique_items[:2]  # 최대 2개까지
        
        return result
    
    def extract_with_ai(self, text_chunk, organization_name):
        """Gemini AI로 정보 추출 (동기식)"""
        if not self.use_ai or not self.ai_model_manager:  # 🔧 수정
            return {}
        
        try:
            prompt = self.create_structured_prompt(text_chunk, organization_name)
            response_text = self.ai_model_manager.generate_text(prompt)  # 🔧 수정
            
            # 마크다운 파싱
            result = self.parse_markdown_to_dict(response_text)
            self.stats['ai_enhanced'] += 1
            return result
            
        except Exception as e:
            print(f"❌ AI 추출 오류 ({organization_name}): {str(e)}")
            return {}
        
    def create_structured_prompt(self, text_chunk, organization_name):
        """🔧 개선된 구조화 프롬프트 생성"""
        # 🆕 스마트 텍스트 절단 (프롬프트용)
        processed_chunk = self._smart_truncate_for_prompt(text_chunk, 2500)
        
        prompt = f"""'{organization_name}' 기관의 연락처 정보를 정확하게 추출해주세요.

                **기관명:** {organization_name}

                **추출 대상:**
                - 전화번호: 한국 형식 (02-1234-5678, 031-123-4567, 010-1234-5678)
                - 팩스번호: 한국 형식 (02-1234-5679)  
                - 이메일: 유효한 형식 (info@example.com)
                - 우편번호: 5자리 숫자 (12345)
                - 주소: 완전한 주소 (시/도부터 상세주소까지)

                **응답 형식:** (정확히 지켜주세요)
                전화번호: [발견된 번호 또는 "없음"]
                팩스번호: [발견된 번호 또는 "없음"]
                이메일: [발견된 이메일 또는 "없음"]
                우편번호: [발견된 우편번호 또는 "없음"]
                주소: [발견된 주소 또는 "없음"]

                **중요 규칙:**
                1. {organization_name}와 직접 관련된 연락처만 추출
                2. 대표번호, 메인 연락처 우선
                3. 여러 개 발견시 가장 공식적인 것 선택
                4. 확실하지 않으면 "없음"으로 표시

                **분석할 텍스트:**
                {processed_chunk}

                위 형식으로 정확하게 답변해주세요."""

        # 프롬프트 로깅
        self.ai_logger.info(f"=== 개선된 프롬프트 생성 [{organization_name}] ===")
        self.ai_logger.info(f"원본 청크 길이: {len(text_chunk)} → 처리된 길이: {len(processed_chunk)}")
        self.ai_logger.info(f"프롬프트 총 길이: {len(prompt)} 문자")
        
        return prompt

    def _smart_truncate_for_prompt(self, text, max_length):
        """🆕 프롬프트용 스마트 텍스트 절단"""
        if len(text) <= max_length:
            return text
        
        try:
            # 1순위: 연락처 패턴 주변 우선 추출
            contact_patterns = [
                r'(전화|tel|phone)[:\s]*\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}',
                r'(팩스|fax)[:\s]*\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}',
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'\d{5}.*?(시|구|군)',
            ]
            
            important_sections = []
            
            for pattern in contact_patterns:
                for match in re.finditer(pattern, text, re.I):
                    start = max(0, match.start() - 200)
                    end = min(len(text), match.end() + 200)
                    section = text[start:end]
                    important_sections.append(section)
            
            if important_sections:
                # 중요 섹션들을 합쳐서 max_length 내에서 반환
                combined = '\n--- 연락처 관련 섹션 ---\n'.join(important_sections)
                if len(combined) <= max_length:
                    return combined
                else:
                    return combined[:max_length]
            
            # 2순위: 문장 단위 절단
            return self._sentence_aware_truncate(text, max_length)
            
        except Exception:
            return text[:max_length]
    
    def parse_markdown_to_dict(self, markdown_text):
        """🔧 강화된 AI 응답 파싱 (정규식 병행)"""
        result = {
            'phone': [],
            'fax': [],
            'email': [],
            'address': [],
            'postal_code': []
        }
        
        try:
            # 1단계: 기존 마크다운 파싱
            lines = markdown_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    try:
                        key, value = line.split(':', 1)
                        key = key.strip().replace('**', '').replace('*', '').lower()
                        value = value.strip()
                        
                        if value and value not in ["정보확인 안됨", "없음", "none", "-", "n/a"]:
                            # 키 매핑 개선
                            if any(keyword in key for keyword in ['전화번호', 'phone', 'tel']):
                                if self._is_valid_phone_format(value):
                                    result['phone'].append(value)
                            elif any(keyword in key for keyword in ['팩스', 'fax']):
                                if self._is_valid_phone_format(value):
                                    result['fax'].append(value)
                            elif any(keyword in key for keyword in ['이메일', 'email', 'mail']):
                                if self._is_valid_email_format(value):
                                    result['email'].append(value)
                            elif any(keyword in key for keyword in ['주소', 'address', 'addr']):
                                if len(value) > 10:  # 의미있는 길이의 주소만
                                    result['address'].append(value)
                            elif any(keyword in key for keyword in ['우편번호', 'postal', 'zip']):
                                if re.match(r'^\d{5}$', value):
                                    result['postal_code'].append(value)
                    except ValueError:
                        continue
            
            # 2단계: 정규식으로 직접 추출 (AI 파싱 보완)
            regex_results = self._extract_with_regex_patterns(markdown_text)
            
            # 3단계: 결과 병합 (중복 제거)
            for key, values in regex_results.items():
                for value in values:
                    if value not in result[key]:
                        result[key].append(value)
            
            # 4단계: 결과 검증 및 정제
            result = self._validate_and_clean_parsed_result(result)
            
            return result
            
        except Exception as e:
            print(f"⚠️ AI 응답 파싱 오류: {e}")
            return result

    def _extract_with_regex_patterns(self, text):
        """🆕 정규식을 통한 직접 추출 (AI 파싱 보완용)"""
        regex_result = {
            'phone': [],
            'fax': [],
            'email': [],
            'address': [],
            'postal_code': []
        }
        
        try:
            # 전화번호 패턴 (더 정교함)
            phone_patterns = [
                r'(\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4})',  # 기본 패턴
                r'(전화|tel|phone)[:\s]*(\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4})',  # 라벨 포함
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, text, re.I)
                for match in matches:
                    phone = match if isinstance(match, str) else match[-1]
                    phone = re.sub(r'[^\d-]', '', phone)  # 숫자와 하이픈만
                    if self._is_valid_phone_format(phone):
                        regex_result['phone'].append(phone)
            
            # 팩스번호 패턴
            fax_patterns = [
                r'(팩스|fax)[:\s]*(\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4})',
            ]
            
            for pattern in fax_patterns:
                matches = re.findall(pattern, text, re.I)
                for match in matches:
                    fax = match[-1] if isinstance(match, tuple) else match
                    fax = re.sub(r'[^\d-]', '', fax)
                    if self._is_valid_phone_format(fax):
                        regex_result['fax'].append(fax)
            
            # 이메일 패턴
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            email_matches = re.findall(email_pattern, text)
            for email in email_matches:
                if self._is_valid_email_format(email):
                    regex_result['email'].append(email)
            
            # 우편번호 패턴
            postal_pattern = r'(\d{5})(?=\s*[가-힣].*?(시|구|군))'
            postal_matches = re.findall(postal_pattern, text)
            for postal in postal_matches:
                regex_result['postal_code'].append(postal)
            
            return regex_result
            
        except Exception as e:
            print(f"⚠️ 정규식 추출 오류: {e}")
            return regex_result

    def _is_valid_phone_format(self, phone):
        """🆕 전화번호 형식 검증"""
        if not phone:
            return False
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 길이 체크 (한국 전화번호: 9-11자리)
        if len(digits) < 9 or len(digits) > 11:
            return False
        
        # 패턴 체크
        phone_patterns = [
            r'^\d{2,3}-\d{3,4}-\d{4}$',  # 02-1234-5678
            r'^\d{3}-\d{4}-\d{4}$',      # 010-1234-5678
        ]
        
        formatted_phone = re.sub(r'(\d{2,3})(\d{3,4})(\d{4})', r'\1-\2-\3', digits)
        
        return any(re.match(pattern, formatted_phone) for pattern in phone_patterns)

    def _is_valid_email_format(self, email):
        """🆕 이메일 형식 검증"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _validate_and_clean_parsed_result(self, result):
        """🆕 파싱 결과 검증 및 정제"""
        cleaned_result = {}
        
        for key, values in result.items():
            cleaned_values = []
            
            for value in values:
                value = value.strip()
                
                # 중복 제거
                if value not in cleaned_values:
                    if key in ['phone', 'fax']:
                        # 전화번호 정규화
                        normalized = self._normalize_phone_number(value)
                        if normalized:
                            cleaned_values.append(normalized)
                    elif key == 'email':
                        # 이메일 소문자 변환
                        cleaned_values.append(value.lower())
                    else:
                        cleaned_values.append(value)
            
            # 최대 2개까지만 유지 (우선순위: 먼저 발견된 것)
            cleaned_result[key] = cleaned_values[:2]
        
        return cleaned_result

    def _normalize_phone_number(self, phone):
        """🆕 전화번호 정규화"""
        if not phone:
            return None
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        if len(digits) == 10:
            # 10자리: 02-1234-5678 형태
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        elif len(digits) == 11:
            # 11자리: 010-1234-5678 형태
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) == 9:
            # 9자리: 31-123-4567 형태
            return f"0{digits[:2]}-{digits[2:5]}-{digits[5:]}"
        
        return phone  # 정규화 실패시 원본 반환
    
    def merge_contact_data(self, json_data, ai_data):
        """JSON 데이터와 AI 추출 데이터 병합"""
        merged = {}
        
        # 모든 키에 대해 병합 수행
        all_keys = set(json_data.keys()) | set(ai_data.keys())
        
        for key in all_keys:
            merged[key] = []
            
            # JSON 데이터 추가
            if key in json_data and json_data[key]:
                if isinstance(json_data[key], list):
                    merged[key].extend(json_data[key])
                else:
                    merged[key].append(json_data[key])
            
            # AI 데이터 추가 (중복 제거)
            if key in ai_data and ai_data[key]:
                if isinstance(ai_data[key], list):
                    for item in ai_data[key]:
                        if item not in merged[key]:
                            merged[key].append(item)
                else:
                    if ai_data[key] not in merged[key]:
                        merged[key].append(ai_data[key])
        
        return merged
    
    async def extract_with_ai_structured_async(self, text_chunk, organization_name):
        """비동기 AI 추출 (TPM 고려)"""
        if not self.use_ai or not self.ai_model_manager:  # 🔧 수정
            return {}
        
        try:
            # TPM 제한 대기
            await self.tpm_manager.wait_if_needed()
            
            # 프롬프트 생성
            prompt = self.create_structured_prompt(text_chunk, organization_name)
            
            # AI 호출 (비동기) - ai_helpers.py 활용
            response_text = await extract_with_gemini_text(text_chunk, prompt)  # 🔧 수정
            
            self.stats['api_calls_made'] += 1
            
            # 마크다운 파싱
            ai_data = self.parse_markdown_to_dict(response_text)
            
            if ai_data:
                self.stats['ai_enhanced'] += 1
                print(f"🤖 AI 추출 성공: {organization_name}")
            
            return ai_data
            
        except Exception as e:
            print(f"❌ 비동기 AI 추출 오류 ({organization_name}): {e}")
            return {}
    
    def crawl_homepage_if_needed(self, url, organization_name):
        """🔧 개선: 연락처 섹션 우선 추출 및 스마트 텍스트 처리"""
        try:
            print(f"🔍 추가 크롤링 시작: {organization_name} ({url})")
            
            # SSL 검증 비활성화로 요청 시도
            try:
                response = self.session.get(url, timeout=10, verify=True)
            except requests.exceptions.SSLError:
                print(f"⚠️ SSL 인증서 문제 감지, 검증 없이 재시도: {organization_name}")
                response = self.session.get(url, timeout=10, verify=False)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 🆕 1단계: 연락처 관련 섹션 우선 추출
            priority_text = self._extract_contact_priority_sections(soup, organization_name)
            
            # 🆕 2단계: 나머지 콘텐츠에서 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'header']):
                tag.decompose()
            
            # 🆕 3단계: 전체 텍스트 추출 (우선순위 고려)
            remaining_text = soup.get_text(separator=' ', strip=True)
            
            # 🆕 4단계: 우선순위 텍스트 + 나머지 텍스트 결합
            if priority_text:
                full_text = f"{priority_text}\n--- 기타 내용 ---\n{remaining_text}"
                print(f"📍 우선순위 섹션 발견: {len(priority_text)} 문자")
            else:
                full_text = remaining_text
            
            self.stats['crawling_performed'] += 1
            print(f"✅ 크롤링 성공: {organization_name} ({len(full_text)} 문자)")
            return full_text
            
        except Exception as e:
            print(f"❌ 크롤링 실패 ({organization_name}): {str(e)[:100]}...")
            return ""
        
    def _extract_contact_priority_sections(self, soup, organization_name):
        """🆕 연락처 관련 섹션 우선 추출"""
        priority_text = ""
        
        try:
            # 연락처 관련 키워드로 섹션 찾기
            contact_keywords = [
                r'contact', r'연락처', r'문의', r'찾아오시는길', 
                r'회사정보', r'about', r'footer', r'company.*info',
                r'tel', r'phone', r'address', r'오시는길'
            ]
            
            contact_pattern = '|'.join(contact_keywords)
            
            # 1순위: class나 id에 연락처 관련 키워드가 있는 요소들
            contact_sections = soup.find_all(['div', 'section', 'footer', 'aside'], 
                                        attrs={'class': re.compile(contact_pattern, re.I)})
            
            contact_sections.extend(soup.find_all(['div', 'section', 'footer', 'aside'], 
                                                attrs={'id': re.compile(contact_pattern, re.I)}))
            
            # 2순위: footer 태그 전체
            if not contact_sections:
                footer = soup.find('footer')
                if footer:
                    contact_sections = [footer]
            
            # 3순위: aside 태그들
            if not contact_sections:
                contact_sections = soup.find_all('aside')
            
            # 텍스트 추출 및 정제
            for section in contact_sections[:3]:  # 최대 3개 섹션만
                section_text = section.get_text(separator=' ', strip=True)
                if len(section_text) > 20:  # 의미있는 길이의 텍스트만
                    priority_text += f"{section_text}\n"
            
            if priority_text:
                priority_text = priority_text.strip()
                print(f"📍 우선순위 섹션 추출: {len(contact_sections)}개 섹션, {len(priority_text)} 문자")
            
            return priority_text
            
        except Exception as e:
            print(f"⚠️ 우선순위 섹션 추출 실패 ({organization_name}): {e}")
            return ""
    
    async def crawl_and_extract_async(self, org_data):
        """🔧 개선된 비동기 크롤링 및 지능형 AI 추출"""
        org_name = org_data.get('name', 'Unknown')
        homepage_url = org_data.get('homepage', '')
        
        if not homepage_url or homepage_url == '정보확인 안됨':
            return {}
        
        # 홈페이지 크롤링
        homepage_text = self.crawl_homepage_if_needed(homepage_url, org_name)
        
        if not homepage_text:
            return {}
        
        # 🆕 스마트 텍스트 길이 제한
        max_text_length = 12000  # 12KB로 증가
        if len(homepage_text) > max_text_length:
            homepage_text = self._smart_truncate_text(homepage_text, max_text_length, org_name)
            print(f"📏 스마트 텍스트 제한: {org_name} ({len(homepage_text)} 문자)")
        
        # 🆕 지능형 청킹
        chunks = self._intelligent_chunking(homepage_text, org_name)
        max_chunks = min(5, len(chunks))  # 최대 5개 청크
        
        print(f"📝 총 {len(chunks)}개 청크 생성, {max_chunks}개 처리 예정: {org_name}")

    def _smart_truncate_text(self, text, max_length, org_name):
        """🆕 스마트 텍스트 절단 (연락처 패턴 보존)"""
        if len(text) <= max_length:
            return text
        
        try:
            # 연락처 패턴이 있는 부분 찾기
            contact_patterns = [
                r'\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}',  # 전화번호
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 이메일
                r'\d{5}',  # 우편번호
            ]
            
            contact_positions = []
            for pattern in contact_patterns:
                for match in re.finditer(pattern, text):
                    contact_positions.append((match.start(), match.end()))
            
            if contact_positions:
                # 연락처 정보 주변을 우선 보존
                contact_positions.sort()
                
                # 가장 빠른 연락처부터 max_length만큼 추출
                start_pos = max(0, contact_positions[0][0] - 1000)  # 앞쪽 1000자 여유
                end_pos = min(len(text), start_pos + max_length)
                
                truncated = text[start_pos:end_pos]
                print(f"📍 연락처 패턴 기준 절단: {org_name} (위치: {start_pos}-{end_pos})")
                return truncated
            else:
                # 연락처 패턴이 없으면 문장 단위로 절단
                return self._sentence_aware_truncate(text, max_length)
                
        except Exception as e:
            print(f"⚠️ 스마트 절단 실패, 기본 절단 사용: {org_name} - {e}")
            return text[:max_length]

    def _sentence_aware_truncate(self, text, max_length):
        """🆕 문장 단위 절단"""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        
        # 문장 끝 찾기
        sentence_ends = ['.', '!', '?', '\n', '다.', '음.', '니다.']
        
        best_cut = max_length
        for end_char in sentence_ends:
            pos = truncated.rfind(end_char)
            if pos > max_length * 0.8:  # 80% 이상 지점에서 발견되면
                best_cut = pos + 1
                break
        
        return text[:best_cut]

    def _intelligent_chunking(self, text, org_name):
        """🆕 지능형 청킹 (연락처 패턴 고려)"""
        chunks = []
        chunk_size = 2000
        min_overlap = 100
        max_overlap = 500
        
        try:
            # 연락처 패턴 위치 파악
            contact_pattern = r'(\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d{5})'
            contact_positions = [m.start() for m in re.finditer(contact_pattern, text)]
            
            i = 0
            while i < len(text):
                chunk_start = i
                chunk_end = min(i + chunk_size, len(text))
                
                # 연락처 패턴이 청크 경계 근처에 있는지 확인
                has_contact_near_boundary = any(
                    abs(pos - chunk_end) < 100 for pos in contact_positions 
                    if chunk_start <= pos <= chunk_end + 100
                )
                
                if has_contact_near_boundary and chunk_end < len(text):
                    # 연락처 근처에서는 더 큰 겹침 사용
                    overlap = max_overlap
                    print(f"📞 연락처 패턴 감지, 큰 겹침 적용: {org_name}")
                else:
                    overlap = min_overlap
                
                chunk = text[chunk_start:chunk_end]
                
                if len(chunk.strip()) > 50:  # 의미있는 길이만
                    chunks.append(chunk)
                
                # 다음 청크 시작점 계산
                i = chunk_end - overlap if chunk_end < len(text) else len(text)
            
            print(f"📊 지능형 청킹 완료: {len(chunks)}개 청크 생성")
            return chunks
            
        except Exception as e:
            print(f"⚠️ 지능형 청킹 실패, 기본 청킹 사용: {org_name} - {e}")
            # 폴백: 기본 청킹
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-200)]

    def needs_additional_crawling(self, json_info):
        """추가 크롤링이 필요한지 판단"""
        missing_count = 0
        
        if not json_info.get('phone'):
            missing_count += 1
        if not json_info.get('fax'):
            missing_count += 1
        if not json_info.get('email'):
            missing_count += 1
        if not json_info.get('address'):
            missing_count += 1
        
        # 2개 이상 정보가 부족하면 크롤링 수행
        return missing_count >= 2
    
    def format_final_result(self, org_data, merged_data):
        """최종 결과 포맷팅"""
        org_name = org_data.get('name', 'Unknown')
        homepage_url = org_data.get('homepage', '')
        
        result = {
            '기관명': org_name,
            '홈페이지': homepage_url,
            '주소': '정보확인 안됨',
            '우편번호': '정보확인 안됨',
            '전화번호': '정보확인 안됨',
            '팩스번호': '정보확인 안됨',
            '이메일': '정보확인 안됨',
            '추출방법': 'JSON',
            '추출상태': '성공'
        }
        
        # 검증 및 정제
        validated_phones, validated_faxes = self.validate_and_clean_contacts(
            merged_data.get('phone', []), merged_data.get('fax', [])
        )
        
        # 결과 적용
        if validated_phones:
            result['전화번호'] = validated_phones[0]
            self.stats['phone_found'] += 1
        
        if validated_faxes:
            result['팩스번호'] = validated_faxes[0]
            self.stats['fax_found'] += 1
        
        if merged_data.get('email'):
            result['이메일'] = merged_data['email'][0]
            self.stats['email_found'] += 1
        
        if merged_data.get('address'):
            result['주소'] = merged_data['address'][0]
            self.stats['address_found'] += 1
        
        if merged_data.get('postal_code'):
            result['우편번호'] = merged_data['postal_code'][0]
            self.stats['postal_code_found'] += 1
        
        # 추출방법 결정
        json_only = not self.needs_additional_crawling(self.extract_from_json_data(org_data))
        if json_only:
            result['추출방법'] = 'JSON만'
            self.stats['json_info_used'] += 1
        else:
            result['추출방법'] = 'JSON+크롤링'
        
        return result

    def save_to_excel_simple(self, results, output_filename=None):
        """결과를 Excel 파일로 저장"""
        if not results:
            print("❌ 저장할 데이터가 없습니다.")
            return None
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"homepage_details_{timestamp}.xlsx"
        
        try:
            df = pd.DataFrame(results)
            
            # 컬럼 순서 정리
            column_order = [
                '기관명', '홈페이지', '주소', 
                '전화번호1', '전화번호2', 
                '팩스번호1', '팩스번호2',
                '이메일1', '이메일2', '추출상태'
            ]
            
            df = df[column_order]
            df.to_excel(output_filename, index=False, engine='openpyxl')
            
            print(f"💾 Excel 파일 저장 완료: {output_filename}")
            print(f"📊 총 {len(results)}개 기관 데이터 저장")
            
            return output_filename
            
        except Exception as e:
            print(f"❌ Excel 저장 오류: {str(e)}")
            return None
    
    # 🔄 기존 process_json_file_async 메서드에서 드라이버 정리 추가
    async def process_json_file_async(self, json_file_path, test_mode=False, test_count=10):
        """JSON 파일 전체 처리 (URL 검색 포함)"""
        print(f"📂 JSON 파일 로드: {json_file_path}")
        
        try:
            data = FileUtils.load_json(json_file_path)
            if not data:
                print("❌ JSON 파일 로드 실패")
                return None
            
            # 데이터 구조 확인 및 변환 (기존 로직)
            all_organizations = []
            
            if isinstance(data, dict):
                print(f"📊 카테고리별 데이터 구조 감지:")
                for category, organizations in data.items():
                    if isinstance(organizations, list):
                        print(f"   📂 {category}: {len(organizations)}개 기관")
                        for org in organizations:
                            org['category'] = category
                        all_organizations.extend(organizations)
                    else:
                        print(f"   ⚠️ {category}: 리스트가 아닌 데이터 타입 ({type(organizations)})")
            elif isinstance(data, list):
                print(f"📊 리스트 데이터 구조 감지")
                all_organizations = data
            else:
                print(f"❌ 지원하지 않는 데이터 구조: {type(data)}")
                return None
            
            total_count = len(all_organizations)
            process_count = min(test_count, total_count) if test_mode else total_count
            
            print(f"📊 총 {total_count}개 기관 중 {process_count}개 처리 예정")
            print(f"🌐 URL 검색 기능: {'활성화' if self.use_selenium else '비활성화'}")
            if test_mode:
                print(f"🧪 테스트 모드: 처음 {process_count}개만 처리")
            
            results = []
            
            for i, org_data in enumerate(all_organizations[:process_count]):
                print(f"\n🔄 진행률: {i+1}/{process_count} ({((i+1)/process_count)*100:.1f}%)")
                
                result = await self.process_single_organization_enhanced(org_data)
                results.append(result)
                
                self.stats['total_processed'] += 1
                
                # 진행 상황 출력
                if (i + 1) % 5 == 0:
                    self.print_progress_stats()
            
            self.merged_results = results
            return results
            
        except Exception as e:
            print(f"❌ 파일 처리 오류: {str(e)}")
            return None
        finally:
            # 🆕 드라이버 정리
            self.close_selenium_driver()
    
    def categorize_results(self, results):
        """결과를 카테고리별로 분류"""
        categorized = {
            'churches': [],
            'taekwondo_centers': [],
            'youth_centers': [],
            'educational_institutions': [],
            'other_organizations': []
        }
        
        for result in results:
            category = result.get('category', 'other_organizations')
            if category in categorized:
                # 카테고리 정보 제거 후 추가
                result_copy = result.copy()
                result_copy.pop('category', None)
                categorized[category].append(result_copy)
            else:
                categorized['other_organizations'].append(result)
        
        return categorized
    
    def save_merged_results_to_json(self, results, filename=None):
        """병합된 결과를 JSON으로 저장"""
        if not filename:
            # ✅ 수정: FileUtils 활용
            filename = FileUtils.create_timestamped_filename("enhanced_contact_data")
        
        try:
            # 카테고리별로 재분류 (기존 로직 유지)
            categorized_data = self.categorize_results(results)
            
            # ✅ 수정: FileUtils 활용
            success = FileUtils.save_json(categorized_data, filename, backup=False)
            
            if success:
                print(f"💾 병합된 JSON 파일 저장: {filename}")
                return filename
            else:
                print(f"❌ JSON 저장 실패")
                return None
                
        except Exception as e:
            print(f"❌ JSON 저장 실패: {e}")
            return None
    
    def create_final_excel_report(self, results, output_filename=None):
        """최종 종합 Excel 리포트 생성"""
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"enhanced_contact_report_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                # 메인 데이터 시트
                df_main = pd.DataFrame(results)
                
                # 컬럼 순서 정리
                column_order = [
                    '기관명', '홈페이지', '주소', '우편번호',
                    '전화번호', '팩스번호', '이메일', 
                    '추출방법', '추출상태'
                ]
                
                # 존재하는 컬럼만 선택
                available_columns = [col for col in column_order if col in df_main.columns]
                df_main = df_main[available_columns]
                
                df_main.to_excel(writer, sheet_name='연락처정보', index=False)
                
                # 통계 시트
                total = max(self.stats['total_processed'], 1)
                stats_data = [
                    ['항목', '개수', '비율(%)'],
                    ['총 기관 수', self.stats['total_processed'], 100.0],
                    ['전화번호 보유', self.stats['phone_found'], 
                     round(self.stats['phone_found']/total*100, 1)],
                    ['팩스번호 보유', self.stats['fax_found'], 
                     round(self.stats['fax_found']/total*100, 1)],
                    ['이메일 보유', self.stats['email_found'], 
                     round(self.stats['email_found']/total*100, 1)],
                    ['주소 보유', self.stats['address_found'], 
                     round(self.stats['address_found']/total*100, 1)],
                    ['우편번호 보유', self.stats['postal_code_found'], 
                     round(self.stats['postal_code_found']/total*100, 1)],
                    ['JSON만 사용', self.stats['json_info_used'], 
                     round(self.stats['json_info_used']/total*100, 1)],
                    ['크롤링 수행', self.stats['crawling_performed'], 
                     round(self.stats['crawling_performed']/total*100, 1)],
                    ['AI 호출 횟수', self.stats['api_calls_made'], '-'],
                    ['중복 제거', self.stats['duplicates_removed'], '-']
                ]
                
                df_stats = pd.DataFrame(stats_data[1:], columns=stats_data[0])
                df_stats.to_excel(writer, sheet_name='통계', index=False)
                
                # 추출방법별 분류 시트
                method_summary = {}
                for result in results:
                    method = result.get('추출방법', 'Unknown')
                    method_summary[method] = method_summary.get(method, 0) + 1
                
                df_methods = pd.DataFrame(list(method_summary.items()), 
                                        columns=['추출방법', '기관수'])
                df_methods.to_excel(writer, sheet_name='추출방법별', index=False)
            
            print(f"📊 최종 Excel 리포트 생성 완료: {output_filename}")
            return output_filename
            
        except Exception as e:
            print(f"❌ Excel 리포트 생성 실패: {e}")
            return None
    
    def create_comprehensive_report(self, results):
        """종합 리포트 생성 (JSON + Excel)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n📋 종합 리포트 생성 중...")
        
        # 1. JSON 파일 저장
        json_file = self.save_merged_results_to_json(results, 
                                                   f"enhanced_final_data_{timestamp}.json")
        
        # 2. Excel 리포트 생성
        excel_file = self.create_final_excel_report(results, 
                                                   f"enhanced_final_report_{timestamp}.xlsx")
        
        return json_file, excel_file
    
    # 🔄 통계 출력 메서드 수정
    def print_progress_stats(self):
        """진행 상황 통계 출력 (URL 검색 포함)"""
        print(f"\n📈 현재 진행 상황:")
        print(f"   🔄 처리 완료: {self.stats['total_processed']}개")
        print(f"   🔍 URL 검색 수행: {self.stats['url_search_performed']}개")
        print(f"   🌐 URL 발견: {self.stats['url_found']}개")
        print(f"   📋 JSON 정보 활용: {self.stats['json_info_used']}개")
        print(f"   🌐 추가 크롤링: {self.stats['crawling_performed']}개")
        print(f"   📞 전화번호 발견: {self.stats['phone_found']}개")
        print(f"   📠 팩스번호 발견: {self.stats['fax_found']}개")
        print(f"   📧 이메일 발견: {self.stats['email_found']}개")
        print(f"   🏠 주소 발견: {self.stats['address_found']}개")
        print(f"   📮 우편번호 발견: {self.stats['postal_code_found']}개")
        print(f"   🗑️ 중복 제거: {self.stats['duplicates_removed']}개")
        if self.use_ai:
            print(f"   🤖 AI 호출: {self.stats['api_calls_made']}회")
            print(f"   🤖 AI 보완: {self.stats['ai_enhanced']}회")
    
    def print_final_stats(self):
        """최종 통계 출력 (URL 검색 포함)"""
        print(f"\n🎉 처리 완료! 최종 통계:")
        print(f"=" * 60)
        total = max(self.stats['total_processed'], 1)
        print(f"📊 총 처리: {self.stats['total_processed']}개 기관")
        print(f"🔍 URL 검색 수행: {self.stats['url_search_performed']}개 ({(self.stats['url_search_performed']/total)*100:.1f}%)")
        print(f"🌐 URL 발견률: {(self.stats['url_found']/max(self.stats['url_search_performed'], 1))*100:.1f}%")
        print(f"📋 JSON 정보만 사용: {self.stats['json_info_used']}개 ({(self.stats['json_info_used']/total)*100:.1f}%)")
        print(f"🌐 추가 크롤링 수행: {self.stats['crawling_performed']}개 ({(self.stats['crawling_performed']/total)*100:.1f}%)")
        print(f"📞 전화번호 발견률: {(self.stats['phone_found']/total)*100:.1f}%")
        print(f"📠 팩스번호 발견률: {(self.stats['fax_found']/total)*100:.1f}%")
        print(f"📧 이메일 발견률: {(self.stats['email_found']/total)*100:.1f}%")
        print(f"🏠 주소 발견률: {(self.stats['address_found']/total)*100:.1f}%")
        print(f"📮 우편번호 발견률: {(self.stats['postal_code_found']/total)*100:.1f}%")
        print(f"🗑️ 중복 제거: {self.stats['duplicates_removed']}개")
        if self.use_ai:
            print(f"🤖 총 AI 호출: {self.stats['api_calls_made']}회")
            print(f"🤖 AI 보완 성공: {self.stats['ai_enhanced']}회")
        print(f"=" * 60)

# 라이브러리 사용 예시 함수
# 🔄 라이브러리 인터페이스 함수 수정
async def extract_enhanced_details_async(json_file_path, api_key=None, test_mode=False, test_count=10, use_selenium=True, headless=False):
    """
    향상된 상세 정보 추출 함수 (URL 검색 기능 포함)
    
    Args:
        json_file_path: JSON 파일 경로
        api_key: Gemini API 키 (선택사항)
        test_mode: 테스트 모드 여부
        test_count: 테스트 모드시 처리할 기관 수
        use_selenium: Selenium 사용 여부 (URL 검색용)
        headless: 헤드리스 모드 여부
    
    Returns:
        tuple: (결과 리스트, JSON 파일명, Excel 파일명, 통계 정보)
    """
    print("🚀 Enhanced Detail Extractor 시작 (URL 검색 + 크롤링)")
    print("=" * 60)
    
    # 추출기 초기화 (URL 검색 기능 포함)
    extractor = EnhancedDetailExtractor(api_key=api_key, use_selenium=use_selenium, headless=headless)
    
    start_time = time.time()
    
    # 처리 실행
    results = await extractor.process_json_file_async(json_file_path, test_mode=test_mode, test_count=test_count)
    
    if results:
        # 종합 리포트 생성
        json_file, excel_file = extractor.create_comprehensive_report(results)
        
        # 최종 통계 출력
        extractor.print_final_stats()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"⏱️ 총 소요 시간: {elapsed_time:.1f}초")
        
        return results, json_file, excel_file, extractor.stats
    else:
        print("❌ 처리 실패")
        return None, None, None, extractor.stats

def extract_enhanced_details(json_file_path, api_key=None, test_mode=False, test_count=10, use_selenium=True, headless=False):
    """
    향상된 상세 정보 추출 함수 (URL 검색 + 크롤링)
    """
    return asyncio.run(extract_enhanced_details_async(
        json_file_path, api_key, test_mode, test_count, use_selenium, headless
    ))

def main():
    """메인 실행 함수 (독립 실행용)"""
    print("🏠 Enhanced Detail Extractor")
    print("=" * 60)
    
    # .env에서 API 키 확인
    api_key_from_env = os.getenv('GEMINI_API_KEY')
    if api_key_from_env:
        print(f"🔑 .env에서 API 키 발견: {api_key_from_env[:10]}...")
        use_env_key = input("🤖 .env의 API 키를 사용하시겠습니까? (Y/n): ").strip().lower()
        if use_env_key in ['', 'y', 'yes']:
            api_key = None  # None이면 __init__에서 환경변수 사용
        else:
            api_key = input("Gemini API 키를 직접 입력하세요: ").strip() or None
    else:
        print("⚠️ .env에서 GEMINI_API_KEY를 찾을 수 없습니다.")
        api_key = input("Gemini API 키를 입력하세요 (엔터 시 정규식 전용 모드): ").strip() or None
    
    # JSON 파일 경로 입력
    json_file = input("JSON 파일 경로를 입력하세요: ").strip()
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return
    
    # 테스트 모드 선택
    test_mode = input("테스트 모드로 실행하시겠습니까? (y/N): ").strip().lower() == 'y'
    test_count = 10
    if test_mode:
        try:
            test_count = int(input(f"테스트할 기관 수를 입력하세요 (기본값: {test_count}): ").strip() or test_count)
        except ValueError:
            test_count = 10
    
    # 라이브러리 함수 호출
    results, json_file, excel_file, stats = extract_enhanced_details(
        json_file, api_key=api_key, test_mode=test_mode, test_count=test_count
    )
    
    if json_file and excel_file:
        print(f"\n📁 최종 결과 파일들:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📊 Excel: {excel_file}")
    else:
        print(f"\n❌ 파일 생성 실패")

if __name__ == "__main__":
    main() 


# # // ... existing imports ...

# # ai_helpers.py의 AIModelManager 활용
# from ai_helpers import AIModelManager, extract_with_gemini_text

# # constants.py에서 AI 관련 설정 import
# from constants import (
#     AI_MODEL_CONFIG, 
#     TPM_LIMITS, 
#     CRAWLING_CONFIG,
#     EXCLUDE_DOMAINS,
#     EXCLUDE_URL_PATTERNS
# )

# class EnhancedDetailExtractor:
#     """Gemini 1.5-flash 제약사항을 고려한 지능형 웹 분석 추출기"""
    
#     def __init__(self, api_key=None, use_selenium=True, headless=False):
#         """초기화 (AI 제약사항 고려)"""
#         # 기존 초기화 코드...
#         self.session = CrawlerUtils.setup_requests_session()
#         self.validator = ContactValidator()
        
#         # 🔧 개선: constants.py의 TPM 설정 사용
#         self.tpm_manager = TPMManager(requests_per_minute=TPM_LIMITS["requests_per_minute"])
        
#         # 🔧 개선: ai_helpers.py의 AIModelManager 활용
#         self.ai_model_manager = None
#         if api_key or os.getenv('GEMINI_API_KEY'):
#             try:
#                 self.ai_model_manager = AIModelManager()
#                 self.use_ai = True
#                 self.use_ai_web_analysis = True
#                 print("🤖 AI 모델 관리자 초기화 성공 (ai_helpers.py 기반)")
#             except Exception as e:
#                 print(f"❌ AI 모델 관리자 초기화 실패: {e}")
#                 self.ai_model_manager = None
#                 self.use_ai = False
#                 self.use_ai_web_analysis = False
#         else:
#             self.use_ai = False
#             self.use_ai_web_analysis = False
#             print("🔧 정규식 전용 모드 (API 키 없음)")
        
#         # 🆕 Gemini 1.5-flash 제약사항 고려한 설정
#         self.max_input_tokens = 30000  # 32K 토큰 제한의 안전 마진
#         self.max_html_chars = 60000    # 대략 30K 토큰에 해당 (한글 기준)
#         self.max_text_chars = 15000    # 연락처 추출용 텍스트 제한
        
#         # Selenium 관련 설정
#         self.use_selenium = use_selenium
#         self.headless = headless
#         self.driver = None
#         self.exclude_domains = EXCLUDE_DOMAINS
        
#         # 기존 통계 정보에 AI 관련 추가
#         self.stats = {
#             'total_processed': 0,
#             'json_info_used': 0,
#             'crawling_performed': 0,
#             'url_search_performed': 0,
#             'url_found': 0,
#             'phone_found': 0,
#             'fax_found': 0,
#             'email_found': 0,
#             'address_found': 0,
#             'postal_code_found': 0,
#             'ai_enhanced': 0,
#             'duplicates_removed': 0,
#             'api_calls_made': 0,
#             'token_limit_exceeded': 0,  # 🆕 토큰 제한 초과 횟수
#             'tpm_wait_count': 0,        # 🆕 TPM 대기 횟수
#         }
        
#         self.ai_logger = LoggerUtils.setup_ai_logger()
#         self.patterns = {
#             'phone': PHONE_EXTRACTION_PATTERNS,
#             'fax': FAX_EXTRACTION_PATTERNS,
#             'email': EMAIL_EXTRACTION_PATTERNS,
#             'address': ADDRESS_EXTRACTION_PATTERNS
#         }
        
#         self.merged_results = []

#     # 🔧 개선: 토큰 수 계산 및 제한 함수
#     def estimate_token_count(self, text: str) -> int:
#         """텍스트의 대략적인 토큰 수 추정"""
#         # 한글/한자: 1글자 ≈ 1.5토큰, 영문: 1단어 ≈ 1토큰, 특수문자 고려
#         korean_chars = len(re.findall(r'[가-힣]', text))
#         english_words = len(re.findall(r'[a-zA-Z]+', text))
#         other_chars = len(text) - korean_chars - sum(len(word) for word in re.findall(r'[a-zA-Z]+', text))
        
#         estimated_tokens = int(korean_chars * 1.5 + english_words + other_chars * 0.5)
#         return estimated_tokens

#     def truncate_text_by_tokens(self, text: str, max_tokens: int = None) -> str:
#         """토큰 수 제한에 맞춰 텍스트 자르기"""
#         if max_tokens is None:
#             max_tokens = self.max_input_tokens
        
#         current_tokens = self.estimate_token_count(text)
        
#         if current_tokens <= max_tokens:
#             return text
        
#         # 토큰 수가 초과하면 비율로 자르기
#         ratio = max_tokens / current_tokens * 0.9  # 안전 마진 10%
#         target_length = int(len(text) * ratio)
        
#         # 앞부분 70%, 뒷부분 30%로 나누어 중요 정보 보존
#         front_length = int(target_length * 0.7)
#         back_length = target_length - front_length
        
#         if back_length > 0:
#             truncated = text[:front_length] + "\n... (중간 생략) ...\n" + text[-back_length:]
#         else:
#             truncated = text[:target_length]
        
#         self.stats['token_limit_exceeded'] += 1
#         print(f"⚠️ 토큰 제한으로 텍스트 축소: {current_tokens} → {self.estimate_token_count(truncated)} 토큰")
        
#         return truncated

#     # 🔧 개선: TPM 관리 클래스 (constants.py 설정 사용)
#     async def wait_for_tpm_limit(self):
#         """TPM 제한 준수를 위한 대기"""
#         await self.tpm_manager.wait_if_needed()
#         self.stats['tpm_wait_count'] += 1

#     # 🔧 개선: AI 기반 홈페이지 검색 (토큰 제한 고려)
#     async def search_homepage_url_with_ai_analysis(self, organization_name: str) -> str:
#         """Gemini AI 기반 지능형 홈페이지 검색 (제약사항 고려)"""
#         if not self.use_selenium or not self.ai_model_manager:
#             print(f"⚠️ Selenium 또는 AI 비활성화됨: {organization_name}")
#             return ""
        
#         if not self.driver:
#             self.setup_selenium_driver()
        
#         if not self.driver:
#             print(f"⚠️ 드라이버 초기화 실패: {organization_name}")
#             return ""
        
#         try:
#             # 검색 쿼리들 (더 제한적으로)
#             search_queries = [
#                 f'{organization_name} 홈페이지',
#                 f'{organization_name} site:or.kr',
#                 f'{organization_name} 공식사이트'
#             ]
            
#             for i, query in enumerate(search_queries, 1):
#                 print(f"🔍 AI 검색 {i}/{len(search_queries)}: {query}")
                
#                 result_url = await self._perform_ai_guided_search_optimized(query, organization_name)
#                 if result_url:
#                     self.stats['url_found'] += 1
#                     return result_url
                
#                 # TPM 제한 고려한 지연
#                 if i < len(search_queries):
#                     await asyncio.sleep(3)
            
#             return ""
            
#         except Exception as e:
#             print(f"❌ AI 기반 검색 실패 ({organization_name}): {e}")
#             return ""

#     async def _perform_ai_guided_search_optimized(self, query: str, organization_name: str) -> str:
#         """최적화된 AI 가이드 검색 (토큰 제한 고려)"""
#         try:
#             # 1. 네이버 검색 실행
#             self.driver.get('https://www.naver.com')
#             time.sleep(2)
            
#             search_box = WebDriverWait(self.driver, 10).until(
#                 EC.presence_of_element_located((By.ID, "query"))
#             )
            
#             search_box.clear()
#             search_box.send_keys(query)
#             search_box.send_keys(Keys.RETURN)
#             time.sleep(4)
            
#             # 2. 페이지 소스 획득 및 전처리
#             page_source = self.driver.page_source
            
#             # 3. HTML을 토큰 제한에 맞게 전처리
#             processed_html = self._preprocess_html_for_ai(page_source)
            
#             # 4. AI 분석 (토큰 제한 고려)
#             if self.use_ai_web_analysis and processed_html:
#                 homepage_url = await self._analyze_search_results_optimized(
#                     processed_html, organization_name, query
#                 )
#                 if homepage_url:
#                     return homepage_url
            
#             # 5. 폴백: 기존 방식
#             print(f"⚠️ AI 분석 실패, 폴백 실행: {organization_name}")
#             return self._fallback_search_method(organization_name)
            
#         except Exception as e:
#             print(f"❌ 최적화된 AI 검색 오류: {e}")
#             return ""

#     def _preprocess_html_for_ai(self, html_content: str) -> str:
#         """AI 분석을 위한 HTML 전처리 (토큰 제한 고려)"""
#         try:
#             soup = BeautifulSoup(html_content, 'html.parser')
            
#             # 불필요한 태그 제거
#             for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'comment']):
#                 tag.decompose()
            
#             # 검색 결과 영역만 추출
#             main_content = ""
#             for selector in ['.main_pack', '.content_area', '.result_area', '.search_area', '.api_subject_bx']:
#                 element = soup.select_one(selector)
#                 if element:
#                     main_content = str(element)
#                     break
            
#             if not main_content:
#                 # 메인 영역을 찾지 못하면 body 전체 사용
#                 body = soup.find('body')
#                 main_content = str(body) if body else html_content
            
#             # 토큰 제한에 맞춰 텍스트 축소
#             processed_content = self.truncate_text_by_tokens(main_content, self.max_input_tokens - 1000)  # 프롬프트 여유분
            
#             return processed_content
            
#         except Exception as e:
#             print(f"⚠️ HTML 전처리 오류: {e}")
#             # 오류 시 원본 텍스트를 안전하게 자르기
#             return self.truncate_text_by_tokens(html_content, self.max_input_tokens - 1000)

#     async def _analyze_search_results_optimized(self, html_content: str, organization_name: str, query: str) -> str:
#         """최적화된 AI HTML 분석 (ai_helpers.py 활용)"""
#         if not self.ai_model_manager:
#             return ""
        
#         try:
#             # TPM 제한 대기
#             await self.wait_for_tpm_limit()
            
#             # 간결한 프롬프트 생성
#             prompt_template = self._create_optimized_html_analysis_prompt(organization_name, query)
            
#             # ai_helpers.py의 extract_with_gemini_text 활용
#             result_text = await extract_with_gemini_text(html_content, prompt_template)
            
#             self.stats['api_calls_made'] += 1
            
#             if result_text:
#                 # 응답 파싱
#                 homepage_url = self._parse_ai_html_response_optimized(result_text, organization_name)
                
#                 if homepage_url:
#                     print(f"🤖 AI가 발견한 홈페이지: {organization_name} -> {homepage_url}")
#                     return homepage_url
            
#             return ""
            
#         except Exception as e:
#             print(f"❌ 최적화된 AI HTML 분석 오류 ({organization_name}): {e}")
#             return ""

#     def _create_optimized_html_analysis_prompt(self, organization_name: str, query: str) -> str:
#         """최적화된 HTML 분석 프롬프트 (토큰 절약)"""
#         prompt = f"""네이버 검색 결과에서 '{organization_name}'의 공식 홈페이지 URL을 찾아주세요.

# 검색어: {query}
# 기관명: {organization_name}

# 규칙:
# 1. 공식 홈페이지만 선택 (.or.kr, .go.kr, .ac.kr, .org, .church 우선)
# 2. 블로그, 카페, SNS 제외
# 3. 기관명 포함 도메인 우선

# 응답 형식:
# URL: [홈페이지 URL 또는 "없음"]

# HTML:
# {{text_content}}

# 위 HTML에서 '{organization_name}'의 공식 홈페이지 URL을 찾아주세요."""

#         return prompt

#     def _parse_ai_html_response_optimized(self, ai_response: str, organization_name: str) -> str:
#         """최적화된 AI HTML 분석 응답 파싱"""
#         try:
#             lines = ai_response.split('\n')
            
#             for line in lines:
#                 line = line.strip()
                
#                 # URL 라인 찾기
#                 if line.startswith('URL:') or line.startswith('url:'):
#                     url_part = line.split(':', 1)[1].strip()
#                     if url_part and url_part != "없음" and url_part.startswith(('http://', 'https://')):
#                         if self._is_valid_homepage_url(url_part, organization_name):
#                             return url_part
                
#                 # 직접 URL 패턴 찾기
#                 elif line.startswith(('http://', 'https://')):
#                     if self._is_valid_homepage_url(line, organization_name):
#                         return line
            
#             return ""
            
#         except Exception as e:
#             print(f"❌ 최적화된 AI 응답 파싱 오류 ({organization_name}): {e}")
#             return ""

#     # 🔧 개선: 연락처 추출도 토큰 제한 고려
#     async def crawl_and_extract_with_ai_optimized(self, org_data):
#         """최적화된 AI 기반 크롤링 및 추출"""
#         org_name = org_data.get('name', 'Unknown')
#         homepage_url = org_data.get('homepage', '')
        
#         if not homepage_url or homepage_url == '정보확인 안됨':
#             return {}
        
#         # 홈페이지 크롤링
#         homepage_text = self.crawl_homepage_if_needed(homepage_url, org_name)
        
#         if not homepage_text:
#             return {}
        
#         # 텍스트 길이 제한 (연락처 추출용)
#         if len(homepage_text) > self.max_text_chars:
#             # Footer 우선 추출 시도
#             soup = BeautifulSoup(homepage_text, 'html.parser')
#             footer = soup.find('footer')
#             contact_section = soup.find(['section', 'div'], class_=re.compile(r'contact|연락처', re.I))
            
#             if footer:
#                 homepage_text = footer.get_text(separator=' ', strip=True)
#             elif contact_section:
#                 homepage_text = contact_section.get_text(separator=' ', strip=True)
#             else:
#                 homepage_text = homepage_text[:self.max_text_chars]
            
#             print(f"📏 연락처 추출용 텍스트 제한: {org_name} ({len(homepage_text)} 문자)")
        
#         # AI 기반 정보 추출
#         if self.use_ai and self.ai_model_manager:
#             ai_results = await self._extract_contact_with_optimized_ai(
#                 homepage_text, org_name, homepage_url
#             )
#             return ai_results
#         else:
#             # AI 없으면 기존 정규식 방식
#             return self.extract_contact_info_sync(homepage_text, org_name)

#     async def _extract_contact_with_optimized_ai(self, text: str, org_name: str, homepage_url: str):
#         """최적화된 AI 기반 연락처 추출"""
#         try:
#             # TPM 제한 대기
#             await self.wait_for_tpm_limit()
            
#             # 토큰 제한 고려한 텍스트 전처리
#             processed_text = self.truncate_text_by_tokens(text, self.max_input_tokens - 800)  # 프롬프트 여유분
            
#             # 간결한 프롬프트 템플릿
#             prompt_template = f"""'{org_name}' 연락처 정보를 추출하세요.

# 기관명: {org_name}
# 홈페이지: {homepage_url}

# 추출 규칙:
# - 한국 전화번호만 (02-1234-5678 형식)
# - 유효한 이메일만
# - 완전한 주소만
# - 정보 없으면 "없음"

# 형식:
# 전화번호: [번호 또는 "없음"]
# 팩스번호: [번호 또는 "없음"]  
# 이메일: [이메일 또는 "없음"]
# 주소: [주소 또는 "없음"]
# 우편번호: [우편번호 또는 "없음"]

# 텍스트:
# {{text_content}}

# 정확한 연락처만 추출하세요."""

#             # ai_helpers.py 활용
#             result_text = await extract_with_gemini_text(processed_text, prompt_template)
            
#             self.stats['api_calls_made'] += 1
            
#             if result_text:
#                 contact_info = self._parse_advanced_ai_response(result_text)
                
#                 if contact_info:
#                     self.stats['ai_enhanced'] += 1
#                     print(f"🤖 AI 연락처 추출 성공: {org_name}")
                
#                 return contact_info
            
#             return {}
            
#         except Exception as e:
#             print(f"❌ 최적화된 AI 추출 오류 ({org_name}): {e}")
#             return {}

#     # 🔧 기존 메서드들은 그대로 유지...
#     def _parse_advanced_ai_response(self, ai_response: str) -> dict:
#         """고급 AI 응답 파싱"""
#         result = {
#             'phone': [],
#             'fax': [],
#             'email': [],
#             'address': [],
#             'postal_code': []
#         }
        
#         try:
#             lines = ai_response.split('\n')
            
#             for line in lines:
#                 line = line.strip()
#                 if ':' in line:
#                     key, value = line.split(':', 1)
#                     key = key.strip().lower()
#                     value = value.strip()
                    
#                     if value and value != "없음":
#                         if '전화번호' in key or 'phone' in key:
#                             result['phone'].append(value)
#                         elif '팩스' in key or 'fax' in key:
#                             result['fax'].append(value)
#                         elif '이메일' in key or 'email' in key:
#                             result['email'].append(value)
#                         elif '주소' in key or 'address' in key:
#                             result['address'].append(value)
#                         elif '우편번호' in key or 'postal' in key:
#                             result['postal_code'].append(value)
            
#             return result
            
#         except Exception as e:
#             print(f"❌ 고급 AI 응답 파싱 오류: {e}")
#             return result

#     # 🔧 개선: 메인 처리 함수 수정
#     async def process_single_organization_enhanced(self, org_data):
#         """완전히 최적화된 단일 기관 처리"""
#         org_name = org_data.get('name', 'Unknown')
#         homepage_url = org_data.get('homepage', '')
        
#         try:
#             start_time = time.time()
            
#             # 1. 홈페이지 URL 확인/AI 검색
#             if not homepage_url or homepage_url == '정보확인 안됨' or not homepage_url.startswith(('http://', 'https://')):
#                 print(f"🤖 AI 홈페이지 검색: {org_name}")
#                 homepage_url = await self.search_homepage_url_with_ai_analysis(org_name)
#                 self.stats['url_search_performed'] += 1
                
#                 if homepage_url:
#                     org_data['homepage'] = homepage_url
#                     print(f"✅ AI 발견: {org_name} -> {homepage_url}")
#                 else:
#                     print(f"❌ 홈페이지 없음: {org_name}")
#             else:
#                 print(f"📋 기존 홈페이지: {org_name}")
            
#             # 2. JSON 데이터 추출
#             json_info = self.extract_from_json_data(org_data)
            
#             # 3. 필요시 AI 크롤링
#             ai_info = {}
#             if homepage_url and homepage_url.startswith(('http://', 'https://')):
#                 if self.needs_additional_crawling(json_info):
#                     print(f"🌐 AI 크롤링: {org_name}")
                    
#                     try:
#                         ai_info = await asyncio.wait_for(
#                             self.crawl_and_extract_with_ai_optimized(org_data), 
#                             timeout=CRAWLING_CONFIG["async_timeout"]
#                         )
#                     except asyncio.TimeoutError:
#                         print(f"⏰ AI 크롤링 시간 초과: {org_name}")
#                         ai_info = {}
#                 else:
#                     print(f"📋 JSON 충분: {org_name}")
            
#             # 4. 데이터 병합 및 결과 포맷팅
#             merged_data = self.merge_contact_data(json_info, ai_info)
#             final_result = self.format_final_result(org_data, merged_data)
            
#             elapsed_time = time.time() - start_time
#             print(f"✅ AI 처리 완료: {org_name} - {elapsed_time:.1f}초")
            
#             return final_result
            
#         except Exception as e:
#             print(f"❌ AI 처리 실패 ({org_name}): {str(e)[:100]}...")
#             return {
#                 '기관명': org_name,
#                 '홈페이지': homepage_url,
#                 '주소': '정보확인 안됨',
#                 '우편번호': '정보확인 안됨',
#                 '전화번호': '정보확인 안됨',
#                 '팩스번호': '정보확인 안됨',
#                 '이메일': '정보확인 안됨',
#                 '추출방법': '실패',
#                 '추출상태': '실패'
#             }

#     # 🔧 개선: 통계 출력에 토큰/TPM 정보 추가
#     def print_final_stats(self):
#         """최종 통계 출력 (토큰/TPM 제한 정보 포함)"""
#         print(f"\n🎉 AI 기반 처리 완료! 최종 통계:")
#         print(f"=" * 60)
#         total = max(self.stats['total_processed'], 1)
#         print(f"📊 총 처리: {self.stats['total_processed']}개 기관")
#         print(f"🤖 AI 웹 분석: {'활성화' if self.use_ai_web_analysis else '비활성화'}")
#         print(f"🔍 URL 검색 수행: {self.stats['url_search_performed']}개")
#         print(f"🌐 URL 발견률: {(self.stats['url_found']/max(self.stats['url_search_performed'], 1))*100:.1f}%")
#         print(f"📞 전화번호 발견률: {(self.stats['phone_found']/total)*100:.1f}%")
#         print(f"📠 팩스번호 발견률: {(self.stats['fax_found']/total)*100:.1f}%")
#         print(f"📧 이메일 발견률: {(self.stats['email_found']/total)*100:.1f}%")
#         print(f"🏠 주소 발견률: {(self.stats['address_found']/total)*100:.1f}%")
#         print(f"🗑️ 중복 제거: {self.stats['duplicates_removed']}개")
#         if self.use_ai:
#             print(f"🤖 총 AI 호출: {self.stats['api_calls_made']}회")
#             print(f"🤖 AI 보완 성공: {self.stats['ai_enhanced']}회")
#             print(f"⚠️ 토큰 제한 초과: {self.stats['token_limit_exceeded']}회")
#             print(f"⏰ TPM 대기: {self.stats['tpm_wait_count']}회")
#         print(f"=" * 60)

# // ... existing code ...
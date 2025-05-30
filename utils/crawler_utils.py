#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
크롤링 관련 유틸리티 통합
기존 3개 크롤러의 중복된 셀레니움 설정 및 검색 기능을 통합
"""

import time
import random
from typing import Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CrawlerUtils:
    """크롤링 관련 유틸리티 클래스 - 중복 제거"""
    
    @staticmethod
    def setup_driver(headless: bool = True, timeout: int = 10) -> Optional[webdriver.Chrome]:
        """
        Chrome 드라이버 설정 (통합)
        fax_crawler.py + naver_map_crawler.py + url_extractor.py 통합
        """
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # 공통 옵션들
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # 성능 최적화
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-extensions")
            
            # 로그 레벨 설정
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(timeout)
            driver.implicitly_wait(timeout)
            
            print(f"✅ Chrome 드라이버 설정 완료 (headless={headless})")
            return driver
            
        except Exception as e:
            print(f"❌ 드라이버 설정 실패: {e}")
            return None
    
    @staticmethod
    def search_google(driver: webdriver.Chrome, query: str) -> bool:
        """
        구글 검색 (통합)
        fax_crawler.py의 search_google() 기반
        """
        try:
            search_url = f"https://www.google.com/search?q={query}"
            driver.get(search_url)
            
            # 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print(f"✅ 구글 검색 완료: {query}")
            return True
            
        except TimeoutException:
            print(f"⏰ 구글 검색 타임아웃: {query}")
            return False
        except Exception as e:
            print(f"❌ 구글 검색 실패: {query}, 오류: {e}")
            return False
    
    @staticmethod
    def search_naver(driver: webdriver.Chrome, query: str) -> bool:
        """
        네이버 검색 (통합)
        url_extractor.py의 search_naver() 기반
        """
        try:
            search_url = f"https://search.naver.com/search.naver?query={query}"
            driver.get(search_url)
            
            # 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lst_total"))
            )
            
            print(f"✅ 네이버 검색 완료: {query}")
            return True
            
        except TimeoutException:
            print(f"⏰ 네이버 검색 타임아웃: {query}")
            return False
        except Exception as e:
            print(f"❌ 네이버 검색 실패: {query}, 오류: {e}")
            return False
    
    @staticmethod
    def restart_driver(driver: Optional[webdriver.Chrome], headless: bool = True) -> Optional[webdriver.Chrome]:
        """
        드라이버 재시작 (통합)
        fax_crawler.py의 restart_driver() 기반
        """
        try:
            if driver:
                driver.quit()
                print("🔄 기존 드라이버 종료")
            
            time.sleep(2)  # 안전한 재시작을 위한 대기
            new_driver = CrawlerUtils.setup_driver(headless=headless)
            
            if new_driver:
                print("✅ 드라이버 재시작 완료")
            else:
                print("❌ 드라이버 재시작 실패")
            
            return new_driver
            
        except Exception as e:
            print(f"❌ 드라이버 재시작 중 오류: {e}")
            return None
    
    @staticmethod
    def safe_close_driver(driver: Optional[webdriver.Chrome]):
        """
        안전한 드라이버 종료 (통합)
        3개 크롤러의 close() 메서드 통합
        """
        try:
            if driver:
                driver.quit()
                print("✅ 드라이버 안전 종료 완료")
        except Exception as e:
            print(f"⚠️ 드라이버 종료 중 오류 (무시됨): {e}")
    
    @staticmethod
    def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """랜덤 지연 (봇 탐지 방지)"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    @staticmethod
    def setup_requests_session() -> requests.Session:
        """
        Requests 세션 설정 (통합)
        enhanced_detail_extractor.py의 세션 설정 기반
        """
        session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # User-Agent 설정
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        return session
    
    @staticmethod
    def extract_urls_from_page(driver: webdriver.Chrome) -> List[str]:
        """페이지에서 URL 추출 (공통 기능)"""
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            urls = []
            
            for link in links:
                href = link.get_attribute("href")
                if href and href.startswith("http"):
                    urls.append(href)
            
            return list(set(urls))  # 중복 제거
            
        except Exception as e:
            print(f"❌ URL 추출 실패: {e}")
            return []
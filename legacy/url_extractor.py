#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 추출 및 홈페이지 찾기 도구 (Selenium 기반 + VPN 우회)
"""

import json
import os
import sys
import time
import random
import re
import logging
import requests
import base64
import tempfile
import subprocess
import threading
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse, unquote
from datetime import datetime

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 강화된 상수 설정
EXCLUDE_DOMAINS = [
    'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com',
    'naver.com', 'daum.net', 'google.com', 'yahoo.com',
    'blog.naver.com', 'cafe.naver.com', 'tistory.com',
    'wikipedia.org', 'namu.wiki', 'blogspot.com', 'wordpress.com'
]

# VPN 관련 상수
VPN_COUNTRIES = ['japan', 'korea', 'singapore', 'thailand', 'malaysia']
VPN_PROCESS = None
VPN_CONFIG_PATH = None

class VPNManager:
    """VPN 연결 관리 클래스"""
    
    def __init__(self):
        self.current_process = None
        self.current_config = None
        self.logger = logging.getLogger('VPNManager')
        self.available_servers = []
        self.current_server_index = 0
    
    def get_vpn_servers(self, country: str) -> List[Dict]:
        """VPN Gate에서 서버 목록 가져오기"""
        try:
            self.logger.info(f"VPN 서버 검색 중: {country}")
            vpn_data = requests.get("http://www.vpngate.net/api/iphone/", timeout=10).text.replace("\r", "")
            servers = [line.split(",") for line in vpn_data.split("\n")]
            labels = servers[1]
            labels[0] = labels[0][1:]
            servers = [s for s in servers[2:] if len(s) > 1]
            
            # 국가 매칭
            if len(country) == 2:
                i = 6  # short name for country
            elif len(country) > 2:
                i = 5  # long name for country
            else:
                return []
            
            desired = [s for s in servers if country.lower() in s[i].lower()]
            supported = [s for s in desired if len(s[-1]) > 0]
            
            # 점수 순으로 정렬
            sorted_servers = sorted(supported, key=lambda s: float(s[2].replace(",", ".")), reverse=True)
            
            server_list = []
            for server in sorted_servers[:3]:  # 상위 3개만
                server_info = {
                    'config': server[-1],
                    'score': float(server[2].replace(",", ".")),
                    'country': server[5] if len(server) > 5 else country,
                    'speed': float(server[4]) / 10**6 if len(server) > 4 else 0
                }
                server_list.append(server_info)
            
            self.logger.info(f"{country}에서 {len(server_list)}개 VPN 서버 발견")
            return server_list
            
        except Exception as e:
            self.logger.error(f"VPN 서버 목록 가져오기 실패: {e}")
            return []
    
    def connect_vpn(self, country: str) -> bool:
        """VPN 연결"""
        try:
            servers = self.get_vpn_servers(country)
            if not servers:
                return False
            
            # 기존 연결 종료
            self.disconnect_vpn()
            
            # 가장 좋은 서버 선택
            server = servers[0]
            self.logger.info(f"VPN 연결 시도: {server['country']} (점수: {server['score']})")
            
            # 임시 설정 파일 생성
            _, config_path = tempfile.mkstemp(suffix='.ovpn')
            self.current_config = config_path
            
            with open(config_path, 'w') as f:
                config_content = base64.b64decode(server['config']).decode()
                f.write(config_content)
                # Windows용 추가 설정
                f.write("\nscript-security 2\n")
            
            # OpenVPN 연결 (백그라운드)
            try:
                # Windows에서는 관리자 권한 필요할 수 있음
                self.current_process = subprocess.Popen(
                    ["openvpn", "--config", config_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 연결 대기 (최대 30초)
                for i in range(30):
                    if self.current_process.poll() is None:
                        time.sleep(1)
                        if i > 10:  # 10초 후부터는 연결된 것으로 간주
                            self.logger.info(f"VPN 연결 성공: {country}")
                            return True
                    else:
                        break
                
                self.logger.warning(f"VPN 연결 실패 또는 시간 초과: {country}")
                return False
                
            except FileNotFoundError:
                self.logger.error("OpenVPN이 설치되지 않았습니다. VPN 기능을 사용할 수 없습니다.")
                return False
            except Exception as e:
                self.logger.error(f"VPN 연결 중 오류: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"VPN 연결 실패: {e}")
            return False
    
    def disconnect_vpn(self):
        """VPN 연결 종료"""
        try:
            if self.current_process:
                self.current_process.terminate()
                # 강제 종료 대기
                for _ in range(5):
                    if self.current_process.poll() is not None:
                        break
                    time.sleep(1)
                else:
                    self.current_process.kill()
                
                self.current_process = None
                self.logger.info("VPN 연결 종료")
            
            if self.current_config and os.path.exists(self.current_config):
                os.unlink(self.current_config)
                self.current_config = None
                
        except Exception as e:
            self.logger.error(f"VPN 종료 중 오류: {e}")
    
    def __del__(self):
        """소멸자에서 VPN 연결 정리"""
        self.disconnect_vpn()

# 기존 경로 설정 뒤에 추가
# 상위 디렉토리 모듈 import (경로 설정 후)
try:
    from validator import AIValidator
    print("✅ AIValidator import 성공")
except ImportError as e:
    print(f"⚠️ AIValidator import 실패: {e}")
    print("🔧 AIValidator 없이 기본 기능만 사용합니다.")
    AIValidator = None

class URLExtractor:
    """URL 추출 및 홈페이지 검색 클래스 (Selenium 기반 + VPN 우회)"""
    
    def __init__(self, headless: bool = False):
        """초기화"""
        self.headless = headless
        self.driver = None
        self.logger = self.setup_logger()
        self.vpn_manager = VPNManager()
        
        # AI 검증기 초기화 (새로 추가)
        self.ai_validator = None
        if AIValidator:
            try:
                self.ai_validator = AIValidator()
                self.use_ai_validation = True
                print("🤖 AI 검증 기능 활성화")
            except Exception as e:
                print(f"❌ AI 검증기 초기화 실패: {e}")
                self.use_ai_validation = False
        else:
            self.use_ai_validation = False
            print("🔧 AI 검증 기능 비활성화")
        
        # 요청 간 지연 시간 (초)
        self.delay_range = (3, 6)
        
        # 검색 결과 제한
        self.max_search_results = 5
        self.max_retries = 3
        
        # VPN 우회 관련
        self.google_blocked = False
        self.vpn_countries = ['japan', 'korea', 'singapore', 'thailand', 'malaysia']
        self.current_vpn_index = 0
    
    def setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('URLExtractor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def setup_driver(self):
        """Selenium WebDriver 설정"""
        try:
            chrome_options = Options()
            
            # headless 모드 설정
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 기본 옵션들
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 자동화 탐지 우회
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # VPN 사용 시 프록시 설정 (필요시)
            # chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:1080')
            
            # 드라이버 생성
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info(f"Chrome 드라이버 설정 완료 (headless: {self.headless})")
            
        except Exception as e:
            self.logger.error(f"드라이버 설정 실패: {e}")
            raise
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("드라이버 종료 완료")
        
        # VPN 연결도 종료
        self.vpn_manager.disconnect_vpn()
    
    def is_google_blocked(self) -> bool:
        """구글에서 차단되었는지 확인"""
        try:
            page_source = self.driver.page_source.lower()
            title = self.driver.title.lower()
            
            # 차단 관련 키워드 확인
            block_keywords = [
                'unusual traffic', 'captcha', 'blocked', 'forbidden',
                'access denied', 'suspicious activity', 'automated queries',
                'robot', 'bot detected', '비정상적인 트래픽'
            ]
            
            for keyword in block_keywords:
                if keyword in page_source or keyword in title:
                    self.logger.warning(f"구글 차단 감지: {keyword}")
                    return True
            
            # CAPTCHA 요소 확인
            captcha_selectors = [
                '#captcha', '.captcha', '[data-recaptcha]',
                '.g-recaptcha', '#recaptcha'
            ]
            
            for selector in captcha_selectors:
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        self.logger.warning("CAPTCHA 감지됨")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"차단 감지 중 오류: {e}")
            return False
    
    def try_vpn_bypass(self) -> bool:
        """VPN을 통한 우회 시도"""
        try:
            self.logger.info("🔧 VPN 우회 시도 중...")
            
            # 사용 가능한 VPN 국가 순차 시도
            for country in self.vpn_countries[self.current_vpn_index:]:
                self.logger.info(f"🌏 VPN 연결 시도: {country}")
                
                if self.vpn_manager.connect_vpn(country):
                    # VPN 연결 후 잠시 대기
                    time.sleep(5)
                    
                    # 드라이버 재시작 (새로운 IP로)
                    self.close_driver()
                    time.sleep(2)
                    self.setup_driver()
                    
                    # 구글 접속 테스트
                    try:
                        self.driver.get("https://www.google.com")
                        time.sleep(3)
                        
                        if not self.is_google_blocked():
                            self.logger.info(f"✅ VPN 우회 성공: {country}")
                            self.google_blocked = False
                            return True
                        else:
                            self.logger.warning(f"❌ {country} VPN으로도 차단됨")
                            
                    except Exception as e:
                        self.logger.warning(f"VPN 연결 후 구글 접속 실패: {e}")
                
                # 다음 국가로
                self.current_vpn_index += 1
                if self.current_vpn_index >= len(self.vpn_countries):
                    self.current_vpn_index = 0
                    break
            
            self.logger.error("모든 VPN 시도 실패")
            return False
            
        except Exception as e:
            self.logger.error(f"VPN 우회 중 오류: {e}")
            return False

    def add_delay(self):
        """요청 간 지연"""
        delay = random.uniform(*self.delay_range)
        self.logger.info(f"지연 시간: {delay:.1f}초")
        time.sleep(delay)
    
    def clean_search_query(self, organization_name: str, location: str = "") -> str:
        """검색 쿼리 정제 (지역 정보 제거)"""
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
    
    def search_organization_homepage(self, organization_name: str, location: str = "") -> Optional[str]:
        """기관 홈페이지 검색 (AI 검증 포함)"""
        try:
            if not self.driver:
                self.setup_driver()
            
            candidate_urls = []
            
            # 네이버 검색 실행
            self.logger.info(f"🔍 네이버 검색 시작: {organization_name}")
            naver_urls = self._search_with_naver(organization_name)
            if naver_urls:
                self.logger.info(f"네이버에서 {len(naver_urls)}개 URL 발견")
                candidate_urls.extend([(url, 'naver') for url in naver_urls])
            
            # 검색 간 지연
            self.add_delay()
            
            # 구글 검색 실행
            self.logger.info(f"🔍 구글 검색 시작: {organization_name}")
            google_urls = self._perform_google_search(organization_name, organization_name)
            if google_urls:
                self.logger.info(f"구글에서 {len(google_urls)}개 URL 발견")
                candidate_urls.extend([(url, 'google') for url in google_urls])
            
            # AI 검증 사용 가능한 경우
            if self.use_ai_validation and candidate_urls:
                return self._select_url_with_ai_validation(candidate_urls, organization_name)
            
            # AI 없는 경우 기존 방식으로 중복 제거 및 최적 URL 선택
            if candidate_urls:
                unique_urls = list(set([url for url, source in candidate_urls]))
                best_url = self.select_best_homepage(unique_urls, organization_name)
                
                # 소스 정보 출력
                sources = [source for url, source in candidate_urls if url == best_url]
                source_info = f" (출처: {', '.join(set(sources))})" if sources else ""
                self.logger.info(f"✅ 최종 선택 URL: {best_url}{source_info}")
                
                return best_url
            
            self.logger.warning(f"❌ {organization_name}의 홈페이지를 찾지 못했습니다")
            return None
            
        except Exception as e:
            self.logger.error(f"검색 중 오류 발생: {e}")
            return None
        
    def _select_url_with_ai_validation(self, candidate_urls: List[Tuple[str, str]], 
                                     organization_name: str) -> Optional[str]:
        """AI 검증으로 최적 URL 선택"""
        import asyncio
        
        async def validate_urls():
            validated_results = []
            
            for url, source in candidate_urls[:5]:  # 최대 5개만 검증
                try:
                    # 페이지 내용 미리보기
                    page_content = self._get_page_preview(url)
                    
                    # AI 검증
                    validation = await self.ai_validator.validate_homepage_url_relevance(
                        organization_name, url, page_content, source
                    )
                    
                    if validation.get("is_relevant", False) and validation.get("confidence", 0) > 0.6:
                        validated_results.append({
                            'url': url,
                            'confidence': validation.get("confidence", 0),
                            'source': source,
                            'reasoning': validation.get("reasoning", "")
                        })
                        self.logger.info(f"✅ AI 검증 통과: {url} (신뢰도: {validation.get('confidence', 0):.2f})")
                    else:
                        self.logger.warning(f"❌ AI 검증 실패: {url} (신뢰도: {validation.get('confidence', 0):.2f})")
                
                except Exception as e:
                    self.logger.warning(f"URL 검증 중 오류: {url} - {e}")
                    continue
            
            return validated_results
        
        try:
            # 비동기 검증 실행
            validated_results = asyncio.run(validate_urls())
            
            if validated_results:
                # 신뢰도 순으로 정렬
                validated_results.sort(key=lambda x: x['confidence'], reverse=True)
                best_result = validated_results[0]
                
                self.logger.info(f"🎯 AI 검증 최종 선택: {best_result['url']} "
                               f"(신뢰도: {best_result['confidence']:.2f}, 출처: {best_result['source']})")
                
                return best_result['url']
            
            # AI 검증 실패시 기존 방식 fallback
            self.logger.warning("AI 검증 결과 없음, 기존 방식으로 fallback")
            unique_urls = list(set([url for url, source in candidate_urls]))
            return self.select_best_homepage(unique_urls, organization_name)
            
        except Exception as e:
            self.logger.error(f"AI 검증 중 오류: {e}")
            # 오류시 기존 방식 사용
            unique_urls = list(set([url for url, source in candidate_urls]))
            return self.select_best_homepage(unique_urls, organization_name)

    def _get_page_preview(self, url: str, max_chars: int = 2000) -> str:
        """페이지 내용 미리보기 (AI 검증용)"""
        try:
            original_window = self.driver.current_window_handle
            
            # 새 탭에서 페이지 로드
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            self.driver.get(url)
            time.sleep(2)
            
            # 페이지 내용 추출
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                preview = body_text[:max_chars] if len(body_text) > max_chars else body_text
            except:
                preview = ""
            
            # 원래 창으로 돌아가기
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            return preview
            
        except Exception as e:
            self.logger.warning(f"페이지 미리보기 실패: {url} - {e}")
            try:
                # 오류 시 원래 창으로 돌아가기
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return ""

    def _search_with_naver(self, organization_name: str) -> List[str]:
        """네이버 검색 실행"""
        found_urls = []
        
        search_queries = [
            f'{organization_name} 홈페이지',
            f'{organization_name} 공식사이트',
            f'{organization_name} site:or.kr',
            f'{organization_name} site:org',
            f'{organization_name}',
        ]
        
        try:
            for i, query in enumerate(search_queries, 1):
                self.logger.info(f"네이버 검색 {i}/{len(search_queries)}: {query}")
                urls = self._perform_naver_search(query, organization_name)
                if urls:
                    found_urls.extend(urls)
                    if len(found_urls) >= self.max_search_results:
                        break
                
                # 쿼리 간 짧은 지연
                time.sleep(1)
                
        except Exception as e:
            self.logger.warning(f"네이버 검색 중 오류: {e}")
        
        return list(set(found_urls))  # 중복 제거

    def _search_with_google(self, query: str, organization_name: str) -> List[str]:
        """구글 검색 수행 (VPN 우회 포함)"""
        found_urls = []
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 구글 검색 페이지로 이동
                google_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko"
                self.driver.get(google_url)
                time.sleep(3)
                
                # 차단 여부 확인
                if self.is_google_blocked():
                    self.logger.warning(f"구글 차단 감지 (시도 {attempt + 1}/{max_retries})")
                    
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면 VPN 우회
                        if self.try_vpn_bypass():
                            self.logger.info("VPN 우회 성공, 구글 검색 재시도")
                            continue
                        else:
                            self.logger.error("VPN 우회 실패")
                            break
                    else:
                        self.logger.error("모든 VPN 우회 시도 실패")
                        break
                
                # 구글 검색 결과 링크 선택자들
                link_selectors = [
                    'h3 a[href*="http"]',
                    '.g a[href*="http"]',
                    '[data-ved] a[href*="http"]',
                    '.yuRUbf a[href*="http"]',
                    '.kCrYT a[href*="http"]',
                    '.tF2Cxc a[href*="http"]',
                    '.LC20lb a[href*="http"]',
                ]
                
                for selector in link_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        self.logger.info(f"구글 선택자 '{selector}'로 {len(elements)}개 요소 발견")
                        
                        for element in elements[:15]:
                            try:
                                href = element.get_attribute('href')
                                if not href:
                                    continue
                                
                                # 구글 리다이렉트 URL 처리
                                if 'google.com' in href and '/url?q=' in href:
                                    actual_url = self._extract_google_redirect_url(href)
                                    if actual_url:
                                        href = actual_url
                                    else:
                                        continue
                                
                                # 구글 내부 링크 제외
                                if 'google.com' in href:
                                    continue
                                
                                if self.is_valid_homepage_url(href, organization_name):
                                    found_urls.append(href)
                                    self.logger.info(f"구글에서 유효한 URL 발견: {href}")
                                    
                            except Exception:
                                continue
                                
                        if found_urls:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"구글 선택자 '{selector}' 처리 중 오류: {e}")
                        continue
                
                # 결과가 있으면 성공
                if found_urls:
                    break
                else:
                    self.logger.warning(f"구글 검색에서 결과 없음 (시도 {attempt + 1})")
                    
            except Exception as e:
                self.logger.warning(f"구글 검색 실행 중 오류: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 재시도 전 대기
                continue
        
        return found_urls[:self.max_search_results]

    def _perform_naver_search(self, query: str, organization_name: str) -> List[str]:
        """실제 네이버 검색 수행 (기존 로직 개선)"""
        found_urls = []
        
        try:
            # 네이버 메인 페이지로 이동
            self.driver.get('https://www.naver.com')
            time.sleep(2)
            
            # 검색창 찾기 및 검색어 입력
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "query"))
            )
            
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # 검색 결과 로드 대기
            time.sleep(3)
            
            # 다양한 선택자로 링크 찾기
            link_selectors = [
                'h3.title a[href*="http"]',
                '.total_wrap a[href*="http"]',
                '.result_area a[href*="http"]',
                '.data_area a[href*="http"]',
                '.web_page a[href*="http"]',
                '.site_area a[href*="http"]',
                'a[href*="http"]:not([href*="naver.com"])',
            ]
            
            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements[:10]:
                        try:
                            href = element.get_attribute('href')
                            if not href:
                                continue
                            
                            # 네이버 리다이렉트 URL 처리
                            if 'naver.com' in href:
                                actual_url = self._extract_redirect_url(href)
                                if actual_url:
                                    href = actual_url
                                else:
                                    continue
                            
                            if self.is_valid_homepage_url(href, organization_name):
                                found_urls.append(href)
                                
                        except Exception:
                            continue
                            
                    if found_urls:
                        break
                        
                except Exception:
                    continue
            
            return found_urls[:self.max_search_results]
            
        except Exception as e:
            self.logger.warning(f"네이버 검색 실행 중 오류: {e}")
            return []

    def _extract_google_redirect_url(self, google_url: str) -> Optional[str]:
        """구글 리다이렉트 URL에서 실제 URL 추출"""
        try:
            if '/url?q=' in google_url:
                # /url?q= 뒤의 URL 추출
                parts = google_url.split('/url?q=')
                if len(parts) > 1:
                    url_part = parts[1].split('&')[0]  # 첫 번째 & 앞까지
                    actual_url = unquote(url_part)
                    return actual_url
            return None
        except Exception:
            return None

    def select_best_homepage(self, urls: List[str], organization_name: str) -> str:
        """가장 적합한 홈페이지 URL 선택 (개선된 버전)"""
        if not urls:
            return ""
        
        if len(urls) == 1:
            return urls[0]
        
        scored_urls = []
        
        for url in urls:
            score = 0
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 1. 도메인 신뢰도 점수
            if '.or.kr' in domain:
                score += 20  # 비영리기관
            elif '.go.kr' in domain:
                score += 18  # 정부기관
            elif '.ac.kr' in domain:
                score += 16  # 교육기관
            elif '.church' in domain:
                score += 15  # 교회 도메인
            elif '.org' in domain:
                score += 12  # 일반 기관
            elif '.co.kr' in domain:
                score += 8   # 기업
            elif '.com' in domain:
                score += 5   # 일반 상업
            
            # 2. 기관명 매칭 점수
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2:
                    if part in domain:
                        score += 10
                    elif any(part in segment for segment in domain.split('.')):
                        score += 5
            
            # 3. URL 구조 점수
            path_depth = len([p for p in parsed.path.strip('/').split('/') if p])
            if path_depth == 0:  # 루트 도메인
                score += 8
            elif path_depth == 1:
                score += 5
            elif path_depth > 3:
                score -= 3
            
            # 4. HTTPS 보너스
            if parsed.scheme == 'https':
                score += 3
            
            # 5. 짧은 도메인 선호
            if len(domain) < 20:
                score += 2
            elif len(domain) > 40:
                score -= 2
            
            # 6. 특수 키워드 보너스/패널티
            if any(keyword in domain for keyword in ['official', 'main', 'home']):
                score += 5
            if any(keyword in url.lower() for keyword in ['blog', 'cafe', 'post', 'board']):
                score -= 10
            
            scored_urls.append((url, score))
        
        # 점수 순으로 정렬
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 결과들 로깅
        self.logger.info("URL 점수 순위:")
        for i, (url, score) in enumerate(scored_urls[:3], 1):
            self.logger.info(f"  {i}. {url} (점수: {score})")
        
        return scored_urls[0][0]

    def _extract_redirect_url(self, naver_url: str) -> Optional[str]:
        """네이버 리다이렉트 URL에서 실제 URL 추출"""
        try:
            if 'url=' in naver_url:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(naver_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'url' in query_params:
                    actual_url = query_params['url'][0]
                    return unquote(actual_url)
            return None
        except:
            return None
    
    def _search_by_title_text(self, organization_name: str) -> List[str]:
        """제목 텍스트로 추가 검색"""
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
                        if href and self.is_valid_homepage_url(href, organization_name):
                            found_urls.append(href)
                            self.logger.info(f"제목 텍스트로 발견: {href}")
                            
                            if len(found_urls) >= self.max_search_results:
                                break
                                
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"제목 텍스트 검색 중 오류: {e}")
            
        return found_urls
    
    def is_valid_homepage_url(self, url: str, organization_name: str) -> bool:
        """유효한 홈페이지 URL인지 확인"""
        try:
            if not url or len(url) < 10:
                return False
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            domain = parsed.netloc.lower()
            
            # 제외할 도메인 체크
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
                self.logger.info(f"공식 도메인 발견: {domain}")
                return True
            
            # 기관명이 도메인에 포함되어 있는지 확인
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    self.logger.info(f"기관명이 도메인에 포함됨: {part} in {domain}")
                    return True
            
            return True
            
        except Exception:
            return False
    
    def verify_homepage_url(self, url: str) -> bool:
        """홈페이지 URL이 실제로 접근 가능한지 확인"""
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
                self.logger.info(f"URL 접근 성공: {url}")
            else:
                self.logger.warning(f"URL 접근 실패: {url}")
            
            return is_accessible
            
        except Exception as e:
            self.logger.warning(f"URL 검증 중 오류: {url} - {e}")
            try:
                # 오류 시 원래 창으로 돌아가기
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
     
    def process_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """기관 목록 처리"""
        processed_orgs = []
        total_count = len(organizations)
        success_count = 0
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    self.logger.info(f"진행 상황: {i}/{total_count} - {org.get('name', 'Unknown')}")
                    
                    # 기존 데이터 완전 복사
                    org_copy = org.copy()
                    
                    # 이미 홈페이지가 있고 유효한 URL이면 스킵
                    if org.get('homepage') and org['homepage'].strip() and org['homepage'].startswith(('http://', 'https://')):
                        self.logger.info(f"이미 유효한 홈페이지가 있음: {org['homepage']}")
                        processed_orgs.append(org_copy)
                        if org['homepage'].strip():
                            success_count += 1
                        continue
                    
                    # 홈페이지 검색 (지역 정보 사용 안함)
                    homepage_url = self.search_organization_homepage(
                        org.get('name', ''),
                        ""  # 지역 정보 전달하지 않음
                    )
                    
                    # homepage 필드 업데이트
                    if homepage_url:
                        # URL 검증
                        if self.verify_homepage_url(homepage_url):
                            org_copy['homepage'] = homepage_url
                            success_count += 1
                            self.logger.info(f"✅ 홈페이지 찾음: {homepage_url}")
                        else:
                            org_copy['homepage'] = ""
                            self.logger.warning(f"⚠️ URL 접근 불가: {homepage_url}")
                    else:
                        org_copy['homepage'] = ""
                        self.logger.warning(f"❌ 홈페이지를 찾지 못함")
                    
                    processed_orgs.append(org_copy)
                    
                    # 진행 상황 출력
                    if i % 5 == 0:
                        self.logger.info(f"📊 중간 통계: {success_count}/{i} 성공 ({success_count/i*100:.1f}%)")
                    
                    # 요청 간 지연
                    if i < total_count:  # 마지막이 아니면 지연
                        self.add_delay()
                    
                except Exception as e:
                    self.logger.error(f"처리 중 오류: {e}")
                    org_copy = org.copy()
                    if not org.get('homepage'):
                        org_copy['homepage'] = ""
                    processed_orgs.append(org_copy)
                    continue
                    
        finally:
            # 드라이버 종료
            self.close_driver()
        
        return processed_orgs

    def save_results(self, organizations: List[Dict], output_file: str) -> bool:
        """결과를 JSON 파일로 저장"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(organizations, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"결과 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"저장 중 오류: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔍 기관 홈페이지 URL 추출기 (Selenium 기반)")
    print("=" * 60)
    
    try:
        # headless 모드 설정 (False로 설정하여 브라우저 창 표시)
        use_headless = False
        print(f"🌐 브라우저 모드: {'Headless' if use_headless else 'GUI'}")
        
        # 추출기 인스턴스 생성
        extractor = URLExtractor(headless=use_headless)
        
        # 입력/출력 파일 설정
        input_file = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\undefined_converted_20250609_134731.json"
        output_file = f"raw_data_with_homepages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📂 입력 파일: {input_file}")
        print(f"💾 출력 파일: {output_file}")
        
        # 입력 파일 존재 확인
        if not os.path.exists(input_file):
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            return 1
        
        # JSON 파일 로드
        print("📖 데이터 로딩 중...")
        with open(input_file, 'r', encoding='utf-8') as f:
            organizations = json.load(f)
        
        print(f"📊 로드된 기관 수: {len(organizations)}")
        
        # 빈 homepage 필드 개수 확인
        empty_homepage_count = sum(1 for org in organizations if not org.get('homepage') or not org['homepage'].strip())
        print(f"🔍 홈페이지가 없는 기관: {empty_homepage_count}개")
        
        # 처리할 기관 수 제한 (테스트용)
        max_process = int(input(f"처리할 기관 수 (전체: {len(organizations)}, 엔터 시 전체): ") or len(organizations))
        organizations = organizations[:max_process]
        
        print(f"🔄 {len(organizations)}개 기관 처리 시작...")
        print("📝 Selenium을 사용하여 실제 브라우저로 검색합니다.")
        
        # 기관 처리
        processed_organizations = extractor.process_organizations(organizations)
        
        # 결과 저장
        if extractor.save_results(processed_organizations, output_file):
            print(f"\n✅ 처리 완료!")
            print(f"📁 결과 파일: {output_file}")
            
            # 통계 출력
            homepage_found = sum(1 for org in processed_organizations if org.get('homepage') and org['homepage'].strip())
            original_homepage_count = sum(1 for org in organizations if org.get('homepage') and org['homepage'].strip())
            new_homepage_count = homepage_found - original_homepage_count
            
            print(f"📈 최종 통계:")
            print(f"  - 기존 홈페이지: {original_homepage_count}개")
            print(f"  - 새로 찾은 홈페이지: {new_homepage_count}개")
            print(f"  - 전체 홈페이지: {homepage_found}/{len(processed_organizations)}개")
            print(f"  - 성공률: {homepage_found/len(processed_organizations)*100:.1f}%")
            
        else:
            print(f"\n❌ 결과 저장 실패")
            return 1
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
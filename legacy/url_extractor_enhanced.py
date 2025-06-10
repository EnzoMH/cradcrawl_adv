#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 추출 및 홈페이지 찾기 도구 (Selenium 기반 + VPN 우회)
구글의 매크로 차단을 VPN Gate를 통해 우회하는 기능 포함
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

# 상위 디렉토리 모듈 import (경로 설정 후)
try:
    from validator import AIValidator
    AI_VALIDATOR_AVAILABLE = True
    print("✅ AIValidator import 성공")
except ImportError as e:
    print(f"⚠️ AIValidator import 실패: {e}")
    print("🔧 AIValidator 없이 기본 기능만 사용합니다.")
    AIValidator = None
    AI_VALIDATOR_AVAILABLE = False

# 강화된 상수 설정
EXCLUDE_DOMAINS = [
    'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com',
    'naver.com', 'daum.net', 'google.com', 'yahoo.com',
    'blog.naver.com', 'cafe.naver.com', 'tistory.com',
    'wikipedia.org', 'namu.wiki', 'blogspot.com', 'wordpress.com'
]

class VPNManager:
    """VPN 연결 관리 클래스"""
    
    def __init__(self):
        self.current_process = None
        self.current_config = None
        self.logger = logging.getLogger('VPNManager')
    
    def get_vpn_servers(self, country: str) -> List[Dict]:
        """VPN Gate에서 서버 목록 가져오기"""
        try:
            self.logger.info(f"VPN 서버 검색 중: {country}")
            vpn_data = requests.get("http://www.vpngate.net/api/iphone/", timeout=10).text.replace("\r", "")
            servers = [line.split(",") for line in vpn_data.split("\n")]
            
            if len(servers) < 3:
                return []
                
            labels = servers[1]
            labels[0] = labels[0][1:]
            servers = [s for s in servers[2:] if len(s) > 1]
            
            # 국가 매칭
            if len(country) == 2:
                i = 6  # short name for country
            else:
                i = 5  # long name for country
            
            desired = [s for s in servers if len(s) > i and country.lower() in s[i].lower()]
            supported = [s for s in desired if len(s) > 14 and len(s[-1]) > 0]
            
            # 점수 순으로 정렬
            sorted_servers = sorted(supported, key=lambda s: float(s[2].replace(",", ".")), reverse=True)
            
            server_list = []
            for server in sorted_servers[:3]:  # 상위 3개만
                server_info = {
                    'config': server[-1],
                    'score': float(server[2].replace(",", ".")),
                    'country': server[5] if len(server) > 5 else country,
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
            self.logger.info(f"VPN 연결 시도: {country} (점수: {server['score']})")
            
            # 임시 설정 파일 생성
            _, config_path = tempfile.mkstemp(suffix='.ovpn')
            self.current_config = config_path
            
            with open(config_path, 'w') as f:
                config_content = base64.b64decode(server['config']).decode()
                f.write(config_content)
            
            # OpenVPN 연결 (백그라운드)
            try:
                self.current_process = subprocess.Popen(
                    ["openvpn", "--config", config_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 연결 대기 (최대 15초)
                for i in range(15):
                    if self.current_process.poll() is None:
                        time.sleep(1)
                        if i > 5:  # 5초 후부터는 연결된 것으로 간주
                            self.logger.info(f"VPN 연결 성공: {country}")
                            return True
                    else:
                        break
                
                self.logger.warning(f"VPN 연결 실패: {country}")
                return False
                
            except FileNotFoundError:
                self.logger.error("OpenVPN이 설치되지 않았습니다. VPN 우회를 건너뜁니다.")
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
                for _ in range(3):
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

class URLExtractorEnhanced:
    """향상된 URL 추출기 (VPN 우회 포함)"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.logger = self.setup_logger()
        self.vpn_manager = VPNManager()
        
        # AI 검증기 초기화 (새로 추가)
        self.ai_validator = None
        self.use_ai_validation = False
        
        if AI_VALIDATOR_AVAILABLE:
            try:
                self.ai_validator = AIValidator()
                self.use_ai_validation = True
                print("🤖 Enhanced URL Extractor: AI 검증 기능 활성화")
            except Exception as e:
                print(f"❌ AI 검증기 초기화 실패: {e}")
                self.use_ai_validation = False
        else:
            print("🔧 Enhanced URL Extractor: AI 검증 기능 비활성화")
        
        # 요청 간 지연 시간 (초)
        self.delay_range = (2, 4)
        
        # 검색 결과 제한
        self.max_search_results = 5
        self.max_retries = 2
        
        # VPN 관련
        self.vpn_countries = ['japan', 'korea', 'singapore']
        self.current_vpn_index = 0
    
    def setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('URLExtractorEnhanced')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def setup_driver(self):
        """Selenium WebDriver 설정"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 기본 옵션들
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 자동화 탐지 우회
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info(f"Chrome 드라이버 설정 완료")
            
        except Exception as e:
            self.logger.error(f"드라이버 설정 실패: {e}")
            raise
    
    def close_driver(self):
        """드라이버 및 VPN 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        self.vpn_manager.disconnect_vpn()
    
    def is_google_blocked(self) -> bool:
        """구글 차단 감지"""
        try:
            page_source = self.driver.page_source.lower()
            title = self.driver.title.lower()
            
            # 차단 키워드
            block_keywords = [
                'unusual traffic', 'captcha', 'blocked', 'forbidden',
                'access denied', 'suspicious activity', 'automated queries',
                'robot', 'bot detected', '비정상적인 트래픽'
            ]
            
            for keyword in block_keywords:
                if keyword in page_source or keyword in title:
                    self.logger.warning(f"구글 차단 감지: {keyword}")
                    return True
            
            # CAPTCHA 확인
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, '#captcha, .captcha, .g-recaptcha'):
                    self.logger.warning("CAPTCHA 감지됨")
                    return True
            except:
                pass
            
            return False
            
        except Exception:
            return False
    
    def try_vpn_bypass(self) -> bool:
        """VPN 우회 시도"""
        try:
            self.logger.info("🔧 VPN 우회 시도 중...")
            
            for country in self.vpn_countries:
                self.logger.info(f"🌏 VPN 연결 시도: {country}")
                
                if self.vpn_manager.connect_vpn(country):
                    time.sleep(3)
                    
                    # 드라이버 재시작
                    if self.driver:
                        self.driver.quit()
                    time.sleep(2)
                    self.setup_driver()
                    
                    # 구글 접속 테스트
                    try:
                        self.driver.get("https://www.google.com")
                        time.sleep(2)
                        
                        if not self.is_google_blocked():
                            self.logger.info(f"✅ VPN 우회 성공: {country}")
                            return True
                        else:
                            self.logger.warning(f"❌ {country} VPN으로도 차단됨")
                            
                    except Exception as e:
                        self.logger.warning(f"VPN 테스트 실패: {e}")
            
            self.logger.error("모든 VPN 시도 실패")
            return False
            
        except Exception as e:
            self.logger.error(f"VPN 우회 중 오류: {e}")
            return False

    def add_delay(self):
        """요청 간 지연"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def search_organization_homepage(self, organization_name: str) -> Optional[str]:
        """기관 홈페이지 검색 (AI 검증 + VPN 우회)"""
        try:
            if not self.driver:
                self.setup_driver()
            
            all_urls = []
            
            # 1. 네이버 검색
            self.logger.info(f"🔍 네이버 검색: {organization_name}")
            naver_urls = self._search_naver(organization_name)
            if naver_urls:
                all_urls.extend([(url, 'naver') for url in naver_urls])
            
            self.add_delay()
            
            # 2. 구글 검색 (VPN 우회 포함)
            self.logger.info(f"🔍 구글 검색: {organization_name}")
            google_urls = self._search_google_with_vpn(organization_name)
            if google_urls:
                all_urls.extend([(url, 'google') for url in google_urls])
            
            # 3. AI 검증으로 최적 URL 선택
            if all_urls:
                if self.use_ai_validation:
                    best_url = self._select_best_url_with_ai(all_urls, organization_name)
                else:
                    # AI 없는 경우 기존 방식
                    unique_urls = list(set([url for url, _ in all_urls]))
                    best_url = self.select_best_homepage(unique_urls, organization_name)
                
                return best_url
            
            self.logger.warning(f"❌ 홈페이지 검색 실패: {organization_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"검색 중 오류: {e}")
            return None
        
    def _select_best_url_with_ai(self, candidate_urls: List[Tuple[str, str]], 
                                 organization_name: str) -> Optional[str]:
        """AI 검증으로 최적 URL 선택 (asyncio 문제 수정)"""
        
        # asyncio.run() 대신 직접 await 사용 (이미 async 컨텍스트에서 호출되므로)
        async def validate_candidates():
            validated_results = []
            
            for url, source in candidate_urls:
                try:
                    # 페이지 내용 미리보기
                    page_preview = self._get_quick_page_content(url)
                    
                    # AI 검증
                    validation = await self.ai_validator.validate_homepage_url_relevance(
                        organization_name, url, page_preview, source
                    )
                    
                    score = validation.get("confidence", 0) * 100
                    if validation.get("is_relevant", False):
                        score += 20  # 관련성 보너스
                    
                    validated_results.append({
                        'url': url,
                        'score': score,
                        'confidence': validation.get("confidence", 0),
                        'source': source,
                        'reasoning': validation.get("reasoning", "")
                    })
                    
                    self.logger.info(f"검증 완료: {url} (점수: {score:.1f}, 출처: {source})")
                    
                except Exception as e:
                    self.logger.warning(f"URL 검증 실패: {url} - {e}")
                    continue
            
            return validated_results
        
        try:
            # asyncio.run() 제거하고 직접 호출
            import asyncio
            
            # 현재 이벤트 루프가 있는지 확인
            try:
                loop = asyncio.get_running_loop()
                # 이미 루프가 실행 중이면 task로 생성
                task = asyncio.create_task(validate_candidates())
                validated_results = loop.run_until_complete(task)
            except RuntimeError:
                # 루프가 없으면 새로 실행
                validated_results = asyncio.run(validate_candidates())
            
            # 점수 순으로 정렬
            if validated_results:
                validated_results.sort(key=lambda x: x['score'], reverse=True)
                best_result = validated_results[0]
                
                self.logger.info(f"🏆 최종 선택: {best_result['url']} "
                               f"(점수: {best_result['score']:.1f}, 신뢰도: {best_result['confidence']:.2f})")
                
                return best_result['url']
            
            # AI 검증 실패시 기존 방식
            self.logger.warning("AI 검증 결과 없음, 기존 방식 사용")
            unique_urls = list(set([url for url, _ in candidate_urls]))
            return self.select_best_homepage(unique_urls, organization_name)
            
        except Exception as e:
            self.logger.error(f"AI 검증 중 오류: {e}")
            # fallback 로직
            unique_urls = list(set([url for url, _ in candidate_urls]))
            return self.select_best_homepage(unique_urls, organization_name)
    
    def _get_quick_page_content(self, url: str) -> str:
        """빠른 페이지 내용 추출"""
        try:
            # 간단한 requests로 내용 가져오기 (빠른 미리보기용)
            import requests
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # 스크립트, 스타일 제거
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()[:2000]  # 앞부분만
                    return text
                except ImportError:
                    # BeautifulSoup 없는 경우 원본 텍스트 일부 사용
                    return response.text[:2000]
        
        except Exception as e:
            self.logger.warning(f"페이지 내용 추출 실패: {url} - {e}")
        
        return ""

    def _search_naver(self, organization_name: str) -> List[str]:
        """네이버 검색"""
        try:
            self.driver.get('https://www.naver.com')
            time.sleep(2)
            
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "query"))
            )
            
            query = f'{organization_name} 홈페이지'
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            
            found_urls = []
            selectors = [
                'h3.title a[href*="http"]',
                '.total_wrap a[href*="http"]',
                '.result_area a[href*="http"]',
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:10]:
                        try:
                            href = element.get_attribute('href')
                            if href and 'naver.com' not in href:
                                if self.is_valid_homepage_url(href, organization_name):
                                    found_urls.append(href)
                        except:
                            continue
                    if found_urls:
                        break
                except:
                    continue
            
            return found_urls[:self.max_search_results]
            
        except Exception as e:
            self.logger.warning(f"네이버 검색 오류: {e}")
            return []

    def _search_google_with_vpn(self, organization_name: str) -> List[str]:
        """구글 검색 (VPN 우회 포함)"""
        for attempt in range(self.max_retries):
            try:
                query = f'{organization_name} 홈페이지'
                google_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko"
                self.driver.get(google_url)
                time.sleep(3)
                
                # 차단 확인
                if self.is_google_blocked():
                    self.logger.warning(f"구글 차단 감지 (시도 {attempt + 1})")
                    
                    if attempt < self.max_retries - 1:
                        if self.try_vpn_bypass():
                            continue
                        else:
                            break
                    else:
                        self.logger.error("VPN 우회 실패")
                        break
                
                # 검색 결과 추출
                found_urls = []
                selectors = [
                    'h3 a[href*="http"]',
                    '.g a[href*="http"]',
                    '.yuRUbf a[href*="http"]',
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements[:10]:
                            try:
                                href = element.get_attribute('href')
                                if not href or 'google.com' in href:
                                    continue
                                
                                # 구글 리다이렉트 URL 처리
                                if '/url?q=' in href:
                                    actual_url = self._extract_google_url(href)
                                    if actual_url:
                                        href = actual_url
                                
                                if self.is_valid_homepage_url(href, organization_name):
                                    found_urls.append(href)
                                    
                            except:
                                continue
                        if found_urls:
                            break
                    except:
                        continue
                
                if found_urls:
                    return found_urls[:self.max_search_results]
                else:
                    self.logger.warning(f"구글 검색 결과 없음 (시도 {attempt + 1})")
                    
            except Exception as e:
                self.logger.warning(f"구글 검색 오류: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
        
        return []

    def _extract_google_url(self, google_url: str) -> Optional[str]:
        """구글 리다이렉트 URL 추출"""
        try:
            if '/url?q=' in google_url:
                parts = google_url.split('/url?q=')
                if len(parts) > 1:
                    url_part = parts[1].split('&')[0]
                    return unquote(url_part)
            return None
        except:
            return None

    def is_valid_homepage_url(self, url: str, organization_name: str) -> bool:
        """유효한 홈페이지 URL 확인"""
        try:
            if not url or len(url) < 10:
                return False
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            domain = parsed.netloc.lower()
            
            # 제외 도메인 체크
            for exclude_domain in EXCLUDE_DOMAINS:
                if exclude_domain in domain:
                    return False
            
            # 파일 확장자 체크
            if any(url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif']):
                return False
            
            # 게시판/블로그 패턴 체크
            if any(pattern in url.lower() for pattern in ['/board/', '/bbs/', 'blog.', 'cafe.']):
                return False
            
            # 공식 도메인 우선
            official_tlds = ['.or.kr', '.go.kr', '.ac.kr', '.org', '.church']
            if any(tld in domain for tld in official_tlds):
                return True
            
            # 기관명 매칭
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    return True
            
            return len(domain) < 50  # 너무 긴 도메인 제외
            
        except:
            return False

    def select_best_homepage(self, urls: List[str], organization_name: str) -> str:
        """최적 홈페이지 URL 선택"""
        if not urls:
            return ""
        
        if len(urls) == 1:
            return urls[0]
        
        scored_urls = []
        
        for url in urls:
            score = 0
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 도메인 신뢰도
            if '.or.kr' in domain:
                score += 20
            elif '.go.kr' in domain:
                score += 18
            elif '.ac.kr' in domain:
                score += 16
            elif '.church' in domain:
                score += 15
            elif '.org' in domain:
                score += 12
            elif '.com' in domain:
                score += 5
            
            # 기관명 매칭
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    score += 10
            
            # URL 구조
            path_depth = len([p for p in parsed.path.strip('/').split('/') if p])
            if path_depth == 0:
                score += 8
            elif path_depth <= 2:
                score += 5
            
            # HTTPS 보너스
            if parsed.scheme == 'https':
                score += 3
            
            scored_urls.append((url, score))
        
        # 점수 순 정렬
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        return scored_urls[0][0]

    def process_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """기관 목록 처리"""
        processed_orgs = []
        total_count = len(organizations)
        success_count = 0
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    self.logger.info(f"처리 중 ({i}/{total_count}): {org.get('name', 'Unknown')}")
                    
                    org_copy = org.copy()
                    
                    # 기존 홈페이지가 있으면 스킵
                    if org.get('homepage') and org['homepage'].strip():
                        if org['homepage'].startswith(('http://', 'https://')):
                            processed_orgs.append(org_copy)
                            success_count += 1
                            continue
                    
                    # 홈페이지 검색
                    homepage_url = self.search_organization_homepage(org.get('name', ''))
                    
                    if homepage_url:
                        org_copy['homepage'] = homepage_url
                        success_count += 1
                        self.logger.info(f"✅ 홈페이지 발견: {homepage_url}")
                    else:
                        org_copy['homepage'] = ""
                        self.logger.warning(f"❌ 홈페이지 검색 실패")
                    
                    processed_orgs.append(org_copy)
                    
                    # 진행률 출력
                    if i % 10 == 0:
                        success_rate = success_count / i * 100
                        self.logger.info(f"📊 진행률: {success_count}/{i} ({success_rate:.1f}%)")
                    
                    # 지연
                    if i < total_count:
                        self.add_delay()
                    
                except Exception as e:
                    self.logger.error(f"처리 오류: {e}")
                    org_copy = org.copy()
                    if not org.get('homepage'):
                        org_copy['homepage'] = ""
                    processed_orgs.append(org_copy)
                    
        finally:
            self.close_driver()
        
        return processed_orgs

    def save_results(self, organizations: List[Dict], output_file: str) -> bool:
        """결과 저장"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(organizations, f, ensure_ascii=False, indent=2)
            self.logger.info(f"결과 저장 완료: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"저장 오류: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🔍 기관 홈페이지 URL 추출기 (VPN 우회 기능 포함)")
    print("=" * 70)
    
    try:
        # 설정
        use_headless = False
        print(f"🌐 브라우저 모드: {'Headless' if use_headless else 'GUI'}")
        print("🔧 VPN 우회: 활성화 (구글 차단 시 자동 실행)")
        
        # 추출기 생성
        extractor = URLExtractorEnhanced(headless=use_headless)
        
        # 파일 설정
        input_file = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\undefined_converted_20250609_134731.json"
        output_file = f"enhanced_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📂 입력 파일: {input_file}")
        print(f"💾 출력 파일: {output_file}")
        
        # 파일 확인
        if not os.path.exists(input_file):
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            return 1
        
        # 데이터 로드
        print("📖 데이터 로딩 중...")
        with open(input_file, 'r', encoding='utf-8') as f:
            organizations = json.load(f)
        
        print(f"📊 로드된 기관 수: {len(organizations)}")
        
        # 처리할 개수 선택
        max_process = int(input(f"처리할 기관 수 (전체: {len(organizations)}, 엔터=전체): ") or len(organizations))
        organizations = organizations[:max_process]
        
        print(f"\n🔄 {len(organizations)}개 기관 처리 시작...")
        print("⚠️  OpenVPN 설치 권장 (VPN 우회 기능)")
        
        # 처리 실행
        processed_organizations = extractor.process_organizations(organizations)
        
        # 결과 저장
        if extractor.save_results(processed_organizations, output_file):
            print(f"\n✅ 처리 완료!")
            print(f"📁 결과 파일: {output_file}")
            
            # 통계
            homepage_found = sum(1 for org in processed_organizations if org.get('homepage') and org['homepage'].strip())
            success_rate = homepage_found / len(processed_organizations) * 100
            
            print(f"📈 최종 통계:")
            print(f"  - 전체 기관: {len(processed_organizations)}개")
            print(f"  - 홈페이지 발견: {homepage_found}개")
            print(f"  - 성공률: {success_rate:.1f}%")
        else:
            print(f"\n❌ 결과 저장 실패")
            return 1
        
    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 
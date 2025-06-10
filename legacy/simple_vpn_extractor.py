#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPN 우회 기능이 포함된 URL 추출기
구글 차단 시 자동으로 VPN Gate를 통해 우회합니다.
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
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse, unquote
from datetime import datetime

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class VPNManager:
    """VPN 연결 관리"""
    
    def __init__(self):
        self.current_process = None
        self.current_config = None
        self.logger = logging.getLogger('VPN')
    
    def get_vpn_servers(self, country: str) -> List[Dict]:
        """VPN Gate 서버 목록 가져오기"""
        try:
            self.logger.info(f"VPN 서버 검색: {country}")
            response = requests.get("http://www.vpngate.net/api/iphone/", timeout=10)
            vpn_data = response.text.replace("\r", "")
            servers = [line.split(",") for line in vpn_data.split("\n")]
            
            if len(servers) < 3:
                return []
                
            servers = [s for s in servers[2:] if len(s) > 14]
            
            # 국가 필터링
            i = 6 if len(country) == 2 else 5
            desired = [s for s in servers if country.lower() in s[i].lower()]
            supported = [s for s in desired if len(s[-1]) > 0]
            
            # 점수 순 정렬
            sorted_servers = sorted(supported, key=lambda s: float(s[2].replace(",", ".")), reverse=True)
            
            result = []
            for server in sorted_servers[:2]:  # 상위 2개만
                result.append({
                    'config': server[-1],
                    'score': float(server[2].replace(",", ".")),
                    'country': country
                })
            
            self.logger.info(f"{country}에서 {len(result)}개 서버 발견")
            return result
            
        except Exception as e:
            self.logger.error(f"VPN 서버 검색 실패: {e}")
            return []
    
    def connect_vpn(self, country: str) -> bool:
        """VPN 연결"""
        try:
            servers = self.get_vpn_servers(country)
            if not servers:
                return False
            
            self.disconnect_vpn()
            
            server = servers[0]
            self.logger.info(f"VPN 연결 시도: {country}")
            
            # 임시 설정 파일 생성
            _, config_path = tempfile.mkstemp(suffix='.ovpn')
            self.current_config = config_path
            
            with open(config_path, 'w') as f:
                config_content = base64.b64decode(server['config']).decode()
                f.write(config_content)
            
            try:
                # OpenVPN 실행
                self.current_process = subprocess.Popen(
                    ["openvpn", "--config", config_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                time.sleep(8)  # 연결 대기
                
                if self.current_process.poll() is None:
                    self.logger.info(f"VPN 연결 성공: {country}")
                    return True
                else:
                    self.logger.warning(f"VPN 연결 실패: {country}")
                    return False
                    
            except FileNotFoundError:
                self.logger.error("OpenVPN이 설치되지 않았습니다. VPN 우회를 건너뜁니다.")
                return False
                
        except Exception as e:
            self.logger.error(f"VPN 연결 오류: {e}")
            return False
    
    def disconnect_vpn(self):
        """VPN 연결 종료"""
        try:
            if self.current_process:
                self.current_process.terminate()
                time.sleep(2)
                if self.current_process.poll() is None:
                    self.current_process.kill()
                self.current_process = None
                self.logger.info("VPN 연결 종료")
            
            if self.current_config and os.path.exists(self.current_config):
                os.unlink(self.current_config)
                self.current_config = None
                
        except Exception as e:
            self.logger.error(f"VPN 종료 오류: {e}")

class URLExtractorVPN:
    """VPN 우회 기능이 포함된 URL 추출기"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.logger = self.setup_logger()
        self.vpn_manager = VPNManager()
        self.vpn_countries = ['japan', 'korea', 'singapore']
    
    def setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('URLExtractor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def setup_driver(self):
        """웹드라이버 설정"""
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("드라이버 설정 완료")
            
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
            
            block_keywords = [
                'unusual traffic', 'captcha', 'blocked', 'automated queries',
                'suspicious activity', 'robot', '비정상적인 트래픽'
            ]
            
            for keyword in block_keywords:
                if keyword in page_source or keyword in title:
                    self.logger.warning(f"구글 차단 감지: {keyword}")
                    return True
            
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, '#captcha, .captcha, .g-recaptcha'):
                    self.logger.warning("CAPTCHA 감지됨")
                    return True
            except:
                pass
            
            return False
        except:
            return False
    
    def try_vpn_bypass(self) -> bool:
        """VPN 우회 시도"""
        try:
            self.logger.info("🔧 VPN 우회 시도 중...")
            
            for country in self.vpn_countries:
                self.logger.info(f"🌏 VPN 연결 시도: {country}")
                
                if self.vpn_manager.connect_vpn(country):
                    if self.driver:
                        self.driver.quit()
                    time.sleep(3)
                    self.setup_driver()
                    
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
            self.logger.error(f"VPN 우회 오류: {e}")
            return False
    
    def search_with_google(self, organization_name: str) -> List[str]:
        """구글 검색 (VPN 우회 포함)"""
        for attempt in range(2):
            try:
                query = f'{organization_name} 홈페이지'
                url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko"
                self.driver.get(url)
                time.sleep(3)
                
                if self.is_google_blocked():
                    self.logger.warning(f"구글 차단 감지 (시도 {attempt + 1}/2)")
                    if attempt == 0 and self.try_vpn_bypass():
                        continue
                    else:
                        break
                
                found_urls = []
                selectors = ['h3 a[href*="http"]', '.g a[href*="http"]', '.yuRUbf a[href*="http"]']
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements[:8]:
                            try:
                                href = element.get_attribute('href')
                                if not href or 'google.com' in href:
                                    continue
                                
                                if '/url?q=' in href:
                                    actual_url = self._extract_google_url(href)
                                    if actual_url:
                                        href = actual_url
                                
                                if self.is_valid_url(href, organization_name):
                                    found_urls.append(href)
                                    self.logger.info(f"구글에서 발견: {href}")
                            except:
                                continue
                        if found_urls:
                            break
                    except:
                        continue
                
                return found_urls[:3]
                
            except Exception as e:
                self.logger.warning(f"구글 검색 오류: {e}")
        
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
    
    def search_with_naver(self, organization_name: str) -> List[str]:
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
            selectors = ['h3.title a[href*="http"]', '.total_wrap a[href*="http"]']
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:8]:
                        try:
                            href = element.get_attribute('href')
                            if href and 'naver.com' not in href:
                                if self.is_valid_url(href, organization_name):
                                    found_urls.append(href)
                                    self.logger.info(f"네이버에서 발견: {href}")
                        except:
                            continue
                    if found_urls:
                        break
                except:
                    continue
            
            return found_urls[:3]
            
        except Exception as e:
            self.logger.warning(f"네이버 검색 오류: {e}")
            return []
    
    def is_valid_url(self, url: str, organization_name: str) -> bool:
        """유효한 홈페이지 URL인지 확인"""
        try:
            if not url or len(url) < 10:
                return False
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            domain = parsed.netloc.lower()
            
            exclude_domains = [
                'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com',
                'blog.naver.com', 'cafe.naver.com', 'tistory.com', 'blogspot.com'
            ]
            
            if any(ex in domain for ex in exclude_domains):
                return False
            
            if url.lower().endswith(('.pdf', '.jpg', '.png', '.gif')):
                return False
            
            if any(pattern in url.lower() for pattern in ['/board/', '/bbs/', '/community/']):
                return False
            
            official_tlds = ['.or.kr', '.go.kr', '.ac.kr', '.org', '.church']
            if any(tld in domain for tld in official_tlds):
                return True
            
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    return True
            
            return len(domain) < 50
            
        except:
            return False
    
    def search_homepage(self, organization_name: str) -> Optional[str]:
        """홈페이지 검색 (네이버 + 구글 + VPN 우회)"""
        try:
            if not self.driver:
                self.setup_driver()
            
            all_urls = []
            
            # 네이버 검색
            self.logger.info(f"🔍 네이버 검색: {organization_name}")
            naver_urls = self.search_with_naver(organization_name)
            all_urls.extend(naver_urls)
            
            time.sleep(random.uniform(2, 4))
            
            # 구글 검색 (VPN 우회 포함)
            self.logger.info(f"🔍 구글 검색: {organization_name}")
            google_urls = self.search_with_google(organization_name)
            all_urls.extend(google_urls)
            
            if all_urls:
                unique_urls = list(set(all_urls))
                best_url = self.select_best_url(unique_urls, organization_name)
                self.logger.info(f"✅ 최종 선택: {best_url}")
                return best_url
            
            self.logger.warning(f"❌ 홈페이지 검색 실패: {organization_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"홈페이지 검색 오류: {e}")
            return None
    
    def select_best_url(self, urls: List[str], organization_name: str) -> str:
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
            
            name_parts = re.findall(r'[가-힣a-zA-Z]+', organization_name.lower())
            for part in name_parts:
                if len(part) > 2 and part in domain:
                    score += 10
            
            path_depth = len([p for p in parsed.path.strip('/').split('/') if p])
            if path_depth == 0:
                score += 8
            elif path_depth <= 2:
                score += 5
            
            if parsed.scheme == 'https':
                score += 3
            
            scored_urls.append((url, score))
        
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        return scored_urls[0][0]
    
    def process_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """기관 목록 처리"""
        processed = []
        total = len(organizations)
        success = 0
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    self.logger.info(f"처리 중 ({i}/{total}): {org.get('name', 'Unknown')}")
                    
                    org_copy = org.copy()
                    
                    if org.get('homepage') and org['homepage'].strip():
                        if org['homepage'].startswith(('http://', 'https://')):
                            processed.append(org_copy)
                            success += 1
                            continue
                    
                    homepage = self.search_homepage(org.get('name', ''))
                    
                    if homepage:
                        org_copy['homepage'] = homepage
                        success += 1
                        self.logger.info(f"✅ 홈페이지 발견: {homepage}")
                    else:
                        org_copy['homepage'] = ""
                        self.logger.warning("❌ 홈페이지 검색 실패")
                    
                    processed.append(org_copy)
                    
                    if i % 5 == 0:
                        rate = success / i * 100
                        self.logger.info(f"📊 진행률: {success}/{i} ({rate:.1f}%)")
                    
                    if i < total:
                        time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    self.logger.error(f"처리 오류: {e}")
                    org_copy = org.copy()
                    if not org.get('homepage'):
                        org_copy['homepage'] = ""
                    processed.append(org_copy)
                    
        finally:
            self.close_driver()
        
        return processed

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🔍 홈페이지 URL 추출기 (VPN 우회 기능 포함)")
    print("=" * 70)
    
    try:
        use_headless = False
        print(f"🌐 브라우저 모드: {'Headless' if use_headless else 'GUI'}")
        print("🔧 VPN 우회: 활성화 (구글 차단 시 자동 실행)")
        print("⚠️  OpenVPN 설치 권장")
        
        extractor = URLExtractorVPN(headless=use_headless)
        
        input_file = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\undefined_converted_20250609_134731.json"
        output_file = f"urls_with_vpn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📂 입력 파일: {input_file}")
        print(f"💾 출력 파일: {output_file}")
        
        if not os.path.exists(input_file):
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            return 1
        
        with open(input_file, 'r', encoding='utf-8') as f:
            organizations = json.load(f)
        
        print(f"📊 로드된 기관 수: {len(organizations)}")
        
        max_process = int(input(f"처리할 기관 수 (전체: {len(organizations)}, 엔터=전체): ") or len(organizations))
        organizations = organizations[:max_process]
        
        print(f"\n🔄 {len(organizations)}개 기관 처리 시작...")
        print("📝 네이버 + 구글 검색으로 홈페이지를 찾습니다.")
        print("🚀 구글 차단 시 자동으로 VPN을 통해 우회합니다.")
        
        processed_organizations = extractor.process_organizations(organizations)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_organizations, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 처리 완료!")
        print(f"📁 결과 파일: {output_file}")
        
        homepage_found = sum(1 for org in processed_organizations if org.get('homepage') and org['homepage'].strip())
        success_rate = homepage_found / len(processed_organizations) * 100
        
        print(f"📈 최종 통계:")
        print(f"  - 전체 기관: {len(processed_organizations)}개")
        print(f"  - 홈페이지 발견: {homepage_found}개")
        print(f"  - 성공률: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 추출 및 홈페이지 찾기 도구 (Selenium 기반)
"""

import json
import os
import sys
import time
import random
import re
import logging
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

class URLExtractor:
    """URL 추출 및 홈페이지 검색 클래스 (Selenium 기반)"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.logger = self.setup_logger()
        
        # 요청 간 지연 시간 (초)
        self.delay_range = (3, 6)
        
        # 검색 결과 제한
        self.max_search_results = 5
        self.max_retries = 3
    
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
        """기관 홈페이지 검색 (네이버 기반) - 지역 정보 사용 안함"""
        try:
            if not self.driver:
                self.setup_driver()
            
            # 지역 정보를 사용하지 않는 검색 쿼리들
            search_queries = [
                self.clean_search_query(organization_name),  # location 제거
                f'{organization_name} 홈페이지',
                f'{organization_name} 공식사이트',
                f'{organization_name} site:or.kr',
                f'{organization_name} site:org',
            ]
            
            for i, query in enumerate(search_queries, 1):
                self.logger.info(f"네이버 검색 시도 {i}/{len(search_queries)}: {query}")
                result = self._perform_naver_search(query, organization_name)
                if result:
                    return result
                
                # 각 시도 간 지연
                self.add_delay()
            
            return None
            
        except Exception as e:
            self.logger.error(f"검색 중 오류 발생: {e}")
            return None

    def _perform_naver_search(self, query: str, organization_name: str) -> Optional[str]:
        """실제 네이버 검색 수행"""
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
            
            self.logger.info(f"네이버 검색 실행: {query}")
            
            # 다양한 선택자로 링크 찾기
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
                    self.logger.info(f"선택자 '{selector}'로 {len(elements)}개 요소 발견")
                    
                    for element in elements[:15]:  # 각 선택자당 15개씩
                        try:
                            href = element.get_attribute('href')
                            
                            if not href or href.startswith('#') or href.startswith('javascript:'):
                                continue
                            
                            # 네이버 내부 링크 필터링
                            if 'naver.com' in href and not self._extract_redirect_url(href):
                                continue
                            
                            # 리다이렉트 URL 처리
                            if 'naver.com' in href:
                                actual_url = self._extract_redirect_url(href)
                                if actual_url:
                                    url = actual_url
                                else:
                                    continue
                            else:
                                url = href
                            
                            # URL 유효성 검사
                            if self.is_valid_homepage_url(url, organization_name):
                                found_urls.append(url)
                                self.logger.info(f"유효한 URL 발견: {url}")
                                
                                if len(found_urls) >= self.max_search_results:
                                    break
                                    
                        except Exception as e:
                            continue
                    
                    if found_urls:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"선택자 '{selector}' 처리 중 오류: {e}")
                    continue
            
            # 추가로 제목 텍스트 확인
            if not found_urls:
                self.logger.info("제목 텍스트 기반 추가 검색")
                found_urls = self._search_by_title_text(organization_name)
            
            # 가장 적합한 URL 선택
            if found_urls:
                best_url = self.select_best_homepage(found_urls, organization_name)
                self.logger.info(f"최종 선택된 URL: {best_url}")
                return best_url
            
            self.logger.warning(f"'{query}' 검색에서 유효한 URL을 찾지 못했습니다")
            return None
            
        except Exception as e:
            self.logger.warning(f"네이버 검색 실행 중 오류: {e}")
            return None
    
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
    
    def select_best_homepage(self, urls: List[str], organization_name: str) -> str:
        """가장 적합한 홈페이지 URL 선택"""
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
            
            # 경로 점수
            path_depth = len(parsed.path.strip('/').split('/')) if parsed.path != '/' else 0
            score += max(0, 3 - path_depth)
            
            scored_urls.append((url, score))
        
        # 점수 순으로 정렬
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        
        best_url = scored_urls[0][0]
        self.logger.info(f"최고 점수 URL 선택: {best_url} (점수: {scored_urls[0][1]})")
        
        return best_url
    
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
        input_file = r"C:\Users\kimyh\makedb\Python\advanced_crawling\raw_data_0530.json"
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
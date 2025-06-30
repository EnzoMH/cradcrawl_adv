#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
홈페이지 직접 파싱 및 AI 정리 도구
기존에 찾아둔 홈페이지 URL들을 실제로 방문하여 내용을 추출하고 AI로 정리
"""

import json
import os
import sys
import time
import random
import re
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# 프로젝트 루트 경로 설정
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# settings.py에서 필요한 것들 import
try:
    from utils.settings import (
        PHONE_EXTRACTION_PATTERNS,
        FAX_EXTRACTION_PATTERNS,
        EMAIL_EXTRACTION_PATTERNS,
        ADDRESS_EXTRACTION_PATTERNS,
        GEMINI_API_KEY,
        LOGGER_NAMES
    )
    print("✅ settings.py import 성공")
except ImportError as e:
    print(f"⚠️ settings.py import 실패: {e}")
    # 기본값 설정
    PHONE_EXTRACTION_PATTERNS = [r'(\d{2,3}[-\.\s]?\d{3,4}[-\.\s]?\d{4})']
    FAX_EXTRACTION_PATTERNS = [r'팩스[\s]*(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})']
    EMAIL_EXTRACTION_PATTERNS = [r'([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})']
    ADDRESS_EXTRACTION_PATTERNS = [r'([가-힣\s\d\-\(\)]+(?:시|군|구|동|로|길)[가-힣\s\d\-\(\)]*)']
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    LOGGER_NAMES = {"parser": "web_parser"}

# AI 및 BS4 초기화 (기존 코드와 동일)
AI_AVAILABLE = False
genai = None
BS4_AVAILABLE = False

# AI 모델 import 및 초기화
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        AI_AVAILABLE = True
        print("🤖 AI 기능 활성화")
    else:
        AI_AVAILABLE = False
        print("⚠️ GEMINI_API_KEY가 설정되지 않음")
except ImportError as e:
    AI_AVAILABLE = False
    genai = None
    print(f"⚠️ google.generativeai 모듈 import 실패: {e}")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
    print("✅ BeautifulSoup 사용 가능")
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️ BeautifulSoup이 없음 - HTML 파싱 제한됨")

class HomepageParser:
    """홈페이지 직접 파싱 및 AI 정리 클래스"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.logger = self.setup_logger()
        
        # AI 모델 설정 (전역 변수 사용)
        self.ai_model = None
        self.use_ai = AI_AVAILABLE  # 전역 변수 사용
        
        if self.use_ai and genai:
            try:
                self.ai_model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini AI 모델 초기화 성공")
            except Exception as e:
                print(f"❌ AI 모델 초기화 실패: {e}")
                self.use_ai = False
                self.ai_model = None
        else:
            print("🔧 AI 기능 비활성화")
        
        # 파싱 설정
        self.page_timeout = 30
        self.delay_range = (2, 4)
        self.max_content_length = 10000  # AI 처리용 최대 텍스트 길이
        self.max_wait_time = 20  # JavaScript 로딩 최대 대기시간

        # 동적 콘텐츠 감지를 위한 선택자들
        self.content_selectors = [
            'main', 'article', '.content', '#content', '.main-content',
            '.container', '.wrapper', 'section', '.section',
            '.page-content', '.post-content', '.entry-content',
            '[role="main"]', '.main'
        ]
        
        # 연락처 관련 선택자들
        self.contact_selectors = [
            '.contact', '#contact', '.contact-info', '.contact-us',
            '.footer', '#footer', '.footer-info',
            '.address', '.phone', '.tel', '.email',
            '[class*="contact"]', '[id*="contact"]',
            '[class*="footer"]', '[id*="footer"]',
            'footer', 'address'
        ]
        
    def setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('homepage_parser')
        logger.setLevel(logging.INFO)  # DEBUG로 변경하면 프롬프트도 볼 수 있음
        
        # 핸들러가 이미 있으면 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # 파일 핸들러도 추가 (선택사항)
        try:
            file_handler = logging.FileHandler('homepage_parser.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # 파일에는 모든 로그 저장
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"파일 로그 핸들러 설정 실패: {e}")
        
        return logger
    
    def setup_driver(self):
        """ChromeDriver 설정 및 초기화 (개선된 오류 처리)"""
        try:
            # 기존 드라이버 정리
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            # Chrome 옵션 설정
            options = webdriver.ChromeOptions()
            
            # 기본 옵션들
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 사용자 에이전트 설정
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 헤드리스 모드 설정
            if self.headless:
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
            
            # 성능 최적화
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # 이미지 로드 비활성화
            options.add_argument('--disable-javascript')  # JS 비활성화 (필요시 제거)
            
            # Chrome WebDriver 초기화 시도
            try:
                self.driver = webdriver.Chrome(options=options)
                self.logger.info("✅ Chrome WebDriver 초기화 성공")
            except Exception as chrome_error:
                self.logger.warning(f"⚠️ Chrome WebDriver 실패: {chrome_error}")
                
                # Edge WebDriver 시도
                try:
                    from selenium.webdriver import Edge
                    from selenium.webdriver.edge.options import Options as EdgeOptions
                    
                    edge_options = EdgeOptions()
                    edge_options.add_argument('--no-sandbox')
                    edge_options.add_argument('--disable-dev-shm-usage')
                    if self.headless:
                        edge_options.add_argument('--headless')
                    
                    self.driver = Edge(options=edge_options)
                    self.logger.info("✅ Edge WebDriver 초기화 성공 (Chrome 대안)")
                except Exception as edge_error:
                    self.logger.error(f"❌ Edge WebDriver도 실패: {edge_error}")
                    raise Exception(f"모든 WebDriver 실패 - Chrome: {chrome_error}, Edge: {edge_error}")
            
            # WebDriver 설정
            if self.driver:
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
                
                # 자동화 감지 방지
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
                self.logger.info("🚀 WebDriver 설정 완료")
            else:
                raise Exception("WebDriver 초기화 실패")
            
        except Exception as e:
            self.logger.error(f"❌ WebDriver 설정 실패: {e}")
            self.driver = None
            raise e
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.logger.info("드라이버 종료 완료")
    
    def add_delay(self):
        """요청 간 지연"""
        delay = random.uniform(*self.delay_range)
        self.logger.info(f"지연 시간: {delay:.1f}초")
        time.sleep(delay)

    def wait_for_dynamic_content(self, url: str) -> bool:
        """동적 콘텐츠 로딩 대기 (강화된 버전)"""
        try:
            self.logger.info("🔄 강화된 동적 콘텐츠 로딩 대기 시작...")
            
            # 1. 기본 페이지 로딩 완료 대기
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 2. 초기 콘텐츠 길이 측정
            initial_length = len(self.driver.page_source)
            
            # 3. 여러 JavaScript 프레임워크 대기
            self._wait_for_js_frameworks()
            
            # 4. 동적 로딩 감지 및 대기
            stable_count = 0
            max_wait_cycles = 8
            
            for cycle in range(max_wait_cycles):
                time.sleep(2)
                
                # 페이지 스크롤로 lazy loading 트리거
                self.trigger_lazy_loading()
                
                # 새로운 콘텐츠 길이 측정
                current_length = len(self.driver.page_source)
                
                # 콘텐츠 변화가 없으면 안정된 것으로 판단
                if abs(current_length - initial_length) < 1000:
                    stable_count += 1
                    if stable_count >= 2:  # 2번 연속 안정되면 완료
                        self.logger.info(f"✅ 콘텐츠 안정화 완료 (사이클 {cycle+1})")
                        break
                else:
                    stable_count = 0
                    initial_length = current_length
                    self.logger.info(f"📊 콘텐츠 변화 감지: {current_length:,} bytes")
            
            # 5. 최종 요소 대기
            return self._wait_for_critical_elements()
            
        except Exception as e:
            self.logger.error(f"❌ 강화된 동적 콘텐츠 대기 중 오류: {e}")
            return False

    def _wait_for_js_frameworks(self):
        """다양한 JavaScript 프레임워크 로딩 대기"""
        try:
            # jQuery 대기
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script(
                        "return typeof jQuery === 'undefined' || (jQuery.active === 0 && jQuery(':animated').length === 0)"
                    )
                )
                self.logger.info("✅ jQuery 완료")
            except:
                pass
            
            # React 대기
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script(
                        """
                        if (typeof React === 'undefined') return true;
                        const reactFiber = document.querySelector('[data-reactroot]');
                        return reactFiber ? true : document.readyState === 'complete';
                        """
                    )
                )
                self.logger.info("✅ React 확인")
            except:
                pass
            
            # Vue.js 대기
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script(
                        """
                        if (typeof Vue === 'undefined') return true;
                        return document.readyState === 'complete';
                        """
                    )
                )
                self.logger.info("✅ Vue.js 확인")
            except:
                pass
            
            # Angular 대기
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script(
                        """
                        if (typeof angular === 'undefined') return true;
                        const injector = angular.element(document).injector();
                        if (!injector) return true;
                        const http = injector.get('$http');
                        return http.pendingRequests.length === 0;
                        """
                    )
                )
                self.logger.info("✅ Angular 확인")
            except:
                pass
                
        except Exception as e:
            self.logger.warning(f"JavaScript 프레임워크 대기 오류: {e}")

    def _wait_for_critical_elements(self) -> bool:
        """핵심 요소들이 로드될 때까지 대기"""
        try:
            # 텍스트 콘텐츠가 있는 주요 요소 대기
            text_selectors = [
                'p', 'div', 'span', 'article', 'section', 
                '.content', '.main', '.container'
            ]
            
            for selector in text_selectors:
                try:
                    WebDriverWait(self.driver, 3).until(
                        lambda driver: len(driver.find_elements(By.CSS_SELECTOR, f"{selector}:not(:empty)")) > 0
                    )
                    self.logger.info(f"✅ 텍스트 요소 발견: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # 이미지 로딩 완료 대기 (선택적)
            try:
                self.driver.execute_script("""
                    const images = document.querySelectorAll('img');
                    return Array.from(images).every(img => img.complete || img.naturalWidth > 0);
                """)
                self.logger.info("✅ 이미지 로딩 확인")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.logger.warning(f"핵심 요소 대기 오류: {e}")
            return False

    def trigger_lazy_loading(self):
        """강화된 Lazy loading 트리거"""
        try:
            # 1. 기본 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 2. 단계별 스크롤 (더 세밀하게)
            scroll_steps = [0.25, 0.5, 0.75, 1.0, 0.5, 0]
            for step in scroll_steps:
                scroll_position = f"document.body.scrollHeight * {step}"
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.8)
            
            # 3. 가시성 트리거 (intersection observer 이벤트)
            self.driver.execute_script("""
                // 모든 요소에 대해 스크롤 이벤트 트리거
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                
                // lazy loading 속성을 가진 이미지들 강제 로딩
                document.querySelectorAll('img[loading="lazy"], img[data-src]').forEach(img => {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                    img.scrollIntoView({behavior: 'smooth', block: 'center'});
                });
            """)
            
            time.sleep(2)
            self.logger.info("📜 강화된 스크롤 트리거 완료")
            
        except Exception as e:
            self.logger.warning(f"강화된 스크롤 트리거 실패: {e}")
    
    def extract_content_with_multiple_strategies(self) -> Dict[str, str]:
        """여러 전략으로 콘텐츠 추출"""
        content_results = {
            "full_text": "",
            "main_content": "",
            "contact_content": "",
            "method_used": "none"
        }
        
        try:
            # 전략 1: BeautifulSoup으로 전체 파싱
            if BS4_AVAILABLE:
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 스크립트, 스타일 제거
                for element in soup(["script", "style", "noscript", "meta", "link"]):
                    element.decompose()
                
                # 전체 텍스트
                full_text = soup.get_text()
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                content_results["full_text"] = full_text
                content_results["method_used"] = "beautifulsoup"
                
                self.logger.info(f"✅ BeautifulSoup 파싱: {len(full_text)} chars")
            
            # 전략 2: 주요 콘텐츠 영역 타겟팅
            main_content_texts = []
            for selector in self.content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 100:  # 의미있는 콘텐츠만
                            main_content_texts.append(text)
                            self.logger.info(f"📝 주요 콘텐츠 발견 ({selector}): {len(text)} chars")
                except:
                    continue
            
            if main_content_texts:
                content_results["main_content"] = " ".join(main_content_texts)
                if not content_results["method_used"] or content_results["method_used"] == "none":
                    content_results["method_used"] = "targeted_selectors"
            
            # 전략 3: 연락처 정보 영역 특별 추출
            contact_texts = []
            for selector in self.contact_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 20:  # 연락처 정보는 더 짧아도 됨
                            contact_texts.append(text)
                except:
                    continue
            
            if contact_texts:
                content_results["contact_content"] = " ".join(contact_texts)
                self.logger.info(f"📞 연락처 영역 발견: {len(contact_texts)}개 섹션")
            
            # 전략 4: Selenium 직접 텍스트 추출 (fallback)
            if not any([content_results["full_text"], content_results["main_content"]]):
                try:
                    body_element = self.driver.find_element(By.TAG_NAME, "body")
                    selenium_text = body_element.text.strip()
                    content_results["full_text"] = selenium_text
                    content_results["method_used"] = "selenium_direct"
                    self.logger.info(f"🔄 Selenium 직접 추출: {len(selenium_text)} chars")
                except:
                    self.logger.warning("❌ 모든 콘텐츠 추출 방법 실패")
            
            # 가장 긴 텍스트를 메인으로 사용
            all_texts = [
                content_results["full_text"],
                content_results["main_content"],
                content_results["contact_content"]
            ]
            
            longest_text = max(all_texts, key=len) if any(all_texts) else ""
            
            self.logger.info(f"📊 콘텐츠 추출 결과:")
            self.logger.info(f"  - 전체 텍스트: {len(content_results['full_text'])} chars")
            self.logger.info(f"  - 주요 콘텐츠: {len(content_results['main_content'])} chars")
            self.logger.info(f"  - 연락처 콘텐츠: {len(content_results['contact_content'])} chars")
            self.logger.info(f"  - 사용된 방법: {content_results['method_used']}")
            self.logger.info(f"  - 최종 선택: {len(longest_text)} chars")
            
            # 최종 텍스트 설정
            if longest_text:
                content_results["final_text"] = longest_text[:self.max_content_length]
            else:
                content_results["final_text"] = ""
            
        except Exception as e:
            self.logger.error(f"❌ 콘텐츠 추출 오류: {e}")
            content_results["final_text"] = ""
            content_results["method_used"] = "error"
        
        return content_results
    
    def extract_page_content(self, url: str) -> Dict[str, Any]:
        """
        향상된 페이지 파싱 (다중 전략 + 동적 콘텐츠 처리)
        """
        result = {
            "url": url,
            "title": "",
            "text_content": "",
            "status": "success",
            "contact_info": {
                "phones": [],
                "faxes": [],
                "emails": [],
                "addresses": []
            },
            "meta_info": {},
            "parsing_details": {},
            "error": None,
            "accessible": False,
            "raw_html": ""  # 원본 HTML 추가
        }
        
        try:
            # WebDriver 초기화 확인
            if not self.driver:
                self.logger.warning("⚠️ WebDriver가 초기화되지 않음. 재초기화 시도...")
                self.setup_driver()
                
                if not self.driver:
                    result["status"] = "error"
                    result["error"] = "WebDriver 초기화 실패"
                    self.logger.error(f"❌ WebDriver 초기화 실패: {url}")
                    return result
            
            self.logger.info(f"🌐 향상된 페이지 접속: {url}")
            
            # 1. 페이지 로드
            load_start_time = time.time()
            self.driver.get(url)
            
            # 2. 동적 콘텐츠 로딩 대기
            if self.wait_for_dynamic_content(url):
                self.logger.info("✅ 동적 콘텐츠 로딩 완료")
            else:
                self.logger.warning("⚠️ 동적 콘텐츠 로딩 시간 초과")
            
            # 3. 페이지 접근 가능성 확인
            if not self.is_page_accessible():
                result["status"] = "error"
                result["error"] = "페이지 접근 불가 (404, 403 등)"
                result["accessible"] = False
                self.logger.warning(f"❌ 페이지 접근 불가: {url}")
                return result
            
                result["accessible"] = True
                
                # 4. 기본 정보 추출
            try:
                result["title"] = self.driver.title.strip()
                result["raw_html"] = self.driver.page_source
                self.logger.info(f"📄 페이지 제목: {result['title']}")
                self.logger.info(f"📊 HTML 크기: {len(result['raw_html']):,} bytes")
            except Exception as e:
                self.logger.warning(f"기본 정보 추출 오류: {e}")
                
            # 5. 콘텐츠 추출 (다중 전략)
            content_results = self.extract_content_with_multiple_strategies()
            result["text_content"] = content_results.get("final_text", "")
                result["parsing_details"] = {
                "content_extraction_method": content_results.get("method_used", "unknown"),
                "full_text_length": len(content_results.get("full_text", "")),
                "main_content_length": len(content_results.get("main_content", "")),
                "contact_content_length": len(content_results.get("contact_content", "")),
                "processing_time": time.time() - load_start_time
                }
                
            # 6. 메타 정보 추출 (BeautifulSoup 사용)
            if BS4_AVAILABLE and result["raw_html"]:
                    try:
                    soup = BeautifulSoup(result["raw_html"], 'html.parser')
                        result["meta_info"] = self.extract_meta_info(soup)
                    except Exception as e:
                    self.logger.warning(f"메타 정보 추출 오류: {e}")
            
            # 7. 연락처 정보 추출
            if result["text_content"]:
                try:
                    result["contact_info"] = self.extract_contact_info(result["text_content"])
                    contact_count = sum(len(v) for v in result["contact_info"].values())
                    self.logger.info(f"📞 추출된 연락처: {contact_count}개")
                    
                    # 연락처별 개수 로깅
                    for contact_type, contacts in result["contact_info"].items():
                        if contacts:
                            self.logger.info(f"  - {contact_type}: {len(contacts)}개 - {contacts[:3]}")  # 최대 3개만 표시
                
                except Exception as e:
                    self.logger.warning(f"연락처 정보 추출 오류: {e}")
            
            # 8. 결과 검증
            if not result["text_content"] or len(result["text_content"]) < 100:
                result["status"] = "warning"
                result["error"] = "추출된 텍스트 콘텐츠가 부족함"
                self.logger.warning(f"⚠️ 텍스트 콘텐츠 부족: {len(result['text_content'])} chars")
            
            load_time = time.time() - load_start_time
            self.logger.info(f"✅ 페이지 파싱 완료: {url} ({load_time:.2f}초)")
        
        except TimeoutException:
            result["status"] = "timeout"
            result["error"] = "페이지 로드 시간 초과"
            self.logger.warning(f"⏰ 타임아웃: {url}")
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.logger.error(f"❌ 파싱 오류: {url} - {e}")
            
            # WebDriver 재초기화 시도
            if "NoneType" in str(e) or "driver" in str(e).lower():
                self.logger.warning("🔄 WebDriver 관련 오류로 재초기화 시도...")
                try:
                    self.setup_driver()
                except Exception as setup_error:
                    self.logger.error(f"❌ WebDriver 재초기화 실패: {setup_error}")
        
        return result
    
    def is_page_accessible(self) -> bool:
        """페이지 접근 가능 여부 확인 (개선된 버전)"""
        try:
            # 1. 타이틀 확인
            title = self.driver.title.lower()
            if any(keyword in title for keyword in ['404', 'not found', 'error', '오류', '찾을 수 없', '접근 거부']):
                return False
            
            # 2. 페이지 소스 크기 확인
            page_source = self.driver.page_source
            if len(page_source) < 1000:  # 최소 크기 증가
                return False
            
            # 3. 실제 body 텍스트 확인
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
                if len(body_text) < 50:  # 실제 텍스트가 너무 적음
                    return False
            except:
                return False
            
            # 4. 에러 메시지 확인 (페이지 소스와 body 텍스트 모두)
            error_keywords = ['404', 'not found', 'page not found', '페이지를 찾을 수 없', 
                            '접근이 거부', 'access denied', 'forbidden', '503', '500']
            
            combined_text = (page_source + " " + body_text).lower()
            if any(keyword in combined_text for keyword in error_keywords):
                return False
            
            return True
            
        except Exception:
            return False
    
    def extract_meta_info(self, soup) -> Dict[str, str]:
        """메타 정보 추출"""
        meta_info = {
            "description": "",
            "keywords": "",
            "author": "",
            "og_title": "",
            "og_description": ""
        }
        
        try:
            # 기본 메타 태그
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', '').lower()
                property_name = tag.get('property', '').lower()
                content = tag.get('content', '')
                
                if name == 'description':
                    meta_info["description"] = content
                elif name == 'keywords':
                    meta_info["keywords"] = content
                elif name == 'author':
                    meta_info["author"] = content
                elif property_name == 'og:title':
                    meta_info["og_title"] = content
                elif property_name == 'og:description':
                    meta_info["og_description"] = content
        
        except Exception as e:
            self.logger.warning(f"메타 정보 추출 오류: {e}")
        
        return meta_info
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """연락처 정보 추출"""
        contact_info = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": []
        }
        
        try:
            # 전화번호 추출
            for pattern in PHONE_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    phone = self.clean_phone_number(match)
                    if phone and phone not in contact_info["phones"]:
                        contact_info["phones"].append(phone)
            
            # 팩스번호 추출
            for pattern in FAX_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    fax = self.clean_phone_number(match)
                    if fax and fax not in contact_info["faxes"]:
                        contact_info["faxes"].append(fax)
            
            # 이메일 추출
            for pattern in EMAIL_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    email = match.strip()
                    if self.is_valid_email(email) and email not in contact_info["emails"]:
                        contact_info["emails"].append(email)
            
            # 주소 추출
            for pattern in ADDRESS_EXTRACTION_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    address = self.clean_address(match)
                    if address and address not in contact_info["addresses"]:
                        contact_info["addresses"].append(address)
        
        except Exception as e:
            self.logger.warning(f"연락처 정보 추출 오류: {e}")
        
        return contact_info
    
    def clean_phone_number(self, phone: str) -> Optional[str]:
        """전화번호 정리"""
        if not phone:
            return None
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 길이 확인
        if len(digits) < 9 or len(digits) > 11:
            return None
        
        # 포맷팅
        if digits.startswith('02'):
            if len(digits) == 9:
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
            else:
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        elif digits.startswith(('010', '011', '016', '017', '018', '019', '070')):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        else:
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    def is_valid_email(self, email: str) -> bool:
        """이메일 유효성 확인"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def clean_address(self, address: str) -> Optional[str]:
        """주소 정리"""
        if not address:
            return None
        
        # 공백 정리
        cleaned = re.sub(r'\s+', ' ', address.strip())
        
        # 최소 길이 확인
        if len(cleaned) < 10:
            return None
        
        return cleaned
    
    def summarize_with_ai(self, organization_name: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI로 페이지 내용 요약 및 정리 (Gemini 텍스트 응답 처리)"""
        if not self.use_ai or not self.ai_model:
            self.logger.warning("AI 기능을 사용할 수 없음")
            return self._create_fallback_summary("AI 기능 비활성화", page_data)
        
        try:
            # AI 프롬프트 구성 (JSON 요청하지만 텍스트로 받을 것을 염두)
            prompt = f"""
    '{organization_name}' 기관의 홈페이지를 분석해주세요.

    **기본 정보:**
    - 제목: {page_data.get('title', '')}
    - URL: {page_data.get('url', '')}
    - 메타 설명: {page_data.get('meta_info', {}).get('description', '')}

    **홈페이지 내용:**
    {page_data.get('text_content', '')[:3000]}

    **추출된 연락처:**
    - 전화번호: {', '.join(page_data.get('contact_info', {}).get('phones', []))}
    - 팩스번호: {', '.join(page_data.get('contact_info', {}).get('faxes', []))}
    - 이메일: {', '.join(page_data.get('contact_info', {}).get('emails', []))}
    - 주소: {', '.join(page_data.get('contact_info', {}).get('addresses', []))}

    **분석 요청:**
    1. 기관 요약 (3-4문장)
    2. 기관 유형 분류 (교회, 병원, 학교, 정부기관, 기업, 단체 등)
    3. 주요 서비스나 활동 (최대 3개)
    4. 설립연도 (홈페이지에서 찾을 수 있다면)
    5. 주요 위치나 지역
    6. 연락처 정보 완성도 평가 (상/중/하)
    7. 홈페이지 품질 평가 (상/중/하)
    8. 특별한 특징이나 서비스

    **응답 형식 (가능하면 이 형식으로, 아니면 일반 텍스트로):**
    SUMMARY: [기관 요약]
    CATEGORY: [기관 유형]
    SERVICES: [서비스1, 서비스2, 서비스3]
    ESTABLISHMENT: [설립연도 또는 "정보없음"]
    LOCATION: [위치정보]
    CONTACT_QUALITY: [상/중/하]
    WEBSITE_QUALITY: [상/중/하]
    FEATURES: [특징1, 특징2]
    """
            
            # 프롬프트 로깅 (디버깅용)
            self.logger.debug(f"🤖 AI 프롬프트 ({organization_name}):\n{'-'*50}\n{prompt}\n{'-'*50}")
            
            # AI 호출
            response = self.ai_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # AI 응답 전체 내용 로깅
            self.logger.info(f"🤖 AI 응답 ({organization_name}) - 길이: {len(response_text)} chars")
            self.logger.info(f"📝 AI 응답 내용:\n{'-'*50}\n{response_text}\n{'-'*50}")
            
            # 응답이 너무 짧으면 경고
            if len(response_text) < 50:
                self.logger.warning(f"⚠️ AI 응답이 너무 짧습니다: {response_text}")
            
            # 응답 파싱 (여러 방법 시도)
            ai_summary = self._parse_ai_summary_response(response_text, organization_name)
            
            # 파싱 결과도 로깅
            self.logger.info(f"🔍 파싱 결과 ({organization_name}):")
            self.logger.info(f"  - 요약: {ai_summary.get('summary', 'None')[:100]}...")
            self.logger.info(f"  - 카테고리: {ai_summary.get('category', 'None')}")
            self.logger.info(f"  - 서비스: {ai_summary.get('services', [])}")
            self.logger.info(f"  - 위치: {ai_summary.get('location', 'None')}")
            
            self.logger.info(f"✅ AI 요약 완료: {organization_name}")
            return ai_summary
            
        except Exception as e:
            self.logger.error(f"❌ AI 요약 실패: {organization_name} - {e}")
            import traceback
            self.logger.error(f"📊 오류 상세:\n{traceback.format_exc()}")
            return self._create_fallback_summary(str(e), page_data)
    
    def _parse_ai_summary_response(self, response_text: str, organization_name: str) -> Dict[str, Any]:
        """AI 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # 방법 1: JSON 형태 응답 시도
            json_result = self._try_parse_json_response(response_text)
            if json_result:
                self.logger.info("JSON 형태 응답 파싱 성공")
                return json_result
            
            # 방법 2: 구조화된 텍스트 응답 파싱
            structured_result = self._parse_structured_text_response(response_text)
            if structured_result:
                self.logger.info("구조화된 텍스트 응답 파싱 성공")
                return structured_result
            
            # 방법 3: 자유 텍스트에서 정보 추출
            text_result = self._extract_from_free_text(response_text, organization_name)
            self.logger.info("자유 텍스트에서 정보 추출 완료")
            return text_result
            
        except Exception as e:
            self.logger.error(f"응답 파싱 중 오류: {e}")
            return self._create_fallback_summary(f"파싱 오류: {e}", {})

    def _try_parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """JSON 형태 응답 파싱 시도"""
        try:
            import json
            
            # ```json 블록에서 추출
            if '```json' in response_text:
                json_part = response_text.split('```json')[1].split('```')[0].strip()
                parsed = json.loads(json_part)
                return self._normalize_json_structure(parsed)
            
            # { } 사이의 JSON 추출
            elif '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                parsed = json.loads(json_str)
                return self._normalize_json_structure(parsed)
            
            return None
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.logger.warning(f"JSON 파싱 실패: {e}")
            return None

    def _parse_structured_text_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """SUMMARY:, CATEGORY: 형태의 구조화된 텍스트 파싱"""
        try:
            result = {
                "summary": "",
                "category": "기타",
                "main_services": [],
                "key_info": {},
                "extracted_features": []
            }
            
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('SUMMARY:'):
                    result["summary"] = line.replace('SUMMARY:', '').strip()
                
                elif line.startswith('CATEGORY:'):
                    result["category"] = line.replace('CATEGORY:', '').strip()
                
                elif line.startswith('SERVICES:'):
                    services_text = line.replace('SERVICES:', '').strip()
                    # [서비스1, 서비스2] 또는 "서비스1, 서비스2" 형태 파싱
                    services = self._parse_list_string(services_text)
                    result["main_services"] = services[:3]  # 최대 3개
                
                elif line.startswith('ESTABLISHMENT:'):
                    establishment = line.replace('ESTABLISHMENT:', '').strip()
                    if establishment and establishment != "정보없음":
                        result["key_info"]["establishment_year"] = establishment
                
                elif line.startswith('LOCATION:'):
                    location = line.replace('LOCATION:', '').strip()
                    if location:
                        result["key_info"]["location"] = location
                
                elif line.startswith('CONTACT_QUALITY:'):
                    contact_quality = line.replace('CONTACT_QUALITY:', '').strip()
                    if contact_quality in ['상', '중', '하']:
                        result["key_info"]["contact_verified"] = contact_quality
                
                elif line.startswith('WEBSITE_QUALITY:'):
                    website_quality = line.replace('WEBSITE_QUALITY:', '').strip()
                    if website_quality in ['상', '중', '하']:
                        result["key_info"]["website_quality"] = website_quality
                
                elif line.startswith('FEATURES:'):
                    features_text = line.replace('FEATURES:', '').strip()
                    features = self._parse_list_string(features_text)
                    result["extracted_features"] = features
            
            # 최소한의 정보가 있는지 확인
            if result["summary"] or result["category"] != "기타":
                return result
            
            return None
            
        except Exception as e:
            self.logger.warning(f"구조화된 텍스트 파싱 실패: {e}")
            return None

    def _extract_from_free_text(self, response_text: str, organization_name: str) -> Dict[str, Any]:
        """자유 텍스트에서 정보 추출 (마지막 수단)"""
        result = {
            "summary": "",
            "category": "기타",
            "main_services": [],
            "key_info": {},
            "extracted_features": []
        }
        
        try:
            # 텍스트를 요약으로 사용 (길이 제한)
            clean_text = re.sub(r'\s+', ' ', response_text).strip()
            result["summary"] = clean_text[:500] + ("..." if len(clean_text) > 500 else "")
            
            # 키워드로 카테고리 추정
            text_lower = response_text.lower()
            
            if any(keyword in text_lower for keyword in ['교회', 'church', '예배', '목회', '신앙', '성당']):
                result["category"] = "교회"
            elif any(keyword in text_lower for keyword in ['병원', 'hospital', '의료', '진료', '치료', '클리닉']):
                result["category"] = "병원"
            elif any(keyword in text_lower for keyword in ['학교', 'school', '교육', '학생', '대학', '학원']):
                result["category"] = "교육기관"
            elif any(keyword in text_lower for keyword in ['정부', '시청', '구청', '관청', '.go.kr', '공공']):
                result["category"] = "정부기관"
            elif any(keyword in text_lower for keyword in ['회사', '기업', '사업', '.co.kr', '주식회사']):
                result["category"] = "기업"
            elif any(keyword in text_lower for keyword in ['단체', '협회', '재단', '센터', '.or.kr']):
                result["category"] = "비영리단체"
            
            # 기본 정보 추가
            result["key_info"]["text_analysis"] = True
            result["key_info"]["organization_name"] = organization_name
            
            self.logger.info(f"자유 텍스트 분석 완료: {result['category']}")
            
        except Exception as e:
            self.logger.error(f"자유 텍스트 추출 오류: {e}")
            result["summary"] = f"텍스트 분석 오류: {str(e)}"
        
        return result

    def _parse_list_string(self, list_str: str) -> List[str]:
        """문자열에서 리스트 추출 (여러 형태 지원)"""
        if not list_str:
            return []
        
        try:
            # [item1, item2] 형태
            if list_str.startswith('[') and list_str.endswith(']'):
                import json
                return json.loads(list_str)
            
            # "item1, item2" 형태
            elif ',' in list_str:
                items = [item.strip().strip('"\'') for item in list_str.split(',')]
                return [item for item in items if item]
            
            # 단일 항목
            else:
                clean_item = list_str.strip().strip('"\'')
                return [clean_item] if clean_item else []
                
        except Exception:
            # 파싱 실패시 텍스트 그대로 반환
            return [list_str.strip()] if list_str.strip() else []

    def _normalize_json_structure(self, parsed_json: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 구조를 표준 형태로 정규화"""
        normalized = {
            "summary": "",
            "category": "기타",
            "main_services": [],
            "key_info": {},
            "extracted_features": []
        }
        
        try:
            # 기본 필드 매핑
            if 'summary' in parsed_json:
                normalized["summary"] = str(parsed_json['summary'])
            
            if 'category' in parsed_json:
                normalized["category"] = str(parsed_json['category'])
            
            if 'main_services' in parsed_json:
                services = parsed_json['main_services']
                if isinstance(services, list):
                    normalized["main_services"] = [str(s) for s in services[:3]]
                elif isinstance(services, str):
                    normalized["main_services"] = [services]
            
            if 'key_info' in parsed_json and isinstance(parsed_json['key_info'], dict):
                normalized["key_info"] = parsed_json['key_info']
            
            if 'extracted_features' in parsed_json:
                features = parsed_json['extracted_features']
                if isinstance(features, list):
                    normalized["extracted_features"] = [str(f) for f in features]
                elif isinstance(features, str):
                    normalized["extracted_features"] = [features]
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"JSON 정규화 오류: {e}")
            return normalized

    def _create_fallback_summary(self, error_msg: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI 실패시 기본 요약 생성"""
        return {
            "summary": f"AI 요약 생성 실패: {error_msg}",
            "category": "분류불가",
            "main_services": [],
            "key_info": {
                "ai_error": True,
                "error_message": error_msg,
                "page_title": page_data.get('title', ''),
                "has_content": bool(page_data.get('text_content', ''))
            },
            "extracted_features": ["AI 분석 실패"]
        }
    
    def process_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """기관 목록 처리"""
        if not self.driver:
            self.setup_driver()
        
        processed_orgs = []
        total_count = len(organizations)
        success_count = 0
        
        try:
            for i, org in enumerate(organizations, 1):
                try:
                    org_name = org.get('name', 'Unknown')
                    homepage_url = org.get('homepage', '').strip()
                    
                    self.logger.info(f"처리 중 ({i}/{total_count}): {org_name}")
                    
                    # 기존 데이터 복사
                    processed_org = org.copy()
                    
                    # 홈페이지 URL이 있는 경우에만 파싱
                    if homepage_url and homepage_url.startswith(('http://', 'https://')):
                        self.logger.info(f"🔍 홈페이지 파싱 시작: {homepage_url}")
                        
                        # 페이지 내용 추출
                        page_data = self.extract_page_content(homepage_url)
                        
                        if page_data["status"] == "success" and page_data["accessible"]:
                            # AI 요약
                            ai_summary = self.summarize_with_ai(org_name, page_data)
                            
                            # 결과 통합
                            processed_org.update({
                                "homepage_parsed": True,
                                "page_title": page_data["title"],
                                "page_content_length": len(page_data["text_content"]),
                                "contact_info_extracted": page_data["contact_info"],
                                "meta_info": page_data["meta_info"],
                                "ai_summary": ai_summary,
                                "parsing_timestamp": datetime.now().isoformat(),
                                "parsing_status": "success"
                            })
                            
                            success_count += 1
                            self.logger.info(f"✅ 파싱 성공: {org_name}")
                            
                        else:
                            # 파싱 실패
                            processed_org.update({
                                "homepage_parsed": False,
                                "parsing_status": "failed",
                                "parsing_error": page_data.get("error", "Unknown error"),
                                "parsing_timestamp": datetime.now().isoformat()
                            })
                            self.logger.warning(f"⚠️ 파싱 실패: {org_name} - {page_data.get('error')}")
                    
                    else:
                        # 홈페이지 URL이 없는 경우
                        processed_org.update({
                            "homepage_parsed": False,
                            "parsing_status": "no_homepage",
                            "parsing_timestamp": datetime.now().isoformat()
                        })
                        self.logger.info(f"⏭️ 홈페이지 없음: {org_name}")
                    
                    processed_orgs.append(processed_org)
                    
                    # 진행 상황 출력
                    if i % 10 == 0:
                        success_rate = success_count / i * 100
                        self.logger.info(f"📊 진행률: {success_count}/{i} ({success_rate:.1f}%)")
                    
                    # 지연 (서버 부하 방지)
                    if i < total_count:
                        self.add_delay()
                
                except Exception as e:
                    self.logger.error(f"❌ 처리 오류: {org.get('name', 'Unknown')} - {e}")
                    # 오류 발생시에도 기본 데이터는 보존
                    processed_org = org.copy()
                    processed_org.update({
                        "homepage_parsed": False,
                        "parsing_status": "error",
                        "parsing_error": str(e),
                        "parsing_timestamp": datetime.now().isoformat()
                    })
                    processed_orgs.append(processed_org)
                    continue
        
        finally:
            self.close_driver()
        
        return processed_orgs
    
    def save_results(self, organizations: List[Dict], output_file: str) -> bool:
        """결과를 JSON 파일로 저장"""
        try:
            # 결과 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(organizations, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"결과 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"저장 중 오류: {e}")
            return False

    async def ai_search_homepage(self, org_name: str, category: str) -> List[Dict]:
        """AI 기반 홈페이지 검색"""
        try:
            self.logger.info(f"🔍 AI 홈페이지 검색: {org_name} ({category})")
            
            # AI를 사용한 검색 전략
            search_results = []
            
            # 1. 기본 검색어 생성
            search_queries = [
                f"{org_name}",
                f"{org_name} {category}",
                f"{org_name} 홈페이지",
                f"{org_name} 공식사이트"
            ]
            
            # 2. AI 모델을 사용하여 검색 쿼리 개선
            if self.use_ai and self.ai_model:
                try:
                    enhanced_query = await self._generate_enhanced_search_query(org_name, category)
                    if enhanced_query:
                        search_queries.append(enhanced_query)
                except Exception as e:
                    self.logger.warning(f"AI 검색 쿼리 생성 실패: {e}")
            
            # 3. 각 검색어로 검색 (간단한 구현)
            for query in search_queries[:3]:  # 최대 3개만
                try:
                    # 실제 검색 로직 (Google 검색 API 등을 사용할 수 있음)
                    # 여기서는 간단한 예시로 구현
                    result = await self._perform_search(query, org_name)
                    if result:
                        search_results.append(result)
                        break  # 첫 번째 결과를 찾으면 중단
                except Exception as e:
                    self.logger.warning(f"검색 실패 [{query}]: {e}")
                    continue
            
            self.logger.info(f"AI 홈페이지 검색 완료: {len(search_results)}개 결과")
            return search_results
            
        except Exception as e:
            self.logger.error(f"AI 홈페이지 검색 오류: {e}")
            return []
    
    async def _generate_enhanced_search_query(self, org_name: str, category: str) -> str:
        """AI로 향상된 검색 쿼리 생성"""
        try:
            prompt = f"""
            다음 기관의 홈페이지를 찾기 위한 최적의 검색어를 생성해주세요:
            
            기관명: {org_name}
            카테고리: {category}
            
            가장 효과적인 검색어 하나만 제안해주세요.
            """
            
            response = self.ai_model.generate_content(prompt)
            enhanced_query = response.text.strip()
            
            # 검색어가 너무 길면 자르기
            if len(enhanced_query) > 100:
                enhanced_query = enhanced_query[:100]
            
            return enhanced_query
            
        except Exception as e:
            self.logger.warning(f"AI 검색 쿼리 생성 오류: {e}")
            return ""
    
    async def _perform_search(self, query: str, org_name: str) -> Optional[Dict]:
        """실제 검색 수행 (간단한 구현)"""
        try:
            # 여기서는 기본적인 URL 패턴을 추정
            # 실제 환경에서는 Google Search API 등을 사용
            
            # 기본 도메인 패턴들
            domain_patterns = [
                f"www.{org_name.lower().replace(' ', '')}.com",
                f"www.{org_name.lower().replace(' ', '')}.co.kr",
                f"www.{org_name.lower().replace(' ', '')}.or.kr",
                f"{org_name.lower().replace(' ', '')}.com",
                f"{org_name.lower().replace(' ', '')}.co.kr"
            ]
            
            # 각 패턴에 대해 접근 시도
            for pattern in domain_patterns:
                try:
                    test_url = f"https://{pattern}"
                    # 실제로는 여기서 HTTP 요청을 보내서 확인
                    # 지금은 간단히 패턴만 반환
                    return {
                        "url": test_url,
                        "type": "추정",
                        "confidence": 0.6,
                        "search_query": query
                    }
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.warning(f"검색 수행 오류: {e}")
            return None

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🔍 홈페이지 직접 파싱 및 AI 정리 도구")
    print("=" * 70)
    
    try:
        # 설정
        use_headless = False  # GUI 모드로 브라우저 창 표시
        print(f"🌐 브라우저 모드: {'Headless' if use_headless else 'GUI'}")
        print(f"🤖 AI 요약 기능: {'활성화' if AI_AVAILABLE else '비활성화'}")
        print(f"🍲 HTML 파싱: {'BeautifulSoup 사용' if BS4_AVAILABLE else '기본 파싱'}")
        
        # 파서 인스턴스 생성
        parser = HomepageParser(headless=use_headless)
        
        # 파일 경로 설정 - 동적으로 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))  # test 디렉토리
        base_dir = os.path.dirname(current_dir)  # 프로젝트 루트 디렉토리
        data_json_dir = os.path.join(base_dir, "data", "json")
        
        print(f"📂 프로젝트 루트: {base_dir}")
        print(f"📂 JSON 디렉토리: {data_json_dir}")
        
        # 우선 순위 파일 목록
        priority_files = [
            "combined.json"
            
        ]
        
        input_file = None
        output_file = os.path.join(base_dir, f"parsed_homepages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # 우선순위 파일들 확인
        for priority_file in priority_files:
            priority_path = os.path.join(data_json_dir, priority_file)
            if os.path.exists(priority_path):
                input_file = priority_path
                print(f"✅ 우선순위 파일 발견: {priority_file}")
                break
        
        # 우선순위 파일이 없으면 data/json 디렉토리에서 탐색
        if not input_file:
            print(f"📂 data/json 디렉토리에서 파일 탐색 중...")
            
            if os.path.exists(data_json_dir):
                json_files = [f for f in os.listdir(data_json_dir) 
                             if f.endswith('.json') and 'homepage' in f.lower()]
                
                if json_files:
                    # 날짜순으로 정렬 (최신 파일 우선)
                    json_files.sort(reverse=True)
                    print(f"📁 data/json 디렉토리의 홈페이지 관련 JSON 파일들:")
                    for i, file in enumerate(json_files, 1):
                        file_path = os.path.join(data_json_dir, file)
                        file_size = os.path.getsize(file_path) // 1024  # KB
                        print(f"  {i}. {file} ({file_size}KB)")
                    
                    # 사용자가 파일 선택할 수 있도록
                    choice = input(f"\n사용할 파일 번호를 선택하세요 (1-{len(json_files)}, 엔터=1번 파일): ").strip()
                    
                    if choice == "":
                        choice_idx = 0  # 기본적으로 첫 번째 파일
                    elif choice.isdigit():
                        choice_idx = int(choice) - 1
                    else:
                        print("❌ 잘못된 선택입니다.")
                        return 1
                    
                    if 0 <= choice_idx < len(json_files):
                        input_file = os.path.join(data_json_dir, json_files[choice_idx])
                        print(f"✅ 선택된 파일: {json_files[choice_idx]}")
                    else:
                        print("❌ 잘못된 선택입니다.")
                        return 1
                else:
                    print("❌ data/json 디렉토리에 홈페이지 관련 JSON 파일이 없습니다.")
                    
                    # 일반 JSON 파일들도 탐색
                    all_json_files = [f for f in os.listdir(data_json_dir) if f.endswith('.json')]
                    if all_json_files:
                        print(f"📁 data/json 디렉토리의 모든 JSON 파일들:")
                        for i, file in enumerate(all_json_files, 1):
                            file_path = os.path.join(data_json_dir, file)
                            file_size = os.path.getsize(file_path) // 1024  # KB
                            print(f"  {i}. {file} ({file_size}KB)")
                        
                        choice = input(f"\n사용할 파일 번호를 선택하세요 (1-{len(all_json_files)}, 엔터=종료): ").strip()
                        if choice and choice.isdigit():
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(all_json_files):
                                input_file = os.path.join(data_json_dir, all_json_files[choice_idx])
                                print(f"✅ 선택된 파일: {all_json_files[choice_idx]}")
                            else:
                                print("❌ 잘못된 선택입니다.")
                                return 1
                        else:
                            print("⏹️ 작업을 취소합니다.")
                            return 1
                    else:
                        print("❌ data/json 디렉토리에 JSON 파일이 없습니다.")
                        return 1
            else:
                print(f"❌ data/json 디렉토리를 찾을 수 없습니다: {data_json_dir}")
                return 1
        
        print(f"📂 입력 파일: {input_file}")
        print(f"💾 출력 파일: {output_file}")
        
        # JSON 파일 로드
        print("📖 데이터 로딩 중...")
        with open(input_file, 'r', encoding='utf-8') as f:
            organizations = json.load(f)
        
        print(f"📊 로드된 기관 수: {len(organizations)}")
        
        # 홈페이지가 있는 기관만 확인
        orgs_with_homepage = [org for org in organizations 
                            if org.get('homepage') and org['homepage'].strip().startswith(('http://', 'https://'))]
        print(f"🌐 홈페이지가 있는 기관: {len(orgs_with_homepage)}개")
        
        # 처리할 기관 수 제한 (테스트용)
        max_process = input(f"처리할 기관 수 (전체: {len(organizations)}, 홈페이지 있음: {len(orgs_with_homepage)}, 엔터=전체): ").strip()
        if max_process:
            max_process = int(max_process)
            organizations = organizations[:max_process]
        
        print(f"\n🔄 {len(organizations)}개 기관 처리 시작...")
        print("📝 실제 브라우저로 홈페이지를 방문하여 파싱합니다.")
        print("🤖 AI가 내용을 요약하고 정리합니다.")
        
        # 처리 시작
        processed_organizations = parser.process_organizations(organizations)
        
        # 결과 저장
        if parser.save_results(processed_organizations, output_file):
            print(f"\n✅ 처리 완료!")
            print(f"📁 결과 파일: {output_file}")
            
            # 통계 계산
            total_processed = len(processed_organizations)
            successful_parses = sum(1 for org in processed_organizations 
                                  if org.get('parsing_status') == 'success')
            failed_parses = sum(1 for org in processed_organizations 
                              if org.get('parsing_status') == 'failed')
            no_homepage = sum(1 for org in processed_organizations 
                            if org.get('parsing_status') == 'no_homepage')
            error_count = sum(1 for org in processed_organizations 
                            if org.get('parsing_status') == 'error')
            
            print(f"\n📈 최종 통계:")
            print(f"  - 전체 기관: {total_processed}개")
            print(f"  - 파싱 성공: {successful_parses}개")
            print(f"  - 파싱 실패: {failed_parses}개")
            print(f"  - 홈페이지 없음: {no_homepage}개")
            print(f"  - 처리 오류: {error_count}개")
            if successful_parses > 0:
                print(f"  - 성공률: {successful_parses/(successful_parses+failed_parses)*100:.1f}%")
            
            # 샘플 결과 출력
            successful_orgs = [org for org in processed_organizations 
                             if org.get('parsing_status') == 'success']
            if successful_orgs:
                print(f"\n📋 샘플 결과:")
                sample_org = successful_orgs[0]
                print(f"  기관명: {sample_org.get('name', 'Unknown')}")
                print(f"  홈페이지: {sample_org.get('homepage', 'None')}")
                print(f"  AI 요약: {sample_org.get('ai_summary', {}).get('summary', 'None')[:100]}...")
        
        else:
            print(f"\n❌ 결과 저장 실패")
            return 1
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
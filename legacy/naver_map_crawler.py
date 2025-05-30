#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 네이버 지도 크롤러 - 더 안정적인 선택자 사용
"""

import json
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from fax_crawler import GoogleContactCrawler

class NaverMapCrawler:
    def __init__(self):
        self.logger = self.setup_logger()
        self.base_url = "https://map.naver.com/p/search/"
        self.driver = None
        self.wait = None
        self.setup_driver()
        
        # 🔧 개선된 선택자들
        self.search_selectors = {
            # 검색창 - 여러 방법으로 찾기
            'input': [
                "input.input_search",  # 클래스 기반 (가장 안정적)
                "#home_search_input_box input[type='text']",  # 컨테이너 + 타입
                "input[class*='input_search']",  # 부분 클래스 매칭
                "input[id*='input_search']",  # 부분 ID 매칭
                "div.input_box input",  # 구조 기반
            ],
            # 검색 버튼
            'button': [
                "button.button_search",  # 클래스 기반 (가장 안정적)
                "#home_search_input_box button[type='button']",
                "button[class*='button_search']",
                "div.search_box button:first-child",  # 구조 기반
            ]
        }
        
        # 연락처 정보 선택자들 (더 유연하게)
        self.contact_selectors = {
            'phone': [
                "span[class*='phone']",
                "a[href^='tel:']",
                "div[class*='contact'] span:contains('02-')",
                "div[class*='contact'] span:contains('031-')",
                "div[class*='contact'] span:contains('032-')",
                # 일반적인 전화번호 패턴들
                "span:contains('-')",
                ".place_section_content span",
            ],
            'fax': [
                "span[class*='fax']",
                "div[class*='contact'] span:contains('팩스')",
                "div:contains('팩스') + span",
                "div:contains('FAX') + span",
            ]
        }
        
        # 구글 연락처 크롤러 인스턴스
        self.google_crawler = None
        
    def setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('naver_map_crawler')
        logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 콘솔 핸들러만 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - [네이버크롤러] - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        self.logger.info("Chrome 드라이버 설정 시작")
        print("🔧 Chrome 드라이버 설정 중...")
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 헤드리스 모드 (필요시 주석 해제)
        # options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)  # 대기 시간 증가
        self.logger.info("Chrome 드라이버 설정 완료")
        print("✅ Chrome 드라이버 설정 완료")
    
    def find_element_by_selectors(self, selectors, element_name="요소"):
        """여러 선택자로 요소 찾기"""
        for i, selector in enumerate(selectors):
            try:
                if selector.startswith("//"):
                    # XPath
                    element = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    # CSS Selector  
                    element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                self.logger.info(f"{element_name} 발견: {selector}")
                print(f"✅ {element_name} 발견: {selector}")
                return element
                
            except TimeoutException:
                self.logger.debug(f"{element_name} 선택자 실패 ({i+1}/{len(selectors)}): {selector}")
                continue
            except Exception as e:
                self.logger.debug(f"{element_name} 선택자 오류 ({i+1}/{len(selectors)}): {selector} - {e}")
                continue
        
        self.logger.warning(f"{element_name}를 찾을 수 없음 - 모든 선택자 실패")
        print(f"❌ {element_name}를 찾을 수 없습니다")
        return None
    
    def search_organization(self, name):
        """기관명`으로 검색 - 개선된 버전"""
        try:
            self.logger.info(f"기관 검색 시작: {name}")
            print(f"🔍 '{name}' 검색 시작...")
            
            # 네이버 지도 페이지로 이동
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # 검색창 찾기
            search_input = self.find_element_by_selectors(
                self.search_selectors['input'], 
                "검색창"
            )
            
            if not search_input:
                return False
            
            # 검색어 입력
            search_input.clear()
            time.sleep(0.5)
            search_input.send_keys(name)
            self.logger.info(f"검색어 입력 완료: {name}")
            print(f"✏️ 검색어 입력: {name}")
            
            # 검색 실행 (Enter 키 또는 버튼 클릭)
            try:
                # 먼저 Enter 키로 시도 (더 안정적)
                search_input.send_keys(Keys.RETURN)
                self.logger.info("Enter 키로 검색 실행")
                print("⌨️ Enter 키로 검색 실행")
                
            except Exception as e:
                # Enter 키 실패시 버튼 클릭 시도
                self.logger.info("Enter 키 실패, 검색 버튼 클릭 시도")
                search_button = self.find_element_by_selectors(
                    self.search_selectors['button'], 
                    "검색 버튼"
                )
                
                if search_button:
                    search_button.click()
                    self.logger.info("검색 버튼 클릭 완료")
                    print("🔍 검색 버튼 클릭")
                else:
                    self.logger.error("검색 실행 실패")
                    return False
            
            # 검색 결과 로딩 대기
            print("⏳ 검색 결과 로딩 중...")
            time.sleep(5)
            
            # 검색 결과 확인
            try:
                # 검색 결과가 로드되었는지 확인
                result_indicators = [
                    ".place_section",  # 장소 정보 섹션
                    ".search_item",    # 검색 결과 아이템
                    ".place_detail",   # 장소 상세 정보
                    "#_title",         # 제목 영역
                ]
                
                result_found = False
                for indicator in result_indicators:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, indicator)
                        result_found = True
                        break
                    except:
                        continue
                
                if result_found:
                    self.logger.info(f"검색 결과 로드 성공: {name}")
                    print(f"✅ '{name}' 검색 결과 로드 완료")
                    return True
                else:
                    self.logger.warning(f"검색 결과 없음: {name}")
                    print(f"⚠️ '{name}' 검색 결과가 없습니다")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"검색 결과 확인 중 오류: {e}")
                print(f"⚠️ 검색 결과 확인 중 오류: {e}")
                return True  # 일단 성공으로 처리하고 연락처 추출 시도
            
        except TimeoutException:
            self.logger.warning(f"기관 검색 시간 초과: {name}")
            print(f"⏰ '{name}' 검색 시간 초과")
            return False
        except Exception as e:
            self.logger.error(f"기관 검색 중 오류: {name}, 오류: {e}")
            print(f"❌ '{name}' 검색 중 오류: {e}")
            return False
    
    def extract_contact_info(self, org_name=""):
        """연락처 정보 추출 - 개선된 버전"""
        self.logger.info(f"연락처 정보 추출 시작: {org_name}")
        print(f"📞 '{org_name}' 연락처 정보 추출 중...")
        
        phone = ""
        fax = ""
        
        try:
            # 전화번호 추출
            for selector in self.contact_selectors['phone']:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        text = element.text.strip()
                        # 전화번호 패턴 체크 (한국 전화번호)
                        if self.is_phone_number(text):
                            phone = text
                            self.logger.info(f"전화번호 추출 성공: {phone} (선택자: {selector})")
                            print(f"📞 전화번호 발견: {phone}")
                            break
                    
                    if phone:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"전화번호 선택자 실패: {selector} - {e}")
                    continue
            
            # 팩스번호 추출
            for selector in self.contact_selectors['fax']:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        text = element.text.strip()
                        # 팩스번호 패턴 체크
                        if self.is_phone_number(text) and ("팩스" in element.get_attribute("outerHTML") or "fax" in element.get_attribute("outerHTML").lower()):
                            fax = text
                            self.logger.info(f"팩스번호 추출 성공: {fax} (선택자: {selector})")
                            print(f"📠 팩스번호 발견: {fax}")
                            break
                    
                    if fax:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"팩스번호 선택자 실패: {selector} - {e}")
                    continue
            
            # 추가: 페이지 전체에서 전화번호 패턴 검색
            if not phone:
                phone = self.extract_phone_from_page()
            
            if not phone:
                self.logger.warning(f"전화번호를 찾을 수 없음: {org_name}")
                print("⚠️ 전화번호를 찾을 수 없습니다")
            
            if not fax:
                self.logger.warning(f"팩스번호를 찾을 수 없음: {org_name}")
                print("⚠️ 팩스번호를 찾을 수 없습니다")
                
        except Exception as e:
            self.logger.error(f"연락처 정보 추출 중 오류: {e}")
            print(f"❌ 연락처 정보 추출 중 오류: {e}")
        
        self.logger.info(f"연락처 정보 추출 완료: 전화번호={phone}, 팩스번호={fax}")
        return phone, fax
    
    def is_phone_number(self, text):
        """전화번호 패턴 검증"""
        import re
        # 한국 전화번호 패턴들
        patterns = [
            r'^0\d{1,2}-\d{3,4}-\d{4}$',  # 지역번호-국번-번호
            r'^01\d-\d{3,4}-\d{4}$',      # 휴대폰
            r'^\d{2,3}-\d{3,4}-\d{4}$',   # 서울 지역번호 등
        ]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        return False
    
    def extract_phone_from_page(self):
        """페이지 전체에서 전화번호 패턴 검색"""
        try:
            import re
            page_text = self.driver.page_source
            
            # 전화번호 패턴으로 검색
            phone_pattern = r'0\d{1,2}-\d{3,4}-\d{4}'
            matches = re.findall(phone_pattern, page_text)
            
            if matches:
                phone = matches[0]  # 첫 번째 매치 사용
                self.logger.info(f"페이지 전체 검색으로 전화번호 발견: {phone}")
                print(f"📞 페이지 검색으로 전화번호 발견: {phone}")
                return phone
                
        except Exception as e:
            self.logger.debug(f"페이지 전체 전화번호 검색 실패: {e}")
        
        return ""
    
    def load_data(self, json_file_path):
        """JSON 파일에서 데이터 로드"""
        try:
            self.logger.info(f"데이터 파일 로드 시작: {json_file_path}")
            print(f"📂 데이터 파일 로드 중: {json_file_path}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"데이터 파일 로드 성공: {json_file_path}, 총 카테고리 수: {len(data)}")
            print(f"✅ 데이터 파일 로드 완료: {json_file_path}")
            return data
        except Exception as e:
            self.logger.error(f"데이터 파일 로드 실패: {json_file_path}, 오류: {e}")
            print(f"❌ 데이터 파일 로드 실패: {e}")
            return None
    
    def save_data(self, data, output_file_path):
        """결과를 JSON 파일로 저장"""
        try:
            self.logger.info(f"결과 저장 시작: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"결과 저장 성공: {output_file_path}")
            print(f"💾 결과 저장 완료: {output_file_path}")
        except Exception as e:
            self.logger.error(f"결과 저장 실패: {output_file_path}, 오류: {e}")
            print(f"❌ 결과 저장 실패: {e}")
    
    def process_organization(self, org_data):
        """개별 기관 처리"""
        name = org_data.get("name", "")
        
        if not name:
            self.logger.warning("기관명이 없음")
            print("⚠️ 기관명이 없습니다.")
            return org_data
        
        self.logger.info(f"기관 처리 시작: {name}")
        print(f"🏢 처리 중: {name}")
        
        # 네이버 지도에서 검색
        if self.search_organization(name):
            # 연락처 정보 추출
            phone, fax = self.extract_contact_info(name)
            
            # 결과 저장
            if phone:
                org_data["phone"] = phone
                self.logger.info(f"네이버 지도 전화번호 추출: {name} -> {phone}")
                print(f"📞 전화번호 추출: {phone}")
            
            if fax:
                org_data["fax"] = fax
                self.logger.info(f"네이버 지도 팩스번호 추출: {name} -> {fax}")
                print(f"📠 팩스번호 추출: {fax}")
        else:
            self.logger.warning(f"네이버 지도 검색 실패: {name}")
            print(f"⚠️ 네이버 지도 검색 실패: {name}")
        
        self.logger.info(f"기관 처리 완료: {name}")
        return org_data
    
    def crawl_all_organizations(self, input_file, output_file):
        """모든 기관 크롤링"""
        self.logger.info(f"전체 크롤링 시작: 입력파일={input_file}, 출력파일={output_file}")
        
        # 데이터 로드
        data = self.load_data(input_file)
        if not data:
            self.logger.error("데이터 로드 실패로 크롤링 중단")
            return
        
        total_processed = 0
        total_organizations = sum(len(orgs) for orgs in data.values())
        self.logger.info(f"총 처리할 기관 수: {total_organizations}")
        
        try:
            # 각 카테고리별 처리
            for category, organizations in data.items():
                self.logger.info(f"카테고리 처리 시작: {category}, 기관 수: {len(organizations)}")
                print(f"📂 카테고리 처리 시작: {category}")
                
                for i, org in enumerate(organizations):
                    self.logger.info(f"[{category}] {i+1}/{len(organizations)} 처리 중: {org.get('name', 'Unknown')}")
                    print(f"[{category}] {i+1}/{len(organizations)} 처리 중...")
                    
                    # 기관 처리
                    updated_org = self.process_organization(org)
                    organizations[i] = updated_org
                    total_processed += 1
                    
                    # 중간 저장 (10개마다)
                    if total_processed % 10 == 0:
                        self.logger.info(f"중간 저장 실행: {total_processed}/{total_organizations}")
                        self.save_data(data, output_file)
                        print(f"💾 중간 저장 완료: {total_processed}개 처리됨")
                    
                    # 요청 간격 조절
                    time.sleep(random.uniform(1, 3))
                
                self.logger.info(f"카테고리 처리 완료: {category}")
            
            # 최종 저장
            self.logger.info("최종 저장 실행")
            self.save_data(data, output_file)
            self.logger.info(f"전체 크롤링 완료: 총 {total_processed}개 기관 처리됨")
            print(f"🎉 크롤링 완료: 총 {total_processed}개 기관 처리됨")
            
        except KeyboardInterrupt:
            self.logger.warning("사용자에 의해 크롤링 중단됨")
            print("⏹️ 사용자에 의해 중단됨")
        except Exception as e:
            self.logger.error(f"크롤링 중 오류 발생: {e}")
            print(f"❌ 크롤링 중 오류: {e}")
        finally:
            self.logger.info("크롤링 종료 및 리소스 정리")
            self.close()
    
    def close(self):
        """리소스 정리"""
        self.logger.info("리소스 정리 시작")
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("Chrome 드라이버 종료 완료")
                print("🔒 드라이버가 종료되었습니다.")
        except Exception as e:
            self.logger.error(f"Chrome 드라이버 종료 중 오류: {e}")
        
        self.logger.info("리소스 정리 완료")

def main():
    """메인 실행 함수"""
    try:
        print("=" * 60)
        print("🗺️ 개선된 네이버 지도 크롤러 시작")
        print("=" * 60)
        
        # 크롤러 인스턴스 생성
        crawler = NaverMapCrawler()
        
        # 입력/출력 파일 설정
        input_file = "raw_data.json"
        output_file = f"raw_data_with_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📂 입력 파일: {input_file}")
        print(f"💾 출력 파일: {output_file}")
        
        # 입력 파일 존재 확인
        import os
        if not os.path.exists(input_file):
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            print("💡 raw_data.json 파일이 현재 디렉토리에 있는지 확인하세요.")
            return
        
        print("=" * 60)
        
        # 크롤링 실행
        crawler.crawl_all_organizations(input_file, output_file)
        
    except Exception as e:
        print(f"❌ 메인 실행 중 오류: {e}")
        if 'crawler' in locals():
            crawler.logger.error(f"메인 실행 중 오류: {e}")
    finally:
        # 리소스 정리
        try:
            if 'crawler' in locals():
                crawler.close()
        except:
            pass

if __name__ == "__main__":
    main()
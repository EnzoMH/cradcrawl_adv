#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글 검색을 통한 연락처 크롤러
기관명을 검색하여 전화번호와 팩스번호를 각각 추출하는 스크립트
"""

import json
import time
import random
import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# settings.py에서 상수들 임포트 (수정)
from settings import (
    PHONE_EXTRACTION_PATTERNS,
    FAX_EXTRACTION_PATTERNS, 
    KOREAN_AREA_CODES,
    AREA_CODE_LENGTH_RULES,
    LOG_FORMAT,
    LOGGER_NAMES,
    get_area_name,
    is_valid_area_code,
    get_length_rules,
    format_phone_number,
    extract_phone_area_code
)

# 로거 설정 (콘솔 출력만)
def setup_logger():
    logger = logging.getLogger(LOGGER_NAMES["fax_crawler"]) 
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 콘솔 핸들러만 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터 설정 (수정: constants에서 가져온 포맷 사용)
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

class GoogleContactCrawler:
    def __init__(self):
        self.logger = setup_logger()
        self.base_url = "https://www.google.com/search"
        self.driver = None
        self.wait = None
        
        # constants.py에서 가져온 패턴들 사용 (수정)
        self.phone_patterns = PHONE_EXTRACTION_PATTERNS
        self.fax_patterns = FAX_EXTRACTION_PATTERNS
        
        self.logger.info(f"구글 연락처 크롤러 초기화 완료 - 전화번호 패턴: {len(self.phone_patterns)}개, 팩스 패턴: {len(self.fax_patterns)}개")
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        self.logger.info("Chrome 드라이버 설정 시작")
        print("🔧 Chrome 드라이버 설정 중...")
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 매크로 감지 방지를 위한 추가 옵션
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        
        # 헤드리스 모드 (필요시 주석 해제)
        # options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        self.logger.info("Chrome 드라이버 설정 완료")
        print("✅ Chrome 드라이버 설정 완료")

    def restart_driver(self):
        """드라이버 재시작 (매크로 감지 방지)"""
        self.logger.info("매크로 감지 방지를 위한 드라이버 재시작")
        print("🔄 드라이버 재시작 중...")
        
        # 기존 드라이버 종료
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        # 잠시 대기
        time.sleep(random.uniform(3, 7))
        
        # 새 드라이버 시작
        self.setup_driver()
        print("✅ 드라이버 재시작 완료")
    
    def load_data(self, json_file_path):
        """JSON 파일에서 데이터 로드"""
        try:
            self.logger.info(f"팩스 크롤러 데이터 파일 로드 시작: {json_file_path}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"팩스 크롤러 데이터 파일 로드 성공: {json_file_path}")
            return data
        except Exception as e:
            self.logger.error(f"팩스 크롤러 데이터 파일 로드 실패: {json_file_path}, 오류: {e}")
            return None
    
    def save_data(self, data, output_file_path):
        """결과를 JSON 파일로 저장"""
        try:
            self.logger.info(f"팩스 크롤러 결과 저장 시작: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"팩스 크롤러 결과 저장 성공: {output_file_path}")
        except Exception as e:
            self.logger.error(f"팩스 크롤러 결과 저장 실패: {output_file_path}, 오류: {e}")
    
    def search_google(self, query):
        """구글 검색 수행"""
        try:
            self.logger.info(f"구글 검색 시작: {query}")
            
            # 드라이버가 없으면 새로 생성
            if not self.driver:
                self.setup_driver()
            
            # 구글 검색 페이지로 이동
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # 검색창 찾기
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.logger.info("구글 검색창 발견")
            
            # 검색어 입력 및 검색
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            self.logger.info(f"검색어 입력 및 검색 실행: {query}")
            
            # 검색 결과 로딩 대기
            time.sleep(random.uniform(3, 5))
            
            self.logger.info(f"구글 검색 완료: {query}")
            print(f"🔍 구글 검색 완료: {query}")
            return True
            
        except TimeoutException:
            self.logger.warning(f"구글 검색 시간 초과: {query}")
            print(f"⏰ 구글 검색 시간 초과: {query}")
            return False
        except Exception as e:
            self.logger.error(f"구글 검색 중 오류: {query}, 오류: {e}")
            print(f"❌ 구글 검색 중 오류: {e}")
            return False
    
    def extract_phone_from_page(self):
        """현재 페이지에서 전화번호 추출"""
        self.logger.info("페이지에서 전화번호 추출 시작")
        phone_numbers = []
        
        try:
            # 페이지 소스 가져오기
            page_source = self.driver.page_source
            self.logger.info(f"페이지 소스 길이: {len(page_source)} 문자")
            
            # 각 패턴으로 전화번호 검색
            for i, pattern in enumerate(self.phone_patterns):
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    self.logger.info(f"전화번호 패턴 {i+1}에서 {len(matches)}개 매치 발견: {pattern}")
                for match in matches:
                    formatted_phone = self.format_phone_number_safe(match)  
                    if formatted_phone and formatted_phone not in phone_numbers:
                        phone_numbers.append(formatted_phone)
                        self.logger.info(f"유효한 전화번호 발견: {formatted_phone}")
                    elif match and not formatted_phone:
                        self.logger.debug(f"유효하지 않은 전화번호 제외: {match}")
            
            # 검색 결과에서 추가 추출
            try:
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".g")
                self.logger.info(f"검색 결과 요소 수: {len(search_results)}")
                for result in search_results[:5]:  # 상위 5개 결과만 확인
                    result_text = result.text
                    for pattern in self.phone_patterns:
                        matches = re.findall(pattern, result_text, re.IGNORECASE)
                        for match in matches:
                            formatted_phone = self.format_phone_number_safe(match)  
                            if formatted_phone and formatted_phone not in phone_numbers:
                                phone_numbers.append(formatted_phone)
                                self.logger.info(f"검색 결과에서 유효한 전화번호 발견: {formatted_phone}")
                            elif match and not formatted_phone:
                                self.logger.debug(f"검색 결과에서 유효하지 않은 전화번호 제외: {match}")
            except Exception as e:
                self.logger.warning(f"검색 결과 추가 추출 중 오류: {e}")
            
        except Exception as e:
            self.logger.error(f"페이지에서 전화번호 추출 중 오류: {e}")
        
        self.logger.info(f"전화번호 추출 완료: 총 {len(phone_numbers)}개 발견")
        return phone_numbers
    
    def extract_fax_from_page(self):
        """현재 페이지에서 팩스번호 추출"""
        self.logger.info("페이지에서 팩스번호 추출 시작")
        fax_numbers = []
        
        try:
            # 페이지 소스 가져오기
            page_source = self.driver.page_source
            self.logger.info(f"페이지 소스 길이: {len(page_source)} 문자")
            
            # 각 패턴으로 팩스번호 검색
            for i, pattern in enumerate(self.fax_patterns):
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    self.logger.info(f"팩스번호 패턴 {i+1}에서 {len(matches)}개 매치 발견: {pattern}")
                for match in matches:
                    formatted_fax = self.format_phone_number_safe(match)
                    if formatted_fax and formatted_fax not in fax_numbers:
                        fax_numbers.append(formatted_fax)
                        self.logger.info(f"유효한 팩스번호 발견: {formatted_fax}")
                    elif match and not formatted_fax:
                        self.logger.debug(f"유효하지 않은 팩스번호 제외: {match}")
            
            # 검색 결과에서 추가 추출
            try:
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".g")
                self.logger.info(f"검색 결과 요소 수: {len(search_results)}")
                for result in search_results[:5]:  # 상위 5개 결과만 확인
                    result_text = result.text
                    for pattern in self.fax_patterns:
                        matches = re.findall(pattern, result_text, re.IGNORECASE)
                        for match in matches:
                            formatted_fax = self.format_phone_number_safe(match)
                            if formatted_fax and formatted_fax not in fax_numbers:
                                fax_numbers.append(formatted_fax)
                                self.logger.info(f"검색 결과에서 유효한 팩스번호 발견: {formatted_fax}")
                            elif match and not formatted_fax:
                                self.logger.debug(f"검색 결과에서 유효하지 않은 팩스번호 제외: {match}")
            except Exception as e:
                self.logger.warning(f"검색 결과 추가 추출 중 오류: {e}")
            
        except Exception as e:
            self.logger.error(f"페이지에서 팩스번호 추출 중 오류: {e}")
        
        self.logger.info(f"팩스번호 추출 완료: 총 {len(fax_numbers)}개 발견")
        return fax_numbers
    
    def get_area_code_info(self, number_str):
        """지역번호 정보 반환 (constants.py 함수 활용)"""
        area_code = extract_phone_area_code(number_str)
        if area_code:
            area_name = get_area_name(area_code)
            return area_code, area_name
        return None, None
    
    def is_valid_korean_phone_number(self, number_str):
        """한국 전화번호 체계 검증 (constants.py 데이터 활용)"""
        # 숫자만 추출
        number = re.sub(r'[^\d]', '', number_str)
        
        # 최소 길이 체크
        if len(number) < 9:
            return False
        
        # constants.py의 지역번호별 길이 규칙 사용 (수정)
        for area_code, rules in AREA_CODE_LENGTH_RULES.items():
            if number.startswith(area_code):
                if rules['min_length'] <= len(number) <= rules['max_length']:
                    area_name = get_area_name(area_code)
                    self.logger.debug(f"유효한 한국 전화번호: {number} (지역번호: {area_code}, 지역: {area_name})")
                    return True
                else:
                    self.logger.debug(f"길이 불일치: {number} (지역번호: {area_code}, 길이: {len(number)})")
                    return False
        
        self.logger.debug(f"유효하지 않은 지역번호: {number}")
        return False
    
    def format_phone_number_safe(self, number_str):  # 메서드명 변경 (충돌 방지)
        """전화번호 포맷팅 (한국 번호 체계 검증 포함)"""
        # 숫자만 추출
        number = re.sub(r'[^\d]', '', number_str)
        
        # 한국 전화번호 체계 검증
        if not self.is_valid_korean_phone_number(number):
            self.logger.debug(f"유효하지 않은 전화번호 제외: {number_str}")
            return None
        
        # constants.py의 포맷팅 함수 사용 (수정)
        area_code = extract_phone_area_code(number)
        if area_code:
            return format_phone_number(number, area_code)
        else:
            return number_str  # 원본 반환
    
    def search_phone_number(self, organization_name):
        """기관명으로 전화번호 검색"""
        self.logger.info(f"기관 전화번호 검색 시작: {organization_name}")
        phone_numbers = []
        
        # 검색 쿼리 리스트
        search_queries = [
            f'"{organization_name}" 전화번호',
            f'"{organization_name}" Tel',
            f'"{organization_name}" 연락처',
            f'{organization_name} 전화',
            f'{organization_name} 대표번호'
        ]
        
        self.logger.info(f"총 {len(search_queries)}개 쿼리로 전화번호 검색 예정")
        
        for i, query in enumerate(search_queries, 1):
            self.logger.info(f"전화번호 쿼리 {i}/{len(search_queries)} 실행: {query}")
            print(f"📞 전화번호 검색 중: {query}")
            
            if self.search_google(query):
                # 전화번호 추출
                extracted_phone = self.extract_phone_from_page()
                if extracted_phone:
                    self.logger.info(f"쿼리에서 {len(extracted_phone)}개 전화번호 추출: {extracted_phone}")
                phone_numbers.extend(extracted_phone)
                
                # 중복 제거
                phone_numbers = list(set(phone_numbers))
                
                # 전화번호를 찾았으면 더 이상 검색하지 않음
                if phone_numbers:
                    self.logger.info(f"전화번호 발견으로 검색 중단: {phone_numbers}")
                    print(f"📞 전화번호 발견: {phone_numbers}")
                    break
            else:
                self.logger.warning(f"전화번호 쿼리 검색 실패: {query}")
            
            # 드라이버 재시작 (매크로 감지 방지)
            self.restart_driver()
            
            # 요청 간격 조절
            sleep_time = random.uniform(3, 6)
            self.logger.info(f"다음 쿼리까지 대기: {sleep_time:.2f}초")
            time.sleep(sleep_time)
        
        self.logger.info(f"기관 전화번호 검색 완료: {organization_name}, 결과: {len(phone_numbers)}개")
        return phone_numbers
    
    def search_fax_number(self, organization_name):
        """기관명으로 팩스번호 검색"""
        self.logger.info(f"기관 팩스번호 검색 시작: {organization_name}")
        fax_numbers = []
        
        # 검색 쿼리 리스트
        search_queries = [
            f'"{organization_name}" 팩스번호',
            f'"{organization_name}" Fax번호',
            f'"{organization_name}" 팩스',
            f'"{organization_name}" FAX',
            f'{organization_name} 연락처 팩스'
        ]
        
        self.logger.info(f"총 {len(search_queries)}개 쿼리로 팩스번호 검색 예정")
        
        for i, query in enumerate(search_queries, 1):
            self.logger.info(f"팩스번호 쿼리 {i}/{len(search_queries)} 실행: {query}")
            print(f"📠 팩스번호 검색 중: {query}")
            
            if self.search_google(query):
                # 팩스번호 추출
                extracted_fax = self.extract_fax_from_page()
                if extracted_fax:
                    self.logger.info(f"쿼리에서 {len(extracted_fax)}개 팩스번호 추출: {extracted_fax}")
                fax_numbers.extend(extracted_fax)
                
                # 중복 제거
                fax_numbers = list(set(fax_numbers))
                
                # 팩스번호를 찾았으면 더 이상 검색하지 않음
                if fax_numbers:
                    self.logger.info(f"팩스번호 발견으로 검색 중단: {fax_numbers}")
                    print(f"📠 팩스번호 발견: {fax_numbers}")
                    break
            else:
                self.logger.warning(f"팩스번호 쿼리 검색 실패: {query}")
            
            # 드라이버 재시작 (매크로 감지 방지)
            self.restart_driver()
            
            # 요청 간격 조절
            sleep_time = random.uniform(3, 6)
            self.logger.info(f"다음 쿼리까지 대기: {sleep_time:.2f}초")
            time.sleep(sleep_time)
        
        self.logger.info(f"기관 팩스번호 검색 완료: {organization_name}, 결과: {len(fax_numbers)}개")
        return fax_numbers
    
    def analyze_phone_fax_relationship(self, phone_numbers, fax_numbers):
        """전화번호와 팩스번호 관계 분석"""
        if not phone_numbers or not fax_numbers:
            return None, None, "no_match"
        
        # 모든 조합을 확인하여 최적의 매칭 찾기
        best_phone = phone_numbers[0]
        best_fax = fax_numbers[0]
        best_relationship = "different"
        
        for phone in phone_numbers:
            for fax in fax_numbers:
                relationship = self.compare_phone_fax(phone, fax)
                
                # 우선순위: exact_match > similar_pattern > different
                if relationship == "exact_match":
                    return phone, fax, relationship
                elif relationship == "similar_pattern" and best_relationship != "exact_match":
                    best_phone, best_fax, best_relationship = phone, fax, relationship
        
        return best_phone, best_fax, best_relationship
    
    def compare_phone_fax(self, phone, fax):
        """전화번호와 팩스번호 비교 분석"""
        if phone == fax:
            return "exact_match"
        
        # 숫자만 추출
        phone_digits = re.sub(r'[^\d]', '', phone)
        fax_digits = re.sub(r'[^\d]', '', fax)
        
        # 길이가 다르면 다른 번호
        if len(phone_digits) != len(fax_digits):
            return "different"
        
        # 10자리 또는 11자리 번호에 대해 패턴 분석
        if len(phone_digits) in [10, 11]:
            # 앞 7자리가 같고 뒤 4자리만 다른 경우 (지역번호 + 국번이 같은 경우)
            if len(phone_digits) == 10:
                # 10자리: 앞 6자리 비교 (지역번호 2-3자리 + 국번 3-4자리)
                if phone_digits[:6] == fax_digits[:6] and phone_digits[6:] != fax_digits[6:]:
                    return "similar_pattern"
            elif len(phone_digits) == 11:
                # 11자리: 앞 7자리 비교 (지역번호 3자리 + 국번 4자리)
                if phone_digits[:7] == fax_digits[:7] and phone_digits[7:] != fax_digits[7:]:
                    return "similar_pattern"
        
        return "different"
    
    def process_organization(self, org_data):
        """개별 기관 연락처 처리 (전화번호 + 팩스번호)"""
        name = org_data.get("name", "")
        
        if not name:
            self.logger.warning("기관명이 없음")
            print("⚠️ 기관명이 없습니다.")
            return org_data
        
        self.logger.info(f"기관 연락처 처리 시작: {name}")
        print(f"🔍 연락처 검색 중: {name}")
        
        # 1. 전화번호 검색
        print(f"📞 전화번호 검색 시작: {name}")
        phone_numbers = self.search_phone_number(name)
        
        # 2. 팩스번호 검색
        print(f"📠 팩스번호 검색 시작: {name}")
        fax_numbers = self.search_fax_number(name)
        
        # 3. 전화번호와 팩스번호 관계 분석
        phone_google, fax_google, relationship = self.analyze_phone_fax_relationship(phone_numbers, fax_numbers)
        
        # 4. 결과 처리 및 저장
        if phone_google and fax_google:
            # 지역 정보 추출
            phone_area_code, phone_area = self.get_area_code_info(phone_google)
            fax_area_code, fax_area = self.get_area_code_info(fax_google)
            
            if relationship == "exact_match":
                # 완전히 같은 번호인 경우
                org_data["phone_google"] = phone_google
                org_data["fax_google"] = "전화번호와 일치"
                self.logger.info(f"전화번호와 팩스번호 완전 일치: {name} -> {phone_google} ({phone_area})")
                print(f"📞📠 전화번호와 팩스번호 완전 일치: {name} -> {phone_google} ({phone_area})")
            elif relationship == "similar_pattern":
                # 앞자리는 같고 뒷자리만 다른 경우 (같은 기관의 다른 라인)
                org_data["phone_google"] = phone_google
                org_data["fax_google"] = fax_google
                self.logger.info(f"전화번호와 팩스번호 유사 패턴: {name} -> 전화: {phone_google} ({phone_area}), 팩스: {fax_google} ({fax_area})")
                print(f"📞📠 유사 패턴 (같은 기관): 전화: {phone_google} ({phone_area}), 팩스: {fax_google} ({fax_area})")
            else:
                # 완전히 다른 번호인 경우
                org_data["phone_google"] = phone_google
                org_data["fax_google"] = fax_google
                self.logger.info(f"전화번호와 팩스번호 별도: {name} -> 전화: {phone_google} ({phone_area}), 팩스: {fax_google} ({fax_area})")
                print(f"📞📠 별도 번호: 전화: {phone_google} ({phone_area}), 팩스: {fax_google} ({fax_area})")
        elif phone_google:
            # 전화번호만 있는 경우
            phone_area_code, phone_area = self.get_area_code_info(phone_google)
            org_data["phone_google"] = phone_google
            org_data["fax_google"] = ""
            self.logger.info(f"전화번호만 발견: {name} -> {phone_google} ({phone_area})")
            print(f"📞 전화번호만 발견: {name} -> {phone_google} ({phone_area})")
        elif fax_google:
            # 팩스번호만 있는 경우
            fax_area_code, fax_area = self.get_area_code_info(fax_google)
            org_data["phone_google"] = ""
            org_data["fax_google"] = fax_google
            self.logger.info(f"팩스번호만 발견: {name} -> {fax_google} ({fax_area})")
            print(f"📠 팩스번호만 발견: {name} -> {fax_google} ({fax_area})")
        else:
            # 둘 다 없는 경우
            org_data["phone_google"] = ""
            org_data["fax_google"] = ""
            self.logger.warning(f"연락처를 찾을 수 없음: {name}")
            print(f"⚠️ 연락처를 찾을 수 없음: {name}")
        
        # 요청 간격 조절 (봇 탐지 방지)
        sleep_time = random.uniform(5, 10)
        self.logger.info(f"다음 기관까지 대기: {sleep_time:.2f}초")
        time.sleep(sleep_time)
        
        self.logger.info(f"기관 연락처 처리 완료: {name}")
        return org_data
    
    def crawl_all_fax_numbers(self, input_file, output_file):
        """모든 기관의 팩스번호 크롤링"""
        self.logger.info(f"전체 팩스번호 크롤링 시작: 입력파일={input_file}, 출력파일={output_file}")
        
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
                    org_name = org.get('name', 'Unknown')
                    self.logger.info(f"[{category}] {i+1}/{len(organizations)} 처리 중: {org_name}")
                    print(f"[{category}] {i+1}/{len(organizations)} 처리 중...")
                    
                    # 기관 처리
                    updated_org = self.process_organization(org)
                    organizations[i] = updated_org
                    total_processed += 1
                    
                    # 중간 저장 (5개마다)
                    if total_processed % 5 == 0:
                        self.logger.info(f"중간 저장 실행: {total_processed}/{total_organizations}")
                        self.save_data(data, output_file)
                        print(f"💾 중간 저장 완료: {total_processed}개 처리됨")
                
                self.logger.info(f"카테고리 처리 완료: {category}")
            
            # 최종 저장
            self.logger.info("최종 저장 실행")
            self.save_data(data, output_file)
            self.logger.info(f"전체 팩스번호 크롤링 완료: 총 {total_processed}개 기관 처리됨")
            print(f"🎉 팩스번호 크롤링 완료: 총 {total_processed}개 기관 처리됨")
            
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
        """드라이버 종료"""
        self.logger.info("팩스 크롤러 리소스 정리 시작")
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("팩스 크롤러 드라이버 종료 완료")
                print("🔒 팩스 크롤러 드라이버가 종료되었습니다.")
        except Exception as e:
            self.logger.error(f"팩스 크롤러 드라이버 종료 중 오류: {e}")
        
        self.logger.info("팩스 크롤러 리소스 정리 완료")

def test_phone_validation():
    """전화번호 검증 테스트 함수"""
    print("=" * 60)
    print("📞 한국 전화번호 검증 시스템 테스트")
    print("=" * 60)
    
    crawler = GoogleContactCrawler()
    
    # 테스트 번호들
    test_numbers = [
        # 유효한 번호들
        "02-123-4567",      # 서울 (9자리)
        "02-1234-5678",     # 서울 (10자리)
        "031-123-4567",     # 경기 (10자리)
        "031-1234-5678",    # 경기 (11자리)
        "010-1234-5678",    # 핸드폰
        "070-1234-5678",    # 인터넷전화
        "051-123-4567",     # 부산
        
        # 유효하지 않은 번호들
        "01-123-4567",      # 잘못된 지역번호
        "02-12-345",        # 너무 짧음
        "031-12345-67890",  # 너무 김
        "080-1234-5678",    # 존재하지 않는 지역번호
        "123-456-7890",     # 잘못된 형식
    ]
    
    print("🔍 테스트 결과:")
    for number in test_numbers:
        is_valid = crawler.is_valid_korean_phone_number(number)
        area_code, area_name = crawler.get_area_code_info(number)
        formatted = crawler.format_phone_number_safe(number)
        
        status = "✅ 유효" if is_valid else "❌ 무효"
        area_info = f"({area_code}-{area_name})" if area_code else "(알 수 없음)"
        formatted_info = f"-> {formatted}" if formatted else "-> 제외됨"
        
        print(f"  {status} {number:15} {area_info:15} {formatted_info}")
    
    print("=" * 60)

def main():
    """메인 실행 함수"""
    try:
        print("=" * 60)
        print("📠 구글 팩스번호 크롤러 시작")
        print("=" * 60)
        
        # 전화번호 검증 테스트 실행
        test_phone_validation()
        
        # 크롤러 인스턴스 생성
        crawler = GoogleContactCrawler()
    
        # 입력/출력 파일 설정
        input_file = "raw_data.json"
        output_file = f"church_data_with_fax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
        crawler.crawl_all_fax_numbers(input_file, output_file)
        
    except Exception as e:
        print(f"❌ 메인 실행 중 오류: {e}")
        try:
            crawler.logger.error(f"메인 실행 중 오류: {e}")
        except:
            pass
    finally:
        # 리소스 정리
        try:
            crawler.close()
        except:
            pass

if __name__ == "__main__":
    main() 
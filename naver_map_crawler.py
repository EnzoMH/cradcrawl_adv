#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 지도 크롤러
교회명을 키워드로 네이버 지도에서 연락처 정보를 크롤링합니다.
"""

import json
import time
import random
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

class NaverMapCrawler:
    def __init__(self):
        """초기화"""
        self.setup_logger()
        self.driver = None
        self.wait = None
        self.setup_driver()
        
        # 크롤링 설정 (블로그 포스트 주의사항 반영)
        self.delay_range = (2, 5)  # 요청 간격 (초)
        self.timeout = 15
        self.max_retries = 3
        
        # 통계
        self.stats = {
            'total_processed': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'contacts_found': 0,
            'no_results': 0
        }
        
        # 네이버 지도 URL
        self.base_url = "https://map.naver.com/p/search"
        
        print("🗺️ 네이버 지도 크롤러 초기화 완료")
        print("⚠️ 크롤링 주의사항:")
        print("   - 적절한 딜레이로 서버 부하 최소화")
        print("   - 개인 연구/학습 목적으로만 사용")
        print("   - robots.txt 권고사항 인지함")
    
    def setup_logger(self):
        """로거 설정"""
        self.logger = logging.getLogger('naver_map_crawler')
        self.logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter('%(asctime)s - [네이버지도] - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def setup_driver(self):
        """Selenium WebDriver 설정"""
        try:
            print("🔧 Chrome WebDriver 설정 중...")
            
            options = Options()
            
            # 봇 감지 방지 설정
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent 설정 (일반 사용자처럼 보이기)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # 기타 설정
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # 헤드리스 모드 (필요시 주석 해제)
            # options.add_argument("--headless")
            
            self.driver = webdriver.Chrome(options=options)
            
            # WebDriver 속성 숨기기
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            print("✅ Chrome WebDriver 설정 완료")
            self.logger.info("WebDriver 초기화 성공")
            
        except Exception as e:
            print(f"❌ WebDriver 설정 실패: {e}")
            self.logger.error(f"WebDriver 설정 실패: {e}")
            raise
    
    def load_json_data(self, filepath: str) -> List[Dict]:
        """JSON 파일 로드"""
        try:
            print(f"📂 JSON 파일 로딩: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                print(f"✅ {len(data)}개 교회 데이터 로드 완료")
                return data
            else:
                print("❌ 지원하지 않는 JSON 형식입니다.")
                return []
                
        except Exception as e:
            print(f"❌ JSON 파일 로딩 실패: {e}")
            return []
    
    def search_on_naver_map(self, keyword: str) -> bool:
        """네이버 지도에서 키워드 검색"""
        try:
            print(f"  🔍 네이버 지도 검색: {keyword}")
            
            # 네이버 지도 메인 페이지로 이동
            self.driver.get("https://map.naver.com/")
            
            # 페이지 로딩 대기
            time.sleep(2)
            
            # 검색창 찾기 (여러 선택자 시도)
            search_selectors = [
                "input.input_search",
                "input[placeholder*='검색']",
                "input[class*='search']",
                "#search-input",
                "input[type='text']"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"  ✅ 검색창 발견: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not search_input:
                print("  ❌ 검색창을 찾을 수 없습니다")
                return False
            
            # 검색어 입력
            search_input.clear()
            time.sleep(0.5)
            search_input.send_keys(keyword)
            time.sleep(1)
            
            # 검색 실행 (Enter 키)
            search_input.send_keys(Keys.RETURN)
            print(f"  ⌨️ 검색어 입력 및 실행: {keyword}")
            
            # 검색 결과 로딩 대기
            time.sleep(3)
            
            # 검색 결과 확인
            result_selectors = [
                ".place_section",
                ".search_item",
                ".place_detail",
                "[class*='search']",
                "[class*='place']"
            ]
            
            result_found = False
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        result_found = True
                        print(f"  ✅ 검색 결과 발견: {len(elements)}개 요소")
                        break
                except:
                    continue
            
            if result_found:
                self.logger.info(f"검색 성공: {keyword}")
                return True
            else:
                print(f"  ⚠️ 검색 결과 없음: {keyword}")
                self.logger.warning(f"검색 결과 없음: {keyword}")
                return False
                
        except Exception as e:
            print(f"  ❌ 검색 오류: {e}")
            self.logger.error(f"검색 오류 ({keyword}): {e}")
            return False
    
    def extract_contact_info(self, keyword: str) -> Dict[str, str]:
        """현재 페이지에서 연락처 정보 추출"""
        try:
            print(f"  📞 연락처 정보 추출 중: {keyword}")
            
            # 페이지 소스 가져오기
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 추출된 정보 저장
            contact_info = {
                'phone': '',
                'fax': '',
                'address': '',
                'postal_code': ''
            }
            
            # 전체 텍스트에서 패턴 매칭
            all_text = soup.get_text()
            
            # 1. 전화번호 추출
            phone_patterns = [
                r'(\d{2,3}-\d{3,4}-\d{4})',  # 기본 패턴
                r'(전화|TEL|Tel|tel)[:\s]*(\d{2,3}[-\s]\d{3,4}[-\s]\d{4})',  # 라벨 포함
                r'(\d{2,3})\s*[-\.]\s*(\d{3,4})\s*[-\.]\s*(\d{4})'  # 구분자 변형
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    if isinstance(match, tuple):
                        # 라벨 포함 패턴의 경우
                        phone = match[-1] if len(match) > 1 else match[0]
                    else:
                        phone = match
                    
                    # 전화번호 검증
                    phone = re.sub(r'[^\d-]', '', str(phone))
                    if self.is_valid_phone_number(phone):
                        contact_info['phone'] = phone
                        print(f"    📞 전화번호 발견: {phone}")
                        break
                
                if contact_info['phone']:
                    break
            
            # 2. 팩스번호 추출
            fax_patterns = [
                r'(팩스|FAX|Fax|fax)[:\s]*(\d{2,3}[-\s]\d{3,4}[-\s]\d{4})',
                r'(F|f)[:\s]*(\d{2,3}[-\s]\d{3,4}[-\s]\d{4})'
            ]
            
            for pattern in fax_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    if isinstance(match, tuple):
                        fax = match[-1]
                    else:
                        fax = match
                    
                    fax = re.sub(r'[^\d-]', '', str(fax))
                    if self.is_valid_phone_number(fax):
                        contact_info['fax'] = fax
                        print(f"    📠 팩스번호 발견: {fax}")
                        break
                
                if contact_info['fax']:
                    break
            
            # 3. 주소 추출
            address_patterns = [
                r'([가-힣]+[시도]\s[가-힣]+[시군구]\s[가-힣0-9\s\-]+)',
                r'(\d{5}\s*[가-힣]+[시도]\s[가-힣]+[시군구][가-힣0-9\s\-]+)',
                r'(주소|위치|소재지)[:\s]*([가-힣0-9\s\-,]+[시도구군][가-힣0-9\s\-,]*)'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    if isinstance(match, tuple):
                        address = match[-1]
                    else:
                        address = match
                    
                    address = address.strip()
                    if len(address) > 10 and ('시' in address or '구' in address or '군' in address):
                        contact_info['address'] = address
                        print(f"    🏠 주소 발견: {address}")
                        break
                
                if contact_info['address']:
                    break
            
            # 4. 우편번호 추출
            postal_matches = re.findall(r'\b(\d{5})\b', all_text)
            for postal in postal_matches:
                # 5자리 숫자가 우편번호 형식에 맞는지 확인
                if postal.startswith(('0', '1', '2', '3', '4', '5', '6')):
                    contact_info['postal_code'] = postal
                    print(f"    📮 우편번호 발견: {postal}")
                    break
            
            # 추출 결과 로깅
            found_count = sum(1 for v in contact_info.values() if v)
            if found_count > 0:
                print(f"  ✅ 연락처 정보 추출 완료: {found_count}개 항목")
                self.stats['contacts_found'] += 1
            else:
                print(f"  ⚠️ 연락처 정보 없음")
            
            return contact_info
            
        except Exception as e:
            print(f"  ❌ 연락처 추출 오류: {e}")
            self.logger.error(f"연락처 추출 오류 ({keyword}): {e}")
            return {'phone': '', 'fax': '', 'address': '', 'postal_code': ''}
    
    def is_valid_phone_number(self, phone: str) -> bool:
        """전화번호 유효성 검증"""
        if not phone:
            return False
        
        # 한국 전화번호 패턴
        patterns = [
            r'^0\d{1,2}-\d{3,4}-\d{4}$',  # 지역번호
            r'^01\d-\d{3,4}-\d{4}$',      # 휴대폰
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return True
        
        return False
    
    def process_single_church(self, church_data: Dict) -> Dict:
        """단일 교회 처리"""
        church_name = church_data.get('name', 'Unknown')
        
        print(f"\n🏢 처리 중: {church_name}")
        self.logger.info(f"교회 처리 시작: {church_name}")
        
        result = church_data.copy()
        self.stats['total_processed'] += 1
        
        # 네이버 지도 크롤링 결과 초기화
        crawling_result = {
            'search_keyword': church_name,
            'search_success': False,
            'extracted_contacts': {},
            'updated_fields': [],
            'crawling_timestamp': datetime.now().isoformat(),
            'error_message': ''
        }
        
        try:
            # 네이버 지도에서 검색
            search_success = self.search_on_naver_map(church_name)
            crawling_result['search_success'] = search_success
            
            if search_success:
                self.stats['successful_searches'] += 1
                
                # 연락처 정보 추출
                extracted_contacts = self.extract_contact_info(church_name)
                crawling_result['extracted_contacts'] = extracted_contacts
                
                # 기존 빈 값을 추출된 값으로 업데이트
                contact_fields = ['phone', 'fax', 'address', 'postal_code']
                updated_fields = []
                
                for field in contact_fields:
                    extracted_value = extracted_contacts.get(field, '')
                    current_value = result.get(field, '')
                    
                    # 현재 값이 비어있고 추출된 값이 있으면 업데이트
                    if not current_value and extracted_value:
                        result[field] = extracted_value
                        updated_fields.append(field)
                
                crawling_result['updated_fields'] = updated_fields
                
                if updated_fields:
                    print(f"  ✨ 업데이트된 필드: {', '.join(updated_fields)}")
                else:
                    print(f"  📋 기존 값 유지 (새로운 정보 없음)")
                
            else:
                self.stats['failed_searches'] += 1
                print(f"  ⚠️ 검색 실패: {church_name}")
                
        except Exception as e:
            error_msg = str(e)
            crawling_result['error_message'] = error_msg
            self.stats['failed_searches'] += 1
            print(f"  ❌ 처리 오류: {error_msg}")
            self.logger.error(f"교회 처리 오류 ({church_name}): {e}")
        
        # 크롤링 결과를 메타데이터로 추가
        result['naver_map_crawling'] = crawling_result
        
        return result
    
    def process_all_churches(self, churches_data: List[Dict]) -> List[Dict]:
        """모든 교회 처리"""
        print(f"\n🚀 총 {len(churches_data)}개 교회 네이버 지도 크롤링 시작")
        print("⚠️ 안전한 크롤링을 위해 적절한 딜레이를 적용합니다")
        
        results = []
        
        for i, church in enumerate(churches_data):
            print(f"\n📍 진행상황: {i+1}/{len(churches_data)}")
            
            # 교회 처리
            result = self.process_single_church(church)
            results.append(result)
            
            # 중간 저장 (50개마다)
            if (i + 1) % 50 == 0:
                self.save_intermediate_results(results, i + 1)
            
            # 요청 간격 조절 (서버 부하 방지)
            if i < len(churches_data) - 1:  # 마지막이 아닌 경우
                delay = random.uniform(*self.delay_range)
                print(f"  ⏳ {delay:.1f}초 대기 중...")
                time.sleep(delay)
        
        return results
    
    def save_intermediate_results(self, results: List[Dict], count: int):
        """중간 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"naver_map_crawled_intermediate_{count}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 중간 저장 완료: {filename} ({count}개 처리됨)")
            
        except Exception as e:
            print(f"❌ 중간 저장 실패: {e}")
    
    def save_final_results(self, results: List[Dict]) -> str:
        """최종 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"naver_map_crawled_final_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 최종 결과 저장: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 최종 저장 실패: {e}")
            return ""
    
    def print_final_statistics(self):
        """최종 통계 출력"""
        print(f"\n📊 네이버 지도 크롤링 완료 통계:")
        print(f"  📋 총 처리: {self.stats['total_processed']}개")
        print(f"  ✅ 검색 성공: {self.stats['successful_searches']}개")
        print(f"  ❌ 검색 실패: {self.stats['failed_searches']}개")
        print(f"  📞 연락처 발견: {self.stats['contacts_found']}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_searches'] / self.stats['total_processed']) * 100
            print(f"  📈 성공률: {success_rate:.1f}%")
    
    def close(self):
        """리소스 정리"""
        try:
            if self.driver:
                self.driver.quit()
                print("🔒 WebDriver 종료 완료")
                self.logger.info("WebDriver 종료")
        except Exception as e:
            print(f"⚠️ WebDriver 종료 중 오류: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🗺️ 네이버 지도 크롤러 v1.0")
    print("=" * 60)
    print("📖 참고: https://bluesparrow.tistory.com/74")
    print("=" * 60)
    
    crawler = None
    
    try:
        # 크롤러 인스턴스 생성
        crawler = NaverMapCrawler()
        
        # JSON 파일 로드
        input_file = "combined_20250605_131931.json"
        churches_data = crawler.load_json_data(input_file)
        
        if not churches_data:
            print("❌ 데이터 로드 실패. 프로그램을 종료합니다.")
            return
        
        print(f"📂 입력 파일: {input_file}")
        print(f"📊 처리할 교회 수: {len(churches_data)}")
        
        # 사용자 확인
        print(f"\n⚠️ 크롤링 주의사항:")
        print(f"   - 네이버 지도 robots.txt 권고사항을 인지하고 있습니다")
        print(f"   - 개인 연구/학습 목적으로만 사용됩니다")
        print(f"   - 서버 부하를 최소화하기 위해 딜레이를 적용합니다")
        print(f"   - {len(churches_data)}개 교회를 처리하는데 시간이 오래 걸릴 수 있습니다")
        
        user_input = input(f"\n계속 진행하시겠습니까? (y/N): ")
        if user_input.lower() not in ['y', 'yes']:
            print("👋 사용자에 의해 취소되었습니다.")
            return
        
        # 모든 교회 처리
        enhanced_results = crawler.process_all_churches(churches_data)
        
        # 최종 결과 저장
        output_file = crawler.save_final_results(enhanced_results)
        
        # 통계 출력
        crawler.print_final_statistics()
        
        print(f"\n🎉 네이버 지도 크롤링 완료!")
        print(f"📁 출력 파일: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
    finally:
        # 리소스 정리
        if crawler:
            crawler.close()

if __name__ == "__main__":
    main()
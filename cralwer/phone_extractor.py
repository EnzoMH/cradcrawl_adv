#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

def setup_driver():
    """Chrome WebDriver 설정"""
    options = Options()
    # headless=False로 설정 (브라우저 창이 보임)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_phone_numbers(text):
    """텍스트에서 전화번호 패턴 추출 (개선된 버전)"""
    if not text:
        return []
    
    # 강화된 전화번호 패턴들
    phone_patterns = [
        # 하이픈으로 구분된 패턴
        r'\b0\d{1,2}-\d{3,4}-\d{4}\b',  # 02-1234-5678, 031-123-4567
        r'\b\d{3}-\d{3,4}-\d{4}\b',     # 051-123-4567
        
        # 공백으로 구분된 패턴
        r'\b0\d{1,2}\s+\d{3,4}\s+\d{4}\b',  # 02 1234 5678
        r'\b\d{3}\s+\d{3,4}\s+\d{4}\b',     # 051 123 4567
        
        # 점으로 구분된 패턴
        r'\b0\d{1,2}\.\d{3,4}\.\d{4}\b',    # 02.1234.5678
        r'\b\d{3}\.\d{3,4}\.\d{4}\b',       # 051.123.4567
        
        # 괄호가 있는 패턴
        r'\b\(0\d{1,2}\)\s*\d{3,4}[-\s]\d{4}\b',  # (02) 1234-5678
        r'\b0\d{1,2}\)\s*\d{3,4}[-\s]\d{4}\b',    # 02) 1234-5678
        
        # 숫자만 있는 패턴 (10-11자리)
        r'\b0\d{9,10}\b',  # 0212345678, 01012345678
        
        # Tel, TEL, 전화 키워드가 있는 패턴
        r'(?:Tel|TEL|전화|연락처|대표번호)[\s:]*(\d{2,3}[-\.\s]*\d{3,4}[-\.\s]*\d{4})',
        r'(?:Tel|TEL|전화|연락처|대표번호)[\s:]*(\(\d{2,3}\)[\s]*\d{3,4}[-\.\s]*\d{4})',
    ]
    
    found_numbers = []
    
    for pattern in phone_patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # 그룹이 있는 경우 첫 번째 그룹 사용
                    number = match[0] if match[0] else ''.join(match)
                else:
                    number = match
                
                if number and number.strip():
                    found_numbers.append(number.strip())
        except Exception as e:
            print(f"⚠️ 패턴 매칭 오류: {pattern} - {str(e)}")
            continue
    
    # 중복 제거 및 정리
    cleaned_numbers = []
    for number in found_numbers:
        try:
            # 숫자만 추출하여 길이 확인
            digits_only = re.sub(r'[^\d]', '', number)
            
            # 유효한 한국 전화번호 길이 확인 (9-11자리)
            if len(digits_only) < 9 or len(digits_only) > 11:
                continue
            
            # 잘못된 패턴 제외 (예: 111-1111-1111, 000-0000-0000)
            if len(set(digits_only)) <= 2:  # 같은 숫자만 반복
                continue
            
            # 형식 정리: 하이픈으로 통일
            clean_number = format_phone_number(digits_only)
            
            if clean_number and clean_number not in cleaned_numbers:
                cleaned_numbers.append(clean_number)
                
        except Exception as e:
            print(f"⚠️ 전화번호 정리 오류: {number} - {str(e)}")
            continue
    
    return cleaned_numbers

def format_phone_number(digits):
    """숫자만 있는 전화번호를 표준 형식으로 포맷팅"""
    if not digits or not digits.isdigit():
        return None
    
    length = len(digits)
    
    try:
        if length == 9:
            # 9자리: 02-XXX-XXXX
            if digits.startswith('02'):
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
            else:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        
        elif length == 10:
            # 10자리: 0XX-XXX-XXXX 또는 0XX-XXXX-XXXX
            if digits.startswith('02'):
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        
        elif length == 11:
            # 11자리: 0XX-XXXX-XXXX (주로 휴대폰)
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        else:
            return None
            
    except Exception:
        return None

def search_phone_number(driver, name):
    """구글에서 전화번호 검색 (개선된 버전)"""
    if not name or not name.strip():
        print(f"❌ 기관명이 비어있음")
        return []
    
    # 다양한 검색 쿼리 시도
    search_queries = [
        f'"{name}" 전화번호',
        f'"{name}" 연락처',
        f'{name} 전화',
        f'{name} Tel',
        f'{name} 대표번호'
    ]
    
    all_phone_numbers = []
    
    for i, search_query in enumerate(search_queries, 1):
        try:
            print(f"📞 전화번호 검색 {i}/{len(search_queries)}: {search_query}")
            
            # 구글 검색 페이지로 이동
            driver.get("https://www.google.com")
            time.sleep(2)
            
            # 검색창 찾기 및 검색어 입력
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.submit()
            
            # 검색 결과 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            time.sleep(3)
            
            # 페이지 텍스트에서 전화번호 추출
            page_text = driver.find_element(By.TAG_NAME, "body").text
            phone_numbers = extract_phone_numbers(page_text)
            
            if phone_numbers:
                print(f"✅ 전화번호 발견: {phone_numbers}")
                all_phone_numbers.extend(phone_numbers)
                # 첫 번째 성공한 검색에서 결과가 있으면 중단
                break
            else:
                print(f"❌ 전화번호 없음: {search_query}")
            
            # 다음 검색 전 잠시 대기
            time.sleep(2)
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ 검색 실패 - {search_query}: {str(e)}")
            continue
        except Exception as e:
            print(f"❌ 예상치 못한 오류 - {search_query}: {str(e)}")
            continue
    
    # 중복 제거 및 정리
    unique_phones = []
    for phone in all_phone_numbers:
        if phone not in unique_phones and len(phone.replace('-', '').replace(' ', '')) >= 9:
            unique_phones.append(phone)
    
    return unique_phones[:3]  # 최대 3개만 반환

def update_phone_data():
    """JSON 파일에서 전화번호 업데이트"""
    # JSON 파일 경로
    base_dir = Path(__file__).parent.parent
    json_dir = base_dir / "data" / "json"
    input_file = json_dir / "filtered_data_converted_20250613_004440.json"
    
    # JSON 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"총 {len(data)}개의 항목을 처리합니다.")
    
    # WebDriver 설정
    driver = setup_driver()
    
    try:
        updated_count = 0
        
        # 각 항목에 대해 전화번호 검색
        for i, item in enumerate(data):
            name = item.get('name', '').strip()
            current_phone = item.get('phone', '').strip()
            
            # 이름이 없거나 이미 전화번호가 있는 경우 스킵
            if not name or current_phone:
                continue
            
            print(f"[{i+1}/{len(data)}] 검색 중: {name}")
            
            # 전화번호 검색
            found_phones = search_phone_number(driver, name)
            
            if found_phones:
                # 첫 번째 검색된 전화번호 사용
                item['phone'] = found_phones[0]
                print(f"✓ 전화번호 발견: {name} -> {found_phones[0]}")
                updated_count += 1
                
                # 추가로 발견된 전화번호들도 기록
                if len(found_phones) > 1:
                    item['additional_phones'] = found_phones[1:]
            else:
                print(f"✗ 전화번호 없음: {name}")
            
            # 요청 간 딜레이 (차단 방지)
            time.sleep(2)
            
            # 중간 저장 (50개마다)
            if (i + 1) % 50 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"filtered_data_updated_temp_{timestamp}.json"
                temp_path = json_dir / temp_filename
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"중간 저장 완료: {temp_path}")
    
    finally:
        driver.quit()
    
    # 최종 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_data_updated_{timestamp}.json"
    output_path = json_dir / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 처리 완료 ===")
    print(f"업데이트된 항목: {updated_count}개")
    print(f"저장된 파일: {output_path}")

if __name__ == "__main__":
    update_phone_data()

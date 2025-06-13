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
import os

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

def extract_fax_numbers(text):
    """텍스트에서 팩스번호 패턴 추출"""
    fax_patterns = [
        r'\b0\d{1,2}-\d{3,4}-\d{4}\b',  # 02-1234-5678, 031-123-4567
        r'\b0\d{1,2}\s\d{3,4}\s\d{4}\b',  # 02 1234 5678
        r'\b0\d{8,10}\b',  # 0212345678
        r'\b\d{3}-\d{3,4}-\d{4}\b',  # 051-123-4567
        r'\b\d{3}\s\d{3,4}\s\d{4}\b',  # 051 123 4567
    ]
    
    found_numbers = []
    for pattern in fax_patterns:
        matches = re.findall(pattern, text)
        found_numbers.extend(matches)
    
    # 중복 제거 및 정리
    cleaned_numbers = []
    for number in found_numbers:
        # 공백 제거 후 하이픈으로 통일
        clean_number = re.sub(r'\s+', '-', number.strip())
        if clean_number not in cleaned_numbers:
            cleaned_numbers.append(clean_number)
    
    return cleaned_numbers

def search_fax_number(driver, name):
    """구글에서 팩스번호 검색"""
    search_query = f"{name} 팩스번호"
    
    try:
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
        
        # 페이지 텍스트에서 팩스번호 추출
        page_text = driver.find_element(By.TAG_NAME, "body").text
        fax_numbers = extract_fax_numbers(page_text)
        
        return fax_numbers
        
    except (TimeoutException, NoSuchElementException) as e:
        print(f"검색 실패 - {name}: {str(e)}")
        return []

def update_fax_data():
    """JSON 파일에서 팩스번호 업데이트"""
    # JSON 파일 경로
    input_file = Path("C:/Users/kimyh/makedb/Python/cradcrawl_adv/data/json/filtered_data_updated_20250613_013541.json")
    base_dir = Path(__file__).parent.parent
    json_dir = base_dir / "data" / "json"
    
    # 시작 전 임시 파일 정리
    cleanup_temp_files(json_dir)
    
    # JSON 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"총 {len(data)}개의 항목을 처리합니다.")
    
    # WebDriver 설정
    driver = setup_driver()
    
    try:
        updated_count = 0
        last_temp_file = None  # 여기에 변수 선언 추가
        
        # 각 항목에 대해 팩스번호 검색
        for i, item in enumerate(data):
            name = item.get('name', '').strip()
            current_fax = item.get('fax', '').strip()
            current_phone = item.get('phone', '').strip()
            
            # 이름이 없거나 이미 팩스번호가 있는 경우 스킵
            if not name or current_fax:
                continue
            
            print(f"[{i+1}/{len(data)}] 검색 중: {name}")
            
            # 팩스번호 검색
            found_faxes = search_fax_number(driver, name)
            
            if found_faxes:
                # 첫 번째 검색된 팩스번호 사용
                found_fax = found_faxes[0]
                
                # 전화번호와 다른 경우에만 저장
                if found_fax != current_phone:
                    item['fax'] = found_fax
                    print(f"✓ 팩스번호 발견: {name} -> {found_fax}")
                    updated_count += 1
                else:
                    print(f"✗ 전화번호와 동일한 팩스번호 발견: {name}")
            else:
                print(f"✗ 팩스번호 없음: {name}")
            
            # 요청 간 딜레이 (차단 방지)
            time.sleep(2)
            
            # 중간 저장 (50개마다)
            if (i + 1) % 50 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"filtered_data_fax_updated_temp_{timestamp}.json"
                temp_path = json_dir / temp_filename
                
                # 이전 임시 파일 삭제
                if last_temp_file and last_temp_file.exists():
                    try:
                        os.remove(last_temp_file)
                        print(f"이전 임시 파일 삭제: {last_temp_file.name}")
                    except Exception as e:
                        print(f"이전 임시 파일 삭제 실패: {str(e)}")
                
                # 새 임시 파일 저장
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"중간 저장 완료: {temp_path}")
                
                # 현재 임시 파일 경로 저장
                last_temp_file = temp_path
    
    finally:
        driver.quit()
        
        # 마지막 임시 파일 삭제
        if last_temp_file and last_temp_file.exists():
            try:
                os.remove(last_temp_file)
                print(f"마지막 임시 파일 삭제: {last_temp_file.name}")
            except Exception as e:
                print(f"마지막 임시 파일 삭제 실패: {str(e)}")
    
    # 최종 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_data_fax_updated_{timestamp}.json"
    output_path = json_dir / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 처리 완료 ===")
    print(f"업데이트된 항목: {updated_count}개")
    print(f"저장된 파일: {output_path}")

def cleanup_temp_files(json_dir):
    """임시 파일 정리"""
    temp_files = list(json_dir.glob("filtered_data_fax_updated_temp_*.json"))
    if temp_files:
        print(f"\n이전 임시 파일 {len(temp_files)}개 정리 중...")
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                print(f"삭제됨: {temp_file.name}")
            except Exception as e:
                print(f"파일 삭제 실패 - {temp_file.name}: {str(e)}")

if __name__ == "__main__":
    update_fax_data()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON to CSV 변환기
홈페이지 크롤링 결과 JSON 파일을 CSV 파일로 변환하는 스크립트
"""

import json
import csv
import os
import glob
from datetime import datetime

def find_latest_json_file():
    """가장 최근의 raw_data_with_homepages_*.json 파일 찾기"""
    pattern = "raw_data_with_homepages_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print("❌ raw_data_with_homepages_*.json 파일을 찾을 수 없습니다.")
        return None
    
    # 파일명에서 날짜/시간 추출하여 가장 최근 파일 선택
    latest_file = max(files, key=os.path.getctime)
    print(f"📂 발견된 파일: {latest_file}")
    return latest_file

def extract_contact_info(org_data):
    """기관 데이터에서 연락처 정보 추출"""
    result = {
        "기관명": org_data.get("name", ""),
        "전화번호": "",
        "emails": "",
        "fax번호": ""
    }
    
    # 기본 필드에서 추출
    if org_data.get("phone"):
        result["전화번호"] = org_data["phone"]
    if org_data.get("fax"):
        result["fax번호"] = org_data["fax"]
    
    # 홈페이지 파싱 결과에서 추출
    homepage_content = org_data.get("homepage_content", {})
    if homepage_content:
        parsed_contact = homepage_content.get("parsed_contact", {})
        
        # 전화번호 추출 (파싱된 결과 우선)
        if parsed_contact.get("phones") and not result["전화번호"]:
            result["전화번호"] = ", ".join(parsed_contact["phones"])
        
        # 팩스번호 추출 (파싱된 결과 우선)
        if parsed_contact.get("faxes") and not result["fax번호"]:
            result["fax번호"] = ", ".join(parsed_contact["faxes"])
        
        # 이메일 추출
        if parsed_contact.get("emails"):
            result["emails"] = ", ".join(parsed_contact["emails"])
    
    return result

def json_to_csv(json_file_path, csv_file_path):
    """JSON 파일을 CSV 파일로 변환"""
    print(f"🔄 JSON to CSV 변환 시작...")
    print(f"📂 입력 파일: {json_file_path}")
    print(f"💾 출력 파일: {csv_file_path}")
    
    try:
        # JSON 파일 로드
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON 파일 로드 완료: {len(data)}개 카테고리")
        
        # CSV 파일 생성
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['기관명', '전화번호', 'emails', 'fax번호']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 헤더 작성
            writer.writeheader()
            
            total_count = 0
            
            # 각 카테고리별로 처리
            for category, organizations in data.items():
                print(f"📂 처리 중: {category} ({len(organizations)}개 기관)")
                
                for org in organizations:
                    contact_info = extract_contact_info(org)
                    writer.writerow(contact_info)
                    total_count += 1
                    
                    # 진행 상황 표시 (50개마다)
                    if total_count % 50 == 0:
                        print(f"   📝 {total_count}개 기관 처리 완료...")
        
        print(f"🎉 CSV 변환 완료!")
        print(f"📊 총 {total_count}개 기관 데이터 변환됨")
        print(f"💾 저장 위치: {csv_file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
        return False

def preview_csv(csv_file_path, num_rows=5):
    """CSV 파일 미리보기"""
    print(f"\n📋 CSV 파일 미리보기 (상위 {num_rows}개 행):")
    print("=" * 80)
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # 헤더 출력
            fieldnames = reader.fieldnames
            header = " | ".join([f"{name:15}" for name in fieldnames])
            print(header)
            print("-" * len(header))
            
            # 데이터 행 출력
            for i, row in enumerate(reader):
                if i >= num_rows:
                    break
                
                row_data = " | ".join([f"{row[name][:15]:15}" for name in fieldnames])
                print(row_data)
            
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ 미리보기 중 오류: {e}")

def count_data_statistics(csv_file_path):
    """데이터 통계 출력"""
    print(f"\n📊 데이터 통계:")
    print("=" * 50)
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            total_count = 0
            phone_count = 0
            email_count = 0
            fax_count = 0
            
            for row in reader:
                total_count += 1
                
                if row['전화번호'].strip():
                    phone_count += 1
                if row['emails'].strip():
                    email_count += 1
                if row['fax번호'].strip():
                    fax_count += 1
            
            print(f"📈 총 기관 수: {total_count}")
            print(f"📞 전화번호 보유: {phone_count}개 ({phone_count/total_count*100:.1f}%)")
            print(f"📧 이메일 보유: {email_count}개 ({email_count/total_count*100:.1f}%)")
            print(f"📠 팩스번호 보유: {fax_count}개 ({fax_count/total_count*100:.1f}%)")
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ 통계 계산 중 오류: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📊 JSON to CSV 변환기")
    print("=" * 60)
    
    # 최신 JSON 파일 찾기
    json_file = find_latest_json_file()
    if not json_file:
        print("💡 raw_data_with_homepages_YYYYMMDD_HHMMSS.json 파일이 현재 디렉토리에 있는지 확인하세요.")
        return
    
    # 출력 CSV 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"contact_data_{timestamp}.csv"
    
    print(f"🔄 변환 시작...")
    
    # JSON to CSV 변환
    success = json_to_csv(json_file, csv_file)
    
    if success:
        # 미리보기 출력
        preview_csv(csv_file)
        
        # 통계 출력
        count_data_statistics(csv_file)
        
        print(f"\n✅ 변환 완료!")
        print(f"📁 생성된 파일: {csv_file}")
    else:
        print(f"\n❌ 변환 실패!")

if __name__ == "__main__":
    main() 
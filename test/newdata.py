#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
교회 Excel 파일을 JSON으로 변환
Excel 파일 구조 확인 및 변환
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def debug_excel_structure(excel_file):
    """Excel 파일 구조 확인"""
    print(f"🔍 Excel 파일 구조 분석: {excel_file}")
    
    # 다양한 방법으로 시도
    print("\n1️⃣ 기본 읽기 (header=0):")
    try:
        df1 = pd.read_excel(excel_file, header=0)
        print(f"   컬럼: {list(df1.columns)}")
        print(f"   첫 번째 행: {df1.iloc[0].to_dict()}")
    except Exception as e:
        print(f"   오류: {e}")
    
    print("\n2️⃣ 헤더 없이 읽기 (header=None):")
    try:
        df2 = pd.read_excel(excel_file, header=None)
        print(f"   컬럼: {list(df2.columns)}")
        print(f"   첫 5행:")
        for i in range(min(5, len(df2))):
            print(f"     행 {i}: {df2.iloc[i].tolist()}")
    except Exception as e:
        print(f"   오류: {e}")
    
    print("\n3️⃣ 1행을 헤더로 (header=1):")
    try:
        df3 = pd.read_excel(excel_file, header=1)
        print(f"   컬럼: {list(df3.columns)}")
        if len(df3) > 0:
            print(f"   첫 번째 행: {df3.iloc[0].to_dict()}")
    except Exception as e:
        print(f"   오류: {e}")

def convert_excel_to_json(excel_file, output_file):
    """Excel 파일을 JSON으로 변환"""
    try:
        print(f"\n📖 Excel 파일 변환 시작: {excel_file}")
        
        # 첫 번째 행이 헤더이므로 header=0으로 읽기
        df = pd.read_excel(excel_file, header=0)
        
        print(f"📋 컬럼: {list(df.columns)}")
        print(f"📊 총 {len(df)}개의 행")
        
        # JSON 데이터 생성
        json_data = []
        processed_count = 0
        
        for index, row in df.iterrows():
            # 실제 컬럼명으로 직접 매핑
            name = str(row['상호명']).strip() if pd.notna(row['상호명']) else ""
            homepage = str(row['홈페이지']).strip() if pd.notna(row['홈페이지']) else ""
            phone = str(row['전화번호 1']).strip() if pd.notna(row['전화번호 1']) else ""
            fax = str(row['전화번호 2']).strip() if pd.notna(row['전화번호 2']) else ""
            address = str(row['도로명 주소']).strip() if pd.notna(row['도로명 주소']) else ""
            postal_code = str(row['우편번호 ']).strip() if pd.notna(row['우편번호 ']) else ""
            
            # 'nan' 문자열 제거
            if name == 'nan': name = ""
            if homepage == 'nan': homepage = ""
            if phone == 'nan': phone = ""
            if fax == 'nan': fax = ""
            if address == 'nan': address = ""
            if postal_code == 'nan': postal_code = ""
            
            # 기관명이 있는 경우만 추가
            if name and len(name) > 1:  # 최소 2글자 이상
                item = {
                    "name": name,
                    "category": "종교시설",
                    "homepage": homepage,
                    "phone": phone,
                    "fax": fax,
                    "email": "",
                    "mobile": "",
                    "postal_code": postal_code,
                    "address": address
                }
                
                json_data.append(item)
                processed_count += 1
                
                # 처리 진행상황 표시
                if processed_count % 5000 == 0:
                    print(f"  처리 중: {processed_count}개...")
        
        # JSON 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 변환 완료: {len(json_data)}개 항목")
        return output_file
        
    except Exception as e:
        print(f"❌ 변환 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🏛️ 교회 Excel → JSON 변환기 (구조 분석)")
    print("=" * 60)
    
    # 파일 경로 설정
    excel_file = "../data/excel/교회_원본_수정01.xlsx"
    
    # 출력 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/json/church_data_converted_{timestamp}.json"
    
    print(f"📂 입력 파일: {excel_file}")
    print(f"💾 출력 파일: {output_file}")
    
    # 파일 존재 확인
    if not os.path.exists(excel_file):
        print(f"❌ Excel 파일을 찾을 수 없습니다: {excel_file}")
        return 1
    
    try:
        # Excel 구조 디버깅
        debug_excel_structure(excel_file)
        
        # 변환 실행
        result_file = convert_excel_to_json(excel_file, output_file)
        
        print(f"\n🎉 변환 완료!")
        print(f"📁 생성된 파일: {result_file}")
        
        # 변환 결과 확인
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 변환된 데이터 수: {len(data)}개")
        
        # 샘플 데이터 출력
        if data:
            print(f"\n📋 샘플 데이터 (처음 3개):")
            for i, sample in enumerate(data[:3]):
                print(f"  {i+1}. {sample['name']}")
                for key, value in sample.items():
                    if value:  # 빈 값이 아닌 것만 출력
                        print(f"     - {key}: {value}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 변환 중 오류: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
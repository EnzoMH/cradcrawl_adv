#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel to JSON 변환기
Excel 파일을 raw_data_0530.json 형태의 JSON으로 변환합니다.

작성자: AI Assistant
생성일: 2025년
목적: undefined.xlsx 파일을 JSON 형태로 변환
"""

import pandas as pd
import json
import os
from datetime import datetime

def excel_to_json(excel_file_path, output_file_path):
    """
    Excel 파일을 JSON 형태로 변환하는 함수
    
    Args:
        excel_file_path (str): 변환할 Excel 파일 경로
        output_file_path (str): 저장할 JSON 파일 경로
    
    Returns:
        bool: 변환 성공 여부
    """
    try:
        # Excel 파일 읽기
        print(f"📖 Excel 파일을 읽는 중: {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        
        # 컬럼명 출력 (디버깅용)
        print(f"📋 Excel 파일의 컬럼: {list(df.columns)}")
        print(f"📊 총 {len(df)}개의 행이 있습니다.")
        
        # 데이터를 JSON 형태로 변환
        json_data = []
        
        for index, row in df.iterrows():
            # raw_data_0530.json 형태에 맞춰 데이터 구조 생성
            # 다양한 컬럼명 변형을 고려하여 매핑
            item = {
                "name": get_value_from_row(row, ['name', '이름', '업체명', '회사명', '기관명', '상호명']),
                "category": get_value_from_row(row, ['category', '카테고리', '업종', '분류', '종류', '업태']),
                "homepage": get_value_from_row(row, ['homepage', '홈페이지', '웹사이트', 'website', 'url']),
                "phone": get_value_from_row(row, ['phone', '전화번호', '전화', 'tel', '연락처']),
                "fax": get_value_from_row(row, ['fax', '팩스', 'facsimile']),
                "email": get_value_from_row(row, ['email', '이메일', 'mail', 'e-mail']),
                "mobile": get_value_from_row(row, ['mobile', '휴대폰', '핸드폰', '모바일', '휴대전화']),
                "postal_code": get_value_from_row(row, ['postal_code', '우편번호', 'zipcode', 'zip', '우편']),
                "address": get_value_from_row(row, ['address', '주소', 'addr', '소재지', '위치'])
            }
            
            json_data.append(item)
        
        # JSON 파일로 저장
        print(f"💾 JSON 파일로 저장 중: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 변환 완료!")
        print(f"📈 총 {len(json_data)}개의 항목이 변환되었습니다.")
        print(f"📁 저장 경로: {output_file_path}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ 오류: Excel 파일을 찾을 수 없습니다. - {excel_file_path}")
        return False
    except Exception as e:
        print(f"❌ 변환 중 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_value_from_row(row, column_names):
    """
    여러 컬럼명 중에서 값을 찾아 반환하는 함수
    
    Args:
        row: 데이터프레임의 행
        column_names: 찾을 컬럼명 리스트
    
    Returns:
        str: 찾은 값 (문자열로 변환) 또는 빈 문자열
    """
    for col_name in column_names:
        if col_name in row.index and pd.notna(row[col_name]):
            value = str(row[col_name]).strip()
            if value and value.lower() not in ['nan', 'none', 'null', '']:
                return value
    return ""

def preview_excel_structure(excel_file_path):
    """
    Excel 파일의 구조를 미리 확인하는 함수
    
    Args:
        excel_file_path (str): Excel 파일 경로
    """
    try:
        df = pd.read_excel(excel_file_path)
        print("=" * 60)
        print("📊 Excel 파일 구조 미리보기")
        print("=" * 60)
        print(f"📏 총 행 수: {len(df)}")
        print(f"📋 총 열 수: {len(df.columns)}")
        print("\n컬럼 목록:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print("\n🔍 첫 3행 데이터 미리보기:")
        print(df.head(3).to_string())
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Excel 파일 미리보기 중 오류: {str(e)}")

def validate_json_structure(json_file_path):
    """
    생성된 JSON 파일의 구조를 검증하는 함수
    
    Args:
        json_file_path (str): 검증할 JSON 파일 경로
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n🔍 생성된 JSON 파일 검증:")
        print(f"📊 총 항목 수: {len(data)}")
        
        if len(data) > 0:
            print("\n첫 번째 항목 예시:")
            first_item = data[0]
            for key, value in first_item.items():
                print(f"  {key}: {value[:50] + '...' if len(str(value)) > 50 else value}")
        
        # 필수 필드 체크
        required_fields = ['name', 'category', 'homepage', 'phone', 'fax', 'email', 'mobile', 'postal_code', 'address']
        missing_fields = [field for field in required_fields if field not in data[0].keys()]
        
        if missing_fields:
            print(f"⚠️  누락된 필드: {missing_fields}")
        else:
            print("✅ 모든 필수 필드가 포함되었습니다.")
            
    except Exception as e:
        print(f"❌ JSON 검증 중 오류: {str(e)}")

def main():
    """
    메인 실행 함수
    """
    # 파일 경로 설정
    excel_file_path = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\undefined.xlsx"
    output_dir = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv"
    
    # 출력 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"undefined_converted_{timestamp}.json"
    output_file_path = os.path.join(output_dir, output_file_name)
    
    print("=" * 60)
    print("🔄 Excel to JSON 변환기")
    print("=" * 60)
    print(f"📥 입력 파일: {excel_file_path}")
    print(f"📤 출력 파일: {output_file_path}")
    print("-" * 60)
    
    # 파일 존재 확인
    if not os.path.exists(excel_file_path):
        print(f"❌ 오류: Excel 파일이 존재하지 않습니다.")
        print(f"   경로: {excel_file_path}")
        return
    
    # 출력 디렉토리 확인 및 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 출력 디렉토리를 생성했습니다: {output_dir}")
    
    # Excel 구조 미리보기
    preview_excel_structure(excel_file_path)
    
    # 사용자 확인 (자동 실행을 위해 주석 처리)
    # user_input = input("\n변환을 계속하시겠습니까? (y/n): ").lower().strip()
    # if user_input not in ['y', 'yes', '']:
    #     print("변환이 취소되었습니다.")
    #     return
    
    print("\n🚀 변환을 시작합니다...")
    
    # 변환 실행
    success = excel_to_json(excel_file_path, output_file_path)
    
    if success:
        print("\n🎉 변환이 성공적으로 완료되었습니다!")
        print(f"📁 저장된 파일: {output_file_path}")
        
        # JSON 구조 검증
        validate_json_structure(output_file_path)
        
        print("\n📝 사용법:")
        print("  생성된 JSON 파일을 확인하고 필요에 따라 수정하세요.")
        print("  raw_data_0530.json과 동일한 구조로 변환되었습니다.")
        
    else:
        print("\n❌ 변환 중 오류가 발생했습니다.")
        print("  Excel 파일의 구조를 확인하고 다시 시도해주세요.")

if __name__ == "__main__":
    main()

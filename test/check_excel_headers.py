#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
엑셀 파일 헤더 및 샘플 데이터 확인 (복잡한 헤더 구조 대응)
"""

import pandas as pd

def check_excel_structure():
    excel_file_path = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\data\excel\25년 학단 전체 DB (20240401 기준_초-중-고-각종학교) 12316.xlsx"
    
    print("=" * 60)
    print("🔍 엑셀 파일 구조 분석 (복잡한 헤더)")
    print("=" * 60)
    
    try:
        # 먼저 원본 구조 확인 (처음 5행)
        print("📋 원본 파일 구조 (처음 5행):")
        df_raw = pd.read_excel(excel_file_path, header=None, nrows=5)
        for i in range(len(df_raw)):
            print(f"\n[행 {i+1}]")
            non_empty_cols = []
            for j, value in enumerate(df_raw.iloc[i]):
                if pd.notna(value) and str(value).strip():
                    non_empty_cols.append(f"컬럼{j}: {value}")
            if non_empty_cols:
                print("  " + " | ".join(non_empty_cols[:10]))  # 처음 10개만 표시
            else:
                print("  (모든 컬럼이 비어있음)")
        
        print("\n" + "="*60)
        print("📊 3행을 헤더로 사용하여 데이터 읽기")
        print("="*60)
        
        # 3행을 헤더로 사용하여 읽기 (header=2, 0-based indexing)
        df = pd.read_excel(excel_file_path, header=2)
        
        print(f"📊 총 행수: {len(df)}")
        print(f"📊 총 열수: {len(df.columns)}")
        
        print(f"\n📋 실제 헤더 (3행 기준):")
        for i, col in enumerate(df.columns):
            # 빈 헤더나 Unnamed 제외하고 의미있는 헤더만 출력
            if pd.notna(col) and str(col).strip() and not str(col).startswith('Unnamed'):
                print(f"  [{i}] '{col}'")
        
        print(f"\n🔍 데이터 샘플 (처음 3행):")
        for i in range(min(3, len(df))):
            print(f"\n[데이터 행 {i+1}]")
            # 데이터가 있는 컬럼만 출력
            data_found = False
            for col in df.columns:
                value = df.iloc[i][col]
                if pd.notna(value) and str(value).strip():
                    print(f"  {col}: {value}")
                    data_found = True
            if not data_found:
                print("  (모든 컬럼이 비어있음)")
        
        # 학교명이나 주소 관련 컬럼 찾기
        school_related_cols = []
        address_related_cols = []
        phone_related_cols = []
        
        for col in df.columns:
            col_str = str(col).lower()
            if '학교' in col_str or '교명' in col_str or '명칭' in col_str:
                school_related_cols.append(col)
            elif '주소' in col_str or '소재지' in col_str or '위치' in col_str:
                address_related_cols.append(col)
            elif '전화' in col_str or '번호' in col_str or 'tel' in col_str or 'phone' in col_str:
                phone_related_cols.append(col)
        
        if school_related_cols:
            print(f"\n🏫 학교명 관련 컬럼:")
            for col in school_related_cols:
                non_empty = df[col].notna() & (df[col] != "")
                non_empty_count = non_empty.sum()
                print(f"  {col}: {non_empty_count}개 데이터 존재")
                if non_empty_count > 0:
                    samples = df[df[col].notna() & (df[col] != "")][col].head(3)
                    print(f"    샘플: {list(samples)}")
        
        if address_related_cols:
            print(f"\n🏢 주소 관련 컬럼:")
            for col in address_related_cols:
                non_empty = df[col].notna() & (df[col] != "")
                non_empty_count = non_empty.sum()
                print(f"  {col}: {non_empty_count}개 데이터 존재")
                if non_empty_count > 0:
                    samples = df[df[col].notna() & (df[col] != "")][col].head(3)
                    print(f"    샘플: {list(samples)}")
                    
        if phone_related_cols:
            print(f"\n📞 전화번호 관련 컬럼:")
            for col in phone_related_cols:
                non_empty = df[col].notna() & (df[col] != "")
                non_empty_count = non_empty.sum()
                print(f"  {col}: {non_empty_count}개 데이터 존재")
                if non_empty_count > 0:
                    samples = df[df[col].notna() & (df[col] != "")][col].head(3)
                    print(f"    샘플: {list(samples)}")
        
        # 다른 방법: 2행을 헤더로 읽어보기
        print("\n" + "="*60)
        print("📊 2행을 헤더로 사용하여 데이터 읽기 (비교용)")
        print("="*60)
        
        df2 = pd.read_excel(excel_file_path, header=1)
        print(f"📊 총 행수: {len(df2)}")
        print(f"📊 총 열수: {len(df2.columns)}")
        
        print(f"\n📋 실제 헤더 (2행 기준, 의미있는 것만):")
        for i, col in enumerate(df2.columns):
            if pd.notna(col) and str(col).strip() and not str(col).startswith('Unnamed'):
                print(f"  [{i}] '{col}'")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_excel_structure()
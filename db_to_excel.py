#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 데이터베이스 → Excel 변환기
churches_crm.db의 organizations 테이블을 지정된 헤더로 엑셀 변환
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

def db_to_excel(db_path, output_path=None):
    """
    SQLite 데이터베이스를 Excel로 변환
    
    Args:
        db_path (str): SQLite 데이터베이스 파일 경로
        output_path (str): 출력 Excel 파일 경로 (선택사항)
    
    Returns:
        str: 생성된 Excel 파일 경로
    """
    
    # 출력 파일명 생성
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"churches_crm_export_{timestamp}.xlsx"
    
    print("=" * 60)
    print("🔄 SQLite → Excel 변환기")
    print("=" * 60)
    print(f"📂 입력 DB: {db_path}")
    print(f"💾 출력 파일: {output_path}")
    print("-" * 60)
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        
        # 지정된 헤더 순서로 쿼리 작성
        query = """
        SELECT 
            id,
            name,
            type,
            category,
            homepage,
            phone,
            fax,
            email,
            postal_code,
            address
        FROM organizations 
        WHERE is_active = 1
        ORDER BY id
        """
        
        print("📊 데이터베이스에서 데이터 조회 중...")
        
        # 데이터 조회
        df = pd.read_sql_query(query, conn)
        
        print(f"✅ 조회 완료: {len(df)}개 레코드")
        print(f"📋 컬럼: {list(df.columns)}")
        
        # 데이터 전처리
        print("🔧 데이터 전처리 중...")
        
        # NaN 값을 빈 문자열로 변경
        df = df.fillna('')
        
        # 데이터 타입 정리
        for col in df.columns:
            if col != 'id':  # id는 정수로 유지
                df[col] = df[col].astype(str)
        
        # Excel 파일로 저장
        print("💾 Excel 파일 생성 중...")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 메인 데이터 시트
            df.to_excel(writer, sheet_name='교회_데이터', index=False)
            
            # 통계 시트 생성
            stats_data = []
            for column in df.columns:
                non_empty_count = (df[column] != '').sum()
                
                stats_data.append({
                    '필드명': column,
                    '전체_레코드수': len(df),
                    '데이터_있는_레코드수': non_empty_count,
                    '채움률_퍼센트': round((non_empty_count / len(df)) * 100, 1),
                    '샘플_데이터': str(df[column].iloc[0] if len(df) > 0 else '')[:50]
                })
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='필드_통계', index=False)
            
            # 요약 정보 시트
            summary_data = [
                ['총 레코드 수', len(df)],
                ['변환 일시', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['원본 DB 파일', db_path],
                ['출력 Excel 파일', output_path]
            ]
            
            summary_df = pd.DataFrame(summary_data, columns=['항목', '값'])
            summary_df.to_excel(writer, sheet_name='변환_정보', index=False)
        
        # 연결 종료
        conn.close()
        
        print("✅ 변환 완료!")
        print(f"📁 생성된 파일: {output_path}")
        print(f"📊 변환된 데이터: {len(df)}개 레코드")
        print(f"📋 포함된 컬럼: {', '.join(df.columns)}")
        
        # 미리보기 출력
        if len(df) > 0:
            print("\n📖 데이터 미리보기 (첫 3개 레코드):")
            print("-" * 80)
            for i in range(min(3, len(df))):
                print(f"[{i+1}] ID: {df.iloc[i]['id']}")
                print(f"    이름: {df.iloc[i]['name']}")
                print(f"    유형: {df.iloc[i]['type']}")
                print(f"    카테고리: {df.iloc[i]['category']}")
                print(f"    전화: {df.iloc[i]['phone']}")
                print(f"    주소: {df.iloc[i]['address'][:50]}..." if len(str(df.iloc[i]['address'])) > 50 else f"    주소: {df.iloc[i]['address']}")
                print("-" * 40)
        
        return output_path
        
    except sqlite3.Error as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 변환 오류: {e}")
        return None

def preview_database_structure(db_path):
    """데이터베이스 구조 미리보기"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 데이터베이스 구조 분석:")
        print("-" * 40)
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 테이블 목록: {[table[0] for table in tables]}")
        
        # organizations 테이블 스키마 조회
        if ('organizations',) in tables:
            cursor.execute("PRAGMA table_info(organizations);")
            columns = cursor.fetchall()
            print(f"\n📊 organizations 테이블 컬럼:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # 레코드 수 조회
            cursor.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1;")
            count = cursor.fetchone()[0]
            print(f"\n📈 활성 레코드 수: {count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 구조 분석 오류: {e}")

def main():
    """메인 실행 함수"""
    # 데이터베이스 파일 경로
    db_path = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\churches_crm.db"
    
    print("🚀 SQLite → Excel 변환 시작")
    print("=" * 60)
    
    # 파일 존재 확인
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return
    
    # 데이터베이스 구조 미리보기
    preview_database_structure(db_path)
    print()
    
    # 변환 실행
    result = db_to_excel(db_path)
    
    if result:
        print(f"\n🎉 변환 성공!")
        print(f"📁 파일 위치: {os.path.abspath(result)}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(result) / 1024  # KB
        print(f"📊 파일 크기: {file_size:.1f} KB")
    else:
        print("\n❌ 변환 실패")

if __name__ == "__main__":
    main()
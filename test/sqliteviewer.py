#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 데이터베이스 뷰어
churches_crm.db 파일의 구조와 내용을 확인하는 도구
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

class SQLiteViewer:
    """SQLite 데이터베이스 뷰어 클래스"""
    
    def __init__(self, db_path: str):
        """초기화"""
        self.db_path = db_path
        self.connection = None
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            print(f"✅ 데이터베이스 연결 성공: {self.db_path}")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            print("✅ 데이터베이스 연결 해제")
    
    def get_database_info(self):
        """데이터베이스 기본 정보 조회"""
        print("\n" + "="*80)
        print("📋 데이터베이스 기본 정보")
        print("="*80)
        
        # 파일 정보
        file_size = os.path.getsize(self.db_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📁 파일 경로: {self.db_path}")
        print(f"📏 파일 크기: {file_size:,} bytes ({file_size_mb:.2f} MB)")
        
        # SQLite 버전
        cursor = self.connection.cursor()
        cursor.execute("SELECT sqlite_version()")
        sqlite_version = cursor.fetchone()[0]
        print(f"🔢 SQLite 버전: {sqlite_version}")
        
        # 수정 시간
        mtime = os.path.getmtime(self.db_path)
        modified_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕒 마지막 수정: {modified_time}")
    
    def get_table_list(self) -> List[str]:
        """테이블 목록 조회"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "="*80)
        print("📊 테이블 목록")
        print("="*80)
        
        if not tables:
            print("❌ 테이블이 없습니다.")
            return tables
        
        for i, table in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{i:2d}. {table:<30} ({count:,} rows)")
        
        return tables
    
    def get_table_schema(self, table_name: str):
        """테이블 스키마 정보 조회"""
        print(f"\n" + "="*80)
        print(f"🗂️  테이블 스키마: {table_name}")
        print("="*80)
        
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"❌ 테이블 '{table_name}'을 찾을 수 없습니다.")
            return
        
        print(f"{'순번':<4} {'컬럼명':<25} {'타입':<15} {'NULL허용':<8} {'기본값':<15} {'PK':<4}")
        print("-" * 80)
        
        for col in columns:
            cid, name, col_type, notnull, dflt_value, pk = col
            null_allowed = "No" if notnull else "Yes"
            default_val = dflt_value if dflt_value is not None else ""
            primary_key = "Yes" if pk else ""
            
            print(f"{cid:<4} {name:<25} {col_type:<15} {null_allowed:<8} {str(default_val):<15} {primary_key:<4}")
    
    def get_sample_data(self, table_name: str, limit: int = 5):
        """테이블 샘플 데이터 조회"""
        print(f"\n" + "="*80)
        print(f"📄 샘플 데이터: {table_name} (최대 {limit}개)")
        print("="*80)
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            
            if not rows:
                print("❌ 데이터가 없습니다.")
                return
            
            # 컬럼명 가져오기
            column_names = [description[0] for description in cursor.description]
            
            # 각 컬럼의 최대 길이 계산 (출력 형식 맞추기)
            col_widths = {}
            for col_name in column_names:
                col_widths[col_name] = max(len(col_name), 15)  # 최소 15자
                for row in rows:
                    if row[col_name] is not None:
                        col_widths[col_name] = max(col_widths[col_name], len(str(row[col_name])))
                col_widths[col_name] = min(col_widths[col_name], 30)  # 최대 30자
            
            # 헤더 출력
            header = ""
            separator = ""
            for col_name in column_names:
                width = col_widths[col_name]
                header += f"{col_name:<{width}} "
                separator += "-" * width + " "
            
            print(header)
            print(separator)
            
            # 데이터 출력
            for row in rows:
                row_str = ""
                for col_name in column_names:
                    width = col_widths[col_name]
                    value = row[col_name] if row[col_name] is not None else "NULL"
                    # 너무 긴 값은 자르기
                    if len(str(value)) > width:
                        value = str(value)[:width-3] + "..."
                    row_str += f"{str(value):<{width}} "
                print(row_str)
                
        except Exception as e:
            print(f"❌ 샘플 데이터 조회 실패: {e}")
    
    def get_table_statistics(self, table_name: str):
        """테이블 통계 정보"""
        print(f"\n" + "="*80)
        print(f"📈 테이블 통계: {table_name}")
        print("="*80)
        
        try:
            cursor = self.connection.cursor()
            
            # 전체 행 수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            print(f"📊 전체 행 수: {total_rows:,}")
            
            # 컬럼별 NULL 값 통계
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("\n🔍 컬럼별 데이터 현황:")
            print(f"{'컬럼명':<25} {'NULL 개수':<12} {'NULL 비율':<12} {'데이터 타입':<15}")
            print("-" * 70)
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                # NULL 개수 계산
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                null_count = cursor.fetchone()[0]
                null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
                
                print(f"{col_name:<25} {null_count:<12} {null_percentage:<11.1f}% {col_type:<15}")
            
            # 특정 컬럼들의 유니크 값 개수 (중요한 컬럼들)
            important_columns = ['name', 'category', 'type', 'phone', 'homepage', 'address']
            
            print("\n🎯 주요 컬럼 유니크 값 개수:")
            for col_name in important_columns:
                try:
                    cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL")
                    unique_count = cursor.fetchone()[0]
                    print(f"  {col_name:<15}: {unique_count:,} 개의 유니크 값")
                except:
                    continue  # 컬럼이 없으면 스킵
                    
        except Exception as e:
            print(f"❌ 통계 정보 조회 실패: {e}")
    
    def search_data(self, table_name: str, search_term: str, limit: int = 10):
        """데이터 검색"""
        print(f"\n" + "="*80)
        print(f"🔍 데이터 검색: '{search_term}' in {table_name}")
        print("="*80)
        
        try:
            cursor = self.connection.cursor()
            
            # 텍스트 컬럼들에서 검색
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            text_columns = []
            for col in columns:
                col_type = col[2].upper()
                if 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
                    text_columns.append(col[1])
            
            if not text_columns:
                print("❌ 검색 가능한 텍스트 컬럼이 없습니다.")
                return
            
            # 검색 쿼리 생성
            where_conditions = []
            for col in text_columns:
                where_conditions.append(f"{col} LIKE '%{search_term}%'")
            
            where_clause = " OR ".join(where_conditions)
            query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                print("❌ 검색 결과가 없습니다.")
                return
            
            print(f"✅ {len(rows)}개의 결과를 찾았습니다:")
            
            # 결과 출력 (간단한 형태)
            column_names = [description[0] for description in cursor.description]
            for i, row in enumerate(rows, 1):
                print(f"\n--- 결과 {i} ---")
                for col_name in column_names[:5]:  # 처음 5개 컬럼만 표시
                    value = row[col_name] if row[col_name] is not None else "NULL"
                    print(f"  {col_name}: {value}")
                    
        except Exception as e:
            print(f"❌ 데이터 검색 실패: {e}")
    
    def run_interactive_viewer(self):
        """대화형 뷰어 실행"""
        print("\n🚀 SQLite 대화형 뷰어 시작")
        print("사용 가능한 명령어:")
        print("  1. info    - 데이터베이스 정보")
        print("  2. tables  - 테이블 목록") 
        print("  3. schema <table_name> - 테이블 스키마")
        print("  4. sample <table_name> [limit] - 샘플 데이터")
        print("  5. stats <table_name> - 테이블 통계")
        print("  6. search <table_name> <search_term> - 데이터 검색")
        print("  7. quit    - 종료")
        
        while True:
            try:
                command = input("\n> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'q':
                    break
                elif cmd == 'info':
                    self.get_database_info()
                elif cmd == 'tables':
                    self.get_table_list()
                elif cmd == 'schema' and len(command) >= 2:
                    self.get_table_schema(command[1])
                elif cmd == 'sample' and len(command) >= 2:
                    limit = int(command[2]) if len(command) >= 3 else 5
                    self.get_sample_data(command[1], limit)
                elif cmd == 'stats' and len(command) >= 2:
                    self.get_table_statistics(command[1])
                elif cmd == 'search' and len(command) >= 3:
                    self.search_data(command[1], command[2])
                else:
                    print("❌ 잘못된 명령어입니다. 사용법을 확인하세요.")
                    
            except KeyboardInterrupt:
                print("\n👋 사용자에 의해 중단되었습니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")

def main():
    """메인 함수"""
    db_path = r"C:\Users\MyoengHo Shin\pjt\advanced_crawling\database\churches_crm.db"
    
    try:
        viewer = SQLiteViewer(db_path)
        viewer.connect()
        
        # 자동으로 기본 정보 표시
        viewer.get_database_info()
        tables = viewer.get_table_list()
        
        # organizations 테이블이 있으면 자동으로 보여주기
        if 'organizations' in tables:
            viewer.get_table_schema('organizations')
            viewer.get_sample_data('organizations', 3)
            viewer.get_table_statistics('organizations')
        
        # 대화형 모드 시작
        viewer.run_interactive_viewer()
        
    except Exception as e:
        print(f"❌ 프로그램 실행 실패: {e}")
    finally:
        if 'viewer' in locals():
            viewer.disconnect()

if __name__ == "__main__":
    main()
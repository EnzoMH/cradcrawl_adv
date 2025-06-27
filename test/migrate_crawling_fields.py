#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
크롤링 추적 필드 마이그레이션 실행 스크립트
organizations 테이블에 ai_crawled, last_crawled_at 필드 추가
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.migration import AIAgenticDataMigrator

def main():
    print("🚀 크롤링 추적 필드 마이그레이션 시작")
    print("="*60)
    
    try:
        # 데이터베이스 경로 확인
        db_path = r"C:\Users\MyoengHo Shin\pjt\advanced_crawling\database\churches_crm.db"
        if not os.path.exists(db_path):
            print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
            return False
        
        print(f"📂 데이터베이스: {db_path}")
        
        # 마이그레이터 초기화
        migrator = AIAgenticDataMigrator(db_path)
        
        # 마이그레이션 실행
        migrator.add_crawling_tracking_fields()
        
        print("="*60)
        print("✅ 크롤링 추적 필드 마이그레이션 완료!")
        print("")
        print("🎯 추가된 필드:")
        print("  - ai_crawled: BOOLEAN DEFAULT 0")
        print("  - last_crawled_at: DATETIME")
        print("")
        print("🔍 추가된 인덱스:")
        print("  - idx_org_ai_crawled")
        print("  - idx_org_last_crawled")
        print("")
        print("📋 다음 단계:")
        print("  1. test/sqliteviewer.py 로 스키마 확인")
        print("  2. crawler_main.py 의 중복 방지 쿼리 업데이트")
        print("  3. 크롤링 테스트 실행")
        
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 마이그레이션 스크립트
JSON 파일의 데이터를 SQLite DB로 이전
"""

# 직접 import 방식으로 변경
from database.database import ChurchCRMDatabase
from database.models import UserRole, OrganizationType
from utils.file_utils import FileUtils
import json
import os

class DataMigrator:
    """JSON 데이터 마이그레이션 클래스"""
    
    def __init__(self):
        self.db = ChurchCRMDatabase()
        self.stats = {
            "total_processed": 0,
            "successfully_migrated": 0,
            "failed": 0,
            "duplicates_skipped": 0,
            "errors": []
        }
    
    def migrate_json_to_db(self, data, source_name="merged_church_data"):
        """JSON 데이터를 DB로 마이그레이션"""
        print(f"🔄 {source_name} 마이그레이션 시작...")
        
        # 데이터 구조 파악
        churches = []
        if isinstance(data, dict):
            if 'churches' in data:
                churches = data['churches']
                print(f"📊 메타데이터: {data.get('metadata', {})}")
            else:
                # 카테고리별로 구성된 데이터 처리
                for category, orgs in data.items():
                    if isinstance(orgs, list):
                        for org in orgs:
                            if isinstance(org, dict):
                                org['category'] = category
                                churches.append(org)
        elif isinstance(data, list):
            churches = data
        
        print(f"📈 총 처리할 기관 수: {len(churches)}")
        
        # 배치 처리
        batch_size = 100
        for i in range(0, len(churches), batch_size):
            batch = churches[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(churches) + batch_size - 1) // batch_size
            
            print(f"📦 배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개)...")
            
            for church in batch:
                try:
                    self.stats["total_processed"] += 1
                    
                    # 데이터 변환
                    org_data = self.transform_church_data(church)
                    
                    # 중복 체크
                    if self.is_duplicate(org_data):
                        self.stats["duplicates_skipped"] += 1
                        continue
                    
                    # DB에 저장
                    org_id = self.db.create_organization(org_data)
                    self.stats["successfully_migrated"] += 1
                    
                    if self.stats["successfully_migrated"] % 50 == 0:
                        print(f"✅ {self.stats['successfully_migrated']}개 처리 완료...")
                        
                except Exception as e:
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"{church.get('name', 'Unknown')}: {str(e)}")
                    print(f"❌ 실패: {church.get('name', 'Unknown')} - {e}")
        
        self.print_migration_summary()
        return True
    
    def transform_church_data(self, church):
        """교회 JSON 데이터를 Organizations 테이블 형식으로 변환"""
        crawling_data = {}
        
        # 크롤링 메타데이터 수집
        crawling_fields = [
            'homepage_parsed', 'page_title', 'page_content_length',
            'contact_info_extracted', 'meta_info', 'ai_summary',
            'parsing_timestamp', 'parsing_status'
        ]
        
        for field in crawling_fields:
            if field in church:
                crawling_data[field] = church[field]
        
        # 기본 조직 데이터 구성
        org_data = {
            'name': church.get('name', '').strip(),
            'type': OrganizationType.CHURCH.value,
            'category': church.get('category', '종교시설'),
            'homepage': church.get('homepage', '').strip(),
            'phone': church.get('phone', '').strip(),
            'fax': church.get('fax', '').strip(),
            'email': church.get('email', '').strip(),
            'mobile': church.get('mobile', '').strip(),
            'postal_code': church.get('postal_code', '').strip(),
            'address': church.get('address', '').strip(),
            'contact_status': 'NEW',
            'priority': 'MEDIUM',
            'lead_source': 'DATABASE',
            'crawling_data': crawling_data,
            'created_by': 'MIGRATION'
        }
        
        return org_data
    
    def is_duplicate(self, org_data):
        """중복 데이터 체크"""
        try:
            with self.db.get_connection() as conn:
                existing = conn.execute('''
                SELECT COUNT(*) FROM organizations 
                WHERE name = ? AND is_active = 1
                ''', (org_data['name'],)).fetchone()[0]
                
                return existing > 0
                
        except Exception as e:
            print(f"⚠️  중복 체크 실패: {e}")
            return False
    
    def print_migration_summary(self):
        """마이그레이션 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 마이그레이션 결과 요약")
        print("="*60)
        print(f"총 처리된 레코드: {self.stats['total_processed']:,}개")
        print(f"성공적으로 마이그레이션: {self.stats['successfully_migrated']:,}개")
        print(f"중복으로 건너뜀: {self.stats['duplicates_skipped']:,}개")
        print(f"실패: {self.stats['failed']:,}개")
        
        if self.stats['errors']:
            print(f"\n❌ 오류 목록 (최대 10개):")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
        
        success_rate = (self.stats['successfully_migrated'] / max(1, self.stats['total_processed'])) * 100
        print(f"\n✅ 성공률: {success_rate:.1f}%")
        print("="*60)

def migrate_data():
    print("🔄 데이터 마이그레이션 시작...")
    
    try:
        migrator = DataMigrator()
        
        # JSON 파일 로드
        print("📁 JSON 파일 로드 중...")
        data = FileUtils.load_json("data/json/merged_church_data_20250618_174032.json")
        
        # 데이터 마이그레이션
        print("🔄 데이터베이스로 마이그레이션 중...")
        migrator.migrate_json_to_db(data, source_name="merged_church_data")
        
        print("✅ 데이터 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_data()
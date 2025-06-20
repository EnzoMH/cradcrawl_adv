#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 데이터를 SQLite CRM 데이터베이스로 마이그레이션
merged_church_data_20250618_174032.json → churches_crm.db
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# 상위 디렉토리에서 모듈 import 가능하도록
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import ChurchCRMDatabase, UserRole, OrganizationType

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
    
    def load_json_data(self, json_file_path: str) -> Optional[List[Dict[str, Any]]]:
        """JSON 파일을 로드하고 교회 데이터 반환"""
        try:
            if not os.path.exists(json_file_path):
                print(f"❌ 파일을 찾을 수 없습니다: {json_file_path}")
                return None
            
            print(f"📂 JSON 파일 로드 중: {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 데이터 구조 감지
            if isinstance(data, dict) and 'churches' in data:
                churches = data['churches']
                print(f"✅ 데이터 구조: {{churches: [...]}}")
                print(f"📊 메타데이터: {data.get('metadata', {})}")
            elif isinstance(data, list):
                churches = data
                print(f"✅ 데이터 구조: [...]")
            else:
                print(f"❌ 지원하지 않는 데이터 구조: {type(data)}")
                return None
            
            print(f"📈 총 교회 수: {len(churches)}")
            
            return churches
            
        except Exception as e:
            print(f"❌ JSON 파일 로드 실패: {e}")
            return None
    
    def create_default_users(self):
        """기본 사용자 계정들 생성"""
        print("\n👥 기본 사용자 계정 생성 중...")
        
        default_users = [
            {
                "username": "admin",
                "password": "admin123",
                "full_name": "시스템 관리자",
                "email": "admin@company.com",
                "role": UserRole.ADMIN1.value
            },
            {
                "username": "manager", 
                "password": "manager123",
                "full_name": "영업 팀장",
                "email": "manager@company.com", 
                "role": UserRole.ADMIN2.value
            },
            {
                "username": "sales1",
                "password": "sales123", 
                "full_name": "영업팀원1",
                "email": "sales1@company.com",
                "role": UserRole.SALES.value,
                "team": "A팀"
            },
            {
                "username": "sales2",
                "password": "sales123",
                "full_name": "영업팀원2", 
                "email": "sales2@company.com",
                "role": UserRole.SALES.value,
                "team": "A팀"
            },
            {
                "username": "sales3",
                "password": "sales123",
                "full_name": "영업팀원3",
                "email": "sales3@company.com", 
                "role": UserRole.SALES.value,
                "team": "B팀"
            },
            {
                "username": "dev",
                "password": "dev123",
                "full_name": "개발자",
                "email": "dev@company.com",
                "role": UserRole.DEVELOPER.value
            }
        ]
        
        created_count = 0
        for user_data in default_users:
            try:
                user_id = self.db.create_user(user_data)
                print(f"✅ 사용자 생성: {user_data['username']} (ID: {user_id})")
                created_count += 1
            except Exception as e:
                if "UNIQUE" in str(e):
                    print(f"⚠️  사용자 이미 존재: {user_data['username']}")
                else:
                    print(f"❌ 사용자 생성 실패: {user_data['username']} - {e}")
        
        print(f"✅ 기본 사용자 계정 생성 완료: {created_count}개")
        return created_count
    
    def transform_church_data(self, church: Dict[str, Any]) -> Dict[str, Any]:
        """교회 JSON 데이터를 Organizations 테이블 형식으로 변환"""
        
        # 크롤링 관련 복잡한 데이터는 JSON으로 저장
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
    
    def is_duplicate(self, org_data: Dict[str, Any]) -> bool:
        """중복 데이터 체크"""
        try:
            with self.db.get_connection() as conn:
                # 이름이 정확히 같은 경우
                existing = conn.execute('''
                SELECT COUNT(*) FROM organizations 
                WHERE name = ? AND is_active = 1
                ''', (org_data['name'],)).fetchone()[0]
                
                return existing > 0
                
        except Exception as e:
            print(f"⚠️  중복 체크 실패: {e}")
            return False
    
    def migrate_churches(self, churches: List[Dict[str, Any]], 
                        batch_size: int = 100) -> bool:
        """교회 데이터를 배치로 마이그레이션"""
        
        print(f"\n🚀 교회 데이터 마이그레이션 시작...")
        print(f"📊 총 처리할 교회 수: {len(churches)}")
        print(f"📦 배치 크기: {batch_size}")
        
        total_churches = len(churches)
        
        for i in range(0, total_churches, batch_size):
            batch = churches[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_churches + batch_size - 1) // batch_size
            
            print(f"\n📦 배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개)...")
            
            batch_success = 0
            batch_failed = 0
            batch_duplicates = 0
            
            for church in batch:
                self.stats["total_processed"] += 1
                
                try:
                    # 데이터 변환
                    org_data = self.transform_church_data(church)
                    
                    # 필수 데이터 검증
                    if not org_data['name']:
                        self.stats["failed"] += 1
                        batch_failed += 1
                        self.stats["errors"].append(f"교회명 없음: {church}")
                        continue
                    
                    # 중복 체크
                    if self.is_duplicate(org_data):
                        self.stats["duplicates_skipped"] += 1
                        batch_duplicates += 1
                        continue
                    
                    # 데이터베이스에 삽입
                    org_id = self.db.create_organization(org_data)
                    
                    if org_id:
                        self.stats["successfully_migrated"] += 1
                        batch_success += 1
                    else:
                        self.stats["failed"] += 1
                        batch_failed += 1
                        
                except Exception as e:
                    self.stats["failed"] += 1
                    batch_failed += 1
                    error_msg = f"교회 '{church.get('name', 'Unknown')}' 마이그레이션 실패: {e}"
                    self.stats["errors"].append(error_msg)
                    print(f"❌ {error_msg}")
            
            # 배치 결과 출력
            print(f"✅ 배치 {batch_num} 완료: 성공 {batch_success}, 실패 {batch_failed}, 중복 {batch_duplicates}")
            
            # 진행률 표시
            progress = (self.stats["total_processed"] / total_churches) * 100
            print(f"📈 전체 진행률: {progress:.1f}% ({self.stats['total_processed']}/{total_churches})")
        
        return self.stats["successfully_migrated"] > 0
    
    def print_migration_summary(self):
        """마이그레이션 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 마이그레이션 완료 요약")
        print("="*60)
        print(f"📈 총 처리된 교회: {self.stats['total_processed']:,}개")
        print(f"✅ 성공적으로 마이그레이션: {self.stats['successfully_migrated']:,}개")
        print(f"🔄 중복으로 건너뜀: {self.stats['duplicates_skipped']:,}개")
        print(f"❌ 실패: {self.stats['failed']:,}개")
        
        success_rate = (self.stats['successfully_migrated'] / self.stats['total_processed']) * 100 if self.stats['total_processed'] > 0 else 0
        print(f"📊 성공률: {success_rate:.1f}%")
        
        if self.stats['errors']:
            print(f"\n❌ 오류 목록 (최근 10개):")
            for error in self.stats['errors'][-10:]:
                print(f"  - {error}")
        
        print("="*60)
    
    def verify_migration(self):
        """마이그레이션 결과 검증"""
        print("\n🔍 마이그레이션 결과 검증 중...")
        
        try:
            dashboard_stats = self.db.get_dashboard_stats()
            
            print(f"✅ 데이터베이스 총 기관 수: {dashboard_stats['total_organizations']:,}개")
            print(f"📊 상태별 분포:")
            for status, count in dashboard_stats['status_counts'].items():
                print(f"  - {status}: {count:,}개")
            
            return True
            
        except Exception as e:
            print(f"❌ 검증 실패: {e}")
            return False

def main():
    """메인 마이그레이션 실행"""
    print("🚀 Church CRM 데이터베이스 마이그레이션 시작")
    print("="*60)
    
    migrator = DataMigrator()
    
    # 1. 기본 사용자 생성
    migrator.create_default_users()
    
    # 2. JSON 파일 경로 설정
    json_file_path = "data/json/merged_church_data_20250618_174032.json"
    
    # 루트 디렉토리에서 실행할 경우를 대비한 경로 확인
    if not os.path.exists(json_file_path):
        # migration.py 위치 기준 상대 경로
        json_file_path = "../data/json/merged_church_data_20250618_174032.json"
    
    if not os.path.exists(json_file_path):
        print(f"❌ JSON 파일을 찾을 수 없습니다.")
        print(f"다음 경로들을 확인해주세요:")
        print(f"  - data/json/merged_church_data_20250618_174032.json")
        print(f"  - ../data/json/merged_church_data_20250618_174032.json")
        return False
    
    # 3. JSON 데이터 로드
    churches = migrator.load_json_data(json_file_path)
    if not churches:
        print("❌ JSON 데이터 로드 실패")
        return False
    
    # 4. 마이그레이션 실행
    print(f"\n⚠️  마이그레이션을 시작하시겠습니까? (y/N): ", end="")
    response = input().strip().lower()
    
    if response not in ['y', 'yes']:
        print("❌ 마이그레이션이 취소되었습니다.")
        return False
    
    start_time = datetime.now()
    
    success = migrator.migrate_churches(churches, batch_size=100)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 5. 결과 요약
    migrator.print_migration_summary()
    print(f"⏱️  소요 시간: {duration}")
    
    # 6. 검증
    migrator.verify_migration()
    
    if success:
        print("\n🎉 마이그레이션이 성공적으로 완료되었습니다!")
        print(f"📊 데이터베이스 파일: churches_crm.db")
        print(f"🌐 웹 애플리케이션에서 확인해보세요!")
        return True
    else:
        print("\n❌ 마이그레이션 중 오류가 발생했습니다.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)
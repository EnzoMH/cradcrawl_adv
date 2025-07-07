# json_to_postgres.py (로컬에서 생성)
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

class JSONToPostgresMigrator:
    def __init__(self, json_file_path: str, postgres_url: str):
        self.json_file_path = json_file_path
        self.postgres_url = postgres_url
        
    def load_json_data(self):
        """JSON 파일 로드"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON 파일 로드 완료: {len(data):,}개 레코드")
            return data
        except Exception as e:
            print(f"❌ JSON 파일 로드 실패: {e}")
            return []
    
    def create_table(self, cursor):
        """PostgreSQL 테이블 생성"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            type VARCHAR(100) DEFAULT 'CHURCH',
            category VARCHAR(50) DEFAULT '종교시설',
            homepage TEXT,
            phone VARCHAR(100),
            fax VARCHAR(100),
            email VARCHAR(100),
            mobile VARCHAR(100),
            postal_code VARCHAR(10),
            address TEXT,
            organization_size VARCHAR(100),
            founding_year INTEGER,
            member_count INTEGER,
            denomination VARCHAR(100),
            contact_status VARCHAR(100) DEFAULT 'NEW',
            priority VARCHAR(50) DEFAULT 'MEDIUM',
            assigned_to VARCHAR(50),
            lead_source VARCHAR(50) DEFAULT 'DATABASE',
            estimated_value INTEGER DEFAULT 0,
            sales_notes TEXT,
            internal_notes TEXT,
            last_contact_date DATE,
            next_follow_up_date DATE,
            crawling_data JSONB,
            ai_crawled BOOLEAN DEFAULT FALSE,
            last_crawled_at TIMESTAMP,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        
        CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);
        CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(type);
        CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON organizations(is_active);
        """
        
        cursor.execute(create_table_sql)
        print("✅ 테이블 생성 완료")
    
    def safe_get_value(self, row_dict, key: str, default=None):
        """안전하게 값 가져오기"""
        value = row_dict.get(key, default)
        if value == '' or value is None:
            return default
        return value
    
    def migrate_data(self, batch_size: int = 1000):
        """JSON 데이터를 PostgreSQL로 마이그레이션"""
        print("🚀 JSON → PostgreSQL 마이그레이션 시작...")
        
        json_data = self.load_json_data()
        if not json_data:
            return
        
        try:
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            
            # 테이블 생성
            self.create_table(cursor)
            
            # 기존 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM organizations")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"⚠️ 기존 데이터 {existing_count:,}개 발견")
                response = input("기존 데이터를 삭제하고 새로 생성하시겠습니까? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    cursor.execute("TRUNCATE TABLE organizations RESTART IDENTITY")
                    print("🧹 기존 데이터 삭제 완료")
                else:
                    print("❌ 마이그레이션 취소")
                    return
            
            # 데이터 마이그레이션
            migrated_count = 0
            batch_data = []
            
            for i, row in enumerate(json_data):
                try:
                    # 데이터 매핑
                    insert_data = (
                        self.safe_get_value(row, 'name', ''),
                        self.safe_get_value(row, 'type', 'CHURCH'),
                        self.safe_get_value(row, 'category', '종교시설'),
                        self.safe_get_value(row, 'homepage'),
                        self.safe_get_value(row, 'phone'),
                        self.safe_get_value(row, 'fax'),
                        self.safe_get_value(row, 'email'),
                        self.safe_get_value(row, 'mobile'),
                        self.safe_get_value(row, 'postal_code'),
                        self.safe_get_value(row, 'address'),
                        self.safe_get_value(row, 'organization_size'),
                        self.safe_get_value(row, 'founding_year'),
                        self.safe_get_value(row, 'member_count'),
                        self.safe_get_value(row, 'denomination'),
                        self.safe_get_value(row, 'contact_status', 'NEW'),
                        self.safe_get_value(row, 'priority', 'MEDIUM'),
                        self.safe_get_value(row, 'assigned_to'),
                        self.safe_get_value(row, 'lead_source', 'DATABASE'),
                        self.safe_get_value(row, 'estimated_value', 0),
                        self.safe_get_value(row, 'sales_notes'),
                        self.safe_get_value(row, 'internal_notes'),
                        self.safe_get_value(row, 'last_contact_date'),
                        self.safe_get_value(row, 'next_follow_up_date'),
                        json.dumps(self.safe_get_value(row, 'crawling_data')) if row.get('crawling_data') else None,
                        bool(self.safe_get_value(row, 'ai_crawled', False)),
                        self.safe_get_value(row, 'last_crawled_at'),
                        self.safe_get_value(row, 'created_by'),
                        self.safe_get_value(row, 'updated_by'),
                        self.safe_get_value(row, 'created_at'),
                        self.safe_get_value(row, 'updated_at'),
                        bool(self.safe_get_value(row, 'is_active', True))
                    )
                    
                    batch_data.append(insert_data)
                    
                    # 배치 단위로 삽입
                    if len(batch_data) >= batch_size:
                        cursor.executemany("""
                            INSERT INTO organizations (
                                name, type, category, homepage, phone, fax, email, mobile,
                                postal_code, address, organization_size, founding_year, 
                                member_count, denomination, contact_status, priority,
                                assigned_to, lead_source, estimated_value, sales_notes,
                                internal_notes, last_contact_date, next_follow_up_date,
                                crawling_data, ai_crawled, last_crawled_at, created_by,
                                updated_by, created_at, updated_at, is_active
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, batch_data)
                        
                        conn.commit()
                        migrated_count += len(batch_data)
                        batch_data = []
                        
                        # 진행 상황 출력
                        percentage = (migrated_count / len(json_data)) * 100
                        print(f"📈 진행률: {migrated_count:,}/{len(json_data):,} ({percentage:.1f}%)")
                
                except Exception as e:
                    print(f"❌ 레코드 {i} 오류: {str(e)[:100]}")
            
            # 남은 배치 처리
            if batch_data:
                cursor.executemany("""
                    INSERT INTO organizations (
                        name, type, category, homepage, phone, fax, email, mobile,
                        postal_code, address, organization_size, founding_year, 
                        member_count, denomination, contact_status, priority,
                        assigned_to, lead_source, estimated_value, sales_notes,
                        internal_notes, last_contact_date, next_follow_up_date,
                        crawling_data, ai_crawled, last_crawled_at, created_by,
                        updated_by, created_at, updated_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch_data)
                conn.commit()
                migrated_count += len(batch_data)
            
            # 최종 결과
            cursor.execute("SELECT COUNT(*) FROM organizations")
            final_count = cursor.fetchone()[0]
            
            print(f"\n🎉 마이그레이션 완료!")
            print(f"📊 최종 PostgreSQL 데이터: {final_count:,}개")
            print(f"✅ 마이그레이션된 데이터: {migrated_count:,}개")
            
        except Exception as e:
            print(f"❌ 마이그레이션 실패: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

def main():
    json_file_path = "database/organizations_backup_utf8.json"
    postgres_url = "postgresql://isgs003:Smh213417!@localhost:5432/crad_db_local"
    
    print("🔄 JSON → PostgreSQL 마이그레이션")
    print("="*50)
    
    migrator = JSONToPostgresMigrator(json_file_path, postgres_url)
    
    try:
        start_time = datetime.now()
        migrator.migrate_data(batch_size=1000)
        end_time = datetime.now()
        
        print(f"\n⏱️ 총 소요 시간: {end_time - start_time}")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
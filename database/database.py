#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 CRM 데이터베이스 모듈
"""

import psycopg2
import psycopg2.extras
import json
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

class ChurchCRMDatabase:
    """PostgreSQL 기반 CRM 데이터베이스 클래스"""
    
    def __init__(self, db_url: str = None):
        # 로컬 개발 시 DATABASE_URL_LOCAL 사용
        self.db_url = db_url or os.getenv("DATABASE_URL_LOCAL") or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL 또는 DATABASE_URL_LOCAL이 설정되지 않았습니다")
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            with self.get_connection() as conn:
                self._create_schema(conn)
                self._create_default_admin(conn)
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
            # 이미 초기화된 경우 무시
            pass
    
    @contextmanager
    def get_connection(self):
        """PostgreSQL 연결 관리"""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = None, fetch_all: bool = True) -> List[Dict[str, Any]]:
        """PostgreSQL 쿼리 실행 (딕셔너리 결과 반환)"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def execute_update(self, query: str, params: Tuple = None) -> int:
        """PostgreSQL 업데이트/삽입/삭제 쿼리 실행"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor.rowcount
    
    def _create_schema(self, conn):
        """PostgreSQL 스키마 생성"""
        cursor = conn.cursor()
        
        # 기존 테이블 확인 후 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                role VARCHAR(20) NOT NULL DEFAULT 'SALES',
                team VARCHAR(50),
                is_active BOOLEAN DEFAULT true,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                type VARCHAR(20) DEFAULT 'CHURCH',
                category VARCHAR(50) DEFAULT '종교시설',
                homepage TEXT,
                phone VARCHAR(20),
                fax VARCHAR(20),
                email VARCHAR(100),
                mobile VARCHAR(20),
                postal_code VARCHAR(10),
                address TEXT,
                organization_size VARCHAR(20),
                founding_year INTEGER,
                member_count INTEGER,
                denomination VARCHAR(100),
                contact_status VARCHAR(20) DEFAULT 'NEW',
                priority VARCHAR(10) DEFAULT 'MEDIUM',
                assigned_to VARCHAR(50),
                lead_source VARCHAR(50) DEFAULT 'DATABASE',
                estimated_value INTEGER DEFAULT 0,
                sales_notes TEXT,
                internal_notes TEXT,
                last_contact_date DATE,
                next_follow_up_date DATE,
                crawling_data JSONB,
                ai_crawled BOOLEAN DEFAULT false,
                last_crawled_at TIMESTAMP,
                created_by VARCHAR(50),
                updated_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_activities (
                id SERIAL PRIMARY KEY,
                organization_id INTEGER REFERENCES organizations(id),
                activity_type VARCHAR(20) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                description TEXT,
                contact_person VARCHAR(100),
                contact_method VARCHAR(50),
                result TEXT,
                next_action TEXT,
                created_by VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_date TIMESTAMP,
                completed_at TIMESTAMP,
                is_completed BOOLEAN DEFAULT false
            );
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_activities_org_id ON contact_activities(organization_id);")
        
        conn.commit()
    
    def _create_default_admin(self, conn):
        """기본 관리자 계정 생성"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = self._hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES ('admin', %s, '시스템 관리자', 'ADMIN1')
            """, (password_hash,))
            conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 통계 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 기본 통계
            cursor.execute("SELECT COUNT(*) as total FROM organizations WHERE is_active = true")
            total_orgs = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_active = true")
            total_users = cursor.fetchone()['total']
            
            # 상태별 통계
            cursor.execute("""
                SELECT contact_status, COUNT(*) as count 
                FROM organizations 
                WHERE is_active = true 
                GROUP BY contact_status
            """)
            status_counts = {row['contact_status']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_organizations': total_orgs,
                'total_users': total_users,
                'status_counts': status_counts,
                'follow_ups_this_week': 0,
                'recent_activities': 0
            }

def get_database() -> ChurchCRMDatabase:
    """데이터베이스 인스턴스 반환"""
    return ChurchCRMDatabase()

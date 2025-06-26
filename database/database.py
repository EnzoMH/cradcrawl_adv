#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 기반 CRM 데이터베이스 모듈
교회/기관 정보 관리 + 영업 활동 추적 + 사용자 인증
"""

import sqlite3
import threading
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple

# 모델 import
from .models import (
    UserRole, OrganizationType, ContactStatus, Priority, ActivityType, CrawlingStatus,
    User, Organization, ContactActivity, CrawlingJob, DashboardStats,
    validate_organization_data, validate_user_data
)

class ChurchCRMDatabase:
    """SQLite 기반 CRM 데이터베이스 클래스"""
    
    def __init__(self, db_path: str = "database/churches_crm.db"):
        self.db_path = db_path
        self.local = threading.local()
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화 및 최적화 설정"""
        with self.get_connection() as conn:
            # SQLite 성능 최적화 설정
            conn.execute("PRAGMA journal_mode=WAL")        # 웹 환경 동시 접근
            conn.execute("PRAGMA synchronous=NORMAL")      # 속도와 안정성 균형
            conn.execute("PRAGMA cache_size=10000")        # 캐시 크기 (10MB)
            conn.execute("PRAGMA temp_store=MEMORY")       # 임시 데이터 메모리 저장
            conn.execute("PRAGMA mmap_size=268435456")     # 메모리 맵 (256MB)
            conn.execute("PRAGMA foreign_keys=ON")         # 외래키 제약 활성화
            
            # 스키마 생성
            self._create_schema(conn)
            
            # 기본 관리자 계정 생성
            self._create_default_admin(conn)
    
    @contextmanager
    def get_connection(self):
        """스레드 안전한 데이터베이스 연결 관리"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            self.local.connection.row_factory = sqlite3.Row
        
        try:
            yield self.local.connection
        except Exception:
            self.local.connection.rollback()
            raise
    
    def _create_schema(self, conn):
        """데이터베이스 스키마 생성"""
        
        # 1. 사용자 인증 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL,
            team TEXT,                        -- 영업팀 구분
            is_active BOOLEAN DEFAULT 1,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. 기관 정보 메인 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'CHURCH',       -- CHURCH/ACADEMY/PUBLIC/SCHOOL
            category TEXT DEFAULT '종교시설',
            
            -- 기본 연락처 정보
            homepage TEXT,
            phone TEXT,
            fax TEXT,
            email TEXT,
            mobile TEXT,
            postal_code TEXT,
            address TEXT,
            
            -- 상세 정보
            organization_size TEXT,           -- 대형/중형/소형
            founding_year INTEGER,
            member_count INTEGER,
            denomination TEXT,                -- 교단(교회), 계열(학원)
            
            -- CRM 영업 정보
            contact_status TEXT DEFAULT 'NEW',
            priority TEXT DEFAULT 'MEDIUM',
            assigned_to TEXT,                 -- 담당 영업 (username)
            lead_source TEXT DEFAULT 'DATABASE',
            estimated_value INTEGER DEFAULT 0,
            
            -- 영업 노트
            sales_notes TEXT,
            internal_notes TEXT,              -- 내부 메모
            last_contact_date DATE,
            next_follow_up_date DATE,
            
            -- 크롤링 메타데이터 (JSON)
            crawling_data TEXT,               -- homepage_parsed, ai_summary 등
            
            -- 시스템 필드
            created_by TEXT,
            updated_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # 3. 영업 활동 로그 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS contact_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,      -- CALL/EMAIL/MEETING/NOTE/VISIT
            subject TEXT NOT NULL,
            description TEXT,
            contact_person TEXT,              -- 연락한 담당자 이름
            contact_method TEXT,              -- 전화/이메일/방문/온라인
            result TEXT,                      -- 결과 요약
            next_action TEXT,                 -- 다음 액션 계획
            created_by TEXT NOT NULL,         -- 작성자 username
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            scheduled_date DATETIME,          -- 예정 활동 시간
            completed_at DATETIME,            -- 완료 시간
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        ''')
        
        # 4. 사용자 세션 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # 5. 일정 관리 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            organization_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            schedule_type TEXT DEFAULT 'MEETING',  -- MEETING/CALL/VISIT/REMINDER
            start_datetime DATETIME NOT NULL,
            end_datetime DATETIME,
            is_all_day BOOLEAN DEFAULT 0,
            reminder_minutes INTEGER DEFAULT 15,
            status TEXT DEFAULT 'SCHEDULED',       -- SCHEDULED/COMPLETED/CANCELLED
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        ''')
        
        # 6. 첨부파일 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            activity_id INTEGER,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            uploaded_by TEXT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id),
            FOREIGN KEY (activity_id) REFERENCES contact_activities(id)
        )
        ''')
        
                # 7. 크롤링 작업 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS crawling_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            status TEXT DEFAULT 'RUNNING',        -- RUNNING/COMPLETED/STOPPED/ERROR
            total_count INTEGER DEFAULT 0,
            processed_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            started_by TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            config_data TEXT,                     -- JSON: 크롤링 설정
            error_message TEXT
        )
        ''')

        # 8. 크롤링 결과 테이블  
        conn.execute('''
        CREATE TABLE IF NOT EXISTS crawling_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            organization_name TEXT NOT NULL,
            category TEXT,
            homepage_url TEXT,
            status TEXT DEFAULT 'PROCESSING',     -- PROCESSING/COMPLETED/FAILED
            current_step TEXT,
            processing_time REAL,
            extraction_method TEXT,
            
            -- 크롤링된 연락처 정보
            phone TEXT,
            fax TEXT,
            email TEXT,
            mobile TEXT,
            postal_code TEXT,
            address TEXT,
            
            -- 상세 크롤링 결과 (JSON)
            crawling_details TEXT,                -- homepage_parsed, ai_summary 등
            
            -- 오류 정보
            error_message TEXT,
            
            -- 시스템 필드
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (job_id) REFERENCES crawling_jobs(id)
        )
        ''')
        
        # 인덱스 생성
        indexes = [
            # 조직/기관
            "CREATE INDEX IF NOT EXISTS idx_org_name ON organizations(name)",
            "CREATE INDEX IF NOT EXISTS idx_org_category ON organizations(category)",
            "CREATE INDEX IF NOT EXISTS idx_org_status ON organizations(contact_status)",
            "CREATE INDEX IF NOT EXISTS idx_org_assigned ON organizations(assigned_to)",
            "CREATE INDEX IF NOT EXISTS idx_org_created ON organizations(created_at)",
            
            # 사용자
            "CREATE INDEX IF NOT EXISTS idx_user_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_role ON users(role)",
            
            # 세션
            "CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_session_expires ON user_sessions(expires_at)",
            
            # 활동 로그
            "CREATE INDEX IF NOT EXISTS idx_activity_org ON contact_activities(organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_date ON contact_activities(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON contact_activities(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_activity_type ON contact_activities(activity_type)",
            
            # 일정 관리
            "CREATE INDEX IF NOT EXISTS idx_schedule_user ON schedules(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedules(start_datetime)",
            "CREATE INDEX IF NOT EXISTS idx_schedule_org ON schedules(organization_id)",
            
            # 🔧 크롤링 관련 인덱스 (주석을 리스트 밖으로 이동)
            "CREATE INDEX IF NOT EXISTS idx_crawling_job_status ON crawling_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_crawling_results_job ON crawling_results(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_crawling_results_status ON crawling_results(status)",
            "CREATE INDEX IF NOT EXISTS idx_crawling_results_name ON crawling_results(organization_name)"
        ]
        
        for index in indexes:
            conn.execute(index)
        
        conn.commit()
        print("✅ 데이터베이스 스키마 생성 완료")
    
    def _create_default_admin(self, conn):
        """기본 관리자 계정 생성"""
        try:
            # 관리자 계정이 이미 있는지 확인
            existing = conn.execute(
                "SELECT COUNT(*) FROM users WHERE username = ?", 
                ("admin",)
            ).fetchone()[0]
            
            if existing == 0:
                admin_data = {
                    "username": "admin",
                    "password": "admin123",  # 첫 로그인 후 변경 필요
                    "full_name": "시스템 관리자",
                    "email": "admin@company.com",
                    "role": UserRole.ADMIN1.value
                }
                
                self.create_user(admin_data, conn)
                print("✅ 기본 관리자 계정 생성: admin/admin123")
                print("⚠️  보안을 위해 첫 로그인 후 비밀번호를 변경하세요!")
                
        except Exception as e:
            print(f"❌ 기본 관리자 계정 생성 실패: {e}")
    
    # ==================== 사용자 인증 관련 메서드 ====================
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, hash_str: str) -> bool:
        """비밀번호 검증"""
        try:
            salt, password_hash = hash_str.split(':')
            new_hash = hashlib.pbkdf2_hmac('sha256',
                                         password.encode('utf-8'),
                                         salt.encode('utf-8'),
                                         100000)
            return password_hash == new_hash.hex()
        except:
            return False
    
    def create_user(self, user_data: Dict[str, Any], conn=None) -> int:
        """사용자 생성"""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection().__enter__()
        
        try:
            password_hash = self._hash_password(user_data['password'])
            
            cursor = conn.execute('''
            INSERT INTO users (username, password_hash, full_name, email, phone, role, team)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                password_hash,
                user_data['full_name'],
                user_data.get('email', ''),
                user_data.get('phone', ''),
                user_data['role'],
                user_data.get('team', '')
            ))
            
            conn.commit()
            return cursor.lastrowid
            
        finally:
            if should_close:
                conn.__exit__(None, None, None)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증"""
        with self.get_connection() as conn:
            user = conn.execute('''
            SELECT id, username, password_hash, full_name, email, phone, role, team, is_active
            FROM users WHERE username = ? AND is_active = 1
            ''', (username,)).fetchone()
            
            if user and self._verify_password(password, user['password_hash']):
                # 마지막 로그인 시간 업데이트
                conn.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user['id'],))
                conn.commit()
                
                return dict(user)
            
            return None
    
    def create_session(self, user_id: int, ip_address: str = "", user_agent: str = "") -> str:
        """사용자 세션 생성"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)  # 7일 후 만료
        
        with self.get_connection() as conn:
            conn.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))
            conn.commit()
        
        return session_token
    
    def get_user_by_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """세션으로 사용자 정보 조회"""
        with self.get_connection() as conn:
            result = conn.execute('''
            SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role, u.team
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = 1
            ''', (session_token,)).fetchone()
            
            return dict(result) if result else None
    
    def delete_session(self, session_token: str) -> bool:
        """세션 삭제 (로그아웃)"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
            DELETE FROM user_sessions WHERE session_token = ?
            ''', (session_token,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== 기관 관리 CRUD 메서드 ====================
    
    def create_organization(self, org_data: Dict[str, Any]) -> int:
        """기관 정보 생성"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
            INSERT INTO organizations (
                name, type, category, homepage, phone, fax, email, mobile,
                postal_code, address, organization_size, founding_year, member_count,
                denomination, contact_status, priority, assigned_to, estimated_value,
                sales_notes, internal_notes, crawling_data, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_data.get('name', ''),
                org_data.get('type', 'CHURCH'),
                org_data.get('category', '종교시설'),
                org_data.get('homepage', ''),
                org_data.get('phone', ''),
                org_data.get('fax', ''),
                org_data.get('email', ''),
                org_data.get('mobile', ''),
                org_data.get('postal_code', ''),
                org_data.get('address', ''),
                org_data.get('organization_size', ''),
                org_data.get('founding_year', None),
                org_data.get('member_count', None),
                org_data.get('denomination', ''),
                org_data.get('contact_status', 'NEW'),
                org_data.get('priority', 'MEDIUM'),
                org_data.get('assigned_to', ''),
                org_data.get('estimated_value', 0),
                org_data.get('sales_notes', ''),
                org_data.get('internal_notes', ''),
                json.dumps(org_data.get('crawling_data', {})),
                org_data.get('created_by', 'SYSTEM')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_organizations_paginated(self, page: int = 1, per_page: int = 20, 
                                   search: str = None, filters: Dict[str, Any] = None,
                                   user_role: str = None, username: str = None) -> Dict[str, Any]:
        """페이징된 기관 목록 조회 (권한 기반 필터링)"""
        with self.get_connection() as conn:
            offset = (page - 1) * per_page
            
            # 기본 WHERE 조건
            where_conditions = ["is_active = 1"]
            params = []
            
            # 권한 기반 필터링
            if user_role == UserRole.SALES.value:
                where_conditions.append("assigned_to = ?")
                params.append(username)
            
            # 검색 조건
            if search:
                where_conditions.append("(name LIKE ? OR address LIKE ? OR phone LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            # 추가 필터
            if filters:
                if filters.get('type'):
                    where_conditions.append("type = ?")
                    params.append(filters['type'])
                if filters.get('contact_status'):
                    where_conditions.append("contact_status = ?")
                    params.append(filters['contact_status'])
                if filters.get('assigned_to'):
                    where_conditions.append("assigned_to = ?")
                    params.append(filters['assigned_to'])
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 총 개수 조회
            count_query = f"SELECT COUNT(*) FROM organizations {where_clause}"
            total_count = conn.execute(count_query, params).fetchone()[0]
            
            # 데이터 조회
            data_query = f'''
            SELECT id, name, type, category, homepage, phone, fax, email,
                   address, contact_status, priority, assigned_to, last_contact_date,
                   next_follow_up_date, updated_at
            FROM organizations {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            '''
            
            organizations = conn.execute(data_query, params + [per_page, offset]).fetchall()
            
            return {
                "organizations": [dict(org) for org in organizations],
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total_count + per_page - 1) // per_page
                }
            }
    
    def get_organization_detail(self, org_id: int, user_role: str = None, 
                               username: str = None) -> Optional[Dict[str, Any]]:
        """기관 상세 정보 조회 (권한 체크 포함)"""
        with self.get_connection() as conn:
            # 권한 체크
            if user_role == UserRole.SALES.value:
                org = conn.execute('''
                SELECT * FROM organizations 
                WHERE id = ? AND assigned_to = ? AND is_active = 1
                ''', (org_id, username)).fetchone()
            else:
                org = conn.execute('''
                SELECT * FROM organizations 
                WHERE id = ? AND is_active = 1
                ''', (org_id,)).fetchone()
            
            if not org:
                return None
            
            # 최근 활동 기록 조회
            activities = conn.execute('''
            SELECT * FROM contact_activities 
            WHERE organization_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
            ''', (org_id,)).fetchall()
            
            # 다가오는 일정 조회
            schedules = conn.execute('''
            SELECT * FROM schedules 
            WHERE organization_id = ? AND start_datetime > CURRENT_TIMESTAMP
            ORDER BY start_datetime ASC
            LIMIT 5
            ''', (org_id,)).fetchall()
            
            return {
                "organization": dict(org),
                "recent_activities": [dict(activity) for activity in activities],
                "upcoming_schedules": [dict(schedule) for schedule in schedules]
            }
    
    def update_organization(self, org_id: int, updates: Dict[str, Any], 
                           updated_by: str) -> bool:
        """기관 정보 수정"""
        with self.get_connection() as conn:
            # 동적 업데이트 쿼리 생성
            allowed_fields = [
                'name', 'type', 'category', 'homepage', 'phone', 'fax', 
                'email', 'mobile', 'postal_code', 'address', 'organization_size',
                'founding_year', 'member_count', 'denomination', 'contact_status',
                'priority', 'assigned_to', 'estimated_value', 'sales_notes',
                'internal_notes', 'last_contact_date', 'next_follow_up_date'
            ]
            
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.extend(["updated_by = ?", "updated_at = CURRENT_TIMESTAMP"])
            values.extend([updated_by, org_id])
            
            query = f"UPDATE organizations SET {', '.join(set_clauses)} WHERE id = ?"
            cursor = conn.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_organization(self, org_id: int) -> bool:
        """기관 정보 삭제 (소프트 삭제)"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
            UPDATE organizations SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            ''', (org_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== 영업 활동 관리 ====================
    
    def add_contact_activity(self, activity_data: Dict[str, Any]) -> int:
        """영업 활동 기록 추가"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
            INSERT INTO contact_activities (
                organization_id, activity_type, subject, description,
                contact_person, contact_method, result, next_action,
                created_by, scheduled_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_data['organization_id'],
                activity_data['activity_type'],
                activity_data['subject'],
                activity_data.get('description', ''),
                activity_data.get('contact_person', ''),
                activity_data.get('contact_method', ''),
                activity_data.get('result', ''),
                activity_data.get('next_action', ''),
                activity_data['created_by'],
                activity_data.get('scheduled_date')
            ))
            
            activity_id = cursor.lastrowid
            
            # 기관의 마지막 연락일 업데이트
            conn.execute('''
            UPDATE organizations SET 
                last_contact_date = CURRENT_DATE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (activity_data['organization_id'],))
            
            conn.commit()
            return activity_id
    
    # ==================== 대시보드 & 통계 ====================
    
    def get_dashboard_stats(self, user_role: str = None, username: str = None) -> Dict[str, Any]:
        """대시보드 통계 데이터"""
        with self.get_connection() as conn:
            stats = {}
            
            # 권한 기반 필터
            user_filter = ""
            params = []
            if user_role == UserRole.SALES.value:
                user_filter = "WHERE assigned_to = ?"
                params = [username]
            
            # 기본 통계
            stats["total_organizations"] = conn.execute(
                f"SELECT COUNT(*) FROM organizations {user_filter}", params
            ).fetchone()[0]
            
            # 사용자 수 추가 (총 활성 사용자)
            stats["total_users"] = conn.execute(
                "SELECT COUNT(*) FROM users WHERE is_active = 1"
            ).fetchone()[0]
            
            # 상태별 통계
            status_query = f'''
            SELECT contact_status, COUNT(*) as count
            FROM organizations {user_filter}
            GROUP BY contact_status
            '''
            status_stats = conn.execute(status_query, params).fetchall()
            stats["status_counts"] = {row[0]: row[1] for row in status_stats}
            
            # 이번 주 후속 조치 필요
            follow_up_filter = user_filter + (" AND" if user_filter else "WHERE")
            stats["follow_ups_this_week"] = conn.execute(f'''
            SELECT COUNT(*) FROM organizations 
            {follow_up_filter} next_follow_up_date BETWEEN date('now') AND date('now', '+7 days')
            ''', params).fetchone()[0]
            
            # 최근 활동 (권한 기반)
            if user_role == UserRole.SALES.value:
                recent_activities = conn.execute('''
                SELECT ca.*, o.name as organization_name
                FROM contact_activities ca
                JOIN organizations o ON ca.organization_id = o.id
                WHERE o.assigned_to = ?
                ORDER BY ca.created_at DESC
                LIMIT 5
                ''', [username]).fetchall()
            else:
                recent_activities = conn.execute('''
                SELECT ca.*, o.name as organization_name
                FROM contact_activities ca
                JOIN organizations o ON ca.organization_id = o.id
                ORDER BY ca.created_at DESC
                LIMIT 5
                ''').fetchall()
            
            stats["recent_activities"] = len(recent_activities)  # 숫자로 변경
            
            return stats
        
    def create_crawling_job(self, job_data: Dict[str, Any]) -> int:
        """크롤링 작업 생성"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
            INSERT INTO crawling_jobs (job_name, total_count, started_by, config_data)
            VALUES (?, ?, ?, ?)
            ''', (
                job_data['job_name'],
                job_data['total_count'],
                job_data['started_by'],
                json.dumps(job_data.get('config', {}))
            ))
            conn.commit()
            return cursor.lastrowid

    def update_crawling_job(self, job_id: int, updates: Dict[str, Any]) -> bool:
        """크롤링 작업 상태 업데이트"""
        with self.get_connection() as conn:
            set_clauses = []
            values = []
            
            allowed_fields = ['status', 'processed_count', 'failed_count', 'completed_at', 'error_message']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            values.append(job_id)
            query = f"UPDATE crawling_jobs SET {', '.join(set_clauses)} WHERE id = ?"
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0

    def add_crawling_result(self, result_data: Dict[str, Any]) -> int:
        """크롤링 결과 추가/업데이트"""
        with self.get_connection() as conn:
            # 기존 결과가 있는지 확인 (같은 job_id + organization_name)
            existing = conn.execute('''
            SELECT id FROM crawling_results 
            WHERE job_id = ? AND organization_name = ?
            ''', (result_data['job_id'], result_data['organization_name'])).fetchone()
            
            if existing:
                # 업데이트
                cursor = conn.execute('''
                UPDATE crawling_results SET
                    status = ?, current_step = ?, processing_time = ?,
                    phone = ?, fax = ?, email = ?, mobile = ?,
                    postal_code = ?, address = ?, crawling_details = ?,
                    error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    result_data.get('status', 'PROCESSING'),
                    result_data.get('current_step', ''),
                    result_data.get('processing_time', 0),
                    result_data.get('phone', ''),
                    result_data.get('fax', ''),
                    result_data.get('email', ''),
                    result_data.get('mobile', ''),
                    result_data.get('postal_code', ''),
                    result_data.get('address', ''),
                    json.dumps(result_data.get('crawling_details', {})),
                    result_data.get('error_message', ''),
                    existing['id']
                ))
                return existing['id']
            else:
                # 새로 추가
                cursor = conn.execute('''
                INSERT INTO crawling_results (
                    job_id, organization_name, category, homepage_url, status,
                    current_step, processing_time, extraction_method, phone, fax,
                    email, mobile, postal_code, address, crawling_details, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result_data['job_id'],
                    result_data['organization_name'],
                    result_data.get('category', ''),
                    result_data.get('homepage_url', ''),
                    result_data.get('status', 'PROCESSING'),
                    result_data.get('current_step', ''),
                    result_data.get('processing_time', 0),
                    result_data.get('extraction_method', ''),
                    result_data.get('phone', ''),
                    result_data.get('fax', ''),
                    result_data.get('email', ''),
                    result_data.get('mobile', ''),
                    result_data.get('postal_code', ''),
                    result_data.get('address', ''),
                    json.dumps(result_data.get('crawling_details', {})),
                    result_data.get('error_message', '')
                ))
            
            conn.commit()
            return cursor.lastrowid

    def get_crawling_progress(self, job_id: int) -> Dict[str, Any]:
        """크롤링 진행 상황 조회"""
        with self.get_connection() as conn:
            # 작업 정보
            job = conn.execute('''
            SELECT * FROM crawling_jobs WHERE id = ?
            ''', (job_id,)).fetchone()
            
            if not job:
                return {"error": "작업을 찾을 수 없습니다."}
            
            # 최신 결과
            latest_result = conn.execute('''
            SELECT * FROM crawling_results 
            WHERE job_id = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
            ''', (job_id,)).fetchone()
            
            return {
                "job_id": job['id'],
                "status": job['status'],
                "total_count": job['total_count'],
                "processed_count": job['processed_count'],
                "failed_count": job['failed_count'],
                "percentage": (job['processed_count'] / job['total_count']) * 100 if job['total_count'] > 0 else 0,
                "current_organization": latest_result['organization_name'] if latest_result else "",
                "latest_result": dict(latest_result) if latest_result else None
            }

    def get_crawling_results(self, job_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """크롤링 결과 목록 조회"""
        with self.get_connection() as conn:
            results = conn.execute('''
            SELECT * FROM crawling_results 
            WHERE job_id = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
            ''', (job_id, limit)).fetchall()
            
            return [dict(result) for result in results]

    def get_latest_crawling_job(self) -> Optional[Dict[str, Any]]:
        """최신 크롤링 작업 조회"""
        with self.get_connection() as conn:
            job = conn.execute('''
            SELECT * FROM crawling_jobs 
            ORDER BY started_at DESC 
            LIMIT 1
            ''').fetchone()
            
            return dict(job) if job else None

# 전역 데이터베이스 인스턴스
_db_instance = None

def get_database() -> ChurchCRMDatabase:
    """싱글톤 데이터베이스 인스턴스 반환"""
    global _db_instance
    if _db_instance is None:
        _db_instance = ChurchCRMDatabase()
    return _db_instance

if __name__ == "__main__":
    # 테스트 실행
    print("🚀 CRM 데이터베이스 초기화 중...")
    db = ChurchCRMDatabase()
    print("✅ 데이터베이스 초기화 완료!")
    
    # 테스트 사용자 생성
    test_users = [
        {"username": "manager", "password": "manager123", "full_name": "팀장", 
         "email": "manager@company.com", "role": UserRole.ADMIN2.value},
        {"username": "sales1", "password": "sales123", "full_name": "영업팀원1", 
         "email": "sales1@company.com", "role": UserRole.SALES.value, "team": "A팀"},
        {"username": "dev", "password": "dev123", "full_name": "개발자", 
         "email": "dev@company.com", "role": UserRole.DEVELOPER.value}
    ]
    
    for user in test_users:
        try:
            db.create_user(user)
            print(f"✅ 사용자 생성: {user['username']}")
        except Exception as e:
            print(f"⚠️  사용자 이미 존재: {user['username']}")
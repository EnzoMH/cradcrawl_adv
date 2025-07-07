#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기관 관리 서비스 - PostgreSQL 완전 호환
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import psycopg2.extras

from database.database import get_database
from utils.logger_utils import LoggerUtils

@dataclass
class OrganizationSearchFilter:
    """기관 검색 필터"""
    search_term: Optional[str] = None
    organization_type: Optional[str] = None
    contact_status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    has_missing_contacts: bool = False
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class OrganizationService:
    """기관 관리 서비스"""
    
    def __init__(self):
        """초기화"""
        try:
            self.db = get_database()
            self.logger = LoggerUtils.setup_logger(name="organization_service", file_logging=False)
            
            # DB 연결 테스트
            test_stats = self.db.get_dashboard_stats()
            self.logger.info(f"🏢 기관 관리 서비스 초기화 완료 - 총 기관 수: {test_stats.get('total_organizations', 0)}")
            
        except Exception as e:
            self.logger = LoggerUtils.setup_logger(name="organization_service", file_logging=False)
            self.logger.error(f"❌ 기관 관리 서비스 초기화 실패: {str(e)}")
            raise
    
    def get_organizations_with_missing_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """누락된 연락처 정보가 있는 기관 목록 조회"""
        try:
            query = """
            SELECT 
                id, name, type, category, homepage, phone, fax, email, address,
                contact_status, priority, assigned_to, created_at, updated_at,
                CASE 
                    WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN fax IS NULL OR fax = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN email IS NULL OR email = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN homepage IS NULL OR homepage = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN address IS NULL OR address = '' THEN 1 ELSE 0 
                END as missing_count
            FROM organizations 
            WHERE is_active = true
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            ORDER BY missing_count DESC, priority ASC, updated_at DESC
            LIMIT %s
            """
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, (limit,))
                organizations = []
                
                for row in cursor.fetchall():
                    org = dict(row)
                    
                    # 누락된 필드 목록 생성
                    missing_fields = []
                    if not org.get('phone') or str(org['phone']).strip() == '':
                        missing_fields.append('phone')
                    if not org.get('fax') or str(org['fax']).strip() == '':
                        missing_fields.append('fax')
                    if not org.get('email') or str(org['email']).strip() == '':
                        missing_fields.append('email')
                    if not org.get('homepage') or str(org['homepage']).strip() == '':
                        missing_fields.append('homepage')
                    if not org.get('address') or str(org['address']).strip() == '':
                        missing_fields.append('address')
                    
                    org['missing_fields'] = missing_fields
                    org['missing_count'] = len(missing_fields)
                    organizations.append(org)
                
                return organizations
                
        except Exception as e:
            self.logger.error(f"❌ 누락 연락처 기관 조회 실패: {str(e)}")
            return []
    
    def search_organizations(self, filters: OrganizationSearchFilter, 
                           page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """고급 기관 검색 - PostgreSQL 호환"""
        try:
            # 기본 쿼리
            base_query = """
            SELECT 
                id, name, type, category, homepage, phone, fax, email, address,
                contact_status, priority, assigned_to, lead_source,
                last_contact_date, next_follow_up_date,
                created_at, updated_at, created_by
            FROM organizations 
            WHERE is_active = true
            """
            
            conditions = []
            params = []
            
            # 검색 조건 추가 (PostgreSQL ILIKE 문법)
            if filters.search_term:
                conditions.append("(name ILIKE %s OR address ILIKE %s OR email ILIKE %s)")
                search_pattern = f"%{filters.search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if filters.organization_type:
                conditions.append("type = %s")
                params.append(filters.organization_type)
            
            if filters.contact_status:
                conditions.append("contact_status = %s")
                params.append(filters.contact_status)
            
            if filters.priority:
                conditions.append("priority = %s")
                params.append(filters.priority)
            
            if filters.assigned_to:
                conditions.append("assigned_to = %s")
                params.append(filters.assigned_to)
            
            if filters.has_missing_contacts:
                conditions.append("""(
                    phone IS NULL OR phone = '' OR
                    fax IS NULL OR fax = '' OR
                    email IS NULL OR email = '' OR
                    homepage IS NULL OR homepage = '' OR
                    address IS NULL OR address = ''
                )""")
            
            if filters.created_after:
                conditions.append("created_at >= %s")
                params.append(filters.created_after)
            
            if filters.created_before:
                conditions.append("created_at <= %s")
                params.append(filters.created_before)
            
            # 조건 결합
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            # 정렬
            base_query += " ORDER BY updated_at DESC"
            
            # 총 개수 조회
            count_query = """
            SELECT COUNT(*) as total
            FROM organizations 
            WHERE is_active = true
            """
            
            if conditions:
                count_query += " AND " + " AND ".join(conditions)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # 총 개수 조회
                cursor.execute(count_query, params)
                count_result = cursor.fetchone()
                total_count = count_result['total'] if count_result else 0
                
                # 페이징 적용
                offset = (page - 1) * per_page
                paginated_query = base_query + " LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                # 데이터 조회
                cursor.execute(paginated_query, params)
                organizations = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'organizations': organizations,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ 기관 검색 실패: {str(e)}")
            return {
                'organizations': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': 0,
                    'total_pages': 0
                }
            }
    
    def get_contact_statistics(self) -> Dict[str, Any]:
        """연락처 통계 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # 전체 기관 수
                cursor.execute("SELECT COUNT(*) as total FROM organizations WHERE is_active = true")
                total_orgs = cursor.fetchone()['total']
                
                # 필드별 완성도 통계
                stats = {}
                contact_fields = ['phone', 'fax', 'email', 'homepage', 'address']
                
                for field in contact_fields:
                    cursor.execute(f"""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN {field} IS NOT NULL AND {field} != '' THEN 1 ELSE 0 END) as filled
                        FROM organizations 
                        WHERE is_active = true
                    """)
                    
                    row = cursor.fetchone()
                    total = row['total']
                    filled = row['filled']
                    missing = total - filled
                    
                    stats[field] = {
                        "total": total,
                        "filled": filled,
                        "missing": missing,
                        "completion_rate": (filled / total * 100) if total > 0 else 0
                    }
                
                # 누락 필드 수별 기관 분포
                cursor.execute("""
                    SELECT 
                        (CASE WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 END +
                         CASE WHEN fax IS NULL OR fax = '' THEN 1 ELSE 0 END +
                         CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END +
                         CASE WHEN homepage IS NULL OR homepage = '' THEN 1 ELSE 0 END +
                         CASE WHEN address IS NULL OR address = '' THEN 1 ELSE 0 END) as missing_count,
                        COUNT(*) as org_count
                    FROM organizations 
                    WHERE is_active = true
                    GROUP BY missing_count
                    ORDER BY missing_count
                """)
                
                missing_distribution = {row['missing_count']: row['org_count'] for row in cursor.fetchall()}
                
                # 전체 완성도
                total_possible_fields = total_orgs * len(contact_fields)
                total_filled_fields = sum(stats[field]['filled'] for field in contact_fields)
                overall_completion = (total_filled_fields / total_possible_fields * 100) if total_possible_fields > 0 else 0
                
                return {
                    "total_organizations": total_orgs,
                    "field_statistics": stats,
                    "missing_distribution": missing_distribution,
                    "overall_completion_rate": overall_completion,
                    "organizations_needing_enrichment": sum(missing_distribution.get(i, 0) for i in range(1, 6)),
                    "complete_organizations": missing_distribution.get(0, 0)
                }
                
        except Exception as e:
            self.logger.error(f"❌ 연락처 통계 조회 실패: {str(e)}")
            return {}
    
    def get_enrichment_candidates_with_pagination(self, page=1, per_page=50, priority=None):
        """페이지네이션된 보강 후보 조회 - PostgreSQL 완전 호환"""
        try:
            base_query = """
            SELECT 
                id, name, type, category, homepage, phone, fax, email, address,
                contact_status, priority, assigned_to, created_at, updated_at
            FROM organizations 
            WHERE is_active = true
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            """
            
            params = []
            if priority:
                base_query += " AND priority = %s"
                params.append(priority)
            
            base_query += " ORDER BY updated_at DESC"
            
            # 총 개수 조회 쿼리
            count_query = """
            SELECT COUNT(*) as total
            FROM organizations 
            WHERE is_active = true
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            """
            
            if priority:
                count_query += " AND priority = %s"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # 총 개수 조회
                cursor.execute(count_query, params)
                count_result = cursor.fetchone()
                total_count = count_result['total'] if count_result else 0
                
                # 페이징 적용
                offset = (page - 1) * per_page
                paginated_query = base_query + " LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                cursor.execute(paginated_query, params)
                organizations = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'organizations': organizations,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ 페이지네이션 보강 후보 조회 실패: {str(e)}")
            return {
                'organizations': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': 0,
                    'total_pages': 0
                }
            }

    def get_enrichment_candidates(self, priority: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """보강 후보 조회 - PostgreSQL 호환"""
        try:
            query = """
            SELECT 
                id, name, type, category, homepage, phone, fax, email, address,
                contact_status, priority, assigned_to, created_at, updated_at,
                CASE 
                    WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN fax IS NULL OR fax = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN email IS NULL OR email = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN homepage IS NULL OR homepage = '' THEN 1 ELSE 0 
                END +
                CASE 
                    WHEN address IS NULL OR address = '' THEN 1 ELSE 0 
                END as missing_count
            FROM organizations 
            WHERE is_active = true
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            """
            
            params = []
            if priority:
                query += " AND priority = %s"
                params.append(priority)
            
            query += """
            ORDER BY 
                CASE 
                    WHEN priority = 'HIGH' THEN 1
                    WHEN priority = 'MEDIUM' THEN 2
                    ELSE 3
                END,
                missing_count DESC,
                updated_at ASC
            LIMIT %s
            """
            
            params.append(limit)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, params)
                candidates = []
                
                for row in cursor.fetchall():
                    org = dict(row)
                    
                    # 누락된 필드 상세 분석
                    missing_fields = []
                    if not org.get('phone') or str(org['phone']).strip() == '':
                        missing_fields.append('phone')
                    if not org.get('fax') or str(org['fax']).strip() == '':
                        missing_fields.append('fax')
                    if not org.get('email') or str(org['email']).strip() == '':
                        missing_fields.append('email')
                    if not org.get('homepage') or str(org['homepage']).strip() == '':
                        missing_fields.append('homepage')
                    if not org.get('address') or str(org['address']).strip() == '':
                        missing_fields.append('address')
                    
                    org['missing_fields'] = missing_fields
                    org['enrichment_priority'] = self._calculate_enrichment_priority(org)
                    candidates.append(org)
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"❌ 보강 후보 조회 실패: {str(e)}")
            return []
    
    def _calculate_enrichment_priority(self, org: Dict[str, Any]) -> str:
        """연락처 보강 우선순위 계산"""
        score = 0
        
        # 기관 우선순위
        if org.get('priority') == 'HIGH':
            score += 3
        elif org.get('priority') == 'MEDIUM':
            score += 2
        else:
            score += 1
        
        # 누락된 필드 수
        missing_count = org.get('missing_count', 0)
        score += missing_count * 0.5
        
        # 최근 업데이트 여부
        if org.get('updated_at'):
            try:
                if isinstance(org['updated_at'], str):
                    updated_date = datetime.fromisoformat(org['updated_at'].replace('Z', '+00:00'))
                else:
                    updated_date = org['updated_at']
                days_since_update = (datetime.now() - updated_date).days
                if days_since_update > 30:
                    score += 1
            except:
                pass
        
        # 점수에 따른 우선순위 반환
        if score >= 5:
            return "URGENT"
        elif score >= 3:
            return "HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"

# 편의 함수들
def get_missing_contacts_summary(limit: int = 100) -> List[Dict[str, Any]]:
    """누락된 연락처 요약 정보 조회"""
    service = OrganizationService()
    return service.get_organizations_with_missing_contacts(limit)

def search_organizations_advanced(search_term: str = None, has_missing_contacts: bool = False, 
                                priority: str = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """고급 기관 검색 편의 함수"""
    service = OrganizationService()
    filters = OrganizationSearchFilter(
        search_term=search_term,
        has_missing_contacts=has_missing_contacts,
        priority=priority
    )
    return service.search_organizations(filters, page, per_page) 
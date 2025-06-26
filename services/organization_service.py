#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기관 관리 서비스
CRM 기관 정보 CRUD 및 비즈니스 로직
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

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
        self.db = get_database()
        self.logger = LoggerUtils.setup_logger("organization_service", file_logging=False)
        self.logger.info("🏢 기관 관리 서비스 초기화 완료")
    
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
            WHERE is_active = 1
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            ORDER BY missing_count DESC, priority ASC, updated_at DESC
            LIMIT ?
            """
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query, (limit,))
                organizations = []
                
                for row in cursor.fetchall():
                    org = dict(row)
                    
                    # 누락된 필드 목록 생성
                    missing_fields = []
                    if not org['phone'] or org['phone'].strip() == '':
                        missing_fields.append('phone')
                    if not org['fax'] or org['fax'].strip() == '':
                        missing_fields.append('fax')
                    if not org['email'] or org['email'].strip() == '':
                        missing_fields.append('email')
                    if not org['homepage'] or org['homepage'].strip() == '':
                        missing_fields.append('homepage')
                    if not org['address'] or org['address'].strip() == '':
                        missing_fields.append('address')
                    
                    org['missing_fields'] = missing_fields
                    org['missing_count'] = len(missing_fields)
                    organizations.append(org)
                
                return organizations
                
        except Exception as e:
            self.logger.error(f"❌ 누락 연락처 기관 조회 실패: {e}")
            return []
    
    def search_organizations(self, filters: OrganizationSearchFilter, 
                           page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """고급 기관 검색"""
        try:
            # 기본 쿼리
            base_query = """
            SELECT 
                id, name, type, category, homepage, phone, fax, email, address,
                contact_status, priority, assigned_to, lead_source,
                last_contact_date, next_follow_up_date,
                created_at, updated_at, created_by
            FROM organizations 
            WHERE is_active = 1
            """
            
            conditions = []
            params = []
            
            # 검색 조건 추가
            if filters.search_term:
                conditions.append("(name LIKE ? OR address LIKE ? OR email LIKE ?)")
                search_pattern = f"%{filters.search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if filters.organization_type:
                conditions.append("type = ?")
                params.append(filters.organization_type)
            
            if filters.contact_status:
                conditions.append("contact_status = ?")
                params.append(filters.contact_status)
            
            if filters.priority:
                conditions.append("priority = ?")
                params.append(filters.priority)
            
            if filters.assigned_to:
                conditions.append("assigned_to = ?")
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
                conditions.append("created_at >= ?")
                params.append(filters.created_after.isoformat())
            
            if filters.created_before:
                conditions.append("created_at <= ?")
                params.append(filters.created_before.isoformat())
            
            # 조건 결합
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            # 정렬
            base_query += " ORDER BY updated_at DESC"
            
            # 페이징을 위한 총 개수 조회
            count_query = base_query.replace(
                "SELECT id, name, type, category, homepage, phone, fax, email, address, contact_status, priority, assigned_to, lead_source, last_contact_date, next_follow_up_date, created_at, updated_at, created_by",
                "SELECT COUNT(*)"
            ).replace(" ORDER BY updated_at DESC", "")
            
            with self.db.get_connection() as conn:
                # 총 개수 조회
                cursor = conn.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # 페이징 적용
                offset = (page - 1) * per_page
                paginated_query = base_query + " LIMIT ? OFFSET ?"
                params.extend([per_page, offset])
                
                # 데이터 조회
                cursor = conn.execute(paginated_query, params)
                organizations = [dict(row) for row in cursor.fetchall()]
                
                # 각 기관의 누락 필드 정보 추가
                for org in organizations:
                    missing_fields = []
                    if not org['phone'] or org['phone'].strip() == '':
                        missing_fields.append('phone')
                    if not org['fax'] or org['fax'].strip() == '':
                        missing_fields.append('fax')
                    if not org['email'] or org['email'].strip() == '':
                        missing_fields.append('email')
                    if not org['homepage'] or org['homepage'].strip() == '':
                        missing_fields.append('homepage')
                    if not org['address'] or org['address'].strip() == '':
                        missing_fields.append('address')
                    
                    org['missing_fields'] = missing_fields
                    org['has_missing_contacts'] = len(missing_fields) > 0
                
                return {
                    "organizations": organizations,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_count": total_count,
                        "total_pages": (total_count + per_page - 1) // per_page,
                        "has_next": page * per_page < total_count,
                        "has_prev": page > 1
                    },
                    "filters_applied": filters.__dict__
                }
                
        except Exception as e:
            self.logger.error(f"❌ 기관 검색 실패: {e}")
            return {
                "organizations": [],
                "pagination": {"page": 1, "per_page": per_page, "total_count": 0, "total_pages": 0},
                "error": str(e)
            }
    
    def get_organization_detail_with_enrichment_info(self, org_id: int) -> Optional[Dict[str, Any]]:
        """기관 상세 정보 + 연락처 보강 정보 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM organizations WHERE id = ? AND is_active = 1
                """, (org_id,))
                
                org = cursor.fetchone()
                if not org:
                    return None
                
                org_dict = dict(org)
                
                # 누락된 필드 분석
                missing_fields = []
                available_fields = []
                
                contact_fields = ['phone', 'fax', 'email', 'homepage', 'address']
                for field in contact_fields:
                    value = org_dict.get(field)
                    if not value or value.strip() == '':
                        missing_fields.append(field)
                    else:
                        available_fields.append(field)
                
                # 연락처 보강 이력 분석
                enrichment_history = []
                if org_dict.get('crawling_data'):
                    try:
                        crawling_data = json.loads(org_dict['crawling_data'])
                        if 'last_enrichment' in crawling_data:
                            enrichment_history.append({
                                "date": crawling_data['last_enrichment'],
                                "source": crawling_data.get('enrichment_source', 'Unknown'),
                                "found_fields": crawling_data.get('found_fields', [])
                            })
                    except:
                        pass
                
                # 연락처 활동 이력 조회
                cursor = conn.execute("""
                    SELECT activity_type, subject, created_at, created_by
                    FROM contact_activities 
                    WHERE organization_id = ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (org_id,))
                
                recent_activities = [dict(row) for row in cursor.fetchall()]
                
                # 종합 정보 반환
                org_dict.update({
                    "missing_fields": missing_fields,
                    "available_fields": available_fields,
                    "missing_count": len(missing_fields),
                    "completion_rate": len(available_fields) / len(contact_fields) * 100,
                    "enrichment_history": enrichment_history,
                    "recent_activities": recent_activities,
                    "needs_enrichment": len(missing_fields) > 0
                })
                
                return org_dict
                
        except Exception as e:
            self.logger.error(f"❌ 기관 상세 조회 실패: {e}")
            return None
    
    def update_organization_with_validation(self, org_id: int, updates: Dict[str, Any], 
                                          updated_by: str) -> Dict[str, Any]:
        """검증을 포함한 기관 정보 업데이트"""
        try:
            # 업데이트 전 현재 데이터 조회
            current_org = self.get_organization_detail_with_enrichment_info(org_id)
            if not current_org:
                return {"success": False, "error": "기관을 찾을 수 없습니다."}
            
            # 변경 이력 추적
            changes = {}
            contact_fields = ['phone', 'fax', 'email', 'homepage', 'address']
            
            for field in contact_fields:
                old_value = current_org.get(field, "")
                new_value = updates.get(field, old_value)
                
                if old_value != new_value:
                    changes[field] = {
                        "old": old_value,
                        "new": new_value
                    }
            
            # 업데이트 실행
            success = self.db.update_organization(org_id, updates, updated_by)
            
            if success and changes:
                # 변경 이력을 활동 로그에 기록
                self.log_contact_update_activity(org_id, changes, updated_by)
                
                return {
                    "success": True,
                    "message": f"{len(changes)}개 필드가 업데이트되었습니다.",
                    "changes": changes
                }
            elif success:
                return {
                    "success": True,
                    "message": "기관 정보가 업데이트되었습니다.",
                    "changes": {}
                }
            else:
                return {"success": False, "error": "업데이트에 실패했습니다."}
                
        except Exception as e:
            self.logger.error(f"❌ 기관 업데이트 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def log_contact_update_activity(self, org_id: int, changes: Dict[str, Any], updated_by: str):
        """연락처 업데이트 활동 로그 기록"""
        try:
            change_summary = []
            for field, change in changes.items():
                old_val = change['old'] if change['old'] else '(없음)'
                new_val = change['new'] if change['new'] else '(삭제됨)'
                change_summary.append(f"{field}: {old_val} → {new_val}")
            
            activity_data = {
                "organization_id": org_id,
                "activity_type": "NOTE",
                "subject": "연락처 정보 업데이트",
                "description": "연락처 정보가 업데이트되었습니다.\n\n" + "\n".join(change_summary),
                "created_by": updated_by,
                "is_completed": True,
                "completed_at": datetime.now().isoformat()
            }
            
            self.db.add_contact_activity(activity_data)
            
        except Exception as e:
            self.logger.error(f"❌ 활동 로그 기록 실패: {e}")
    
    def get_enrichment_candidates(self, priority: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """연락처 보강 후보 기관 목록 조회"""
        try:
            # 우선순위별 필터링
            priority_filter = ""
            params = []
            
            if priority:
                priority_filter = "AND priority = ?"
                params.append(priority)
            
            query = f"""
            SELECT 
                id, name, type, category, priority, assigned_to,
                homepage, phone, fax, email, address,
                last_contact_date, updated_at,
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
            WHERE is_active = 1
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            {priority_filter}
            ORDER BY 
                CASE 
                    WHEN priority = 'HIGH' THEN 1
                    WHEN priority = 'MEDIUM' THEN 2
                    ELSE 3
                END,
                missing_count DESC,
                updated_at ASC
            LIMIT ?
            """
            
            params.append(limit)
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query, params)
                candidates = []
                
                for row in cursor.fetchall():
                    org = dict(row)
                    
                    # 누락된 필드 상세 분석
                    missing_fields = []
                    if not org['phone'] or org['phone'].strip() == '':
                        missing_fields.append('phone')
                    if not org['fax'] or org['fax'].strip() == '':
                        missing_fields.append('fax')
                    if not org['email'] or org['email'].strip() == '':
                        missing_fields.append('email')
                    if not org['homepage'] or org['homepage'].strip() == '':
                        missing_fields.append('homepage')
                    if not org['address'] or org['address'].strip() == '':
                        missing_fields.append('address')
                    
                    org['missing_fields'] = missing_fields
                    org['enrichment_priority'] = self._calculate_enrichment_priority(org)
                    candidates.append(org)
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"❌ 보강 후보 조회 실패: {e}")
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
                updated_date = datetime.fromisoformat(org['updated_at'].replace('Z', '+00:00'))
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
    
    def get_contact_statistics(self) -> Dict[str, Any]:
        """연락처 정보 통계 조회"""
        try:
            with self.db.get_connection() as conn:
                # 전체 기관 수
                cursor = conn.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1")
                total_orgs = cursor.fetchone()[0]
                
                # 필드별 완성도 통계
                stats = {}
                contact_fields = ['phone', 'fax', 'email', 'homepage', 'address']
                
                for field in contact_fields:
                    cursor = conn.execute(f"""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN {field} IS NOT NULL AND {field} != '' THEN 1 ELSE 0 END) as filled
                        FROM organizations 
                        WHERE is_active = 1
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
                cursor = conn.execute("""
                    SELECT 
                        (CASE WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 END +
                         CASE WHEN fax IS NULL OR fax = '' THEN 1 ELSE 0 END +
                         CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END +
                         CASE WHEN homepage IS NULL OR homepage = '' THEN 1 ELSE 0 END +
                         CASE WHEN address IS NULL OR address = '' THEN 1 ELSE 0 END) as missing_count,
                        COUNT(*) as org_count
                    FROM organizations 
                    WHERE is_active = 1
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
                    "organizations_needing_enrichment": missing_distribution.get(1, 0) + missing_distribution.get(2, 0) + missing_distribution.get(3, 0) + missing_distribution.get(4, 0) + missing_distribution.get(5, 0),
                    "complete_organizations": missing_distribution.get(0, 0)
                }
                
        except Exception as e:
            self.logger.error(f"❌ 연락처 통계 조회 실패: {e}")
            return {}

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
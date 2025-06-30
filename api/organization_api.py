#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기관 관리 API 엔드포인트
CRM 기관 정보 CRUD 및 연락처 보강 상태 관리
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field

from services.organization_service import OrganizationService, OrganizationSearchFilter
from services.contact_enrichment_service import enrich_organization_by_id
from database.database import get_database
from utils.logger_utils import LoggerUtils

router = APIRouter(prefix="/api/organizations", tags=["기관 관리"])
logger = LoggerUtils.setup_logger(name="organization_api", file_logging=False)

# Pydantic 모델들
class OrganizationUpdateModel(BaseModel):
    """기관 정보 업데이트 모델"""
    name: Optional[str] = Field(None, description="기관명")
    type: Optional[str] = Field(None, description="기관 유형")
    category: Optional[str] = Field(None, description="카테고리")
    homepage: Optional[str] = Field(None, description="홈페이지")
    phone: Optional[str] = Field(None, description="전화번호")
    fax: Optional[str] = Field(None, description="팩스번호")
    email: Optional[str] = Field(None, description="이메일")
    mobile: Optional[str] = Field(None, description="휴대폰")
    address: Optional[str] = Field(None, description="주소")
    postal_code: Optional[str] = Field(None, description="우편번호")
    contact_status: Optional[str] = Field(None, description="연락 상태")
    priority: Optional[str] = Field(None, description="우선순위")
    assigned_to: Optional[str] = Field(None, description="담당자")
    sales_notes: Optional[str] = Field(None, description="영업 노트")
    internal_notes: Optional[str] = Field(None, description="내부 메모")

class OrganizationSearchModel(BaseModel):
    """기관 검색 모델"""
    search_term: Optional[str] = Field(None, description="검색어")
    organization_type: Optional[str] = Field(None, description="기관 유형")
    contact_status: Optional[str] = Field(None, description="연락 상태")
    priority: Optional[str] = Field(None, description="우선순위")
    assigned_to: Optional[str] = Field(None, description="담당자")
    has_missing_contacts: bool = Field(False, description="누락된 연락처 있음")
    page: int = Field(1, description="페이지 번호", ge=1)
    per_page: int = Field(20, description="페이지당 항목 수", ge=1, le=100)

@router.get("/", summary="기관 목록 조회")
async def get_organizations(
    page: int = Query(1, description="페이지 번호", ge=1),
    per_page: int = Query(20, description="페이지당 항목 수", ge=1, le=100),
    search: Optional[str] = Query(None, description="검색어"),
    type: Optional[str] = Query(None, description="기관 유형"),
    status: Optional[str] = Query(None, description="연락 상태"),
    priority: Optional[str] = Query(None, description="우선순위"),
    assigned_to: Optional[str] = Query(None, description="담당자"),
    missing_contacts: bool = Query(False, description="누락된 연락처만 조회")
):
    """
    기관 목록을 조회합니다.
    
    - **page**: 페이지 번호
    - **per_page**: 페이지당 항목 수
    - **search**: 기관명, 주소, 이메일 검색
    - **type**: 기관 유형 필터
    - **status**: 연락 상태 필터
    - **priority**: 우선순위 필터
    - **assigned_to**: 담당자 필터
    - **missing_contacts**: 누락된 연락처가 있는 기관만 조회
    """
    try:
        logger.info(f"🔍 기관 목록 조회 시작 - page: {page}, per_page: {per_page}")
        
        org_service = OrganizationService()
        logger.info("✅ OrganizationService 초기화 성공")
        
        # 검색 필터 생성
        filters = OrganizationSearchFilter(
            search_term=search,
            organization_type=type,
            contact_status=status,
            priority=priority,
            assigned_to=assigned_to,
            has_missing_contacts=missing_contacts
        )
        logger.info(f"📋 검색 필터: {filters.__dict__}")
        
        # 검색 실행
        result = org_service.search_organizations(filters, page, per_page)
        logger.info(f"📊 검색 결과: {len(result.get('organizations', []))}개 기관")
        
        pagination = result.get("pagination", {})
        total_count = pagination.get("total_count", 0)
        
        return {
            "status": "success",
            "organizations": result.get("organizations", []),
            "pagination": pagination,
            "filters_applied": result.get("filters_applied", {}),
            "total_count": total_count
        }
        
    except Exception as e:
        logger.error(f"❌ 기관 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.get("/missing-contacts", summary="누락된 연락처 기관 목록")
async def get_organizations_missing_contacts(
    limit: int = Query(100, description="최대 조회 수", ge=1, le=500),
    priority: Optional[str] = Query(None, description="우선순위 필터")
):
    """
    누락된 연락처 정보가 있는 기관 목록을 조회합니다.
    
    - **limit**: 최대 조회할 기관 수
    - **priority**: 우선순위 필터 (HIGH/MEDIUM/LOW)
    """
    try:
        org_service = OrganizationService()
        
        if priority:
            organizations = org_service.get_enrichment_candidates(priority=priority, limit=limit)
        else:
            organizations = org_service.get_organizations_with_missing_contacts(limit=limit)
        
        # 통계 계산
        total_missing_fields = sum(org.get('missing_count', 0) for org in organizations)
        field_distribution = {}
        
        for org in organizations:
            for field in org.get('missing_fields', []):
                field_distribution[field] = field_distribution.get(field, 0) + 1
        
        return {
            "status": "success",
            "count": len(organizations),
            "organizations": organizations,
            "statistics": {
                "total_organizations": len(organizations),
                "total_missing_fields": total_missing_fields,
                "avg_missing_per_org": total_missing_fields / len(organizations) if organizations else 0,
                "field_distribution": field_distribution
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 누락 연락처 기관 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

# 이 엔드포인트는 파일 끝으로 이동됨 (/{org_id} 패턴이 다른 경로와 충돌 방지)

@router.put("/{org_id}", summary="기관 정보 수정")
async def update_organization(
    org_id: int = Path(..., description="기관 ID"),
    updates: OrganizationUpdateModel = ...,
    updated_by: str = Query("API_USER", description="수정자")
):
    """
    기관 정보를 수정합니다.
    
    - **org_id**: 수정할 기관의 ID
    - **updates**: 수정할 정보
    - **updated_by**: 수정자 정보
    """
    try:
        org_service = OrganizationService()
        
        # None이 아닌 필드만 업데이트 데이터에 포함
        update_data = {}
        for field, value in updates.dict().items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다.")
        
        # 업데이트 실행
        result = org_service.update_organization_with_validation(org_id, update_data, updated_by)
        
        if result['success']:
            return {
                "status": "success",
                "message": result['message'],
                "changes": result.get('changes', {}),
                "organization_id": org_id
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 정보 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")

@router.post("/{org_id}/enrich", summary="기관 연락처 보강")
async def enrich_organization_contacts(org_id: int = Path(..., description="기관 ID")):
    """
    특정 기관의 연락처 정보를 크롤링하여 보강합니다.
    
    - **org_id**: 보강할 기관의 ID
    """
    try:
        # 기관 존재 확인
        org_service = OrganizationService()
        organization = org_service.get_organization_detail_with_enrichment_info(org_id)
        
        if not organization:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        if not organization.get('needs_enrichment', False):
            return {
                "status": "skipped",
                "message": "해당 기관은 모든 연락처 정보가 완성되어 있습니다.",
                "organization": {
                    "id": org_id,
                    "name": organization['name'],
                    "completion_rate": organization.get('completion_rate', 100)
                }
            }
        
        # 연락처 보강 실행
        result = await enrich_organization_by_id(org_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="연락처 보강에 실패했습니다.")
        
        return {
            "status": "completed" if result.success else "failed",
            "message": f"연락처 보강 완료: {len(result.found_data)}개 필드 발견" if result.success else "연락처 보강 실패",
            "organization_id": org_id,
            "found_data": result.found_data,
            "still_missing": result.missing_fields,
            "processing_time": result.processing_time,
            "success": result.success,
            "error_message": result.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 연락처 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보강 실패: {str(e)}")

@router.get("/{org_id}/enrichment-history", summary="연락처 보강 이력")
async def get_organization_enrichment_history(org_id: int = Path(..., description="기관 ID")):
    """
    특정 기관의 연락처 보강 이력을 조회합니다.
    
    - **org_id**: 기관 ID
    """
    try:
        from services.contact_enrichment_service import ContactEnrichmentService
        
        enrichment_service = ContactEnrichmentService()
        history = enrichment_service.get_enrichment_history(org_id)
        
        return {
            "status": "success",
            "organization_id": org_id,
            "enrichment_history": history
        }
        
    except Exception as e:
        logger.error(f"❌ 보강 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이력 조회 실패: {str(e)}")

@router.delete("/{org_id}", summary="기관 삭제")
async def delete_organization(
    org_id: int = Path(..., description="기관 ID"),
    deleted_by: str = Query("API_USER", description="삭제자")
):
    """
    기관을 삭제합니다. (실제로는 비활성화)
    
    - **org_id**: 삭제할 기관의 ID
    - **deleted_by**: 삭제자 정보
    """
    try:
        db = get_database()
        
        # 기관 존재 확인
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM organizations WHERE id = ? AND is_active = 1", (org_id,))
            org = cursor.fetchone()
            
            if not org:
                raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 소프트 삭제 (is_active = 0)
        success = db.update_organization(org_id, {
            "is_active": False,
            "updated_by": deleted_by,
            "updated_at": datetime.now().isoformat()
        }, deleted_by)
        
        if success:
            # 삭제 활동 로그 기록
            activity_data = {
                "organization_id": org_id,
                "activity_type": "NOTE",
                "subject": "기관 삭제",
                "description": f"기관이 삭제되었습니다. (삭제자: {deleted_by})",
                "created_by": deleted_by,
                "is_completed": True,
                "completed_at": datetime.now().isoformat()
            }
            db.add_contact_activity(activity_data)
            
            return {
                "status": "success",
                "message": f"기관 '{org['name']}'이 삭제되었습니다.",
                "organization_id": org_id
            }
        else:
            raise HTTPException(status_code=500, detail="기관 삭제에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

@router.get("/{org_id}/activities", summary="기관 활동 이력")
async def get_organization_activities(
    org_id: int = Path(..., description="기관 ID"),
    limit: int = Query(20, description="최대 조회 수", ge=1, le=100)
):
    """
    특정 기관의 활동 이력을 조회합니다.
    
    - **org_id**: 기관 ID
    - **limit**: 최대 조회할 활동 수
    """
    try:
        db = get_database()
        
        with db.get_connection() as conn:
            # 기관 존재 확인
            cursor = conn.execute("SELECT id, name FROM organizations WHERE id = ?", (org_id,))
            org = cursor.fetchone()
            
            if not org:
                raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
            
            # 활동 이력 조회
            cursor = conn.execute("""
                SELECT 
                    id, activity_type, subject, description, contact_person,
                    contact_method, result, next_action, created_by, created_at,
                    scheduled_date, completed_at, is_completed
                FROM contact_activities 
                WHERE organization_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (org_id, limit))
            
            activities = [dict(row) for row in cursor.fetchall()]
        
        return {
            "status": "success",
            "organization_id": org_id,
            "organization_name": org['name'],
            "activities": activities,
            "count": len(activities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 활동 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이력 조회 실패: {str(e)}")

@router.post("/{org_id}/activities", summary="기관 활동 추가")
async def add_organization_activity(
    org_id: int = Path(..., description="기관 ID"),
    activity_type: str = Query(..., description="활동 유형 (CALL/EMAIL/MEETING/NOTE/VISIT)"),
    subject: str = Query(..., description="활동 제목"),
    description: Optional[str] = Query(None, description="활동 내용"),
    contact_person: Optional[str] = Query(None, description="연락한 담당자"),
    contact_method: Optional[str] = Query(None, description="연락 방법"),
    result: Optional[str] = Query(None, description="결과"),
    next_action: Optional[str] = Query(None, description="다음 액션"),
    created_by: str = Query("API_USER", description="작성자")
):
    """
    기관에 새로운 활동을 추가합니다.
    
    - **org_id**: 기관 ID
    - **activity_type**: 활동 유형
    - **subject**: 활동 제목
    - **description**: 활동 내용
    - **contact_person**: 연락한 담당자
    - **contact_method**: 연락 방법
    - **result**: 결과
    - **next_action**: 다음 액션
    - **created_by**: 작성자
    """
    try:
        db = get_database()
        
        # 기관 존재 확인
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM organizations WHERE id = ? AND is_active = 1", (org_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 활동 데이터 생성
        activity_data = {
            "organization_id": org_id,
            "activity_type": activity_type,
            "subject": subject,
            "description": description,
            "contact_person": contact_person,
            "contact_method": contact_method,
            "result": result,
            "next_action": next_action,
            "created_by": created_by,
            "is_completed": True,
            "completed_at": datetime.now().isoformat()
        }
        
        # 활동 추가
        activity_id = db.add_contact_activity(activity_data)
        
        return {
            "status": "success",
            "message": "활동이 추가되었습니다.",
            "activity_id": activity_id,
            "organization_id": org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 활동 추가 실패: {e}")
        raise HTTPException(status_code=500, detail=f"활동 추가 실패: {str(e)}")

@router.get("/statistics/contacts", summary="연락처 완성도 통계")
async def get_contact_completion_statistics():
    """
    전체 기관의 연락처 정보 완성도 통계를 조회합니다.
    """
    try:
        org_service = OrganizationService()
        stats = org_service.get_contact_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ 연락처 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}") 

@router.get("/enrichment-candidates", summary="연락처 보강 후보 기관 목록")
async def get_enrichment_candidates(
    limit: int = Query(20, description="최대 조회 수", ge=1, le=500),
    priority: Optional[str] = Query(None, description="우선순위 필터 (HIGH/MEDIUM/LOW)")
):
    """
    연락처 보강이 필요한 후보 기관 목록을 조회합니다.
    
    - **limit**: 최대 조회할 기관 수
    - **priority**: 우선순위 필터
    """
    try:
        logger.info(f"🔍 보강 후보 조회 시작 - limit: {limit}, priority: {priority}")
        
        org_service = OrganizationService()
        
        if priority:
            logger.info(f"📋 우선순위별 후보 조회: {priority}")
            candidates = org_service.get_enrichment_candidates(priority=priority, limit=limit)
        else:
            logger.info("📋 전체 누락 연락처 기관 조회")
            candidates = org_service.get_organizations_with_missing_contacts(limit=limit)
        
        logger.info(f"✅ 후보 조회 완료 - 총 {len(candidates)}개 기관")
        
        # 통계 계산
        total_missing_fields = sum(org.get('missing_count', 0) for org in candidates)
        field_distribution = {}
        
        for org in candidates:
            for field in org.get('missing_fields', []):
                field_distribution[field] = field_distribution.get(field, 0) + 1
        
        result = {
            "status": "success",
            "candidates": candidates,
            "count": len(candidates),
            "statistics": {
                "total_candidates": len(candidates),
                "total_missing_fields": total_missing_fields,
                "avg_missing_per_org": total_missing_fields / len(candidates) if candidates else 0,
                "field_distribution": field_distribution
            }
        }
        
        logger.info(f"📊 결과 통계 - 총 후보: {len(candidates)}, 누락 필드: {total_missing_fields}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 보강 후보 조회 실패: {e}")
        import traceback
        logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

# /{org_id} 패턴은 마지막에 정의 (다른 경로와의 충돌 방지)
@router.get("/{org_id}", summary="기관 상세 정보 조회")
async def get_organization_detail(org_id: int = Path(..., description="기관 ID")):
    """
    특정 기관의 상세 정보를 조회합니다.
    
    - **org_id**: 조회할 기관의 ID
    """
    try:
        org_service = OrganizationService()
        organization = org_service.get_organization_detail_with_enrichment_info(org_id)
        
        if not organization:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        return {
            "status": "success",
            "organization": organization
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연락처 보강 API 엔드포인트
CRM DB의 누락된 연락처 정보를 자동으로 크롤링하는 API
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field

from services.contact_enrichment_service import ContactEnrichmentService, EnrichmentRequest
from services.organization_service import OrganizationService
from utils.logger_utils import LoggerUtils

router = APIRouter(prefix="/api/enrichment", tags=["연락처 보강"])
logger = LoggerUtils.setup_logger("enrichment_api", file_logging=False)

# Pydantic 모델들
class EnrichmentRequestModel(BaseModel):
    """연락처 보강 요청 모델"""
    org_ids: List[int] = Field(..., description="보강할 기관 ID 목록")
    priority: str = Field("MEDIUM", description="우선순위 (HIGH/MEDIUM/LOW)")
    requested_by: str = Field("API_USER", description="요청자")
    max_concurrent: int = Field(3, description="최대 동시 처리 수", ge=1, le=10)

class AutoEnrichmentRequestModel(BaseModel):
    """자동 보강 요청 모델"""
    limit: int = Field(50, description="최대 처리 기관 수", ge=1, le=200)
    priority_filter: Optional[str] = Field(None, description="우선순위 필터 (HIGH/MEDIUM/LOW)")
    max_concurrent: int = Field(3, description="최대 동시 처리 수", ge=1, le=10)

class EnrichmentResponseModel(BaseModel):
    """연락처 보강 응답 모델"""
    status: str
    message: str
    processed_count: int
    successful_count: int
    total_fields_found: int
    results: List[Dict[str, Any]]

# 전역 변수 (진행 상황 추적용)
current_enrichment_job = None
enrichment_progress = {}

@router.get("/missing-contacts", summary="누락된 연락처 정보 기관 목록")
async def get_organizations_with_missing_contacts(
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
            # 우선순위별 필터링
            candidates = org_service.get_enrichment_candidates(priority=priority, limit=limit)
        else:
            # 전체 누락 기관 조회
            candidates = org_service.get_organizations_with_missing_contacts(limit=limit)
        
        return {
            "status": "success",
            "count": len(candidates),
            "organizations": candidates,
            "summary": {
                "total_missing_organizations": len(candidates),
                "avg_missing_fields": sum(org.get('missing_count', 0) for org in candidates) / len(candidates) if candidates else 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 누락 연락처 기관 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.get("/statistics", summary="연락처 정보 통계")
async def get_contact_statistics():
    """
    전체 연락처 정보 완성도 통계를 조회합니다.
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

@router.post("/enrich-single/{org_id}", summary="단일 기관 연락처 보강")
async def enrich_single_organization(
    org_id: int = Path(..., description="기관 ID"),
    background_tasks: BackgroundTasks = None
):
    """
    특정 기관의 연락처 정보를 크롤링하여 보강합니다.
    
    - **org_id**: 보강할 기관의 ID
    """
    try:
        enrichment_service = ContactEnrichmentService()
        
        # 기관 정보 확인
        org_service = OrganizationService()
        org_detail = org_service.get_organization_detail_with_enrichment_info(org_id)
        
        if not org_detail:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        if not org_detail.get('needs_enrichment', False):
            return {
                "status": "skipped",
                "message": "해당 기관은 모든 연락처 정보가 완성되어 있습니다.",
                "organization": org_detail
            }
        
        # 보강 요청 생성
        request = EnrichmentRequest(
            org_id=org_id,
            org_name=org_detail['name'],
            missing_fields=org_detail['missing_fields'],
            requested_by="API_USER"
        )
        
        # 보강 실행
        result = await enrichment_service.enrich_single_organization(request)
        
        return {
            "status": "completed",
            "message": f"연락처 보강 완료: {len(result.found_data)}개 필드 발견",
            "organization_id": org_id,
            "organization_name": org_detail['name'],
            "found_data": result.found_data,
            "still_missing": result.missing_fields,
            "processing_time": result.processing_time,
            "success": result.success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단일 기관 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보강 실패: {str(e)}")

@router.post("/enrich-multiple", summary="다중 기관 연락처 보강")
async def enrich_multiple_organizations(
    request: EnrichmentRequestModel,
    background_tasks: BackgroundTasks
):
    """
    여러 기관의 연락처 정보를 일괄 보강합니다.
    
    - **org_ids**: 보강할 기관 ID 목록
    - **priority**: 우선순위
    - **max_concurrent**: 최대 동시 처리 수
    """
    try:
        global current_enrichment_job, enrichment_progress
        
        if current_enrichment_job and current_enrichment_job.get('status') == 'running':
            raise HTTPException(status_code=409, detail="다른 보강 작업이 진행 중입니다.")
        
        # 작업 ID 생성
        job_id = f"enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 진행 상황 초기화
        enrichment_progress[job_id] = {
            "status": "starting",
            "total_count": len(request.org_ids),
            "processed_count": 0,
            "successful_count": 0,
            "failed_count": 0,
            "start_time": datetime.now().isoformat(),
            "current_org": None
        }
        
        current_enrichment_job = {
            "job_id": job_id,
            "status": "running",
            "org_ids": request.org_ids,
            "start_time": datetime.now().isoformat()
        }
        
        # 백그라운드에서 보강 실행
        background_tasks.add_task(
            run_multiple_enrichment,
            job_id,
            request.org_ids,
            request.priority,
            request.requested_by,
            request.max_concurrent
        )
        
        return {
            "status": "started",
            "message": f"{len(request.org_ids)}개 기관 연락처 보강을 시작했습니다.",
            "job_id": job_id,
            "total_count": len(request.org_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 다중 기관 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보강 시작 실패: {str(e)}")

@router.post("/auto-enrich", summary="자동 연락처 보강")
async def auto_enrich_missing_contacts(
    request: AutoEnrichmentRequestModel,
    background_tasks: BackgroundTasks
):
    """
    누락된 연락처 정보가 있는 기관들을 자동으로 찾아서 보강합니다.
    
    - **limit**: 최대 처리할 기관 수
    - **priority_filter**: 우선순위 필터
    - **max_concurrent**: 최대 동시 처리 수
    """
    try:
        global current_enrichment_job, enrichment_progress
        
        if current_enrichment_job and current_enrichment_job.get('status') == 'running':
            raise HTTPException(status_code=409, detail="다른 보강 작업이 진행 중입니다.")
        
        # 작업 ID 생성
        job_id = f"auto_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 진행 상황 초기화
        enrichment_progress[job_id] = {
            "status": "starting",
            "total_count": 0,
            "processed_count": 0,
            "successful_count": 0,
            "failed_count": 0,
            "start_time": datetime.now().isoformat(),
            "current_org": None
        }
        
        current_enrichment_job = {
            "job_id": job_id,
            "status": "running",
            "auto_mode": True,
            "start_time": datetime.now().isoformat()
        }
        
        # 백그라운드에서 자동 보강 실행
        background_tasks.add_task(
            run_auto_enrichment,
            job_id,
            request.limit,
            request.priority_filter,
            request.max_concurrent
        )
        
        return {
            "status": "started",
            "message": f"자동 연락처 보강을 시작했습니다. (최대 {request.limit}개 기관)",
            "job_id": job_id,
            "limit": request.limit,
            "priority_filter": request.priority_filter
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 자동 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자동 보강 시작 실패: {str(e)}")

@router.get("/progress/{job_id}", summary="보강 진행 상황 조회")
async def get_enrichment_progress(job_id: str = Path(..., description="작업 ID")):
    """
    연락처 보강 작업의 진행 상황을 조회합니다.
    
    - **job_id**: 작업 ID
    """
    try:
        global enrichment_progress
        
        if job_id not in enrichment_progress:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        progress = enrichment_progress[job_id].copy()
        
        # 진행률 계산
        if progress['total_count'] > 0:
            progress['progress_percentage'] = (progress['processed_count'] / progress['total_count']) * 100
        else:
            progress['progress_percentage'] = 0
        
        # 소요 시간 계산
        start_time = datetime.fromisoformat(progress['start_time'])
        elapsed_time = (datetime.now() - start_time).total_seconds()
        progress['elapsed_time'] = elapsed_time
        
        # 예상 완료 시간 계산
        if progress['processed_count'] > 0 and progress['status'] == 'running':
            avg_time_per_org = elapsed_time / progress['processed_count']
            remaining_orgs = progress['total_count'] - progress['processed_count']
            estimated_remaining_time = remaining_orgs * avg_time_per_org
            progress['estimated_remaining_time'] = estimated_remaining_time
        
        return {
            "status": "success",
            "job_id": job_id,
            "progress": progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 진행 상황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"진행 상황 조회 실패: {str(e)}")

@router.get("/history/{org_id}", summary="기관 연락처 보강 이력")
async def get_enrichment_history(org_id: int = Path(..., description="기관 ID")):
    """
    특정 기관의 연락처 보강 이력을 조회합니다.
    
    - **org_id**: 기관 ID
    """
    try:
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

@router.delete("/cancel/{job_id}", summary="보강 작업 취소")
async def cancel_enrichment_job(job_id: str = Path(..., description="작업 ID")):
    """
    진행 중인 연락처 보강 작업을 취소합니다.
    
    - **job_id**: 취소할 작업 ID
    """
    try:
        global current_enrichment_job, enrichment_progress
        
        if job_id not in enrichment_progress:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        if enrichment_progress[job_id]['status'] not in ['running', 'starting']:
            raise HTTPException(status_code=400, detail="취소할 수 있는 상태가 아닙니다.")
        
        # 작업 취소 표시
        enrichment_progress[job_id]['status'] = 'cancelled'
        enrichment_progress[job_id]['end_time'] = datetime.now().isoformat()
        
        if current_enrichment_job and current_enrichment_job.get('job_id') == job_id:
            current_enrichment_job['status'] = 'cancelled'
        
        return {
            "status": "success",
            "message": f"작업 {job_id}가 취소되었습니다.",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=f"작업 취소 실패: {str(e)}")

# 백그라운드 작업 함수들
async def run_multiple_enrichment(job_id: str, org_ids: List[int], priority: str, 
                                requested_by: str, max_concurrent: int):
    """다중 기관 보강 백그라운드 작업"""
    global current_enrichment_job, enrichment_progress
    
    try:
        enrichment_service = ContactEnrichmentService()
        org_service = OrganizationService()
        
        # 보강 요청 목록 생성
        requests = []
        for org_id in org_ids:
            org_detail = org_service.get_organization_detail_with_enrichment_info(org_id)
            if org_detail and org_detail.get('needs_enrichment', False):
                requests.append(EnrichmentRequest(
                    org_id=org_id,
                    org_name=org_detail['name'],
                    missing_fields=org_detail['missing_fields'],
                    priority=priority,
                    requested_by=requested_by
                ))
        
        # 총 개수 업데이트
        enrichment_progress[job_id]['total_count'] = len(requests)
        enrichment_progress[job_id]['status'] = 'running'
        
        # 보강 실행
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def enrich_with_progress(request):
            async with semaphore:
                # 진행 상황 업데이트
                enrichment_progress[job_id]['current_org'] = request.org_name
                
                # 취소 확인
                if enrichment_progress[job_id]['status'] == 'cancelled':
                    return None
                
                # 보강 실행
                result = await enrichment_service.enrich_single_organization(request)
                
                # 진행 상황 업데이트
                enrichment_progress[job_id]['processed_count'] += 1
                if result.success:
                    enrichment_progress[job_id]['successful_count'] += 1
                else:
                    enrichment_progress[job_id]['failed_count'] += 1
                
                return result
        
        # 병렬 처리
        tasks = [enrich_with_progress(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 완료 처리
        enrichment_progress[job_id]['status'] = 'completed'
        enrichment_progress[job_id]['end_time'] = datetime.now().isoformat()
        enrichment_progress[job_id]['results'] = [r for r in results if r is not None]
        
        current_enrichment_job['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"❌ 다중 보강 백그라운드 작업 실패: {e}")
        enrichment_progress[job_id]['status'] = 'error'
        enrichment_progress[job_id]['error'] = str(e)
        enrichment_progress[job_id]['end_time'] = datetime.now().isoformat()
        
        if current_enrichment_job:
            current_enrichment_job['status'] = 'error'

async def run_auto_enrichment(job_id: str, limit: int, priority_filter: Optional[str], 
                            max_concurrent: int):
    """자동 보강 백그라운드 작업"""
    global current_enrichment_job, enrichment_progress
    
    try:
        enrichment_service = ContactEnrichmentService()
        
        # 자동 보강 실행
        enrichment_progress[job_id]['status'] = 'running'
        
        # 진행 상황 업데이트를 위한 콜백
        def progress_callback(processed, total, current_org):
            enrichment_progress[job_id]['processed_count'] = processed
            enrichment_progress[job_id]['total_count'] = total
            enrichment_progress[job_id]['current_org'] = current_org
        
        # 자동 보강 실행
        summary = await enrichment_service.auto_enrich_missing_contacts(limit, max_concurrent)
        
        # 완료 처리
        enrichment_progress[job_id]['status'] = 'completed'
        enrichment_progress[job_id]['end_time'] = datetime.now().isoformat()
        enrichment_progress[job_id]['summary'] = summary
        enrichment_progress[job_id]['successful_count'] = summary.get('successful_count', 0)
        enrichment_progress[job_id]['total_count'] = summary.get('processed_count', 0)
        
        current_enrichment_job['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"❌ 자동 보강 백그라운드 작업 실패: {e}")
        enrichment_progress[job_id]['status'] = 'error'
        enrichment_progress[job_id]['error'] = str(e)
        enrichment_progress[job_id]['end_time'] = datetime.now().isoformat()
        
        if current_enrichment_job:
            current_enrichment_job['status'] = 'error' 
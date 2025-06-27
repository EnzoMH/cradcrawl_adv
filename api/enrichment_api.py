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
import json
import threading
import os

from services.contact_enrichment_service import ContactEnrichmentService, EnrichmentRequest
from services.organization_service import OrganizationService
from utils.logger_utils import LoggerUtils

router = APIRouter(prefix="/api/enrichment", tags=["연락처 보강"])
logger = LoggerUtils.setup_logger(name="enrichment_api", file_logging=False)

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

# 전역 변수들은 CrawlingService로 이관됨

# ==================== 크롤링 API (CrawlingService 통합) ====================

from services.crawling_service import get_crawling_service, CrawlingJobConfig

class FileCrawlingRequestModel(BaseModel):
    """파일 기반 크롤링 요청 모델"""
    test_mode: bool = Field(False, description="테스트 모드")
    test_count: int = Field(10, description="테스트 개수", ge=1, le=100)
    use_ai: bool = Field(True, description="AI 사용 여부")
    job_name: Optional[str] = Field(None, description="작업명")
    started_by: str = Field("API_USER", description="시작자")

class DBCrawlingRequestModel(BaseModel):
    """DB 기반 크롤링 요청 모델"""
    use_ai: bool = Field(True, description="AI 사용 여부")
    max_concurrent: int = Field(3, description="최대 동시 처리 수", ge=1, le=10)
    job_name: Optional[str] = Field(None, description="작업명")
    started_by: str = Field("API_USER", description="시작자")

@router.post("/start-file-crawling", summary="파일 기반 크롤링 시작")
async def start_file_crawling(request: FileCrawlingRequestModel):
    """파일 기반 Enhanced 크롤링 시작 (CrawlingService 사용)"""
    try:
        # CrawlingService 인스턴스 가져오기
        crawling_service = get_crawling_service()
        
        # 설정 변환
        config = CrawlingJobConfig(
            test_mode=request.test_mode,
            test_count=request.test_count,
            use_ai=request.use_ai,
            job_name=request.job_name,
            started_by=request.started_by
        )
        
        # 파일 기반 크롤링 시작
        result = await crawling_service.start_file_crawling(config)
        
        logger.info(f"✅ 파일 기반 크롤링 시작: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 파일 기반 크롤링 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")

@router.post("/start-db-crawling", summary="DB 기반 크롤링 시작")
async def start_db_crawling(request: DBCrawlingRequestModel):
    """DB 기반 크롤링 시작 (CrawlingService 사용)"""
    try:
        # CrawlingService 인스턴스 가져오기
        crawling_service = get_crawling_service()
        
        # 설정 변환
        config = CrawlingJobConfig(
            use_ai=request.use_ai,
            max_concurrent=request.max_concurrent,
            job_name=request.job_name,
            started_by=request.started_by
        )
        
        # DB 기반 크롤링 시작
        result = await crawling_service.start_db_crawling(config)
        
        logger.info(f"✅ DB 기반 크롤링 시작: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ DB 기반 크롤링 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"DB 크롤링 시작 실패: {str(e)}")

@router.get("/crawling-progress", summary="크롤링 진행 상황 조회")
async def get_crawling_progress():
    """크롤링 진행 상황 조회 (CrawlingService 사용)"""
    try:
        crawling_service = get_crawling_service()
        progress = crawling_service.get_crawling_progress()
        return progress
    except Exception as e:
        logger.error(f"❌ 진행 상황 조회 실패: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/crawling-results", summary="크롤링 결과 조회")
async def get_crawling_results(
    limit: int = Query(10, ge=1, le=100, description="조회할 결과 수"),
    all_results: bool = Query(False, description="모든 결과 조회 여부")
):
    """크롤링 결과 조회 (CrawlingService 사용)"""
    try:
        crawling_service = get_crawling_service()
        results = crawling_service.get_crawling_results(limit=limit, all_results=all_results)
        return results
    except Exception as e:
        logger.error(f"❌ 크롤링 결과 조회 실패: {e}")
        return {"results": [], "total_count": 0, "error": str(e)}

@router.get("/latest-crawling-results", summary="최신 크롤링 결과 조회")
async def get_latest_crawling_results():
    """최신 크롤링 작업 결과 조회 (CrawlingService 사용)"""
    try:
        crawling_service = get_crawling_service()
        results = crawling_service.get_latest_crawling_results()
        return results
        
    except Exception as e:
        logger.error(f"❌ 최신 크롤링 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"결과 조회 실패: {str(e)}")

@router.post("/stop-crawling", summary="크롤링 중지")
async def stop_crawling():
    """진행 중인 크롤링 작업 중지 (CrawlingService 사용)"""
    try:
        crawling_service = get_crawling_service()
        result = crawling_service.stop_crawling()
        
        logger.info(f"✅ 크롤링 중지: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 크롤링 중지 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 중지 실패: {str(e)}")

@router.get("/missing-contacts", summary="누락된 연락처 정보 기관 목록")
async def get_organizations_with_missing_contacts(
    page: int = Query(1, description="페이지 번호", ge=1),
    per_page: int = Query(50, description="페이지당 항목 수", ge=1, le=100),
    priority: Optional[str] = Query(None, description="우선순위 필터")
):
    """
    누락된 연락처 정보가 있는 기관 목록을 조회합니다.
    
    - **page**: 페이지 번호
    - **per_page**: 페이지당 항목 수
    - **priority**: 우선순위 필터 (HIGH/MEDIUM/LOW)
    """
    try:
        org_service = OrganizationService()
        
        # 페이지네이션을 지원하는 보강 후보 조회
        result = org_service.get_enrichment_candidates_with_pagination(
            page=page, 
            per_page=per_page, 
            priority=priority
        )
        
        candidates = result.get("candidates", [])
        pagination = result.get("pagination", {})
        
        # 필드 분포 계산
        field_distribution = {}
        for candidate in candidates:
            for field in candidate.get('missing_fields', []):
                field_distribution[field] = field_distribution.get(field, 0) + 1
        
        return {
            "status": "success",
            "candidates": candidates,
            "pagination": pagination,
            "count": len(candidates),
            "statistics": {
                "total_candidates": pagination.get("total_count", len(candidates)),
                "total_missing_fields": sum(org.get('missing_count', 0) for org in candidates),
                "avg_missing_fields": sum(org.get('missing_count', 0) for org in candidates) / len(candidates) if candidates else 0,
                "field_distribution": field_distribution
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
        # CrawlingService를 사용하여 작업 상태 관리
        crawling_service = get_crawling_service()
        
        # 현재 진행 중인 크롤링 작업이 있는지 확인
        current_progress = crawling_service.get_crawling_progress()
        if current_progress.get('status') == 'running':
            raise HTTPException(status_code=409, detail="다른 크롤링 작업이 진행 중입니다.")
        
        # 작업 ID 생성
        job_id = f"enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # CrawlingService를 통한 다중 보강 시작
        config = CrawlingJobConfig(
            use_ai=True,
            max_concurrent=request.max_concurrent,
            job_name=f"다중 기관 보강 ({len(request.org_ids)}개)",
            started_by=request.requested_by
        )
        
        # DB 기반 크롤링으로 처리
        result = await crawling_service.start_db_crawling(config)
        
        return {
            "status": "started",
            "message": f"{len(request.org_ids)}개 기관 연락처 보강을 시작했습니다.",
            "job_id": result.get('job_id', job_id),
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
        # CrawlingService를 사용하여 작업 상태 관리
        crawling_service = get_crawling_service()
        
        # 현재 진행 중인 크롤링 작업이 있는지 확인
        current_progress = crawling_service.get_crawling_progress()
        if current_progress.get('status') == 'running':
            raise HTTPException(status_code=409, detail="다른 크롤링 작업이 진행 중입니다.")
        
        # 작업 ID 생성
        job_id = f"auto_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # CrawlingService를 통한 자동 보강 시작
        config = CrawlingJobConfig(
            use_ai=True,
            max_concurrent=request.max_concurrent,
            job_name=f"자동 연락처 보강 (최대 {request.limit}개)",
            started_by="API_USER"
        )
        
        # DB 기반 크롤링으로 자동 보강 실행
        result = await crawling_service.start_db_crawling(config)
        
        return {
            "status": "started",
            "message": f"자동 연락처 보강을 시작했습니다. (최대 {request.limit}개 기관)",
            "job_id": result.get('job_id', job_id),
            "limit": request.limit,
            "priority_filter": request.priority_filter
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 자동 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자동 보강 시작 실패: {str(e)}")

@router.post("/auto", summary="자동 연락처 보강 (GET 파라미터 버전)")
async def auto_enrich_with_params(
    background_tasks: BackgroundTasks,
    limit: int = Query(100, description="최대 처리 기관 수", ge=1, le=200),
    priority_filter: Optional[str] = Query(None, description="우선순위 필터 (HIGH/MEDIUM/LOW)"),
    max_concurrent: int = Query(3, description="최대 동시 처리 수", ge=1, le=10)
):
    """
    GET 파라미터를 사용한 자동 연락처 보강 (JavaScript 호환성)
    
    - **limit**: 최대 처리할 기관 수
    - **priority_filter**: 우선순위 필터
    - **max_concurrent**: 최대 동시 처리 수
    """
    try:
        # AutoEnrichmentRequestModel 생성
        request = AutoEnrichmentRequestModel(
            limit=limit,
            priority_filter=priority_filter,
            max_concurrent=max_concurrent
        )
        
        # 기존 auto_enrich_missing_contacts 함수 재사용
        return await auto_enrich_missing_contacts(request, background_tasks)
        
    except Exception as e:
        logger.error(f"❌ 자동 보강 (파라미터 버전) 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자동 보강 시작 실패: {str(e)}")

@router.get("/progress/{job_id}", summary="보강 진행 상황 조회")
async def get_enrichment_progress(job_id: str = Path(..., description="작업 ID")):
    """
    연락처 보강 작업의 진행 상황을 조회합니다.
    
    - **job_id**: 작업 ID
    """
    try:
        # CrawlingService를 통해 진행 상황 조회
        crawling_service = get_crawling_service()
        progress = crawling_service.get_crawling_progress()
        
        if not progress or progress.get('job_id') != job_id:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
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
        # CrawlingService를 통해 작업 중지
        crawling_service = get_crawling_service()
        result = crawling_service.stop_crawling()
        
        return {
            "status": "success",
            "message": f"작업 {job_id}가 취소되었습니다.",
            "job_id": job_id,
            "stop_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=f"작업 취소 실패: {str(e)}")

# 백그라운드 작업 함수들은 CrawlingService로 대체됨
# 필요시 ContactEnrichmentService를 직접 사용 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM 기반 CRUD 애플리케이션
교회/기관 데이터베이스 관리 + 자동 연락처 보강 시스템
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))

import uvicorn
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, List

# 프로젝트 모듈 import
try:
    from api.organization_api import router as organization_router
    from api.enrichment_api import router as enrichment_router
except ImportError:
    # API 라우터가 없는 경우 None으로 설정
    organization_router = None
    enrichment_router = None

from database.database import get_database
from services.organization_service import OrganizationService, OrganizationSearchFilter
try:
    from services.contact_enrichment_service import ContactEnrichmentService
except ImportError:
    # ContactEnrichmentService가 없는 경우 None으로 설정
    ContactEnrichmentService = None

from utils.logger_utils import LoggerUtils
from utils.settings import *

# 로거 설정
logger = LoggerUtils.setup_logger("crm_app", file_logging=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("🚀 CRM 애플리케이션 시작")
    
    # 데이터베이스 연결 확인
    try:
        db = get_database()
        stats = db.get_dashboard_stats()
        logger.info(f"📊 DB 연결 성공 - 총 기관 수: {stats.get('total_organizations', 0)}")
    except Exception as e:
        logger.error(f"❌ DB 연결 실패: {e}")
        raise
    
    yield
    
    # 종료 시
    logger.info("⏹️ CRM 애플리케이션 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Church CRM System",
    description="""
    🏢 **교회/기관 CRM 관리 시스템**
    
    ## 주요 기능
    - 📋 **기관 정보 CRUD**: 교회, 학원, 공공기관 등 관리
    - 🤖 **자동 연락처 보강**: 누락된 연락처 정보 자동 크롤링
    - 📊 **통계 및 분석**: 연락처 완성도, 보강 현황 분석
    - 🔍 **고급 검색**: 다양한 조건으로 기관 검색
    - 📝 **활동 이력 관리**: 영업 활동 및 연락 이력 추적
    
    ## API 엔드포인트
    - `/api/organizations`: 기관 관리 API
    - `/api/enrichment`: 연락처 보강 API
    - `/dashboard`: 웹 대시보드
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 정적 파일 및 템플릿 설정
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(directory="templates")

# API 라우터 등록 (있는 경우에만)
if organization_router:
    app.include_router(organization_router)
if enrichment_router:
    app.include_router(enrichment_router)

# 홈페이지 및 대시보드 라우트
@app.get("/", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def home(request: Request):
    """메인 홈페이지"""
    try:
        # 기본 통계 정보 조회
        db = get_database()
        stats = db.get_dashboard_stats()
        
        # 연락처 완성도 통계
        org_service = OrganizationService()
        contact_stats = org_service.get_contact_statistics()
        
        # 최근 보강 후보 기관들
        missing_contacts = org_service.get_organizations_with_missing_contacts(limit=10)
        
        return templates.TemplateResponse("html/index.html", {
            "request": request,
            "stats": stats,
            "contact_stats": contact_stats,
            "missing_contacts": missing_contacts,
            "title": "Church CRM System"
        })
        
    except Exception as e:
        logger.error(f"❌ 홈페이지 로드 실패: {e}")
        return templates.TemplateResponse("html/index.html", {
            "request": request,
            "error": "데이터 로드 중 오류가 발생했습니다.",
            "title": "Church CRM System"
        })

@app.get("/dashboard", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def dashboard(request: Request):
    """대시보드 페이지"""
    try:
        # 상세 통계 정보 조회
        db = get_database()
        dashboard_stats = db.get_dashboard_stats()
        
        org_service = OrganizationService()
        contact_stats = org_service.get_contact_statistics()
        
        # 보강 후보 기관들
        enrichment_candidates = org_service.get_enrichment_candidates(limit=20)
        
        return templates.TemplateResponse("html/dashboard.html", {
            "request": request,
            "dashboard_stats": dashboard_stats,
            "contact_stats": contact_stats,
            "enrichment_candidates": enrichment_candidates,
            "title": "CRM 대시보드"
        })
        
    except Exception as e:
        logger.error(f"❌ 대시보드 로드 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "대시보드 데이터 로드 실패", "detail": str(e)}
        )

@app.get("/organizations", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def organizations_page(request: Request):
    """기관 관리 페이지"""
    return templates.TemplateResponse("html/organizations.html", {
        "request": request,
        "title": "기관 관리"
    })

@app.get("/enrichment", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def enrichment_page(request: Request):
    """연락처 보강 페이지"""
    return templates.TemplateResponse("html/enrichment.html", {
        "request": request,
        "title": "연락처 보강"
    })

@app.get("/login", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("html/login.html", {
        "request": request,
        "title": "로그인"
    })

@app.post("/login", tags=["인증"])
async def login(request: Request):
    """로그인 처리"""
    try:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # 간단한 인증 (실제 프로덕션에서는 보안 강화 필요)
        if username == "admin" and password == "admin123":
            # 로그인 성공 시 대시보드로 리다이렉트
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/dashboard", status_code=302)
        else:
            # 로그인 실패 시 에러 메시지와 함께 로그인 페이지 다시 표시
            return templates.TemplateResponse("html/login.html", {
                "request": request,
                "error": "사용자명 또는 비밀번호가 올바르지 않습니다.",
                "title": "로그인"
            })
            
    except Exception as e:
        logger.error(f"❌ 로그인 처리 실패: {e}")
        return templates.TemplateResponse("html/login.html", {
            "request": request,
            "error": "로그인 처리 중 오류가 발생했습니다.",
            "title": "로그인"
        })

# 상태 확인 엔드포인트
@app.get("/health", tags=["시스템"])
async def health_check():
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        db = get_database()
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1")
            org_count = cursor.fetchone()[0]
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_organizations": org_count,
            "version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"❌ 상태 확인 실패: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@app.get("/api/stats/summary", tags=["통계"])
async def get_summary_stats():
    """요약 통계 API"""
    try:
        db = get_database()
        org_service = OrganizationService()
        
        # 기본 통계
        dashboard_stats = db.get_dashboard_stats()
        
        # 연락처 통계
        contact_stats = org_service.get_contact_statistics()
        
        # 보강 필요 기관 수
        missing_contacts_count = len(org_service.get_organizations_with_missing_contacts(limit=1000))
        
        return {
            "status": "success",
            "summary": {
                "total_organizations": dashboard_stats.get("total_organizations", 0),
                "contact_completion_rate": contact_stats.get("overall_completion_rate", 0),
                "organizations_needing_enrichment": missing_contacts_count,
                "complete_organizations": contact_stats.get("complete_organizations", 0)
            },
            "dashboard_stats": dashboard_stats,
            "contact_stats": contact_stats
        }
        
    except Exception as e:
        logger.error(f"❌ 요약 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@app.get("/api/stats/dashboard-data", tags=["통계"])
async def get_dashboard_data():
    """대시보드 차트용 데이터 조회"""
    try:
        db = get_database()
        dashboard_stats = db.get_dashboard_stats()
        
        org_service = OrganizationService()
        contact_stats = org_service.get_contact_statistics()
        
        return {
            "complete_contacts": contact_stats.get("complete_contacts", 0),
            "missing_contacts": contact_stats.get("missing_contacts", 0),
            "categories": dashboard_stats.get("categories", []),
            "category_counts": dashboard_stats.get("category_counts", []),
            "total_organizations": dashboard_stats.get("total_organizations", 0),
            "completion_rate": contact_stats.get("completion_rate", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ 대시보드 데이터 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "대시보드 데이터 조회 실패", "detail": str(e)}
        )

@app.get("/api/organizations/enrichment-candidates", tags=["기관"])
async def get_enrichment_candidates():
    """보강 후보 기관 목록 조회"""
    try:
        org_service = OrganizationService()
        candidates = org_service.get_enrichment_candidates(limit=20)
        return candidates
        
    except Exception as e:
        logger.error(f"❌ 보강 후보 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "보강 후보 조회 실패", "detail": str(e)}
        )

@app.get("/api/statistics", tags=["통계"])
async def get_statistics():
    """통계 API (main.js에서 호출)"""
    try:
        db = get_database()
        org_service = OrganizationService()
        
        # 기본 통계
        dashboard_stats = db.get_dashboard_stats()
        contact_stats = org_service.get_contact_statistics()
        
        # 보강 필요 기관 수
        missing_contacts_count = len(org_service.get_organizations_with_missing_contacts(limit=1000))
        
        return {
            "status": "success",
            "data": {
                "total_organizations": dashboard_stats.get("total_organizations", 0),
                "total_users": 1,  # 현재는 단일 사용자
                "recent_activities": contact_stats.get("complete_contacts", 0),
                "crawling_jobs": 0,  # 현재 진행 중인 크롤링 작업 수
                "completion_rate": contact_stats.get("completion_rate", 0.0),
                "organizations_needing_enrichment": missing_contacts_count
            },
            "dashboard_stats": dashboard_stats,
            "contact_stats": contact_stats
        }
        
    except Exception as e:
        logger.error(f"❌ 통계 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error", 
                "message": f"통계 조회 실패: {str(e)}"
            }
        )

@app.get("/api/progress", tags=["진행상황"])
async def get_progress():
    """크롤링 진행 상황 조회"""
    try:
        # 실제 크롤링 시스템이 구현되면 해당 상태를 반환
        # 현재는 기본 상태 반환
        return {
            "status": "idle",  # idle, running, completed, error
            "progress": 0,
            "total": 0,
            "current_task": "",
            "elapsed_time": 0,
            "estimated_remaining": 0,
            "errors": [],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 진행 상황 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "진행 상황 조회 실패", "detail": str(e)}
        )

@app.get("/api/real-time-results", tags=["진행상황"])
async def get_real_time_results(limit: int = Query(5, ge=1, le=50)):
    """실시간 크롤링 결과 조회"""
    try:
        db = get_database()
        org_service = OrganizationService()
        
        # 최근 업데이트된 기관들 조회 (실시간 결과로 사용)
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    id, name, category, address, phone, homepage, 
                    updated_at, contact_status
                FROM organizations 
                WHERE updated_at IS NOT NULL 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "address": row[3],
                    "phone": row[4],
                    "homepage": row[5],
                    "updated_at": row[6],
                    "contact_status": row[7],
                    "action": "updated" if row[6] else "new"
                })
        
        return {
            "status": "success",
            "results": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 실시간 결과 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "실시간 결과 조회 실패", "detail": str(e)}
        )

# ==================== 기관 CRUD API ====================

@app.get("/api/organizations", tags=["기관"])
async def get_organizations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """기관 목록 조회 (페이징, 검색, 필터링)"""
    try:
        org_service = OrganizationService()
        
        # 검색 필터 구성
        filters = OrganizationSearchFilter(
            search_term=search,
            organization_type=category,
            contact_status=status,
            priority=priority
        )
        
        result = org_service.search_organizations(filters, page, per_page)
        
        return {
            "status": "success",
            "organizations": result["organizations"],
            "pagination": result["pagination"],
            "filters_applied": result.get("filters_applied", {})
        }
        
    except Exception as e:
        logger.error(f"❌ 기관 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기관 목록 조회 실패: {str(e)}")

@app.get("/api/organizations/{org_id}", tags=["기관"])
async def get_organization_detail(org_id: int):
    """기관 상세 정보 조회"""
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
        raise HTTPException(status_code=500, detail=f"기관 상세 조회 실패: {str(e)}")

@app.post("/api/organizations", tags=["기관"])
async def create_organization(organization: dict):
    """새 기관 생성"""
    try:
        db = get_database()
        
        # 필수 필드 검증
        required_fields = ['name', 'type']
        for field in required_fields:
            if not organization.get(field):
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 기본값 설정
        organization.setdefault('category', '기타')
        organization.setdefault('contact_status', 'NEW')
        organization.setdefault('priority', 'MEDIUM')
        organization.setdefault('created_by', 'system')
        organization.setdefault('updated_by', 'system')
        
        org_id = db.create_organization(organization)
        
        return {
            "status": "success",
            "message": "기관이 성공적으로 생성되었습니다.",
            "organization_id": org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기관 생성 실패: {str(e)}")

@app.put("/api/organizations/{org_id}", tags=["기관"])
async def update_organization(org_id: int, updates: dict):
    """기관 정보 수정"""
    try:
        org_service = OrganizationService()
        
        # 업데이트 실행
        result = org_service.update_organization_with_validation(
            org_id, updates, updated_by="system"
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": result["message"],
            "changes": result.get("changes", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기관 수정 실패: {str(e)}")

@app.delete("/api/organizations/{org_id}", tags=["기관"])
async def delete_organization(org_id: int):
    """기관 삭제 (소프트 삭제)"""
    try:
        db = get_database()
        
        # 기관 존재 확인
        org = db.get_organization_detail(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 소프트 삭제 실행
        success = db.delete_organization(org_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="기관 삭제에 실패했습니다.")
        
        return {
            "status": "success",
            "message": "기관이 성공적으로 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 기관 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기관 삭제 실패: {str(e)}")

# ==================== 연락처 보강 API ====================

@app.post("/api/enrichment/single/{org_id}", tags=["연락처 보강"])
async def enrich_single_organization(org_id: int):
    """단일 기관 연락처 보강"""
    try:
        if ContactEnrichmentService is None:
            raise HTTPException(status_code=501, detail="연락처 보강 서비스가 구현되지 않았습니다.")
            
        enrichment_service = ContactEnrichmentService()
        
        # 기관 존재 확인
        db = get_database()
        org = db.get_organization_detail(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 보강 실행
        result = await enrichment_service.enrich_single_organization(org_id)
        
        return {
            "status": "success" if result["success"] else "error",
            "message": result["message"],
            "enriched_fields": result.get("enriched_fields", []),
            "found_data": result.get("found_data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단일 기관 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"연락처 보강 실패: {str(e)}")

@app.post("/api/enrichment/batch", tags=["연락처 보강"])
async def enrich_batch_organizations(organization_ids: List[int]):
    """다중 기관 일괄 보강"""
    try:
        if ContactEnrichmentService is None:
            raise HTTPException(status_code=501, detail="연락처 보강 서비스가 구현되지 않았습니다.")
            
        enrichment_service = ContactEnrichmentService()
        
        if len(organization_ids) > 50:
            raise HTTPException(status_code=400, detail="한 번에 최대 50개 기관까지만 처리할 수 있습니다.")
        
        # 일괄 보강 실행
        results = await enrichment_service.enrich_multiple_organizations(organization_ids)
        
        return {
            "status": "success",
            "message": f"{len(organization_ids)}개 기관 보강이 시작되었습니다.",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 일괄 보강 실패: {e}")
        raise HTTPException(status_code=500, detail=f"일괄 보강 실패: {str(e)}")

@app.post("/api/enrichment/auto", tags=["연락처 보강"])
async def start_auto_enrichment(limit: int = Query(100, ge=1, le=500)):
    """자동 보강 시작 (누락 기관 자동 탐지)"""
    try:
        if ContactEnrichmentService is None:
            raise HTTPException(status_code=501, detail="연락처 보강 서비스가 구현되지 않았습니다.")
            
        enrichment_service = ContactEnrichmentService()
        
        # 자동 보강 시작
        result = await enrichment_service.start_auto_enrichment(limit=limit)
        
        return {
            "status": "success",
            "message": f"자동 보강이 시작되었습니다. (최대 {limit}개 기관)",
            "job_id": result.get("job_id"),
            "estimated_time": result.get("estimated_time")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 자동 보강 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자동 보강 시작 실패: {str(e)}")

# ==================== 활동 로그 API ====================

@app.get("/api/organizations/{org_id}/activities", tags=["활동"])
async def get_organization_activities(
    org_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """기관별 활동 이력 조회"""
    try:
        db = get_database()
        
        # 기관 존재 확인
        org = db.get_organization_detail(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 활동 이력 조회 (구현 필요)
        # activities = db.get_organization_activities(org_id, page, per_page)
        
        return {
            "status": "success",
            "activities": [],  # 임시
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": 0,
                "total_pages": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 활동 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"활동 이력 조회 실패: {str(e)}")

@app.post("/api/organizations/{org_id}/activities", tags=["활동"])
async def create_activity(org_id: int, activity: dict):
    """새 활동 기록 생성"""
    try:
        db = get_database()
        
        # 기관 존재 확인
        org = db.get_organization_detail(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 필수 필드 검증
        required_fields = ['activity_type', 'subject']
        for field in required_fields:
            if not activity.get(field):
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 활동 데이터 설정
        activity['organization_id'] = org_id
        activity.setdefault('created_by', 'system')
        
        activity_id = db.add_contact_activity(activity)
        
        return {
            "status": "success",
            "message": "활동이 성공적으로 기록되었습니다.",
            "activity_id": activity_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 활동 기록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"활동 기록 실패: {str(e)}")

# 예외 처리 핸들러
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 에러 처리"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "API 엔드포인트를 찾을 수 없습니다.", "path": request.url.path}
        )
    else:
        return templates.TemplateResponse("html/404.html", {
            "request": request,
            "title": "페이지를 찾을 수 없습니다."
        })

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500 에러 처리"""
    logger.error(f"❌ 내부 서버 오류: {exc}")
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "내부 서버 오류", "detail": str(exc)}
        )
    else:
        return templates.TemplateResponse("html/500.html", {
            "request": request,
            "title": "서버 오류",
            "error": str(exc)
        })

# 개발 서버 실행
if __name__ == "__main__":
    print("🚀 CRM 애플리케이션 시작")
    print("=" * 60)
    print("📋 주요 기능:")
    print("  - 기관 정보 CRUD 관리")
    print("  - 자동 연락처 보강 (크롤링)")
    print("  - 통계 및 분석 대시보드")
    print("  - RESTful API 제공")
    print("=" * 60)
    print("🌐 접속 URL:")
    print("  - 메인 페이지: http://localhost:8000")
    print("  - API 문서: http://localhost:8000/docs")
    print("  - 대시보드: http://localhost:8000/dashboard")
    print("  - 기관 관리: http://localhost:8000/organizations")
    print("  - 연락처 보강: http://localhost:8000/enrichment")
    print("=" * 60)
    
    uvicorn.run(
        "crm_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
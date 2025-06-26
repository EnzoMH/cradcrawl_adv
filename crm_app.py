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
    from api.statistics_api import router as statistics_router
except ImportError:
    # API 라우터가 없는 경우 None으로 설정
    organization_router = None
    enrichment_router = None
    statistics_router = None

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
logger = LoggerUtils.setup_logger(name="crm_app", file_logging=False)

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
if statistics_router:
    app.include_router(statistics_router)

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
async def get_enrichment_candidates(
    limit: int = Query(20, ge=1, le=100, description="최대 조회 수"),
    priority: Optional[str] = Query(None, description="우선순위 필터 (HIGH/MEDIUM/LOW)")
):
    """보강 후보 기관 목록 조회"""
    try:
        logger.info(f"📋 보강 후보 조회 요청 시작: limit={limit}, priority={priority}")
        
        # 1단계: OrganizationService 초기화 확인
        try:
            org_service = OrganizationService()
            logger.info("✅ OrganizationService 초기화 성공")
        except Exception as init_error:
            logger.error(f"❌ OrganizationService 초기화 실패: {init_error}")
            raise HTTPException(status_code=500, detail=f"서비스 초기화 실패: {str(init_error)}")
        
        # 2단계: 데이터베이스 연결 확인
        try:
            candidates = org_service.get_enrichment_candidates(priority=priority, limit=limit)
            logger.info(f"✅ 보강 후보 조회 성공: {len(candidates)}개 발견")
        except Exception as db_error:
            logger.error(f"❌ 데이터베이스 조회 실패: {db_error}")
            logger.error(f"❌ 에러 타입: {type(db_error)}")
            import traceback
            logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 조회 실패: {str(db_error)}")
        
        return {
            "status": "success",
            "count": len(candidates),
            "candidates": candidates,
            "summary": {
                "total_candidates": len(candidates),
                "priority_filter": priority,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        logger.error(f"❌ 에러 타입: {type(e)}")
        import traceback
        logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 내부 오류: {str(e)}"
        )
        
@app.get("/statistics", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def statistics_page(request: Request):
    """통계 분석 페이지"""
    try:
        # 기본 통계 정보 조회
        db = get_database()
        dashboard_stats = db.get_dashboard_stats()
        
        org_service = OrganizationService()
        contact_stats = org_service.get_contact_statistics()
        
        return templates.TemplateResponse("html/statistics.html", {
            "request": request,
            "dashboard_stats": dashboard_stats,
            "contact_stats": contact_stats,
            "title": "통계 분석"
        })
        
    except Exception as e:
        logger.error(f"❌ 통계 페이지 로드 실패: {e}")
        return templates.TemplateResponse("html/statistics.html", {
            "request": request,
            "error": "통계 데이터 로드 중 오류가 발생했습니다.",
            "title": "통계 분석"
        })

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
        enrichment_service = ContactEnrichmentService()
        
        # 기관 존재 확인
        db = get_database()
        org = db.get_organization_detail(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        # 보강 실행
        result = await enrichment_service.enrich_organization_by_id(org_id)
        
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
        results = await enrichment_service.enrich_organizations_by_ids(organization_ids)
        
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
        
        # 자동 보강 시작 - 메서드명 확인
        if hasattr(enrichment_service, 'start_auto_enrichment'):
            result = await enrichment_service.start_auto_enrichment(limit=limit)
        else:
            # 대안 메서드 사용
            result = await enrichment_service.auto_enrich_missing_contacts(limit=limit)
            result["job_id"] = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result["estimated_time"] = limit * 2
        
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
        
    except Exception as e:
        logger.error(f"❌ 활동 기록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"활동 기록 실패: {str(e)}")

@app.get("/api/real-time-results", tags=["통계"])
async def get_real_time_results(limit: int = Query(5, ge=1, le=20, description="최대 조회 수")):
    """실시간 결과 조회 - 최근 업데이트된 기관들"""
    try:
        # 최근 업데이트된 기관들 조회
        with get_database().get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, category, phone, email, updated_at
                FROM organizations 
                WHERE is_active = 1 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                org_id, name, category, phone, email, updated_at = row
                results.append({
                    "id": org_id,
                    "name": name,
                    "category": category,
                    "phone": phone,
                    "email": email,
                    "updated_at": updated_at,
                    "has_complete_contact": bool(phone and email)
                })
        
        return {
            "status": "success",
            "data": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 실시간 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실시간 결과 조회 실패: {str(e)}")

# ==================== 추가 통계 API 엔드포인트 ====================

@app.get("/api/statistics/overview", tags=["통계"])
async def get_statistics_overview():
    """통계 분석 개요"""
    try:
        from api.statistics_api import analyzer
        
        contact_analysis = analyzer.analyze_contact_data()
        
        return {
            "status": "success",
            "data": {
                "basic_stats": contact_analysis.get("basic_stats", {}),
                "contact_coverage": contact_analysis.get("contact_coverage", {}),
                "quality_metrics": contact_analysis.get("quality_metrics", {}),
                "top_categories": dict(list(contact_analysis.get("category_breakdown", {}).items())[:5])
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 통계 개요 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 개요 조회 실패: {str(e)}")

@app.get("/api/statistics/contact-analysis", tags=["통계"])
async def get_contact_analysis():
    """연락처 분석"""
    try:
        from api.statistics_api import analyzer
        
        analysis = analyzer.analyze_contact_data()
        
        return {
            "status": "success",
            "data": analysis
        }
        
    except Exception as e:
        logger.error(f"❌ 연락처 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"연락처 분석 실패: {str(e)}")

@app.get("/api/statistics/geographic-distribution", tags=["통계"])
async def get_geographic_distribution():
    """지역별 분포 분석"""
    try:
        from api.statistics_api import analyzer
        
        distribution = analyzer.analyze_geographic_distribution()
        
        return {
            "status": "success",
            "data": distribution
        }
        
    except Exception as e:
        logger.error(f"❌ 지역 분포 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"지역 분포 분석 실패: {str(e)}")

@app.get("/api/statistics/email-analysis", tags=["통계"])
async def get_email_analysis():
    """이메일 분석"""
    try:
        from api.statistics_api import analyzer
        
        analysis = analyzer.analyze_email_data()
        
        return {
            "status": "success",
            "data": analysis
        }
        
    except Exception as e:
        logger.error(f"❌ 이메일 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이메일 분석 실패: {str(e)}")

@app.get("/api/statistics/category-breakdown", tags=["통계"])
async def get_category_breakdown():
    """카테고리별 분석"""
    try:
        from api.statistics_api import analyzer
        
        contact_analysis = analyzer.analyze_contact_data()
        category_breakdown = contact_analysis.get("category_breakdown", {})
        
        return {
            "status": "success",
            "data": category_breakdown
        }
        
    except Exception as e:
        logger.error(f"❌ 카테고리 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"카테고리 분석 실패: {str(e)}")

@app.get("/api/statistics/quality-report", tags=["통계"])
async def get_quality_report():
    """데이터 품질 리포트"""
    try:
        from api.statistics_api import analyzer
        
        report = analyzer.generate_quality_report()
        
        return {
            "status": "success",
            "data": report
        }
        
    except Exception as e:
        logger.error(f"❌ 품질 리포트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"품질 리포트 생성 실패: {str(e)}")

@app.get("/api/statistics/enrichment-trends", tags=["통계"])
async def get_enrichment_trends(days: int = Query(30, ge=1, le=365)):
    """보강 트렌드 분석"""
    try:
        # 간단한 트렌드 분석 (실제 구현)
        db = get_database()
        
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    DATE(updated_at) as date,
                    COUNT(*) as updates_count
                FROM organizations 
                WHERE updated_at >= date('now', '-{} days')
                AND is_active = 1
                GROUP BY DATE(updated_at)
                ORDER BY date DESC
            """.format(days))
            
            trends = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return {
            "status": "success",
            "data": {
                "trends": trends,
                "period_days": days,
                "total_updates": sum(t["count"] for t in trends)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 보강 트렌드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보강 트렌드 분석 실패: {str(e)}")

@app.get("/api/statistics/field-completion-rates", tags=["통계"])
async def get_field_completion_rates():
    """필드별 완성도 분석"""
    try:
        org_service = OrganizationService()
        contact_stats = org_service.get_contact_statistics()
        
        field_stats = contact_stats.get("field_statistics", {})
        
        # 완성도 비율 계산
        completion_rates = {}
        for field, stats in field_stats.items():
            total = stats.get("filled", 0) + stats.get("empty", 0)
            if total > 0:
                completion_rates[field] = {
                    "completion_rate": (stats.get("filled", 0) / total) * 100,
                    "filled_count": stats.get("filled", 0),
                    "empty_count": stats.get("empty", 0),
                    "total_count": total
                }
        
        return {
            "status": "success",
            "data": completion_rates
        }
        
    except Exception as e:
        logger.error(f"❌ 필드 완성도 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"필드 완성도 분석 실패: {str(e)}")

@app.get("/api/statistics/recent-activities", tags=["통계"])
async def get_recent_activities(limit: int = Query(10, ge=1, le=50)):
    """최근 활동 내역"""
    try:
        db = get_database()
        
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    o.name as organization_name,
                    ca.activity_type,
                    ca.subject,
                    ca.created_at,
                    ca.created_by
                FROM contact_activities ca
                JOIN organizations o ON ca.organization_id = o.id
                WHERE o.is_active = 1
                ORDER BY ca.created_at DESC
                LIMIT ?
            """, (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "organization_name": row[0],
                    "activity_type": row[1],
                    "subject": row[2],
                    "created_at": row[3],
                    "created_by": row[4]
                })
        
        return {
            "status": "success",
            "data": activities
        }
        
    except Exception as e:
        logger.error(f"❌ 최근 활동 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"최근 활동 조회 실패: {str(e)}")

@app.get("/api/statistics/performance-metrics", tags=["통계"])
async def get_performance_metrics():
    """성과 지표"""
    try:
        db = get_database()
        org_service = OrganizationService()
        
        # 기본 통계
        dashboard_stats = db.get_dashboard_stats()
        contact_stats = org_service.get_contact_statistics()
        
        # 성과 지표 계산
        total_orgs = dashboard_stats.get("total_organizations", 0)
        complete_orgs = contact_stats.get("complete_organizations", 0)
        
        metrics = {
            "total_organizations": total_orgs,
            "complete_organizations": complete_orgs,
            "completion_rate": (complete_orgs / total_orgs * 100) if total_orgs > 0 else 0,
            "organizations_needing_enrichment": total_orgs - complete_orgs,
            "data_quality_score": contact_stats.get("overall_completion_rate", 0),
            "recent_updates_count": dashboard_stats.get("recent_activities", 0)
        }
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"❌ 성과 지표 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성과 지표 조회 실패: {str(e)}")

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
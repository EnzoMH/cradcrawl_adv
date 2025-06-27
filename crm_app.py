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

# ==================== 웹 인터페이스 라우트 ====================

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

@app.get("/login", response_class=HTMLResponse, tags=["웹 인터페이스"])
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("html/login.html", {
        "request": request,
        "title": "로그인"
    })

# ==================== 시스템 및 인증 API ====================

@app.post("/login", tags=["인증"])
async def login(request: Request):
    """로그인 처리 (임시)"""
    try:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # 임시 인증 로직 (실제로는 데이터베이스 확인 필요)
        if username == "admin" and password == "admin":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "로그인 성공",
                    "user": {"username": username, "role": "admin"}
                }
            )
        else:
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": "잘못된 사용자명 또는 비밀번호"}
            )
            
    except Exception as e:
        logger.error(f"❌ 로그인 처리 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "로그인 처리 중 오류가 발생했습니다."}
        )

@app.get("/health", tags=["시스템"])
async def health_check():
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        db = get_database()
        stats = db.get_dashboard_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_organizations": stats.get("total_organizations", 0),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"❌ 헬스체크 실패: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# ==================== 하위 호환성을 위한 기본 API ====================

@app.get("/api/stats/summary", tags=["호환성"])
async def get_summary_stats():
    """요약 통계 API (하위 호환성)"""
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

# ==================== 에러 핸들러 ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 에러 핸들러"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "API 엔드포인트를 찾을 수 없습니다.", "path": request.url.path}
        )
    else:
        return templates.TemplateResponse("html/404.html", {
            "request": request,
            "title": "페이지를 찾을 수 없습니다"
        })

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500 에러 핸들러"""
    logger.error(f"❌ 서버 내부 오류: {exc}")
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "서버 내부 오류가 발생했습니다.", "detail": str(exc)}
        )
    else:
        return templates.TemplateResponse("html/500.html", {
            "request": request,
            "title": "서버 오류",
            "error": str(exc)
        })

# ==================== 메인 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "crm_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
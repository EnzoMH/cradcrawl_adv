#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 기반 크롤링 제어 시스템 - DB 기반
FastAPI + SQLite를 활용한 크롤링 결과 관리
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
import threading
import logging
from datetime import datetime
from typing import Optional
import uvicorn

import os
from dotenv import load_dotenv
load_dotenv()
print(f"🔑 .env 로드 완료: GEMINI_API_KEY={'설정됨' if os.getenv('GEMINI_API_KEY') else '없음'}")

# 필요한 모듈들
from crawler_main import UnifiedCrawler
# from legacy.data_statistics import DataStatisticsAnalyzer
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from database.database import get_database

# 전역 변수
db = get_database()  # ✅ DB 인스턴스 초기화
current_crawling_job_id: Optional[int] = None
extractor_instance = None
total_organizations = []
current_data_file = None
logger = LoggerUtils.setup_app_logger()

app = FastAPI(title="DB 기반 크롤링 시스템", version="2.0.0")

# 정적 파일 및 템플릿 설정
app.mount("/static/css", StaticFiles(directory="templates/css"), name="css")
app.mount("/static/js", StaticFiles(directory="templates/js"), name="js")
templates = Jinja2Templates(directory="templates/html")

if os.path.exists("static"):
    app.mount("/static/files", StaticFiles(directory="static"), name="files")

# progress_callback 함수
def progress_callback(result: dict):
    """DB 기반 진행 상황 콜백 함수"""
    global current_crawling_job_id
    
    if not current_crawling_job_id:
        logger.error("크롤링 작업 ID가 없습니다.")
        return
    
    try:
        # DB에 결과 저장
        result_data = {
            'job_id': current_crawling_job_id,
            'organization_name': result.get('name', ''),
            'category': result.get('category', ''),
            'homepage_url': result.get('homepage_url', ''),
            'status': result.get('status', 'PROCESSING'),
            'current_step': result.get('current_step', ''),
            'processing_time': result.get('processing_time', 0),
            'extraction_method': result.get('extraction_method', ''),
            'phone': result.get('phone', ''),
            'fax': result.get('fax', ''),
            'email': result.get('email', ''),
            'mobile': result.get('mobile', ''),
            'address': result.get('address', ''),
            'crawling_details': {
                'homepage_parsed': result.get('homepage_parsed'),
                'ai_summary': result.get('ai_summary'),
                'meta_info': result.get('meta_info'),
                'contact_info_extracted': result.get('contact_info_extracted')
            },
            'error_message': result.get('error_message', '')
        }
        
        db.add_crawling_result(result_data)
        
        # 작업 진행 상황 업데이트
        if result.get('status') == 'completed':
            progress = db.get_crawling_progress(current_crawling_job_id)
            completed_count = progress['processed_count'] + 1
            
            db.update_crawling_job(current_crawling_job_id, {
                'processed_count': completed_count
            })
        
        logger.info(f"DB 저장 완료: {result.get('name')} - {result.get('status')}")
        
    except Exception as e:
        logger.error(f"크롤링 결과 DB 저장 실패: {e}")

# 웹 페이지 라우트
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    logger.info("메인 페이지 요청")
    return templates.TemplateResponse("index.html", {"request": request})

# API 엔드포인트들
@app.post("/api/start-enhanced-crawling")
async def start_enhanced_crawling(request: Request):
    """DB 기반 Enhanced 크롤링 시작"""
    global extractor_instance, total_organizations, current_crawling_job_id, current_data_file
    
    try:
        config_data = await request.json()
    except:
        config_data = {"test_mode": False, "test_count": 10, "use_ai": True}
    
    logger.info(f"Enhanced 크롤링 시작 요청: {config_data}")
    
    try:
        # 121-128 라인 수정
        if os.path.exists("data/json/merged_church_data_20250618_174032.json"):
            current_data_file = "data/json/merged_church_data_20250618_174032.json"
            data = FileUtils.load_json(current_data_file)
        elif os.path.exists("raw_data_0530.json"):
            current_data_file = "raw_data_0530.json"
            data = FileUtils.load_json(current_data_file)
        elif os.path.exists("raw_data.json"):
            current_data_file = "raw_data.json"
            data = FileUtils.load_json(current_data_file)
        else:
            raise HTTPException(status_code=404, detail="데이터 파일을 찾을 수 없습니다.")
        
        # 데이터 처리
        total_organizations = []
        if isinstance(data, dict):
            for category, orgs in data.items():
                if isinstance(orgs, list):
                    for org in orgs:
                        if isinstance(org, dict):
                            org["category"] = category
                            total_organizations.append(org)
        elif isinstance(data, list):
            total_organizations = [org for org in data if isinstance(org, dict)]
        
        # DB에 크롤링 작업 생성
        job_data = {
            'job_name': f"Enhanced Crawling {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'total_count': config_data.get('test_count', 10) if config_data.get('test_mode', False) else len(total_organizations),
            'started_by': 'SYSTEM',
            'config': config_data
        }
        
        current_crawling_job_id = db.create_crawling_job(job_data)
        logger.info(f"크롤링 작업 생성: ID {current_crawling_job_id}")
        
        # Enhanced Detail Extractor 인스턴스 생성
        api_key = os.getenv('GEMINI_API_KEY') if config_data.get('use_ai', True) else None
        extractor_instance = UnifiedCrawler(
            api_key=api_key, 
            progress_callback=progress_callback
        )
        
        # 백그라운드 실행
        threading.Thread(target=run_enhanced_crawling_db, args=(config_data,), daemon=True).start()
        
        return {
            "message": "Enhanced 크롤링이 시작되었습니다.", 
            "job_id": current_crawling_job_id,
            "total_count": job_data['total_count']
        }
        
    except Exception as e:
        logger.error(f"Enhanced 크롤링 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")

def run_enhanced_crawling_db(config_data: dict):
    """DB 기반 크롤링 실행"""
    global current_crawling_job_id, extractor_instance, current_data_file
    
    logger.info(f"DB 기반 Enhanced 크롤링 시작: Job ID {current_crawling_job_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        test_mode = config_data.get('test_mode', False)
        test_count = config_data.get('test_count', 10)
        
        # 크롤링 실행
        results = loop.run_until_complete(
            extractor_instance.process_json_file_async(
                json_file_path=current_data_file,
                test_mode=test_mode,
                test_count=test_count
            )
        )
        
        # 작업 완료 처리
        db.update_crawling_job(current_crawling_job_id, {
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info(f"크롤링 완료: Job ID {current_crawling_job_id}")
        
    except Exception as e:
        logger.error(f"크롤링 실행 실패: {e}")
        
        if current_crawling_job_id:
            db.update_crawling_job(current_crawling_job_id, {
                'status': 'ERROR',
                'error_message': str(e),
                'completed_at': datetime.now().isoformat()
            })

@app.get("/api/progress")
async def get_progress():
    """DB 기반 크롤링 진행 상황 조회"""
    if not current_crawling_job_id:
        return {"status": "idle", "message": "진행 중인 크롤링이 없습니다."}
    
    try:
        progress = db.get_crawling_progress(current_crawling_job_id)
        return progress
    except Exception as e:
        logger.error(f"진행 상황 조회 실패: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/real-time-results")
async def get_real_time_results(limit: int = 10):
    """DB 기반 실시간 크롤링 결과 조회"""
    if not current_crawling_job_id:
        return {"results": [], "total_count": 0}
    
    try:
        results = db.get_crawling_results(current_crawling_job_id, limit)
        progress = db.get_crawling_progress(current_crawling_job_id)
        
        return {
            "results": results,
            "total_count": progress.get('processed_count', 0),
            "progress": progress
        }
    except Exception as e:
        logger.error(f"실시간 결과 조회 실패: {e}")
        return {"results": [], "total_count": 0, "error": str(e)}

@app.get("/api/all-real-time-results")
async def get_all_real_time_results():
    """DB 기반 모든 크롤링 결과 조회"""
    if not current_crawling_job_id:
        return {"results": [], "total_count": 0}
    
    try:
        results = db.get_crawling_results(current_crawling_job_id, limit=10000)
        progress = db.get_crawling_progress(current_crawling_job_id)
        
        completed_count = len([r for r in results if r['status'] == 'COMPLETED'])
        failed_count = len([r for r in results if r['status'] == 'FAILED'])
        
        return {
            "results": results,
            "total_count": len(results),
            "completed_count": completed_count,
            "failed_count": failed_count,
            "progress": progress
        }
    except Exception as e:
        logger.error(f"전체 결과 조회 실패: {e}")
        return {"results": [], "total_count": 0, "error": str(e)}

@app.get("/api/results")
async def get_results():
    """DB에서 크롤링 결과 조회"""
    job = db.get_latest_crawling_job()
    if not job:
        return {"results": [], "count": 0}
    
    results = db.get_crawling_results(job['id'], limit=1000)
    return {"results": results, "count": len(results)}

# 기존 통계 API (유지)
@app.get('/api/statistics')
def get_statistics():
    """간단한 데이터 통계 API - DB 기반"""
    try:
        # DB에서 직접 통계 조회
        stats = db.get_dashboard_stats()
        
        return JSONResponse({
            'status': 'success',
            'data': {
                'total_organizations': stats['total_organizations'],
                'total_users': stats['total_users'],
                'recent_activities': stats['recent_activities'],
                'crawling_jobs': stats.get('crawling_jobs', 0),
                'analysis_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 통계 API 오류: {e}")
        return JSONResponse({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }, status_code=500)

# Organizations API 수정 (기존 코드 교체)
@app.get("/api/organizations")
async def get_organizations(
    page: int = 1,
    per_page: int = 50,  # 50개로 증가
    search: str = None,
    category: str = None,
    status: str = None
):
    """기관 목록 조회 (무한 스크롤용)"""
    try:
        filters = {}
        if category:
            filters['category'] = category
        if status:
            filters['contact_status'] = status
            
        result = db.get_organizations_paginated(
            page=page,
            per_page=per_page,
            search=search,
            filters=filters
        )
        
        return JSONResponse({
            "organizations": result["organizations"],
            "pagination": {
                "current_page": result["pagination"]["page"],
                "per_page": result["pagination"]["per_page"], 
                "total_count": result["pagination"]["total_count"],
                "total_pages": result["pagination"]["total_pages"],
                "has_next": result["pagination"]["page"] < result["pagination"]["total_pages"]
            }
        })
        
    except Exception as e:
        logger.error(f"기관 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/organizations/{org_id}")
async def get_organization_detail(org_id: int):
    """기관 상세 정보 조회"""
    try:
        organization = db.get_organization_detail(org_id)
        if not organization:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
        
        return {"organization": organization}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기관 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/organizations/{org_id}")
async def update_organization(org_id: int, request: Request):
    """기관 정보 업데이트"""
    try:
        updates = await request.json()
        success = db.update_organization(org_id, updates, updated_by="SYSTEM")
        
        if success:
            return {"message": "기관 정보가 업데이트되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기관 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/organizations/{org_id}")
async def delete_organization(org_id: int):
    """기관 삭제"""
    try:
        success = db.delete_organization(org_id)
        
        if success:
            return {"message": "기관이 삭제되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기관 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 필요한 디렉토리 생성
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates/html", exist_ok=True)
    os.makedirs("templates/css", exist_ok=True)
    os.makedirs("templates/js", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("=" * 80)
    print("🌐 DB 기반 크롤링 시스템 v2.0 시작")
    print("=" * 80)
    print("🤖 크롤링 기능:")
    print("  📄 Enhanced Detail Extractor")
    print("  📊 실시간 모니터링")
    print("  🗄️  SQLite DB 저장")
    print()
    print("🌍 접속 정보:")
    print("  📱 브라우저: http://localhost:8000")
    print("=" * 80)
    
    # 데이터베이스 상태 확인
    try:
        stats = db.get_dashboard_stats()
        print(f"✅ 데이터베이스 연결 확인: {stats['total_organizations']:,}개 기관")
    except Exception as e:
        print(f"⚠️  데이터베이스 연결 확인 실패: {e}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
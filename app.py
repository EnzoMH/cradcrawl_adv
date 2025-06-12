#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 기반 크롤링 제어 시스템
FastAPI + HTML/CSS/JS를 활용한 크롤링 결과 확인 및 제어
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn
from pydantic import BaseModel

import os
from dotenv import load_dotenv
load_dotenv()
print(f"🔑 .env 로드 완료: GEMINI_API_KEY={'설정됨' if os.getenv('GEMINI_API_KEY') else '없음'}")

# ✅ 수정: enhanced_detail_extractor 사용
from crawler_main import CrawlerMain
# 통계 분석은 기존 사용

from legacy.data_statistics import DataStatisticsAnalyzer

# ✅ 수정: 유틸리티 활용
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils

# 🆕 추가: 실시간 크롤링 결과 모델
class CrawlingResult(BaseModel):
    """실시간 크롤링 결과 모델"""
    name: str
    category: str = ""
    phone: str = ""
    fax: str = ""
    email: str = ""
    postal_code: str = ""
    address: str = ""
    homepage_url: str = ""
    status: str = "processing"  # processing, completed, failed
    processed_at: str = ""
    error_message: str = ""
    current_step: str = ""
    processing_time: str = ""
    extraction_method: str = ""

class CrawlingProgress(BaseModel):
    """크롤링 진행 상황 모델"""
    current_index: int
    total_count: int
    current_organization: str
    percentage: float
    latest_result: Optional[CrawlingResult] = None
    status: str = "idle"  # idle, running, completed, stopped, error

class CrawlingConfig(BaseModel):
    mode: str = "enhanced"  # "enhanced" 또는 "legacy"
    test_mode: bool = False
    test_count: int = 10
    use_ai: bool = True

# 로거 인스턴스 생성 (✅ 수정: LoggerUtils 활용)
logger = LoggerUtils.setup_app_logger()

app = FastAPI(title="향상된 크롤링 제어 시스템")

# 정적 파일 및 템플릿 설정
app.mount("/static/css", StaticFiles(directory="templates/css"), name="css")
app.mount("/static/js", StaticFiles(directory="templates/js"), name="js")
templates = Jinja2Templates(directory="templates/html")

# 기타 정적 파일들 (다운로드 파일 등)을 위한 static 디렉토리
if os.path.exists("static"):
    app.mount("/static/files", StaticFiles(directory="static"), name="files")

# 🔧 수정: 전역 변수 개선
extractor_instance = None  # Enhanced Detail Extractor 인스턴스
total_organizations = []
crawling_results = []  # 기존 결과 저장 (하위 호환성)
current_data_file = None  # 현재 사용 중인 데이터 파일

# 🆕 추가: 실시간 진행 상황 관리
crawling_progress = CrawlingProgress(
    current_index=0,
    total_count=0,
    current_organization="",
    percentage=0.0,
    status="idle"
)
real_time_results = []  # 실시간 결과 저장

# 기존 crawling_status (하위 호환성 유지)
crawling_status = {
    "is_running": False,
    "processed_count": 0,
    "total_count": 0,
    "current_organization": "",
    "extraction_mode": "enhanced"
}

def progress_callback(result: dict):
    """🆕 추가: 진행 상황 콜백 함수"""
    global crawling_progress, real_time_results, crawling_status
    
    try:
        # 실시간 결과에 추가
        crawling_result = CrawlingResult(**result)
        
        # 기존 결과가 있으면 업데이트, 없으면 추가
        existing_index = -1
        for i, existing_result in enumerate(real_time_results):
            if existing_result.name == crawling_result.name:
                existing_index = i
                break
        
        if existing_index >= 0:
            real_time_results[existing_index] = crawling_result
        else:
            real_time_results.append(crawling_result)
        
        # 완료된 기관만 카운트
        if result.get("status") == "completed":
            crawling_progress.current_index = len([r for r in real_time_results if r.status == "completed"])
        
        # 진행 상황 업데이트
        crawling_progress.current_organization = result.get("name", "")
        crawling_progress.percentage = (crawling_progress.current_index / crawling_progress.total_count) * 100 if crawling_progress.total_count > 0 else 0
        crawling_progress.latest_result = crawling_result
        
        # 기존 crawling_status도 업데이트 (하위 호환성)
        crawling_status["processed_count"] = crawling_progress.current_index
        crawling_status["current_organization"] = result.get("name", "")
        
        logger.info(f"실시간 업데이트: {result.get('name')} - {result.get('status')} - {result.get('current_step', '')}")
        
    except Exception as e:
        logger.error(f"진행 상황 콜백 오류: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    logger.info("메인 페이지 요청")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status")
async def get_status():
    """크롤링 상태 조회 (기존 호환성)"""
    logger.debug(f"상태 조회 요청: {crawling_status}")
    return crawling_status

@app.post("/api/start-enhanced-crawling")
async def start_enhanced_crawling(config: CrawlingConfig):
    """✅ 새로운: Enhanced Detail Extractor 크롤링 시작"""
    global extractor_instance, total_organizations, crawling_status, crawling_results, crawling_progress, real_time_results, current_data_file
    
    logger.info(f"Enhanced 크롤링 시작 요청: {config}")
    
    try:
        # ✅ 수정: 데이터 파일 로드
        logger.info("데이터 파일 로드 시작")
        
        # 파일 존재 확인 및 로드
        if os.path.exists("raw_data_0530.json"):
            current_data_file = "raw_data_0530.json"
            data = FileUtils.load_json(current_data_file)
        elif os.path.exists("raw_data.json"):
            current_data_file = "raw_data.json"
            data = FileUtils.load_json(current_data_file)
        else:
            raise HTTPException(status_code=404, detail="raw_data.json 또는 raw_data_0530.json 파일을 찾을 수 없습니다.")
        
        if not data:
            raise HTTPException(status_code=500, detail="데이터 파일을 읽을 수 없습니다.")
        
        logger.info(f"사용할 데이터 파일: {current_data_file}")
        
        # 🔧 핵심 수정: 데이터 구조 자동 감지 및 처리
        total_organizations = []
        
        if isinstance(data, dict):
            # Dictionary 구조: {"카테고리": [기관들]}
            logger.info(f"Dictionary 구조 데이터 처리: {len(data)}개 카테고리")
            for category, orgs in data.items():
                if isinstance(orgs, list):
                    for org in orgs:
                        if isinstance(org, dict):
                            org["category"] = category
                            total_organizations.append(org)
                        
        elif isinstance(data, list):
            # List 구조: [{"name": "기관", "category": "카테고리"}]
            logger.info(f"List 구조 데이터 처리: {len(data)}개 기관")
            total_organizations = [org for org in data if isinstance(org, dict)]
            
        else:
            raise ValueError("지원하지 않는 데이터 구조입니다. Dictionary 또는 List 형태여야 합니다.")
        
        logger.info(f"총 {len(total_organizations)}개 기관 로드 완료")
        
        # 🔧 수정: Enhanced Detail Extractor 인스턴스 생성 (콜백 포함)
        logger.info("Enhanced Detail Extractor 인스턴스 생성")
        api_key = os.getenv('GEMINI_API_KEY') if config.use_ai else None
        extractor_instance = CrawlerMain(
            api_key=api_key, 
            progress_callback=progress_callback  # 🆕 추가: 콜백 함수 전달
        )
        
        # 🔧 수정: 진행 상황 초기화
        real_time_results = []
        crawling_progress = CrawlingProgress(
            current_index=0,
            total_count=len(total_organizations),
            current_organization="",
            percentage=0.0,
            status="running"
        )
        
        # 상태 초기화 (기존 호환성)
        crawling_results = []
        crawling_status.update({
            "is_running": True,
            "processed_count": 0,
            "total_count": len(total_organizations),
            "current_organization": "",
            "extraction_mode": "enhanced"
        })
        
        logger.info(f"크롤링 상태 초기화 완료: 총 {len(total_organizations)}개 기관")
        
        # ✅ 수정: 백그라운드에서 Enhanced 크롤링 시작
        logger.info("백그라운드 Enhanced 크롤링 스레드 시작")
        threading.Thread(target=run_enhanced_crawling, args=(config,), daemon=True).start()
        
        logger.info("Enhanced 크롤링 시작 완료")
        return {
            "message": "Enhanced 크롤링이 시작되었습니다.", 
            "total_count": len(total_organizations),
            "mode": "enhanced",
            "ai_enabled": config.use_ai
        }
        
    except Exception as e:
        logger.error(f"Enhanced 크롤링 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")

def run_enhanced_crawling(config: CrawlingConfig):
    """✅ 새로운: Enhanced Detail Extractor 실행"""
    global crawling_status, total_organizations, crawling_results, extractor_instance, crawling_progress, current_data_file
    
    logger.info(f"Enhanced 크롤링 시작: 총기관수={len(total_organizations)}")
    
    try:
        # 비동기 실행을 위한 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 처리할 기관 수 결정
        process_count = config.test_count if config.test_mode else len(total_organizations)
        organizations_to_process = total_organizations[:process_count]
        
        # ✅ Enhanced Detail Extractor 비동기 실행
        results = loop.run_until_complete(
            extractor_instance.process_json_file_async(
                json_file_path=current_data_file,  # 🔧 수정: 실제 파일명 사용
                test_mode=config.test_mode,
                test_count=config.test_count
            )
        )
        
        if results:
            crawling_results = results
            
            # ✅ 결과 자동 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"enhanced_results_{timestamp}.json"
            excel_file = f"enhanced_report_{timestamp}.xlsx"
            
            # JSON 저장
            extractor_instance.save_merged_results_to_json(results, json_file)
            
            # Excel 저장
            extractor_instance.create_final_excel_report(results, excel_file)
            
            logger.info(f"Enhanced 크롤링 완료: {len(results)}개 결과 저장")
        
        # 크롤링 완료
        crawling_status["is_running"] = False
        crawling_status["current_organization"] = ""
        crawling_progress.status = "completed"
        
        logger.info("Enhanced 크롤링 완료")
        print("Enhanced 크롤링 완료")
        
    except Exception as e:
        logger.error(f"Enhanced 크롤링 중 오류: {e}")
        print(f"Enhanced 크롤링 중 오류: {e}")
        crawling_status["is_running"] = False
        crawling_status["current_organization"] = ""
        crawling_progress.status = "error"

# 🆕 추가: 실시간 진행 상황 API
@app.get("/api/progress")
async def get_progress():
    """실시간 크롤링 진행 상황 조회"""
    return crawling_progress

# 🆕 추가: 실시간 결과 API
@app.get("/api/real-time-results")
async def get_real_time_results(limit: int = 10):
    """실시간 크롤링 결과 조회 (최신 N개)"""
    return {
        "results": real_time_results[-limit:] if real_time_results else [],
        "total_count": len(real_time_results),
        "progress": crawling_progress
    }

# 🆕 추가: 전체 실시간 결과 조회
@app.get("/api/all-real-time-results")
async def get_all_real_time_results():
    """모든 실시간 크롤링 결과 조회"""
    return {
        "results": real_time_results,
        "total_count": len(real_time_results),
        "completed_count": len([r for r in real_time_results if r.status == "completed"]),
        "failed_count": len([r for r in real_time_results if r.status == "failed"]),
        "progress": crawling_progress
    }

# 🆕 추가: 특정 기관 결과 조회
@app.get("/api/result/{organization_name}")
async def get_organization_result(organization_name: str):
    """특정 기관의 크롤링 결과 조회"""
    for result in real_time_results:
        if result.name == organization_name:
            return result
    raise HTTPException(status_code=404, detail="기관을 찾을 수 없습니다.")

@app.post("/api/start-crawling")
async def start_crawling(config: CrawlingConfig):
    """기존 크롤링 (하위 호환성)"""
    # Enhanced 크롤링으로 리다이렉트
    return await start_enhanced_crawling(config)

@app.get("/api/results")
async def get_results():
    """실시간 크롤링 결과 조회"""
    global crawling_results
    logger.debug(f"실시간 결과 조회: {len(crawling_results)}개 항목")
    return {"results": crawling_results, "count": len(crawling_results)}

@app.get("/api/latest-result")
async def get_latest_result():
    """최신 크롤링 결과 1개 조회"""
    global crawling_results
    if crawling_results:
        latest = crawling_results[-1]
        logger.debug(f"최신 결과 조회: {latest.get('기관명', 'Unknown')}")
        return {"result": latest, "index": len(crawling_results) - 1}
    return {"result": None, "index": -1}

@app.post("/api/stop-crawling")
async def stop_crawling():
    """크롤링 중지"""
    global extractor_instance, crawling_status, crawling_progress
    
    logger.info("크롤링 중지 요청")
    crawling_status["is_running"] = False
    crawling_progress.status = "stopped"
    
    # Enhanced Detail Extractor는 별도 종료 로직 없음 (세션 기반)
    logger.info("크롤링 중지 완료")
    return {"message": "크롤링이 중지되었습니다."}

@app.get("/api/download-results")
async def download_results():
    """결과 파일 다운로드 링크 제공"""
    try:
        # ✅ 수정: Enhanced 결과 파일 찾기
        enhanced_files = [f for f in os.listdir(".") if f.startswith("enhanced_results_")]
        legacy_files = [f for f in os.listdir(".") if f.startswith("raw_data_with_contacts_")]
        
        result_files = enhanced_files + legacy_files
        
        if not result_files:
            raise HTTPException(status_code=404, detail="결과 파일을 찾을 수 없습니다.")
        
        latest_file = max(result_files, key=lambda x: os.path.getctime(x))
        return {"filename": latest_file, "download_url": f"/static/files/{latest_file}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 조회 실패: {str(e)}")

@app.get("/api/extractor-stats")
async def get_extractor_stats():
    """✅ 새로운: Enhanced Detail Extractor 통계 조회"""
    global extractor_instance
    
    if not extractor_instance:
        return {"error": "Extractor 인스턴스가 없습니다."}
    
    return {
        "stats": extractor_instance.stats,
        "ai_enabled": extractor_instance.use_ai,
        "total_processed": len(crawling_results),
        "real_time_count": len(real_time_results),
        "progress": crawling_progress
    }

# 기존 통계 API들은 그대로 유지...
@app.get('/api/statistics')
def get_statistics():
    """데이터 통계 API (기존 유지)"""
    try:
        analyzer = DataStatisticsAnalyzer()
        files = analyzer.find_latest_files()
        
        if not files['json'] and not files['excel']:
            return JSONResponse({
                'status': 'error',
                'message': '분석할 데이터 파일이 없습니다.'
            }, status_code=404)
        
        # JSON 데이터 분석
        json_stats = {}
        if files['json']:
            json_stats = analyzer.analyze_json_data(files['json'])
        
        # API용 요약 데이터 생성
        if json_stats:
            api_summary = analyzer.get_api_summary(json_stats)
            return JSONResponse({
                'status': 'success',
                'data': api_summary,
                'file_info': {
                    'json_file': files.get('json', ''),
                    'excel_file': files.get('excel', ''),
                    'analysis_time': datetime.now().isoformat()
                }
            })
        else:
            return JSONResponse({
                'status': 'error',
                'message': '데이터 분석에 실패했습니다.'
            }, status_code=500)
            
    except Exception as e:
        print(f"❌ 통계 API 오류: {e}")
        return JSONResponse({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }, status_code=500)

if __name__ == "__main__":
    # 필요한 디렉토리 생성
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates/html", exist_ok=True)
    os.makedirs("templates/css", exist_ok=True)
    os.makedirs("templates/js", exist_ok=True)
    os.makedirs("logs", exist_ok=True)  # ✅ 추가: 로그 디렉토리
    
    print("=" * 60)
    print("🌐 향상된 웹 크롤링 제어 시스템 시작")
    print("=" * 60)
    print("🌍 브라우저에서 http://localhost:8000 접속")
    print("🤖 Enhanced Detail Extractor 지원")
    print("📁 모듈화된 구조:")
    print("  📄 HTML: templates/html/")
    print("  🎨 CSS: templates/css/")
    print("  ⚡ JS: templates/js/")
    print("  📊 로그: logs/")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 
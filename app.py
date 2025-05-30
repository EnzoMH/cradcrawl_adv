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

# ✅ 수정: enhanced_detail_extractor 사용
from enhanced_detail_extractor import EnhancedDetailExtractor

# 통계 분석은 기존 사용
from legacy.data_statistics import DataStatisticsAnalyzer

# ✅ 수정: 유틸리티 활용
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils

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

# ✅ 수정: 전역 변수 개선
extractor_instance = None  # Enhanced Detail Extractor 인스턴스
total_organizations = []
crawling_results = []  # 실시간 결과 저장
crawling_status = {
    "is_running": False,
    "processed_count": 0,
    "total_count": 0,
    "current_organization": "",
    "extraction_mode": "enhanced"  # 새로운 모드 추가
}

class CrawlingConfig(BaseModel):
    mode: str = "enhanced"  # "enhanced" 또는 "legacy"
    test_mode: bool = False
    test_count: int = 10
    use_ai: bool = True

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    logger.info("메인 페이지 요청")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status")
async def get_status():
    """크롤링 상태 조회"""
    logger.debug(f"상태 조회 요청: {crawling_status}")
    return crawling_status

@app.post("/api/start-enhanced-crawling")
async def start_enhanced_crawling(config: CrawlingConfig):
    """✅ 새로운: Enhanced Detail Extractor 크롤링 시작"""
    global extractor_instance, total_organizations, crawling_status, crawling_results
    
    logger.info(f"Enhanced 크롤링 시작 요청: {config}")
    
    try:
        # ✅ 수정: FileUtils 활용하여 데이터 로드
        logger.info("데이터 파일 로드 시작")
        data = FileUtils.load_json("raw_data.json")
        if not data:
            raise HTTPException(status_code=404, detail="raw_data.json 파일을 찾을 수 없습니다.")
        
        logger.info(f"데이터 로드 완료: {len(data)}개 카테고리")
        
        # 모든 기관을 하나의 리스트로 변환
        total_organizations = []
        for category, orgs in data.items():
            for org in orgs:
                org["category"] = category
                total_organizations.append(org)
        logger.info(f"총 {len(total_organizations)}개 기관 로드 완료")
        
        # ✅ 수정: Enhanced Detail Extractor 인스턴스 생성
        logger.info("Enhanced Detail Extractor 인스턴스 생성")
        api_key = os.getenv('GEMINI_API_KEY') if config.use_ai else None
        extractor_instance = EnhancedDetailExtractor(api_key=api_key)
        
        # 상태 초기화
        crawling_results = []  # 결과 초기화
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
    global crawling_status, total_organizations, crawling_results, extractor_instance
    
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
                json_file_path="raw_data.json",
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
        
        logger.info("Enhanced 크롤링 완료")
        print("Enhanced 크롤링 완료")
        
    except Exception as e:
        logger.error(f"Enhanced 크롤링 중 오류: {e}")
        print(f"Enhanced 크롤링 중 오류: {e}")
        crawling_status["is_running"] = False
        crawling_status["current_organization"] = ""

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
    global extractor_instance, crawling_status
    
    logger.info("크롤링 중지 요청")
    crawling_status["is_running"] = False
    
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
        "total_processed": len(crawling_results)
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
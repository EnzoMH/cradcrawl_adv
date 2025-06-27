#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
크롤링 서비스
파일 기반 크롤링과 DB 기반 크롤링을 통합 관리
"""

import asyncio
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from database.database import get_database
from utils.file_utils import FileUtils
from utils.logger_utils import LoggerUtils

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

logger = LoggerUtils.setup_logger(name="crawling_service", file_logging=True)

@dataclass
class CrawlingJobConfig:
    """크롤링 작업 설정"""
    test_mode: bool = False
    test_count: int = 10
    use_ai: bool = True
    max_concurrent: int = 3
    job_name: Optional[str] = None
    started_by: str = "SYSTEM"

@dataclass
class CrawlingJobStatus:
    """크롤링 작업 상태"""
    job_id: Optional[int] = None
    status: str = "IDLE"  # IDLE, RUNNING, COMPLETED, ERROR
    total_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    data_file: Optional[str] = None

class CrawlingService:
    """크롤링 서비스 통합 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.db = get_database()
        self.logger = logger
        
        # 크롤링 상태 관리
        self.current_job: Optional[CrawlingJobStatus] = None
        self.extractor_instance = None
        self.total_organizations = []
        
        # 지원하는 데이터 파일 경로들
        self.data_file_paths = [
            "data/json/merged_church_data_20250618_174032.json",
            "raw_data_0530.json", 
            "raw_data.json"
        ]
    
    def find_data_file(self) -> Optional[str]:
        """사용 가능한 데이터 파일 찾기"""
        for file_path in self.data_file_paths:
            if os.path.exists(file_path):
                self.logger.info(f"✅ 데이터 파일 발견: {file_path}")
                return file_path
        
        self.logger.error("❌ 사용 가능한 데이터 파일이 없습니다.")
        return None
    
    def load_organizations_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """파일에서 조직 데이터 로드"""
        try:
            data = FileUtils.load_json(file_path)
            organizations = []
            
            if isinstance(data, dict):
                for category, orgs in data.items():
                    if isinstance(orgs, list):
                        for org in orgs:
                            if isinstance(org, dict):
                                org["category"] = category
                                organizations.append(org)
            elif isinstance(data, list):
                organizations = [org for org in data if isinstance(org, dict)]
            
            self.logger.info(f"✅ 조직 데이터 로드: {len(organizations)}개")
            return organizations
            
        except Exception as e:
            self.logger.error(f"❌ 조직 데이터 로드 실패: {e}")
            return []
    
    def create_crawling_job(self, config: CrawlingJobConfig, organizations: List[Dict]) -> int:
        """크롤링 작업 생성"""
        try:
            job_name = config.job_name or f"Crawling Job {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            total_count = config.test_count if config.test_mode else len(organizations)
            
            job_data = {
                'job_name': job_name,
                'total_count': total_count,
                'started_by': config.started_by,
                'config_data': json.dumps(config.__dict__)
            }
            
            job_id = self.db.create_crawling_job(job_data)
            self.logger.info(f"✅ 크롤링 작업 생성: ID {job_id}, 총 {total_count}개")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 작업 생성 실패: {e}")
            raise
    
    def create_progress_callback(self, job_id: int) -> Callable:
        """진행 상황 콜백 함수 생성"""
        def progress_callback(result: dict):
            """크롤링 진행 상황 콜백"""
            try:
                result_data = {
                    'job_id': job_id,
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
                    'crawling_details': json.dumps({
                        'homepage_parsed': result.get('homepage_parsed'),
                        'ai_summary': result.get('ai_summary'),
                        'meta_info': result.get('meta_info'),
                        'contact_info_extracted': result.get('contact_info_extracted')
                    }),
                    'error_message': result.get('error_message', '')
                }
                
                self.db.add_crawling_result(result_data)
                
                # 완료된 경우 진행률 업데이트
                if result.get('status') == 'COMPLETED':
                    progress = self.db.get_crawling_progress(job_id)
                    completed_count = progress.get('processed_count', 0) + 1
                    self.db.update_crawling_job(job_id, {
                        'processed_count': completed_count
                    })
                
                self.logger.debug(f"✅ 진행 상황 저장: {result.get('name')} - {result.get('status')}")
                
            except Exception as e:
                self.logger.error(f"❌ 진행 상황 저장 실패: {e}")
        
        return progress_callback
    
    async def start_file_crawling(self, config: CrawlingJobConfig) -> Dict[str, Any]:
        """파일 기반 크롤링 시작"""
        try:
            # 1. 데이터 파일 찾기
            data_file = self.find_data_file()
            if not data_file:
                raise ValueError("사용 가능한 데이터 파일이 없습니다.")
            
            # 2. 조직 데이터 로드
            organizations = self.load_organizations_from_file(data_file)
            if not organizations:
                raise ValueError("조직 데이터가 없습니다.")
            
            # 3. 크롤링 작업 생성
            job_id = self.create_crawling_job(config, organizations)
            
            # 4. 크롤링 상태 업데이트
            self.current_job = CrawlingJobStatus(
                job_id=job_id,
                status="RUNNING",
                total_count=config.test_count if config.test_mode else len(organizations),
                started_at=datetime.now().isoformat(),
                data_file=data_file
            )
            
            # 5. 크롤러 인스턴스 생성
            from crawler_main import AIEnhancedModularUnifiedCrawler
            api_key = os.getenv('GEMINI_API_KEY') if config.use_ai else None
            progress_callback = self.create_progress_callback(job_id)
            
            self.extractor_instance = AIEnhancedModularUnifiedCrawler(
                api_key=api_key,
                progress_callback=progress_callback
            )
            
            # 6. 백그라운드에서 크롤링 실행
            def run_crawling():
                """백그라운드 크롤링 실행"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 크롤링 실행
                    results = loop.run_until_complete(
                        self.extractor_instance.process_json_file_async(
                            json_file_path=data_file,
                            test_mode=config.test_mode,
                            test_count=config.test_count
                        )
                    )
                    
                    # 성공 완료
                    self.db.update_crawling_job(job_id, {
                        'status': 'COMPLETED',
                        'completed_at': datetime.now().isoformat()
                    })
                    
                    if self.current_job:
                        self.current_job.status = "COMPLETED"
                        self.current_job.completed_at = datetime.now().isoformat()
                    
                    self.logger.info(f"✅ 파일 기반 크롤링 완료: Job ID {job_id}")
                    
                except Exception as e:
                    # 오류 처리
                    self.logger.error(f"❌ 크롤링 실행 실패: {e}")
                    
                    self.db.update_crawling_job(job_id, {
                        'status': 'ERROR',
                        'error_message': str(e),
                        'completed_at': datetime.now().isoformat()
                    })
                    
                    if self.current_job:
                        self.current_job.status = "ERROR"
                        self.current_job.error_message = str(e)
                        self.current_job.completed_at = datetime.now().isoformat()
            
            # 백그라운드 스레드 시작
            threading.Thread(target=run_crawling, daemon=True).start()
            
            return {
                "status": "success",
                "message": "파일 기반 크롤링이 시작되었습니다.",
                "job_id": job_id,
                "total_count": self.current_job.total_count,
                "data_file": data_file,
                "config": config.__dict__
            }
            
        except Exception as e:
            self.logger.error(f"❌ 파일 기반 크롤링 시작 실패: {e}")
            raise
    
    async def start_db_crawling(self, config: CrawlingJobConfig) -> Dict[str, Any]:
        """DB 기반 크롤링 시작 (crawler_main.py 통합)"""
        try:
            from crawler_main import crawl_ai_enhanced_from_database
            
            # DB 크롤링 실행
            self.logger.info("🚀 DB 기반 크롤링 시작")
            
            # 백그라운드에서 실행
            def run_db_crawling():
                try:
                    # 새 이벤트 루프 생성 (백그라운드 스레드용)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # async 함수를 올바르게 실행
                    results = loop.run_until_complete(crawl_ai_enhanced_from_database())
                    self.logger.info(f"✅ DB 기반 크롤링 완료: {len(results)}개 처리")
                    
                    # 이벤트 루프 정리
                    loop.close()
                    
                except Exception as e:
                    self.logger.error(f"❌ DB 기반 크롤링 실패: {e}")
            
            threading.Thread(target=run_db_crawling, daemon=True).start()
            
            return {
                "status": "success",
                "message": "DB 기반 크롤링이 시작되었습니다.",
                "config": config.__dict__
            }
            
        except Exception as e:
            self.logger.error(f"❌ DB 기반 크롤링 시작 실패: {e}")
            raise
    
    def get_crawling_progress(self) -> Dict[str, Any]:
        """현재 크롤링 진행 상황 조회"""
        if not self.current_job or not self.current_job.job_id:
            return {
                "status": "idle",
                "message": "진행 중인 크롤링이 없습니다."
            }
        
        try:
            progress = self.db.get_crawling_progress(self.current_job.job_id)
            
            # 현재 작업 상태와 DB 상태 동기화
            if self.current_job:
                progress.update({
                    "current_job_status": self.current_job.status,
                    "data_file": self.current_job.data_file,
                    "started_at": self.current_job.started_at,
                    "completed_at": self.current_job.completed_at,
                    "error_message": self.current_job.error_message
                })
            
            return progress
            
        except Exception as e:
            self.logger.error(f"❌ 진행 상황 조회 실패: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_crawling_results(self, limit: int = 10, all_results: bool = False) -> Dict[str, Any]:
        """크롤링 결과 조회"""
        job_id = self.current_job.job_id if self.current_job else None
        
        if not job_id:
            return {"results": [], "total_count": 0}
        
        try:
            if all_results:
                results = self.db.get_crawling_results(job_id, limit=10000)
                progress = self.db.get_crawling_progress(job_id)
                
                completed_count = len([r for r in results if r['status'] == 'COMPLETED'])
                failed_count = len([r for r in results if r['status'] == 'FAILED'])
                
                return {
                    "results": results,
                    "total_count": len(results),
                    "completed_count": completed_count,
                    "failed_count": failed_count,
                    "progress": progress
                }
            else:
                results = self.db.get_crawling_results(job_id, limit)
                progress = self.db.get_crawling_progress(job_id)
                
                return {
                    "results": results,
                    "total_count": progress.get('processed_count', 0),
                    "progress": progress
                }
                
        except Exception as e:
            self.logger.error(f"❌ 크롤링 결과 조회 실패: {e}")
            return {"results": [], "total_count": 0, "error": str(e)}
    
    def get_latest_crawling_results(self) -> Dict[str, Any]:
        """최신 크롤링 작업 결과 조회"""
        try:
            job = self.db.get_latest_crawling_job()
            if not job:
                return {"results": [], "count": 0}
            
            results = self.db.get_crawling_results(job['id'], limit=1000)
            return {
                "results": results,
                "count": len(results),
                "job_info": job
            }
            
        except Exception as e:
            self.logger.error(f"❌ 최신 크롤링 결과 조회 실패: {e}")
            return {"results": [], "count": 0, "error": str(e)}
    
    def stop_crawling(self) -> Dict[str, Any]:
        """크롤링 중지"""
        if not self.current_job or self.current_job.status != "RUNNING":
            return {"status": "error", "message": "중지할 크롤링이 없습니다."}
        
        try:
            # 크롤링 상태 업데이트
            if self.current_job.job_id:
                self.db.update_crawling_job(self.current_job.job_id, {
                    'status': 'STOPPED',
                    'completed_at': datetime.now().isoformat()
                })
            
            self.current_job.status = "STOPPED"
            self.current_job.completed_at = datetime.now().isoformat()
            
            self.logger.info(f"⏹️ 크롤링 중지: Job ID {self.current_job.job_id}")
            
            return {
                "status": "success",
                "message": "크롤링이 중지되었습니다."
            }
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 중지 실패: {e}")
            return {"status": "error", "message": str(e)}

# 싱글톤 인스턴스
_crawling_service_instance = None

def get_crawling_service() -> CrawlingService:
    """크롤링 서비스 인스턴스 반환 (싱글톤)"""
    global _crawling_service_instance
    if _crawling_service_instance is None:
        _crawling_service_instance = CrawlingService()
    return _crawling_service_instance 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CenterCrawlingBot과 AI 에이전트 시스템 통합 레이어
기존 시스템의 안정성과 새로운 AI 기능을 결합

주요 기능:
1. 기존 CenterCrawlingBot 클래스 확장
2. AI 에이전트 시스템 통합
3. 하이브리드 크롤링 (기존 방식 + AI 검증)
4. 점진적 업그레이드 지원
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json

# 기존 시스템 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from centercrawling import CenterCrawlingBot
from database.database import ChurchCRMDatabase
from database.models import Organization, CrawlingJob

# AI 에이전트 시스템 import
from aiagent.core.enhanced_agent_system import (
    EnhancedAIAgentSystem, 
    CrawlingResult, 
    SearchStrategyAgent, 
    ValidationAgent,
    ResourceManager,
    DataQualityGrade
)


class IntegratedCrawlingBot(CenterCrawlingBot):
    """통합 크롤링 봇 - 기존 시스템 + AI 에이전트"""
    
    def __init__(self, excel_path: str = None, use_ai: bool = True, send_email: bool = True, 
                 use_database: bool = True, integration_mode: str = "hybrid"):
        """
        초기화
        
        Args:
            excel_path: 엑셀 파일 경로 (선택사항)
            use_ai: AI 기능 사용 여부
            send_email: 이메일 전송 여부
            use_database: 데이터베이스 직접 사용 여부
            integration_mode: 통합 모드 ('hybrid', 'ai_only', 'legacy_only')
        """
        self.use_database = use_database
        self.integration_mode = integration_mode
        
        # 데이터베이스 연결
        if use_database:
            self.db = ChurchCRMDatabase()
            self.logger = logging.getLogger("IntegratedCrawlingBot")
        
        # AI 에이전트 시스템 초기화
        if use_ai and integration_mode in ['hybrid', 'ai_only']:
            self.ai_agent_system = EnhancedAIAgentSystem()
        else:
            self.ai_agent_system = None
        
        # 기존 시스템 초기화 (excel_path가 있는 경우만)
        if excel_path and integration_mode in ['hybrid', 'legacy_only']:
            super().__init__(excel_path, use_ai, send_email)
        else:
            # 기본 초기화
            self.use_ai = use_ai
            self.send_email = send_email
            self.logger = logging.getLogger("IntegratedCrawlingBot")
            
            # 환경 변수 로드
            from dotenv import load_dotenv
            load_dotenv()
            
            # AI 모델 초기화
            if use_ai:
                self._initialize_ai()
            
            # WebDriver 초기화
            self.driver = None
            self._initialize_webdriver()
            
            # 결과 저장용
            self.results = []
            self.processed_count = 0
            self.success_count = 0
            self.start_time = datetime.now()
        
        self.logger.info(f"🚀 통합 크롤링 봇 초기화 완료 (모드: {integration_mode})")
    
    def run_database_crawling(self, batch_size: int = 50, max_workers: int = None) -> Dict[str, Any]:
        """데이터베이스 기반 크롤링 실행"""
        try:
            if not self.use_database:
                raise ValueError("데이터베이스 모드가 활성화되지 않았습니다.")
            
            self.logger.info("🎯 데이터베이스 기반 크롤링 시작")
            
            # 크롤링 작업 시작
            job_id = None
            if self.ai_agent_system:
                job_id = self.ai_agent_system.start_crawling_job(
                    "통합 크롤링 작업", "system"
                )
            
            # 크롤링 대상 조회
            organizations = self._get_organizations_to_crawl()
            total_count = len(organizations)
            
            if total_count == 0:
                self.logger.info("📋 크롤링할 기관이 없습니다.")
                return self._get_crawling_summary()
            
            self.logger.info(f"📊 총 {total_count}개 기관 크롤링 시작")
            
            # 배치 처리
            processed_count = 0
            success_count = 0
            
            for i in range(0, total_count, batch_size):
                batch = organizations[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                self.logger.info(f"📦 배치 {batch_num} 처리 시작 ({len(batch)}개)")
                
                # 배치 처리
                batch_results = self._process_organization_batch(batch)
                
                # 결과 집계
                processed_count += len(batch)
                success_count += len([r for r in batch_results if r])
                
                # 진행률 업데이트
                progress = (processed_count / total_count) * 100
                self.logger.info(f"📈 진행률: {progress:.1f}% ({processed_count}/{total_count})")
                
                # 중간 저장 및 통계 업데이트
                if job_id:
                    self._update_crawling_job_progress(job_id, processed_count, total_count)
                
                # 리소스 관리
                if self.ai_agent_system:
                    stats = self.ai_agent_system.resource_manager.get_system_stats()
                    if stats['memory_percent'] > 80:
                        self.logger.warning("⚠️ 메모리 사용률 높음, 잠시 대기...")
                        time.sleep(10)
            
            # 크롤링 완료
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            # 최종 통계
            final_stats = self._get_crawling_summary()
            final_stats.update({
                'total_processed': processed_count,
                'success_count': success_count,
                'duration': str(duration),
                'job_id': job_id
            })
            
            self.logger.info(f"🎉 데이터베이스 크롤링 완료: {duration}")
            
            # 이메일 전송
            if self.send_email:
                self._send_database_completion_email(final_stats)
            
            return final_stats
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 크롤링 실패: {e}")
            if self.send_email:
                self._send_error_email(str(e))
            raise
    
    def _get_organizations_to_crawl(self) -> List[Dict[str, Any]]:
        """크롤링할 기관 목록 조회"""
        try:
            # 우선순위 기반 쿼리
            query = """
                SELECT id, name, address, phone, fax, homepage, email, mobile,
                       contact_status, priority, last_crawled_at, ai_crawled
                FROM organizations 
                WHERE is_active = true
                AND (
                    ai_crawled = false 
                    OR last_crawled_at IS NULL 
                    OR last_crawled_at < NOW() - INTERVAL '30 days'
                    OR (phone IS NULL OR phone = '')
                    OR (fax IS NULL OR fax = '')
                    OR (homepage IS NULL OR homepage = '')
                    OR (email IS NULL OR email = '')
                )
                ORDER BY 
                    CASE priority 
                        WHEN 'HIGH' THEN 1 
                        WHEN 'MEDIUM' THEN 2 
                        WHEN 'LOW' THEN 3 
                        ELSE 4 
                    END,
                    last_crawled_at ASC NULLS FIRST,
                    id ASC
            """
            
            results = self.db.execute_query(query)
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 대상 조회 실패: {e}")
            return []
    
    def _process_organization_batch(self, batch: List[Dict[str, Any]]) -> List[Optional[CrawlingResult]]:
        """기관 배치 처리 - 하이브리드 모드"""
        results = []
        
        for org_data in batch:
            try:
                result = self._process_single_organization_hybrid(org_data)
                results.append(result)
                
                if result:
                    self.success_count += 1
                    self.logger.info(f"✅ 기관 처리 성공: {org_data['name']} (등급: {result.data_quality_grade})")
                else:
                    self.logger.warning(f"⚠️ 기관 처리 실패: {org_data['name']}")
                
                self.processed_count += 1
                
            except Exception as e:
                self.logger.error(f"❌ 기관 처리 오류: {org_data['name']} - {e}")
                results.append(None)
                continue
        
        return results
    
    def _process_single_organization_hybrid(self, org_data: Dict[str, Any]) -> Optional[CrawlingResult]:
        """단일 기관 하이브리드 처리"""
        try:
            name = org_data['name']
            address = org_data['address']
            
            if not name or not address:
                return None
            
            # 1단계: AI 에이전트 시스템 사용 (우선)
            if self.ai_agent_system and self.integration_mode in ['hybrid', 'ai_only']:
                ai_result = self.ai_agent_system.process_single_organization(org_data)
                
                if ai_result and ai_result.validation_score > 0.7:
                    self.logger.info(f"🤖 AI 에이전트 성공: {name} (점수: {ai_result.validation_score:.2f})")
                    return ai_result
            
            # 2단계: 기존 시스템 사용 (fallback)
            if self.integration_mode in ['hybrid', 'legacy_only']:
                legacy_result = self._process_with_legacy_system(org_data)
                
                if legacy_result:
                    self.logger.info(f"🔧 기존 시스템 성공: {name}")
                    return legacy_result
            
            # 3단계: 최소한의 결과라도 저장
            minimal_result = CrawlingResult(
                organization_id=org_data['id'],
                name=name,
                address=address,
                phone=org_data.get('phone', ''),
                fax=org_data.get('fax', ''),
                homepage=org_data.get('homepage', ''),
                email=org_data.get('email', ''),
                data_quality_grade=DataQualityGrade.F.value,
                crawling_source="minimal_update"
            )
            
            return minimal_result
            
        except Exception as e:
            self.logger.error(f"❌ 하이브리드 처리 오류: {org_data['name']} - {e}")
            return None
    
    def _process_with_legacy_system(self, org_data: Dict[str, Any]) -> Optional[CrawlingResult]:
        """기존 시스템으로 처리"""
        try:
            name = org_data['name']
            address = org_data['address']
            existing_phone = org_data.get('phone', '')
            
            # 기존 시스템의 검색 로직 활용
            found_data = {}
            
            # 팩스번호 검색
            if not org_data.get('fax'):
                fax_query = f"{name} 팩스번호"
                fax_result = self._search_with_multiple_engines(fax_query, name, 'fax')
                if fax_result:
                    found_data['fax'] = fax_result
            
            # 홈페이지 검색
            if not org_data.get('homepage'):
                homepage_query = f"{name} 홈페이지"
                homepage_result = self._search_for_homepage(homepage_query, name)
                if homepage_result:
                    found_data['homepage'] = homepage_result
            
            # 결과가 있으면 CrawlingResult 생성
            if found_data:
                result = CrawlingResult(
                    organization_id=org_data['id'],
                    name=name,
                    address=address,
                    phone=existing_phone,
                    fax=found_data.get('fax', ''),
                    homepage=found_data.get('homepage', ''),
                    crawling_source="legacy_system"
                )
                
                # 데이터베이스에 저장
                self._save_to_database(result)
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 기존 시스템 처리 오류: {org_data['name']} - {e}")
            return None
    
    def _save_to_database(self, result: CrawlingResult):
        """데이터베이스에 결과 저장"""
        try:
            update_query = """
                UPDATE organizations 
                SET phone = COALESCE(NULLIF(%(phone)s, ''), phone),
                    fax = COALESCE(NULLIF(%(fax)s, ''), fax),
                    homepage = COALESCE(NULLIF(%(homepage)s, ''), homepage),
                    email = COALESCE(NULLIF(%(email)s, ''), email),
                    mobile = COALESCE(NULLIF(%(mobile)s, ''), mobile),
                    ai_crawled = true,
                    last_crawled_at = %(crawled_at)s,
                    crawling_data = %(crawling_data)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(organization_id)s
            """
            
            crawling_data = {
                'data_quality_grade': result.data_quality_grade,
                'validation_score': result.validation_score,
                'crawling_source': result.crawling_source,
                'ai_confidence': result.ai_confidence,
                'processed_at': result.crawled_at.isoformat()
            }
            
            params = {
                'phone': result.phone,
                'fax': result.fax,
                'homepage': result.homepage,
                'email': result.email,
                'mobile': result.mobile,
                'crawled_at': result.crawled_at,
                'crawling_data': json.dumps(crawling_data),
                'organization_id': result.organization_id
            }
            
            self.db.execute_update(update_query, params)
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 저장 실패: {result.name} - {e}")
    
    def _update_crawling_job_progress(self, job_id: int, processed: int, total: int):
        """크롤링 작업 진행률 업데이트"""
        try:
            query = """
                UPDATE crawling_jobs 
                SET processed_count = %s, total_count = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            self.db.execute_update(query, (processed, total, job_id))
            
        except Exception as e:
            self.logger.error(f"❌ 작업 진행률 업데이트 실패: {e}")
    
    def _get_crawling_summary(self) -> Dict[str, Any]:
        """크롤링 요약 통계"""
        try:
            # 기본 통계
            summary = {
                'total_organizations': 0,
                'ai_crawled_count': 0,
                'contact_info_counts': {},
                'quality_distribution': {},
                'recent_crawling_stats': {}
            }
            
            if self.ai_agent_system:
                summary = self.ai_agent_system.get_crawling_statistics()
            
            # 추가 통계
            recent_stats_query = """
                SELECT 
                    COUNT(*) as recently_crawled,
                    AVG(CAST(crawling_data->>'validation_score' AS FLOAT)) as avg_validation_score
                FROM organizations 
                WHERE last_crawled_at >= NOW() - INTERVAL '1 day'
                AND crawling_data IS NOT NULL
            """
            
            recent_stats = self.db.execute_query(recent_stats_query, fetch_all=False)
            if recent_stats:
                summary['recent_crawling_stats'] = recent_stats
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 요약 조회 실패: {e}")
            return {}
    
    def _send_database_completion_email(self, stats: Dict[str, Any]):
        """데이터베이스 크롤링 완료 이메일"""
        try:
            subject = "🎉 통합 AI 크롤링 시스템 완료"
            
            body = f"""
안녕하세요! 대표님!

통합 AI 크롤링 시스템이 성공적으로 완료되었습니다.

📊 **크롤링 결과 요약:**
- 총 처리 기관: {stats.get('total_processed', 0):,}개
- 성공 처리: {stats.get('success_count', 0):,}개
- 실행 시간: {stats.get('duration', 'N/A')}

📈 **연락처 정보 현황:**
- 전화번호: {stats.get('contact_info', {}).get('phone', 0):,}개
- 팩스번호: {stats.get('contact_info', {}).get('fax', 0):,}개
- 홈페이지: {stats.get('contact_info', {}).get('homepage', 0):,}개
- 이메일: {stats.get('contact_info', {}).get('email', 0):,}개

🏆 **데이터 품질 등급:**
{self._format_quality_grades(stats.get('quality_grades', {}))}

🤖 **AI 시스템 성능:**
- AI 크롤링 완료: {stats.get('ai_crawled_count', 0):,}개
- 평균 검증 점수: {stats.get('recent_crawling_stats', {}).get('avg_validation_score', 0):.2f}

🔧 **시스템 리소스:**
- 최대 워커 수: {stats.get('system_stats', {}).get('max_workers', 'N/A')}
- 메모리 사용률: {stats.get('system_stats', {}).get('memory_percent', 0):.1f}%

통합 AI 시스템이 성공적으로 작동했습니다!

감사합니다!
-통합 AI 크롤링 시스템-
"""
            
            self._send_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"❌ 완료 이메일 전송 실패: {e}")
    
    def _format_quality_grades(self, grades: Dict[str, int]) -> str:
        """품질 등급 포맷팅"""
        if not grades:
            return "- 데이터 없음"
        
        formatted = []
        for grade in ['A', 'B', 'C', 'D', 'E', 'F']:
            count = grades.get(grade, 0)
            if count > 0:
                formatted.append(f"- {grade}등급: {count:,}개")
        
        return '\n'.join(formatted) if formatted else "- 데이터 없음"
    
    def run_hybrid_crawling(self, excel_path: str = None) -> Dict[str, Any]:
        """하이브리드 크롤링 실행 (엑셀 + 데이터베이스)"""
        try:
            results = {}
            
            # 1. 엑셀 기반 크롤링 (기존 방식)
            if excel_path and os.path.exists(excel_path):
                self.logger.info("📊 엑셀 기반 크롤링 시작")
                self.excel_path = excel_path
                self._load_data()
                
                # 기존 방식으로 크롤링
                super().run_extraction()
                
                # 결과를 데이터베이스에 저장
                self._import_excel_results_to_database()
                
                results['excel_crawling'] = {
                    'processed_count': self.processed_count,
                    'success_count': self.success_count
                }
            
            # 2. 데이터베이스 기반 AI 크롤링
            if self.use_database:
                self.logger.info("🤖 데이터베이스 기반 AI 크롤링 시작")
                db_results = self.run_database_crawling()
                results['database_crawling'] = db_results
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 하이브리드 크롤링 실패: {e}")
            raise
    
    def _import_excel_results_to_database(self):
        """엑셀 결과를 데이터베이스로 가져오기"""
        try:
            if not hasattr(self, 'df') or self.df is None:
                return
            
            self.logger.info("📥 엑셀 결과를 데이터베이스로 가져오기 시작")
            
            for _, row in self.df.iterrows():
                try:
                    # 기존 기관 확인
                    existing_query = """
                        SELECT id FROM organizations 
                        WHERE name = %s AND address = %s
                    """
                    existing = self.db.execute_query(
                        existing_query, (row['name'], row['address']), fetch_all=False
                    )
                    
                    if existing:
                        # 업데이트
                        update_query = """
                            UPDATE organizations 
                            SET phone = COALESCE(NULLIF(%s, ''), phone),
                                fax = COALESCE(NULLIF(%s, ''), fax),
                                homepage = COALESCE(NULLIF(%s, ''), homepage),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """
                        self.db.execute_update(update_query, (
                            row.get('phone', ''), 
                            row.get('fax', ''), 
                            row.get('homepage', ''),
                            existing['id']
                        ))
                    else:
                        # 새로 삽입
                        insert_query = """
                            INSERT INTO organizations (name, address, phone, fax, homepage, created_by)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        self.db.execute_update(insert_query, (
                            row['name'],
                            row['address'],
                            row.get('phone', ''),
                            row.get('fax', ''),
                            row.get('homepage', ''),
                            'excel_import'
                        ))
                
                except Exception as e:
                    self.logger.error(f"❌ 행 가져오기 실패: {row.get('name', 'Unknown')} - {e}")
                    continue
            
            self.logger.info("✅ 엑셀 결과 데이터베이스 가져오기 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 엑셀 결과 가져오기 실패: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        try:
            status = {
                'integration_mode': self.integration_mode,
                'use_database': self.use_database,
                'ai_agent_available': self.ai_agent_system is not None,
                'webdriver_available': self.driver is not None,
                'database_connection': False,
                'crawling_active': getattr(self, 'is_running', False)
            }
            
            # 데이터베이스 연결 확인
            if self.use_database:
                try:
                    self.db.execute_query("SELECT 1", fetch_all=False)
                    status['database_connection'] = True
                except:
                    status['database_connection'] = False
            
            # AI 에이전트 상태
            if self.ai_agent_system:
                status['ai_system_stats'] = self.ai_agent_system.resource_manager.get_system_stats()
            
            # 크롤링 통계
            if self.use_database:
                status['crawling_stats'] = self._get_crawling_summary()
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 상태 조회 실패: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """리소스 정리"""
        try:
            # AI 에이전트 시스템 정리
            if self.ai_agent_system:
                self.ai_agent_system.stop_crawling()
            
            # 기존 시스템 정리
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
            
            self.logger.info("🧹 통합 크롤링 시스템 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 정리 오류: {e}")
    
    def __del__(self):
        """소멸자"""
        try:
            self.cleanup()
        except:
            pass


# ==================== 사용 예제 ====================

def main():
    """메인 함수 - 통합 시스템 테스트"""
    try:
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 통합 크롤링 봇 초기화
        bot = IntegratedCrawlingBot(
            use_ai=True,
            send_email=True,
            use_database=True,
            integration_mode="hybrid"
        )
        
        # 시스템 상태 확인
        status = bot.get_system_status()
        print(f"🔍 시스템 상태: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        # 데이터베이스 기반 크롤링 실행
        results = bot.run_database_crawling(batch_size=10)
        print(f"📊 크롤링 결과: {json.dumps(results, ensure_ascii=False, indent=2)}")
        
        # 시스템 정리
        bot.cleanup()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
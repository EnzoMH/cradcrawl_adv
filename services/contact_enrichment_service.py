#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연락처 정보 보강 서비스
CRM DB에서 누락된 phone/homepage/address/fax 정보를 crawler_main.py로 자동 검색
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from database.database import get_database
from crawler_main import UnifiedCrawler
from utils.logger_utils import LoggerUtils

@dataclass
class EnrichmentRequest:
    """연락처 보강 요청"""
    org_id: int
    org_name: str
    missing_fields: List[str]
    priority: str = "MEDIUM"
    requested_by: str = "SYSTEM"

@dataclass
class EnrichmentResult:
    """연락처 보강 결과"""
    org_id: int
    success: bool
    found_data: Dict[str, str]
    missing_fields: List[str]
    error_message: Optional[str] = None
    processing_time: float = 0.0

class ContactEnrichmentService:
    """연락처 정보 보강 서비스"""
    
    def __init__(self):
        """초기화"""
        self.db = get_database()
        self.logger = LoggerUtils.setup_logger("contact_enrichment", file_logging=False)
        self.crawler = None
        
        # 통계
        self.stats = {
            "total_processed": 0,
            "successful_enrichments": 0,
            "failed_enrichments": 0,
            "fields_found": {
                "phone": 0,
                "fax": 0,
                "email": 0,
                "homepage": 0,
                "address": 0
            }
        }
        
        self.logger.info("🔍 연락처 보강 서비스 초기화 완료")
    
    def get_crawler(self) -> UnifiedCrawler:
        """크롤러 인스턴스 가져오기 (지연 초기화)"""
        if not self.crawler:
            try:
                self.crawler = UnifiedCrawler()
                self.logger.info("🤖 UnifiedCrawler 초기화 성공")
            except Exception as e:
                self.logger.error(f"❌ UnifiedCrawler 초기화 실패: {e}")
                raise
        return self.crawler
    
    def find_organizations_with_missing_contacts(self, limit: int = 100) -> List[EnrichmentRequest]:
        """누락된 연락처 정보가 있는 기관들 찾기"""
        try:
            self.logger.info(f"🔍 누락된 연락처 정보 기관 검색 (최대 {limit}개)")
            
            query = """
            SELECT id, name, homepage, phone, fax, email, address, type, category
            FROM organizations 
            WHERE is_active = 1
            AND (
                phone IS NULL OR phone = '' OR
                fax IS NULL OR fax = '' OR
                email IS NULL OR email = '' OR
                homepage IS NULL OR homepage = '' OR
                address IS NULL OR address = ''
            )
            ORDER BY 
                CASE 
                    WHEN priority = 'HIGH' THEN 1
                    WHEN priority = 'MEDIUM' THEN 2
                    ELSE 3
                END,
                updated_at DESC
            LIMIT ?
            """
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query, (limit,))
                organizations = cursor.fetchall()
            
            requests = []
            for org in organizations:
                missing_fields = []
                
                # 각 필드별 누락 확인
                if not org['phone'] or org['phone'].strip() == '':
                    missing_fields.append('phone')
                if not org['fax'] or org['fax'].strip() == '':
                    missing_fields.append('fax')
                if not org['email'] or org['email'].strip() == '':
                    missing_fields.append('email')
                if not org['homepage'] or org['homepage'].strip() == '':
                    missing_fields.append('homepage')
                if not org['address'] or org['address'].strip() == '':
                    missing_fields.append('address')
                
                if missing_fields:
                    requests.append(EnrichmentRequest(
                        org_id=org['id'],
                        org_name=org['name'],
                        missing_fields=missing_fields
                    ))
            
            self.logger.info(f"✅ {len(requests)}개 기관에 누락된 연락처 정보 발견")
            return requests
            
        except Exception as e:
            self.logger.error(f"❌ 누락 기관 검색 실패: {e}")
            return []
    
    async def enrich_single_organization(self, request: EnrichmentRequest) -> EnrichmentResult:
        """단일 기관의 연락처 정보 보강"""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🔍 연락처 보강 시작: {request.org_name} (ID: {request.org_id})")
            self.logger.info(f"  📋 누락 필드: {', '.join(request.missing_fields)}")
            
            # 크롤러로 정보 검색
            crawler = self.get_crawler()
            
            # 기관 정보를 크롤러 형식으로 변환
            org_data = {
                "name": request.org_name,
                "category": "기관",  # 기본값
                "homepage": "",
                "phone": "",
                "fax": "",
                "email": "",
                "address": ""
            }
            
            # 크롤러로 단일 기관 처리
            processed_org = await crawler.process_single_organization(org_data, 1)
            
            # 결과에서 찾은 데이터 추출
            found_data = {}
            still_missing = []
            
            for field in request.missing_fields:
                value = processed_org.get(field, "")
                if value and value.strip():
                    found_data[field] = value.strip()
                    self.stats["fields_found"][field] += 1
                    self.logger.info(f"  ✅ {field} 발견: {value}")
                else:
                    still_missing.append(field)
            
            # DB 업데이트
            if found_data:
                success = self.update_organization_contacts(request.org_id, found_data, request.requested_by)
                if success:
                    self.logger.info(f"  💾 DB 업데이트 성공: {len(found_data)}개 필드")
                else:
                    self.logger.warning(f"  ⚠️ DB 업데이트 실패")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = EnrichmentResult(
                org_id=request.org_id,
                success=len(found_data) > 0,
                found_data=found_data,
                missing_fields=still_missing,
                processing_time=processing_time
            )
            
            if result.success:
                self.stats["successful_enrichments"] += 1
            else:
                self.stats["failed_enrichments"] += 1
            
            self.stats["total_processed"] += 1
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ 연락처 보강 실패: {request.org_name} - {e}")
            
            self.stats["failed_enrichments"] += 1
            self.stats["total_processed"] += 1
            
            return EnrichmentResult(
                org_id=request.org_id,
                success=False,
                found_data={},
                missing_fields=request.missing_fields,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def update_organization_contacts(self, org_id: int, contact_data: Dict[str, str], updated_by: str) -> bool:
        """기관의 연락처 정보 업데이트"""
        try:
            # 업데이트할 필드 준비
            updates = contact_data.copy()
            updates['updated_by'] = updated_by
            updates['updated_at'] = datetime.now().isoformat()
            
            # 크롤링 메타데이터 추가
            crawling_metadata = {
                "last_enrichment": datetime.now().isoformat(),
                "enrichment_source": "UnifiedCrawler",
                "found_fields": list(contact_data.keys())
            }
            
            # 기존 크롤링 데이터가 있으면 병합
            with self.db.get_connection() as conn:
                cursor = conn.execute("SELECT crawling_data FROM organizations WHERE id = ?", (org_id,))
                row = cursor.fetchone()
                
                if row and row['crawling_data']:
                    try:
                        existing_data = json.loads(row['crawling_data'])
                        existing_data.update(crawling_metadata)
                        updates['crawling_data'] = json.dumps(existing_data, ensure_ascii=False)
                    except:
                        updates['crawling_data'] = json.dumps(crawling_metadata, ensure_ascii=False)
                else:
                    updates['crawling_data'] = json.dumps(crawling_metadata, ensure_ascii=False)
            
            # DB 업데이트
            success = self.db.update_organization(org_id, updates, updated_by)
            
            if success:
                self.logger.info(f"✅ 기관 ID {org_id} 연락처 정보 업데이트 완료")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 기관 연락처 업데이트 실패: {e}")
            return False
    
    async def enrich_multiple_organizations(self, requests: List[EnrichmentRequest], 
                                          max_concurrent: int = 3) -> List[EnrichmentResult]:
        """여러 기관의 연락처 정보 일괄 보강"""
        try:
            self.logger.info(f"🚀 일괄 연락처 보강 시작: {len(requests)}개 기관")
            
            # 세마포어로 동시 실행 수 제한
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def enrich_with_semaphore(request):
                async with semaphore:
                    return await self.enrich_single_organization(request)
            
            # 병렬 처리
            tasks = [enrich_with_semaphore(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ 기관 {requests[i].org_name} 처리 중 예외: {result}")
                    final_results.append(EnrichmentResult(
                        org_id=requests[i].org_id,
                        success=False,
                        found_data={},
                        missing_fields=requests[i].missing_fields,
                        error_message=str(result)
                    ))
                else:
                    final_results.append(result)
            
            # 통계 출력
            self.print_enrichment_statistics(final_results)
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ 일괄 연락처 보강 실패: {e}")
            return []
    
    async def auto_enrich_missing_contacts(self, limit: int = 50, max_concurrent: int = 3) -> Dict[str, Any]:
        """누락된 연락처 정보 자동 보강"""
        try:
            self.logger.info(f"🤖 자동 연락처 보강 시작 (최대 {limit}개 기관)")
            
            # 1. 누락된 연락처가 있는 기관들 찾기
            requests = self.find_organizations_with_missing_contacts(limit)
            
            if not requests:
                self.logger.info("✅ 보강이 필요한 기관이 없습니다.")
                return {
                    "status": "completed",
                    "message": "보강이 필요한 기관이 없습니다.",
                    "processed_count": 0,
                    "successful_count": 0,
                    "results": []
                }
            
            # 2. 일괄 보강 실행
            results = await self.enrich_multiple_organizations(requests, max_concurrent)
            
            # 3. 결과 요약
            successful_count = sum(1 for r in results if r.success)
            
            summary = {
                "status": "completed",
                "message": f"{successful_count}/{len(results)}개 기관 연락처 보강 완료",
                "processed_count": len(results),
                "successful_count": successful_count,
                "total_fields_found": sum(len(r.found_data) for r in results),
                "results": results,
                "statistics": self.stats.copy()
            }
            
            self.logger.info(f"🎉 자동 연락처 보강 완료: {successful_count}/{len(results)}개 성공")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 자동 연락처 보강 실패: {e}")
            return {
                "status": "error",
                "message": f"자동 보강 실패: {str(e)}",
                "processed_count": 0,
                "successful_count": 0,
                "results": []
            }
    
    def print_enrichment_statistics(self, results: List[EnrichmentResult]):
        """보강 통계 출력"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_fields_found = sum(len(r.found_data) for r in successful)
        avg_processing_time = sum(r.processing_time for r in results) / len(results) if results else 0
        
        print("\n" + "="*60)
        print("📊 연락처 보강 통계")
        print("="*60)
        print(f"📋 총 처리: {len(results)}개 기관")
        print(f"✅ 성공: {len(successful)}개")
        print(f"❌ 실패: {len(failed)}개")
        print(f"📞 발견된 연락처: {total_fields_found}개")
        print(f"⏱️ 평균 처리시간: {avg_processing_time:.2f}초")
        
        if total_fields_found > 0:
            print("\n📈 필드별 발견 통계:")
            for field, count in self.stats["fields_found"].items():
                if count > 0:
                    print(f"  {field}: {count}개")
        
        print("="*60)
    
    def get_enrichment_history(self, org_id: int) -> List[Dict[str, Any]]:
        """기관의 연락처 보강 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT crawling_data, updated_at, updated_by
                    FROM organizations 
                    WHERE id = ?
                """, (org_id,))
                
                row = cursor.fetchone()
                if row and row['crawling_data']:
                    try:
                        crawling_data = json.loads(row['crawling_data'])
                        return [{
                            "enrichment_date": crawling_data.get('last_enrichment'),
                            "source": crawling_data.get('enrichment_source'),
                            "found_fields": crawling_data.get('found_fields', []),
                            "updated_by": row['updated_by'],
                            "updated_at": row['updated_at']
                        }]
                    except:
                        pass
                
                return []
                
        except Exception as e:
            self.logger.error(f"❌ 보강 이력 조회 실패: {e}")
            return []

# 편의 함수들
async def auto_enrich_contacts(limit: int = 50) -> Dict[str, Any]:
    """연락처 자동 보강 편의 함수"""
    service = ContactEnrichmentService()
    return await service.auto_enrich_missing_contacts(limit)

async def enrich_organization_by_id(org_id: int) -> Optional[EnrichmentResult]:
    """특정 기관 연락처 보강 편의 함수"""
    try:
        service = ContactEnrichmentService()
        db = get_database()
        
        # 기관 정보 조회
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM organizations WHERE id = ?", (org_id,))
            org = cursor.fetchone()
            
            if not org:
                return None
        
        # 보강 요청 생성
        request = EnrichmentRequest(
            org_id=org['id'],
            org_name=org['name'],
            missing_fields=['phone', 'fax', 'email', 'homepage', 'address']  # 모든 필드 체크
        )
        
        # 보강 실행
        result = await service.enrich_single_organization(request)
        return result
        
    except Exception as e:
        logging.error(f"❌ 기관 ID {org_id} 연락처 보강 실패: {e}")
        return None 
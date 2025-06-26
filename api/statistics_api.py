#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통계 분석 API
CRM 데이터베이스의 통계 분석 및 리포트 생성 API
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

# 프로젝트 모듈 import
from database.database import get_database
from services.organization_service import OrganizationService
from utils.logger_utils import LoggerUtils
from utils.settings import (
    KOREAN_AREA_CODES,
    PORTAL_EMAIL_DOMAINS,
    GOVERNMENT_EMAIL_SUFFIXES,
    EDUCATION_EMAIL_SUFFIXES,
    BUSINESS_EMAIL_SUFFIXES,
    RELIGIOUS_EMAIL_KEYWORDS,
    format_phone_number,
    extract_phone_area_code
)

# 로거 설정
logger = LoggerUtils.setup_logger(name="statistics_api", file_logging=False)

# 라우터 생성
router = APIRouter(prefix="/api/statistics", tags=["통계 분석"])

class CRMStatisticsAnalyzer:
    """CRM 데이터 통계 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.db = get_database()
        self.org_service = OrganizationService()
    
    def validate_korean_phone(self, phone: str) -> Dict[str, Any]:
        """한국 전화번호 유효성 검증"""
        if not phone:
            return {"is_valid": False, "reason": "번호 없음"}
        
        import re
        digits = re.sub(r'[^\d]', '', phone)
        
        # 길이 체크
        if len(digits) < 9 or len(digits) > 11:
            return {"is_valid": False, "reason": "길이 오류"}
        
        # 지역코드 체크
        area_code = extract_phone_area_code(phone)
        if not area_code:
            return {"is_valid": False, "reason": "지역코드 오류"}
        
        # 길이별 유효성 체크
        expected_lengths = {
            '02': [9, 10],  # 서울
            '070': [11],    # 인터넷전화
            '010': [11], '017': [11]  # 핸드폰
        }
        
        if area_code in expected_lengths:
            if len(digits) not in expected_lengths[area_code]:
                return {"is_valid": False, "reason": "길이 불일치"}
        else:
            # 기타 지역번호는 10-11자리
            if len(digits) not in [10, 11]:
                return {"is_valid": False, "reason": "길이 불일치"}
        
        return {
            "is_valid": True,
            "area_code": area_code,
            "area_name": KOREAN_AREA_CODES.get(area_code, "알 수 없음"),
            "formatted": format_phone_number(digits, area_code)
        }
    
    def extract_email_domain(self, email: str) -> Optional[str]:
        """이메일에서 도메인 추출"""
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower()
            return domain
        except:
            return None
    
    def categorize_email_domain(self, domain: str) -> str:
        """이메일 도메인 카테고리 분류"""
        if not domain:
            return "기타"
        
        if domain in PORTAL_EMAIL_DOMAINS:
            return "포털"
        
        if any(domain.endswith(suffix) for suffix in GOVERNMENT_EMAIL_SUFFIXES):
            return "정부/공공"
        
        if any(domain.endswith(suffix) for suffix in EDUCATION_EMAIL_SUFFIXES):
            return "교육기관"
        
        if any(domain.endswith(suffix) for suffix in BUSINESS_EMAIL_SUFFIXES):
            return "기업/조직"
        
        if any(keyword in domain for keyword in RELIGIOUS_EMAIL_KEYWORDS):
            return "종교기관"
        
        return "기타"
    
    def analyze_contact_data(self) -> Dict[str, Any]:
        """연락처 데이터 분석"""
        logger.info("🔍 CRM 연락처 데이터 분석 시작")
        
        try:
            stats = {
                "analysis_info": {
                    "analysis_time": datetime.now().isoformat(),
                    "analysis_type": "contact_analysis"
                },
                "basic_stats": {},
                "contact_coverage": {},
                "quality_metrics": {},
                "geographic_distribution": {},
                "email_analysis": {},
                "category_breakdown": {}
            }
            
            # 기본 통계 조회
            with self.db.get_connection() as conn:
                # 전체 기관 수
                cursor = conn.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1")
                total_orgs = cursor.fetchone()[0]
                
                # 연락처별 보유 현황
                cursor = conn.execute("""
                    SELECT 
                        COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as phone_count,
                        COUNT(CASE WHEN fax IS NOT NULL AND fax != '' THEN 1 END) as fax_count,
                        COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as email_count,
                        COUNT(CASE WHEN homepage IS NOT NULL AND homepage != '' THEN 1 END) as homepage_count,
                        COUNT(CASE WHEN phone IS NOT NULL AND phone != '' 
                                   AND fax IS NOT NULL AND fax != ''
                                   AND email IS NOT NULL AND email != '' THEN 1 END) as complete_count
                    FROM organizations WHERE is_active = 1
                """)
                
                contact_counts = cursor.fetchone()
                phone_count, fax_count, email_count, homepage_count, complete_count = contact_counts
                
                # 카테고리별 분석
                cursor = conn.execute("""
                    SELECT 
                        category,
                        COUNT(*) as total,
                        COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as has_phone,
                        COUNT(CASE WHEN fax IS NOT NULL AND fax != '' THEN 1 END) as has_fax,
                        COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as has_email,
                        COUNT(CASE WHEN homepage IS NOT NULL AND homepage != '' THEN 1 END) as has_homepage
                    FROM organizations 
                    WHERE is_active = 1 
                    GROUP BY category
                    ORDER BY total DESC
                """)
                
                category_stats = {}
                for row in cursor.fetchall():
                    category, total, has_phone, has_fax, has_email, has_homepage = row
                    category_stats[category] = {
                        "total": total,
                        "phone_coverage": round((has_phone / total * 100), 1) if total > 0 else 0,
                        "fax_coverage": round((has_fax / total * 100), 1) if total > 0 else 0,
                        "email_coverage": round((has_email / total * 100), 1) if total > 0 else 0,
                        "homepage_coverage": round((has_homepage / total * 100), 1) if total > 0 else 0,
                        "contact_counts": {
                            "phone": has_phone,
                            "fax": has_fax,
                            "email": has_email,
                            "homepage": has_homepage
                        }
                    }
            
            # 기본 통계
            stats["basic_stats"] = {
                "total_organizations": total_orgs,
                "complete_contacts": complete_count,
                "incomplete_contacts": total_orgs - complete_count
            }
            
            # 연락처 커버리지
            stats["contact_coverage"] = {
                "phone": {
                    "count": phone_count,
                    "rate": round((phone_count / total_orgs * 100), 1) if total_orgs > 0 else 0
                },
                "fax": {
                    "count": fax_count,
                    "rate": round((fax_count / total_orgs * 100), 1) if total_orgs > 0 else 0
                },
                "email": {
                    "count": email_count,
                    "rate": round((email_count / total_orgs * 100), 1) if total_orgs > 0 else 0
                },
                "homepage": {
                    "count": homepage_count,
                    "rate": round((homepage_count / total_orgs * 100), 1) if total_orgs > 0 else 0
                }
            }
            
            # 품질 지표 분석
            valid_phones = 0
            valid_faxes = 0
            phone_areas = Counter()
            fax_areas = Counter()
            email_domains = Counter()
            
            with self.db.get_connection() as conn:
                # 전화번호 품질 분석
                cursor = conn.execute("SELECT phone FROM organizations WHERE phone IS NOT NULL AND phone != '' AND is_active = 1")
                for (phone,) in cursor.fetchall():
                    validation = self.validate_korean_phone(phone)
                    if validation["is_valid"]:
                        valid_phones += 1
                        phone_areas[validation["area_code"]] += 1
                
                # 팩스번호 품질 분석
                cursor = conn.execute("SELECT fax FROM organizations WHERE fax IS NOT NULL AND fax != '' AND is_active = 1")
                for (fax,) in cursor.fetchall():
                    validation = self.validate_korean_phone(fax)
                    if validation["is_valid"]:
                        valid_faxes += 1
                        fax_areas[validation["area_code"]] += 1
                
                # 이메일 도메인 분석
                cursor = conn.execute("SELECT email FROM organizations WHERE email IS NOT NULL AND email != '' AND is_active = 1")
                for (email,) in cursor.fetchall():
                    domain = self.extract_email_domain(email)
                    if domain:
                        email_domains[domain] += 1
            
            # 품질 지표
            stats["quality_metrics"] = {
                "phone_validity_rate": round((valid_phones / phone_count * 100), 1) if phone_count > 0 else 0,
                "fax_validity_rate": round((valid_faxes / fax_count * 100), 1) if fax_count > 0 else 0,
                "completeness_rate": round((complete_count / total_orgs * 100), 1) if total_orgs > 0 else 0,
                "valid_phones": valid_phones,
                "valid_faxes": valid_faxes
            }
            
            # 지역 분포
            all_areas = Counter()
            all_areas.update(phone_areas)
            all_areas.update(fax_areas)
            
            stats["geographic_distribution"] = {
                area_code: {
                    "area_name": KOREAN_AREA_CODES.get(area_code, "알 수 없음"),
                    "total_contacts": count,
                    "phone_count": phone_areas.get(area_code, 0),
                    "fax_count": fax_areas.get(area_code, 0)
                }
                for area_code, count in all_areas.most_common(20)
            }
            
            # 이메일 도메인 분석
            email_categories = Counter()
            for domain, count in email_domains.most_common(100):
                category = self.categorize_email_domain(domain)
                email_categories[category] += count
            
            stats["email_analysis"] = {
                "top_domains": dict(email_domains.most_common(20)),
                "domain_categories": dict(email_categories),
                "total_unique_domains": len(email_domains)
            }
            
            # 카테고리별 분석
            stats["category_breakdown"] = category_stats
            
            logger.info(f"✅ CRM 연락처 분석 완료 - 총 {total_orgs:,}개 기관")
            return stats
            
        except Exception as e:
            logger.error(f"❌ CRM 연락처 분석 실패: {e}")
            raise
    
    def analyze_enrichment_history(self, days: int = 30) -> Dict[str, Any]:
        """보강 이력 분석"""
        logger.info(f"📈 최근 {days}일 보강 이력 분석 시작")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.db.get_connection() as conn:
                # 보강 활동 분석 (enrichment_history 테이블이 있다고 가정)
                cursor = conn.execute("""
                    SELECT 
                        DATE(updated_at) as date,
                        COUNT(*) as updated_count
                    FROM organizations 
                    WHERE updated_at >= ? AND is_active = 1
                    GROUP BY DATE(updated_at)
                    ORDER BY date DESC
                """, (cutoff_date.isoformat(),))
                
                daily_updates = {}
                for row in cursor.fetchall():
                    date, count = row
                    daily_updates[date] = count
            
            return {
                "analysis_period": f"최근 {days}일",
                "daily_updates": daily_updates,
                "total_updates": sum(daily_updates.values()),
                "average_daily_updates": round(sum(daily_updates.values()) / len(daily_updates), 1) if daily_updates else 0
            }
            
        except Exception as e:
            logger.error(f"❌ 보강 이력 분석 실패: {e}")
            return {}
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """데이터 품질 리포트 생성"""
        logger.info("📋 데이터 품질 리포트 생성 시작")
        
        try:
            contact_analysis = self.analyze_contact_data()
            enrichment_history = self.analyze_enrichment_history()
            
            # 품질 점수 계산
            quality_metrics = contact_analysis.get("quality_metrics", {})
            coverage = contact_analysis.get("contact_coverage", {})
            
            coverage_score = (
                coverage.get("phone", {}).get("rate", 0) +
                coverage.get("fax", {}).get("rate", 0) +
                coverage.get("email", {}).get("rate", 0) +
                coverage.get("homepage", {}).get("rate", 0)
            ) / 4
            
            validity_score = (
                quality_metrics.get("phone_validity_rate", 0) +
                quality_metrics.get("fax_validity_rate", 0)
            ) / 2
            
            completeness_score = quality_metrics.get("completeness_rate", 0)
            
            overall_score = (coverage_score * 0.4 + validity_score * 0.3 + completeness_score * 0.3)
            
            # 권장사항 생성
            recommendations = []
            
            if quality_metrics.get("phone_validity_rate", 0) < 90:
                recommendations.append({
                    "priority": "high",
                    "category": "data_quality",
                    "issue": "전화번호 유효성 낮음",
                    "description": f"전화번호 유효성이 {quality_metrics.get('phone_validity_rate', 0):.1f}%입니다.",
                    "action": "전화번호 형식 검증 및 정리 필요"
                })
            
            if completeness_score < 50:
                recommendations.append({
                    "priority": "medium",
                    "category": "data_coverage",
                    "issue": "연락처 정보 완성도 낮음",
                    "description": f"완전한 연락처 정보를 가진 기관이 {completeness_score:.1f}%입니다.",
                    "action": "자동 보강 시스템 활용 권장"
                })
            
            if coverage.get("email", {}).get("rate", 0) < 30:
                recommendations.append({
                    "priority": "medium",
                    "category": "data_coverage",
                    "issue": "이메일 정보 부족",
                    "description": f"이메일 정보 보유율이 {coverage.get('email', {}).get('rate', 0):.1f}%입니다.",
                    "action": "이메일 수집 강화 필요"
                })
            
            return {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "data_quality"
                },
                "overall_score": round(overall_score, 1),
                "score_breakdown": {
                    "coverage_score": round(coverage_score, 1),
                    "validity_score": round(validity_score, 1),
                    "completeness_score": round(completeness_score, 1)
                },
                "contact_analysis": contact_analysis,
                "enrichment_history": enrichment_history,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ 데이터 품질 리포트 생성 실패: {e}")
            raise

# 전역 분석기 인스턴스
analyzer = CRMStatisticsAnalyzer()

# ==================== API 엔드포인트 ====================

@router.get("/overview", summary="통계 개요")
async def get_statistics_overview():
    """통계 분석 개요 조회"""
    try:
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

@router.get("/contact-analysis", summary="연락처 분석")
async def get_contact_analysis():
    """상세 연락처 분석 데이터"""
    try:
        analysis = analyzer.analyze_contact_data()
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"❌ 연락처 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"연락처 분석 실패: {str(e)}")

@router.get("/geographic-distribution", summary="지역별 분포")
async def get_geographic_distribution():
    """지역별 연락처 분포 분석"""
    try:
        analysis = analyzer.analyze_contact_data()
        geo_distribution = analysis.get("geographic_distribution", {})
        
        return {
            "status": "success",
            "geographic_data": geo_distribution,
            "summary": {
                "total_regions": len(geo_distribution),
                "top_region": list(geo_distribution.keys())[0] if geo_distribution else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 지역별 분포 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"지역별 분포 분석 실패: {str(e)}")

@router.get("/email-analysis", summary="이메일 분석")
async def get_email_analysis():
    """이메일 도메인 및 카테고리 분석"""
    try:
        analysis = analyzer.analyze_contact_data()
        email_analysis = analysis.get("email_analysis", {})
        
        return {
            "status": "success",
            "email_data": email_analysis
        }
        
    except Exception as e:
        logger.error(f"❌ 이메일 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이메일 분석 실패: {str(e)}")

@router.get("/quality-report", summary="데이터 품질 리포트")
async def get_quality_report():
    """종합 데이터 품질 리포트"""
    try:
        report = analyzer.generate_data_quality_report()
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"❌ 품질 리포트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"품질 리포트 생성 실패: {str(e)}")

@router.get("/enrichment-history", summary="보강 이력")
async def get_enrichment_history(days: int = Query(30, ge=1, le=365, description="분석 기간 (일)")):
    """보강 활동 이력 분석"""
    try:
        history = analyzer.analyze_enrichment_history(days)
        
        return {
            "status": "success",
            "history": history
        }
        
    except Exception as e:
        logger.error(f"❌ 보강 이력 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보강 이력 분석 실패: {str(e)}")

@router.get("/category-breakdown", summary="카테고리별 분석")
async def get_category_breakdown():
    """카테고리별 상세 분석"""
    try:
        analysis = analyzer.analyze_contact_data()
        category_breakdown = analysis.get("category_breakdown", {})
        
        # 카테고리별 완성도 순위
        category_scores = []
        for category, stats in category_breakdown.items():
            avg_coverage = (
                stats.get("phone_coverage", 0) +
                stats.get("fax_coverage", 0) +
                stats.get("email_coverage", 0) +
                stats.get("homepage_coverage", 0)
            ) / 4
            
            category_scores.append({
                "category": category,
                "total_organizations": stats.get("total", 0),
                "average_coverage": round(avg_coverage, 1),
                "coverage_details": {
                    "phone": stats.get("phone_coverage", 0),
                    "fax": stats.get("fax_coverage", 0),
                    "email": stats.get("email_coverage", 0),
                    "homepage": stats.get("homepage_coverage", 0)
                }
            })
        
        # 완성도 순으로 정렬
        category_scores.sort(key=lambda x: x["average_coverage"], reverse=True)
        
        return {
            "status": "success",
            "category_breakdown": category_breakdown,
            "category_ranking": category_scores
        }
        
    except Exception as e:
        logger.error(f"❌ 카테고리별 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"카테고리별 분석 실패: {str(e)}")

@router.post("/generate-report", summary="리포트 생성")
async def generate_comprehensive_report(background_tasks: BackgroundTasks):
    """종합 분석 리포트 생성 (백그라운드 작업)"""
    try:
        # 즉시 응답 후 백그라운드에서 리포트 생성
        def generate_report():
            try:
                report = analyzer.generate_data_quality_report()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"crm_statistics_report_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                logger.info(f"📋 통계 리포트 생성 완료: {filename}")
                
            except Exception as e:
                logger.error(f"❌ 백그라운드 리포트 생성 실패: {e}")
        
        background_tasks.add_task(generate_report)
        
        return {
            "status": "success",
            "message": "리포트 생성이 시작되었습니다.",
            "estimated_time": "2-3분 소요 예상"
        }
        
    except Exception as e:
        logger.error(f"❌ 리포트 생성 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")

@router.get("/export-data", summary="데이터 내보내기")
async def export_statistics_data(
    format: str = Query("json", regex="^(json|csv)$", description="내보내기 형식"),
    include_details: bool = Query(True, description="상세 정보 포함 여부")
):
    """통계 데이터 내보내기"""
    try:
        analysis = analyzer.analyze_contact_data()
        
        if format == "json":
            return {
                "status": "success",
                "format": "json",
                "data": analysis if include_details else {
                    "basic_stats": analysis.get("basic_stats", {}),
                    "contact_coverage": analysis.get("contact_coverage", {}),
                    "quality_metrics": analysis.get("quality_metrics", {})
                }
            }
        
        elif format == "csv":
            # CSV 형식으로 변환 (간단한 버전)
            csv_data = []
            csv_data.append("Category,Total,Phone_Coverage,Fax_Coverage,Email_Coverage,Homepage_Coverage")
            
            for category, stats in analysis.get("category_breakdown", {}).items():
                csv_data.append(f"{category},{stats.get('total', 0)},{stats.get('phone_coverage', 0)},{stats.get('fax_coverage', 0)},{stats.get('email_coverage', 0)},{stats.get('homepage_coverage', 0)}")
            
            return {
                "status": "success",
                "format": "csv",
                "data": "\n".join(csv_data)
            }
        
    except Exception as e:
        logger.error(f"❌ 데이터 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 내보내기 실패: {str(e)}")
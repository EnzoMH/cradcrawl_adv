#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM 시스템 테스트 스크립트
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_organization_service():
    """기관 서비스 테스트"""
    print("🔍 기관 서비스 테스트 시작")
    
    try:
        from services.organization_service import OrganizationService
        
        org_service = OrganizationService()
        print("✅ OrganizationService 초기화 성공")
        
        # 누락된 연락처 기관 조회
        missing_contacts = org_service.get_organizations_with_missing_contacts(limit=5)
        print(f"📊 누락된 연락처 기관: {len(missing_contacts)}개")
        
        if missing_contacts:
            print("📋 처음 3개 기관:")
            for i, org in enumerate(missing_contacts[:3], 1):
                print(f"  {i}. {org['name']} (누락: {', '.join(org['missing_fields'])})")
        
        # 연락처 통계
        stats = org_service.get_contact_statistics()
        print(f"📈 전체 완성도: {stats.get('overall_completion_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 기관 서비스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("🗄️ 데이터베이스 연결 테스트 시작")
    
    try:
        from database.database import get_database
        
        db = get_database()
        print("✅ 데이터베이스 연결 성공")
        
        # 기본 통계 조회
        stats = db.get_dashboard_stats()
        print(f"📊 총 기관 수: {stats.get('total_organizations', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enrichment_service():
    """연락처 보강 서비스 테스트"""
    print("🤖 연락처 보강 서비스 테스트 시작")
    
    try:
        from services.contact_enrichment_service import ContactEnrichmentService
        
        enrichment_service = ContactEnrichmentService()
        print("✅ ContactEnrichmentService 초기화 성공")
        
        # 보강 후보 기관 찾기
        requests = enrichment_service.find_organizations_with_missing_contacts(limit=3)
        print(f"📋 보강 후보 기관: {len(requests)}개")
        
        if requests:
            print("🎯 첫 번째 기관 보강 테스트:")
            first_request = requests[0]
            print(f"  기관명: {first_request.org_name}")
            print(f"  누락 필드: {', '.join(first_request.missing_fields)}")
            
            # 실제 보강은 시간이 오래 걸리므로 스킵
            print("  (실제 크롤링은 스킵)")
        
        return True
        
    except Exception as e:
        print(f"❌ 연락처 보강 서비스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crawler_main():
    """크롤러 메인 모듈 테스트"""
    print("🕷️ 크롤러 메인 모듈 테스트 시작")
    
    try:
        from crawler_main import UnifiedCrawler
        
        # 크롤러 초기화 (API 키 없이)
        crawler = UnifiedCrawler()
        print("✅ UnifiedCrawler 초기화 성공")
        
        # 통계 확인
        print(f"📊 크롤러 통계: {crawler.stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 크롤러 메인 모듈 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 CRM 시스템 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("기관 서비스", test_organization_service),
        ("크롤러 메인", test_crawler_main),
        ("연락처 보강 서비스", test_enrichment_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트")
        print("-" * 30)
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name} 테스트 통과")
        else:
            print(f"❌ {test_name} 테스트 실패")
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    print(f"\n📈 전체 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
        print("🚀 CRM 애플리케이션을 실행할 준비가 완료되었습니다.")
        print("\n실행 방법:")
        print("  python crm_app.py")
        print("  또는")
        print("  uvicorn crm_app:app --reload")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 문제를 해결한 후 다시 시도해주세요.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main()) 
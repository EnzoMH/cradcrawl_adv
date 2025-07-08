#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 AI 에이전트 크롤링 시스템 통합 예제
기존 centercrawling.py + 새로운 AI 에이전트 시스템 완전 통합

이 예제는 다음을 포함합니다:
1. 하이브리드 크롤링 (엑셀 + 데이터베이스)
2. AI 기반 검색 전략 및 검증
3. GCP e2-small 최적화
4. 실시간 성능 모니터링
5. 데이터 품질 등급 시스템
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 통합 시스템 import
from aiagent.integration.crawler_integration import IntegratedCrawlingBot
from aiagent.core.enhanced_agent_system import EnhancedAIAgentSystem
from aiagent.config.gcp_optimization import GCPOptimizer, GCPDeploymentHelper
from database.database import ChurchCRMDatabase


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('complete_integration.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("CompleteIntegration")


def test_database_connection():
    """데이터베이스 연결 테스트"""
    logger = logging.getLogger("DatabaseTest")
    
    try:
        logger.info("🔍 데이터베이스 연결 테스트 시작")
        
        db = ChurchCRMDatabase()
        result = db.execute_query("SELECT COUNT(*) as count FROM organizations", fetch_all=False)
        
        logger.info(f"✅ 데이터베이스 연결 성공: {result['count']}개 기관 확인")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False


def test_ai_agent_system():
    """AI 에이전트 시스템 테스트"""
    logger = logging.getLogger("AIAgentTest")
    
    try:
        logger.info("🤖 AI 에이전트 시스템 테스트 시작")
        
        # AI 에이전트 시스템 초기화
        agent_system = EnhancedAIAgentSystem()
        
        # 테스트 데이터
        test_organization = {
            'id': 999,
            'name': '테스트교회',
            'address': '서울시 강남구 테헤란로',
            'phone': '02-1234-5678'
        }
        
        # 단일 기관 처리 테스트
        result = agent_system.process_single_organization(test_organization)
        
        if result:
            logger.info(f"✅ AI 에이전트 테스트 성공: 등급 {result.data_quality_grade}")
            logger.info(f"   검증 점수: {result.validation_score:.2f}")
            logger.info(f"   크롤링 소스: {result.crawling_source}")
        else:
            logger.warning("⚠️ AI 에이전트 테스트 결과 없음")
        
        # 통계 조회
        stats = agent_system.get_crawling_statistics()
        logger.info(f"📊 시스템 통계: {stats.get('total_organizations', 0)}개 기관")
        
        # 시스템 정리
        agent_system.stop_crawling()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI 에이전트 시스템 테스트 실패: {e}")
        return False


def test_gcp_optimization():
    """GCP 최적화 시스템 테스트"""
    logger = logging.getLogger("GCPOptimizationTest")
    
    try:
        logger.info("⚡ GCP 최적화 시스템 테스트 시작")
        
        # GCP 최적화 관리자 초기화
        optimizer = GCPOptimizer()
        optimizer.start_monitoring()
        
        # 시스템 상태 확인
        batch_size = optimizer.get_optimal_batch_size()
        logger.info(f"🔧 최적 배치 크기: {batch_size}")
        
        # WebDriver 옵션 확인
        webdriver_options = optimizer.get_webdriver_options()
        logger.info(f"🌐 WebDriver 옵션: {len(webdriver_options['chrome_options'])}개")
        
        # Gemini 설정 확인
        gemini_config = optimizer.get_gemini_config()
        logger.info(f"🤖 Gemini RPM 제한: {gemini_config['rate_limits']['requests_per_minute']}")
        
        # 성능 보고서 생성 (5초 대기)
        time.sleep(5)
        report = optimizer.get_performance_report()
        
        logger.info(f"📊 현재 메모리: {report['current_status']['memory_percent']:.1f}%")
        logger.info(f"📊 현재 CPU: {report['current_status']['cpu_percent']:.1f}%")
        
        # 경고 확인
        alerts = optimizer.get_alerts()
        if alerts:
            logger.warning(f"🚨 시스템 경고: {len(alerts)}개")
        else:
            logger.info("✅ 시스템 상태 정상")
        
        # 모니터링 중지
        optimizer.stop_monitoring()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GCP 최적화 시스템 테스트 실패: {e}")
        return False


def run_complete_integration_demo():
    """완전한 통합 시스템 데모"""
    logger = logging.getLogger("CompleteDemo")
    
    try:
        logger.info("🚀 완전한 통합 시스템 데모 시작")
        
        # 1. 통합 크롤링 봇 초기화
        logger.info("1️⃣ 통합 크롤링 봇 초기화")
        bot = IntegratedCrawlingBot(
            use_ai=True,
            send_email=False,  # 데모에서는 이메일 비활성화
            use_database=True,
            integration_mode="hybrid"
        )
        
        # 2. 시스템 상태 확인
        logger.info("2️⃣ 시스템 상태 확인")
        status = bot.get_system_status()
        logger.info(f"   통합 모드: {status['integration_mode']}")
        logger.info(f"   데이터베이스 연결: {status['database_connection']}")
        logger.info(f"   AI 에이전트 사용 가능: {status['ai_agent_available']}")
        
        # 3. 소규모 데이터베이스 크롤링 실행
        logger.info("3️⃣ 소규모 데이터베이스 크롤링 실행")
        results = bot.run_database_crawling(batch_size=3)  # 작은 배치로 테스트
        
        logger.info(f"   총 처리: {results.get('total_processed', 0)}개")
        logger.info(f"   성공: {results.get('success_count', 0)}개")
        logger.info(f"   작업 ID: {results.get('job_id', 'N/A')}")
        
        # 4. 통계 확인
        logger.info("4️⃣ 크롤링 통계 확인")
        if 'crawling_stats' in results:
            stats = results['crawling_stats']
            logger.info(f"   전체 기관: {stats.get('total_organizations', 0)}개")
            logger.info(f"   AI 크롤링 완료: {stats.get('ai_crawled_count', 0)}개")
            
            # 품질 등급 분포
            quality_grades = stats.get('quality_grades', {})
            if quality_grades:
                logger.info("   품질 등급 분포:")
                for grade, count in quality_grades.items():
                    logger.info(f"     {grade}등급: {count}개")
        
        # 5. 성능 보고서 생성
        logger.info("5️⃣ 성능 보고서 생성")
        if hasattr(bot, 'ai_agent_system') and bot.ai_agent_system:
            system_stats = bot.ai_agent_system.resource_manager.get_system_stats()
            logger.info(f"   현재 워커: {system_stats['current_workers']}")
            logger.info(f"   최대 워커: {system_stats['max_workers']}")
            logger.info(f"   메모리: {system_stats['memory_percent']:.1f}%")
        
        # 6. 시스템 정리
        logger.info("6️⃣ 시스템 정리")
        bot.cleanup()
        
        logger.info("🎉 완전한 통합 시스템 데모 완료!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 통합 시스템 데모 실패: {e}")
        return False


def run_excel_integration_demo():
    """엑셀 통합 데모 (파일이 있는 경우)"""
    logger = logging.getLogger("ExcelDemo")
    
    try:
        # 엑셀 파일 경로 확인
        excel_path = project_root / "childcenter.xlsx"
        
        if not excel_path.exists():
            logger.info("📊 엑셀 파일이 없어 엑셀 통합 데모를 건너뜁니다")
            return True
        
        logger.info("📊 엑셀 통합 데모 시작")
        
        # 통합 크롤링 봇 초기화
        bot = IntegratedCrawlingBot(
            use_ai=True,
            send_email=False,
            use_database=True,
            integration_mode="hybrid"
        )
        
        # 하이브리드 크롤링 실행 (소규모)
        logger.info("   하이브리드 크롤링 실행 중...")
        
        # 실제로는 전체 파일을 처리하지만, 데모에서는 제한
        results = bot.run_hybrid_crawling(str(excel_path))
        
        # 결과 출력
        if 'excel_crawling' in results:
            excel_stats = results['excel_crawling']
            logger.info(f"   엑셀 처리: {excel_stats.get('processed_count', 0)}개")
            logger.info(f"   엑셀 성공: {excel_stats.get('success_count', 0)}개")
        
        if 'database_crawling' in results:
            db_stats = results['database_crawling']
            logger.info(f"   DB 처리: {db_stats.get('total_processed', 0)}개")
            logger.info(f"   DB 성공: {db_stats.get('success_count', 0)}개")
        
        # 시스템 정리
        bot.cleanup()
        
        logger.info("✅ 엑셀 통합 데모 완료!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 엑셀 통합 데모 실패: {e}")
        return False


def generate_deployment_files():
    """GCP 배포 파일 생성"""
    logger = logging.getLogger("DeploymentFiles")
    
    try:
        logger.info("📦 GCP 배포 파일 생성 시작")
        
        # 배포 디렉토리 생성
        deployment_dir = project_root / "deployment"
        deployment_dir.mkdir(exist_ok=True)
        
        # 시작 스크립트 생성
        startup_script = GCPDeploymentHelper.create_startup_script()
        with open(deployment_dir / "startup.sh", "w", encoding="utf-8") as f:
            f.write(startup_script)
        logger.info("   ✅ startup.sh 생성 완료")
        
        # systemd 서비스 파일 생성
        service_config = GCPDeploymentHelper.create_systemd_service()
        with open(deployment_dir / "crawling-system.service", "w", encoding="utf-8") as f:
            f.write(service_config)
        logger.info("   ✅ crawling-system.service 생성 완료")
        
        # requirements.txt 생성
        requirements = GCPDeploymentHelper.create_requirements_txt()
        with open(deployment_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements)
        logger.info("   ✅ requirements.txt 생성 완료")
        
        # 배포 가이드 생성
        deployment_guide = f"""# GCP e2-small 배포 가이드

## 1. 인스턴스 생성
```bash
gcloud compute instances create crawling-system \\
    --zone=asia-northeast3-a \\
    --machine-type=e2-small \\
    --image-family=ubuntu-2004-lts \\
    --image-project=ubuntu-os-cloud \\
    --boot-disk-size=20GB \\
    --boot-disk-type=pd-standard
```

## 2. 파일 업로드
```bash
gcloud compute scp startup.sh crawling-system:~/ --zone=asia-northeast3-a
gcloud compute scp crawling-system.service crawling-system:~/ --zone=asia-northeast3-a
gcloud compute scp requirements.txt crawling-system:~/ --zone=asia-northeast3-a
```

## 3. 설정 실행
```bash
gcloud compute ssh crawling-system --zone=asia-northeast3-a

# 인스턴스 내에서 실행
chmod +x startup.sh
sudo ./startup.sh

# 서비스 등록
sudo cp crawling-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crawling-system
sudo systemctl start crawling-system
```

## 4. 상태 확인
```bash
sudo systemctl status crawling-system
sudo journalctl -u crawling-system -f
```

생성 시간: {datetime.now().isoformat()}
"""
        
        with open(deployment_dir / "DEPLOYMENT_GUIDE.md", "w", encoding="utf-8") as f:
            f.write(deployment_guide)
        logger.info("   ✅ DEPLOYMENT_GUIDE.md 생성 완료")
        
        logger.info(f"📦 배포 파일 생성 완료: {deployment_dir}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 배포 파일 생성 실패: {e}")
        return False


def main():
    """메인 함수 - 전체 통합 테스트 실행"""
    print("🚀 완전한 AI 에이전트 크롤링 시스템 통합 테스트")
    print("=" * 60)
    
    # 로깅 설정
    logger = setup_logging()
    logger.info("🎯 통합 테스트 시작")
    
    # 테스트 결과 추적
    test_results = {}
    
    # 1. 데이터베이스 연결 테스트
    print("\n1️⃣ 데이터베이스 연결 테스트")
    test_results['database'] = test_database_connection()
    
    # 2. AI 에이전트 시스템 테스트
    print("\n2️⃣ AI 에이전트 시스템 테스트")
    test_results['ai_agent'] = test_ai_agent_system()
    
    # 3. GCP 최적화 시스템 테스트
    print("\n3️⃣ GCP 최적화 시스템 테스트")
    test_results['gcp_optimization'] = test_gcp_optimization()
    
    # 4. 완전한 통합 시스템 데모
    print("\n4️⃣ 완전한 통합 시스템 데모")
    test_results['complete_integration'] = run_complete_integration_demo()
    
    # 5. 엑셀 통합 데모
    print("\n5️⃣ 엑셀 통합 데모")
    test_results['excel_integration'] = run_excel_integration_demo()
    
    # 6. 배포 파일 생성
    print("\n6️⃣ GCP 배포 파일 생성")
    test_results['deployment_files'] = generate_deployment_files()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 테스트 통과")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📋 다음 단계:")
        print("   1. deployment/ 폴더의 파일들을 GCP에 업로드")
        print("   2. DEPLOYMENT_GUIDE.md를 참고하여 배포 실행")
        print("   3. 실제 크롤링 작업 시작")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    logger.info(f"🏁 통합 테스트 완료: {passed_tests}/{total_tests} 성공")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc() 
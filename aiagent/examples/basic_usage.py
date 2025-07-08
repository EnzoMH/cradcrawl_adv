#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 기본 사용 예제
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from aiagent.utils.gemini_client import GeminiClient
from aiagent.metrics.performance import PerformanceTracker, PerformanceMetric

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BasicUsageExample:
    """기본 사용 예제"""
    
    def __init__(self):
        """초기화"""
        self.gemini_client = None
        self.performance_tracker = PerformanceTracker()
        logger.info("기본 사용 예제 초기화 완료")
    
    def setup_gemini_client(self):
        """Gemini 클라이언트 설정"""
        try:
            # 환경 변수에서 API 키 확인
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️  GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
                print("   다음 중 하나의 방법으로 설정해주세요:")
                print("   1. .env 파일에 GEMINI_API_KEY=your_api_key 추가")
                print("   2. 시스템 환경 변수로 설정")
                print("   3. 코드에서 직접 설정")
                return False
            
            self.gemini_client = GeminiClient(api_key=api_key)
            
            # 연결 테스트
            if self.gemini_client.test_connection():
                logger.info("✅ Gemini 클라이언트 연결 성공")
                return True
            else:
                logger.error("❌ Gemini 클라이언트 연결 실패")
                return False
                
        except Exception as e:
            logger.error(f"Gemini 클라이언트 설정 실패: {str(e)}")
            return False
    
    def example_text_generation(self):
        """텍스트 생성 예제"""
        if not self.gemini_client:
            print("❌ Gemini 클라이언트가 설정되지 않았습니다.")
            return
        
        print("\n🤖 === 텍스트 생성 예제 ===")
        
        # 성능 추적 시작
        metric = PerformanceMetric(
            agent_name="text_generator",
            task_type="text_generation",
            start_time=datetime.now()
        )
        
        try:
            prompt = "아동센터 크롤링 시스템에 대한 간단한 설명을 작성해주세요."
            
            print(f"📝 프롬프트: {prompt}")
            print("🔄 생성 중...")
            
            response = self.gemini_client.generate_content(prompt)
            
            print(f"✅ 생성 결과:\n{response}")
            
            # 성능 추적 완료
            metric.end_time = datetime.now()
            metric.success = True
            metric.confidence_score = 0.8
            self.performance_tracker.add_metric(metric)
            
        except Exception as e:
            print(f"❌ 텍스트 생성 실패: {str(e)}")
            metric.end_time = datetime.now()
            metric.success = False
            metric.error_message = str(e)
            self.performance_tracker.add_metric(metric)
    
    def example_structured_generation(self):
        """구조화된 컨텐츠 생성 예제"""
        if not self.gemini_client:
            print("❌ Gemini 클라이언트가 설정되지 않았습니다.")
            return
        
        print("\n📊 === 구조화된 컨텐츠 생성 예제 ===")
        
        # 성능 추적 시작
        metric = PerformanceMetric(
            agent_name="structured_generator",
            task_type="structured_generation",
            start_time=datetime.now()
        )
        
        try:
            prompt = """
다음 아동센터 정보를 분석하고 구조화된 데이터로 정리해주세요:

센터명: 행복한 아동센터
주소: 서울시 강남구 테헤란로 123
전화: 02-1234-5678
팩스: 02-1234-5679
홈페이지: http://happy-center.co.kr
"""
            
            print(f"📝 프롬프트: {prompt}")
            print("🔄 구조화된 데이터 생성 중...")
            
            response = self.gemini_client.generate_structured_content(prompt, "json")
            
            print(f"✅ 구조화된 결과:")
            import json
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # 성능 추적 완료
            metric.end_time = datetime.now()
            metric.success = True
            metric.confidence_score = 0.9
            self.performance_tracker.add_metric(metric)
            
        except Exception as e:
            print(f"❌ 구조화된 생성 실패: {str(e)}")
            metric.end_time = datetime.now()
            metric.success = False
            metric.error_message = str(e)
            self.performance_tracker.add_metric(metric)
    
    def example_contact_extraction(self):
        """연락처 추출 예제"""
        if not self.gemini_client:
            print("❌ Gemini 클라이언트가 설정되지 않았습니다.")
            return
        
        print("\n📞 === 연락처 추출 예제 ===")
        
        # 성능 추적 시작
        metric = PerformanceMetric(
            agent_name="contact_extractor",
            task_type="contact_extraction",
            start_time=datetime.now()
        )
        
        try:
            sample_text = """
행복한 아동센터에 오신 것을 환영합니다!
문의사항이 있으시면 언제든지 연락주세요.
전화: 02-1234-5678, 010-9876-5432
팩스: 02-1234-5679
이메일: info@happy-center.co.kr, admin@happy-center.co.kr
홈페이지: http://happy-center.co.kr
주소: 서울시 강남구 테헤란로 123, 행복빌딩 5층
"""
            
            print(f"📝 추출할 텍스트:\n{sample_text}")
            print("🔄 연락처 추출 중...")
            
            response = self.gemini_client.analyze_text(sample_text, "contact")
            
            print(f"✅ 추출 결과:")
            import json
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # 성능 추적 완료
            metric.end_time = datetime.now()
            metric.success = True
            metric.confidence_score = response.get('confidence', 0.7)
            self.performance_tracker.add_metric(metric)
            
        except Exception as e:
            print(f"❌ 연락처 추출 실패: {str(e)}")
            metric.end_time = datetime.now()
            metric.success = False
            metric.error_message = str(e)
            self.performance_tracker.add_metric(metric)
    
    def example_data_validation(self):
        """데이터 검증 예제"""
        if not self.gemini_client:
            print("❌ Gemini 클라이언트가 설정되지 않았습니다.")
            return
        
        print("\n✅ === 데이터 검증 예제 ===")
        
        # 성능 추적 시작
        metric = PerformanceMetric(
            agent_name="data_validator",
            task_type="data_validation",
            start_time=datetime.now()
        )
        
        try:
            test_data = {
                "센터명": "행복한 아동센터",
                "전화번호": "02-1234-5678",
                "팩스번호": "02-1234-5679",
                "이메일": "info@happy-center.co.kr",
                "홈페이지": "http://happy-center.co.kr",
                "주소": "서울시 강남구 테헤란로 123"
            }
            
            print(f"📝 검증할 데이터:")
            import json
            print(json.dumps(test_data, indent=2, ensure_ascii=False))
            print("🔄 데이터 검증 중...")
            
            response = self.gemini_client.analyze_text(str(test_data), "validation")
            
            print(f"✅ 검증 결과:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # 성능 추적 완료
            metric.end_time = datetime.now()
            metric.success = True
            metric.confidence_score = response.get('confidence', 0.7)
            self.performance_tracker.add_metric(metric)
            
        except Exception as e:
            print(f"❌ 데이터 검증 실패: {str(e)}")
            metric.end_time = datetime.now()
            metric.success = False
            metric.error_message = str(e)
            self.performance_tracker.add_metric(metric)
    
    def show_performance_stats(self):
        """성능 통계 표시"""
        print("\n📊 === 성능 통계 ===")
        
        # 전체 통계
        all_stats = self.performance_tracker.get_all_stats()
        if all_stats:
            for agent_name, stats in all_stats.items():
                print(f"\n🤖 에이전트: {agent_name}")
                print(f"   총 작업: {stats['total_tasks']}")
                print(f"   성공: {stats['successful_tasks']}")
                print(f"   실패: {stats['failed_tasks']}")
                print(f"   성공률: {stats['success_rate']:.2%}")
                print(f"   평균 소요시간: {stats['average_duration']:.2f}초")
                print(f"   평균 신뢰도: {stats['average_confidence']:.2f}")
        else:
            print("📊 아직 수집된 성능 데이터가 없습니다.")
        
        # 시스템 개요
        report = self.performance_tracker.generate_performance_report()
        system_overview = report.get('system_overview', {})
        
        if system_overview:
            print(f"\n🔍 시스템 개요:")
            print(f"   전체 작업: {system_overview.get('total_tasks', 0)}")
            print(f"   전체 성공률: {system_overview.get('overall_success_rate', 0):.2%}")
            print(f"   평균 소요시간: {system_overview.get('average_duration', 0):.2f}초")
            print(f"   활성 에이전트: {system_overview.get('active_agents', 0)}")
    
    def run_all_examples(self):
        """모든 예제 실행"""
        print("🚀 === AI 에이전트 시스템 기본 사용 예제 ===")
        
        # Gemini 클라이언트 설정
        if not self.setup_gemini_client():
            print("❌ Gemini 클라이언트 설정에 실패했습니다. 예제를 종료합니다.")
            return
        
        # 각 예제 실행
        self.example_text_generation()
        self.example_structured_generation()
        self.example_contact_extraction()
        self.example_data_validation()
        
        # 성능 통계 표시
        self.show_performance_stats()
        
        print("\n🎉 === 모든 예제 완료 ===")

def main():
    """메인 함수"""
    example = BasicUsageExample()
    example.run_all_examples()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 고급 데모 예제
실제 크롤링 시나리오를 시뮬레이션하는 종합 데모
"""

import asyncio
import logging
import json
from typing import Dict, List, Any
from datetime import datetime
import time

# AI 에이전트 시스템 import
from ..core.agent_system import AIAgentSystem
from ..core.coordinator import AgentCoordinator
from ..agents import HomepageAgent, ContactAgent, ValidationAgent, OptimizerAgent
from ..config.agent_config import ConfigPresets
from ..metrics.performance import PerformanceTracker

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedDemoExample:
    """고급 데모 예제 클래스"""
    
    def __init__(self):
        """데모 초기화"""
        self.demo_data = self._load_demo_data()
        self.results = []
        
    def _load_demo_data(self) -> List[Dict[str, Any]]:
        """데모용 조직 데이터 로드"""
        return [
            {
                'organization_name': '서울시립어린이병원',
                'address': '서울특별시 중구 소공로 120',
                'phone': '02-570-8000',
                'category': '의료기관'
            },
            {
                'organization_name': '부산광역시청',
                'address': '부산광역시 연제구 중앙대로 1001',
                'phone': '051-888-1000',
                'category': '공공기관'
            },
            {
                'organization_name': '경기도교육청',
                'address': '경기도 수원시 영통구 도청로 30',
                'phone': '031-820-0114',
                'category': '교육기관'
            },
            {
                'organization_name': '대한적십자사',
                'address': '서울특별시 중구 남산동2가 98-5',
                'phone': '02-3705-3705',
                'category': '비영리단체'
            },
            {
                'organization_name': '국립중앙박물관',
                'address': '서울특별시 용산구 서빙고로 137',
                'phone': '02-2077-9000',
                'category': '문화기관'
            }
        ]
    
    async def run_comprehensive_demo(self):
        """종합 데모 실행"""
        print("🚀 AI 에이전트 시스템 - 고급 데모 시작")
        print("=" * 60)
        
        # 1. 시스템 초기화 데모
        await self._demo_system_initialization()
        
        # 2. 단일 조직 처리 데모
        await self._demo_single_organization_processing()
        
        # 3. 배치 처리 데모
        await self._demo_batch_processing()
        
        # 4. 성능 분석 데모
        await self._demo_performance_analysis()
        
        # 5. 오류 처리 데모
        await self._demo_error_handling()
        
        # 6. 최종 결과 분석
        await self._demo_final_analysis()
        
        print("\n✅ 고급 데모 완료!")
    
    async def _demo_system_initialization(self):
        """시스템 초기화 데모"""
        print("\n📋 1. 시스템 초기화 데모")
        print("-" * 40)
        
        # 다양한 설정으로 시스템 초기화
        configs = ['development', 'production', 'high_performance']
        
        for config in configs:
            print(f"\n🔧 {config} 환경 초기화...")
            
            system = AIAgentSystem(config_preset=config)
            system.start_system()
            
            # 시스템 상태 확인
            stats = system.get_system_statistics()
            print(f"   ✓ 활성 에이전트: {stats['system_stats']['active_agents']}개")
            print(f"   ✓ 설정 프리셋: {stats['config_preset']}")
            
            # 헬스체크
            health = await system.health_check()
            print(f"   ✓ 시스템 상태: {health['overall_health']}")
            
            system.stop_system()
            print(f"   ✓ {config} 환경 정리 완료")
    
    async def _demo_single_organization_processing(self):
        """단일 조직 처리 데모"""
        print("\n🏢 2. 단일 조직 처리 데모")
        print("-" * 40)
        
        # 고성능 설정으로 시스템 초기화
        system = AIAgentSystem(config_preset='high_performance')
        system.start_system()
        
        # 첫 번째 조직 데이터 선택
        org_data = self.demo_data[0]
        print(f"\n📊 처리 대상: {org_data['organization_name']}")
        
        # 단계별 처리 과정 시뮬레이션
        start_time = time.time()
        
        try:
            # 크롤링 작업 실행
            result = await system.process_crawling_task(org_data)
            
            processing_time = time.time() - start_time
            
            if result['success']:
                print(f"✅ 처리 완료 ({processing_time:.2f}초)")
                print(f"   📈 전체 신뢰도: {result['overall_confidence']:.2%}")
                
                # 결과 상세 분석
                final_data = result['final_data']
                print(f"   📞 전화번호: {len(final_data.get('phone_numbers', []))}개")
                print(f"   📠 팩스번호: {len(final_data.get('fax_numbers', []))}개")
                print(f"   📧 이메일: {len(final_data.get('email_addresses', []))}개")
                print(f"   🌐 웹사이트: {len(final_data.get('websites', []))}개")
                print(f"   🏆 품질 등급: {final_data.get('quality_grade', 'N/A')}")
                
                self.results.append(result)
                
            else:
                print(f"❌ 처리 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")
        
        finally:
            system.stop_system()
    
    async def _demo_batch_processing(self):
        """배치 처리 데모"""
        print("\n📦 3. 배치 처리 데모")
        print("-" * 40)
        
        # 운영 환경 설정으로 시스템 초기화
        system = AIAgentSystem(config_preset='production')
        system.start_system()
        
        print(f"📋 총 {len(self.demo_data)}개 조직 배치 처리 시작...")
        
        batch_start_time = time.time()
        successful_count = 0
        failed_count = 0
        
        # 동시 처리 (최대 3개)
        semaphore = asyncio.Semaphore(3)
        
        async def process_single_org(org_data):
            async with semaphore:
                try:
                    result = await system.process_crawling_task(org_data)
                    return result
                except Exception as e:
                    return {'success': False, 'error': str(e), 'org_data': org_data}
        
        # 모든 조직 동시 처리
        tasks = [process_single_org(org_data) for org_data in self.demo_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 분석
        for i, result in enumerate(results):
            org_name = self.demo_data[i]['organization_name']
            
            if isinstance(result, Exception):
                print(f"❌ {org_name}: 예외 발생 - {str(result)}")
                failed_count += 1
            elif result.get('success', False):
                confidence = result.get('overall_confidence', 0)
                print(f"✅ {org_name}: 성공 (신뢰도: {confidence:.1%})")
                successful_count += 1
                self.results.append(result)
            else:
                print(f"❌ {org_name}: 실패 - {result.get('error', 'Unknown')}")
                failed_count += 1
        
        batch_time = time.time() - batch_start_time
        
        print(f"\n📊 배치 처리 결과:")
        print(f"   ✅ 성공: {successful_count}개")
        print(f"   ❌ 실패: {failed_count}개")
        print(f"   📈 성공률: {successful_count/(successful_count+failed_count)*100:.1f}%")
        print(f"   ⏱️ 총 처리시간: {batch_time:.2f}초")
        print(f"   ⚡ 평균 처리시간: {batch_time/len(self.demo_data):.2f}초/건")
        
        system.stop_system()
    
    async def _demo_performance_analysis(self):
        """성능 분석 데모"""
        print("\n📈 4. 성능 분석 데모")
        print("-" * 40)
        
        if not self.results:
            print("❌ 분석할 결과가 없습니다.")
            return
        
        # 성능 메트릭 수집
        confidence_scores = [r['overall_confidence'] for r in self.results]
        processing_times = [r.get('processing_time', 0) for r in self.results]
        quality_grades = [r['final_data'].get('quality_grade', 'F') for r in self.results]
        
        # 통계 계산
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # 품질 등급 분포
        grade_counts = {}
        for grade in quality_grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        print(f"📊 성능 분석 결과:")
        print(f"   🎯 평균 신뢰도: {avg_confidence:.2%}")
        print(f"   ⏱️ 평균 처리시간: {avg_processing_time:.2f}초")
        print(f"   🏆 품질 등급 분포:")
        for grade, count in sorted(grade_counts.items()):
            print(f"      {grade}급: {count}개 ({count/len(self.results)*100:.1f}%)")
        
        # 성능 트렌드 분석
        print(f"\n📈 성능 트렌드:")
        if len(confidence_scores) >= 3:
            first_half = confidence_scores[:len(confidence_scores)//2]
            second_half = confidence_scores[len(confidence_scores)//2:]
            
            trend = "개선" if sum(second_half)/len(second_half) > sum(first_half)/len(first_half) else "유지"
            print(f"   📊 신뢰도 트렌드: {trend}")
        
        # 최고/최저 성능 사례
        best_idx = confidence_scores.index(max(confidence_scores))
        worst_idx = confidence_scores.index(min(confidence_scores))
        
        print(f"\n🏆 최고 성능:")
        best_org = next(org for org in self.demo_data if org['organization_name'] in str(self.results[best_idx]))
        print(f"   기관: {best_org['organization_name'] if best_org else 'Unknown'}")
        print(f"   신뢰도: {confidence_scores[best_idx]:.2%}")
        
        print(f"\n⚠️ 개선 필요:")
        worst_org = next(org for org in self.demo_data if org['organization_name'] in str(self.results[worst_idx]))
        print(f"   기관: {worst_org['organization_name'] if worst_org else 'Unknown'}")
        print(f"   신뢰도: {confidence_scores[worst_idx]:.2%}")
    
    async def _demo_error_handling(self):
        """오류 처리 데모"""
        print("\n🚨 5. 오류 처리 데모")
        print("-" * 40)
        
        system = AIAgentSystem(config_preset='development')
        system.start_system()
        
        # 다양한 오류 시나리오 테스트
        error_scenarios = [
            {
                'name': '빈 데이터',
                'data': {}
            },
            {
                'name': '잘못된 형식',
                'data': {
                    'organization_name': '',
                    'address': None,
                    'phone': 'invalid'
                }
            },
            {
                'name': '부분 데이터',
                'data': {
                    'organization_name': '테스트기관'
                    # 주소, 전화번호 누락
                }
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n🧪 테스트: {scenario['name']}")
            
            try:
                result = await system.process_crawling_task(scenario['data'])
                
                if result['success']:
                    print(f"   ✅ 예상과 달리 성공 (신뢰도: {result.get('overall_confidence', 0):.1%})")
                else:
                    print(f"   ⚠️ 예상대로 실패: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ 예외 발생: {str(e)}")
        
        # 시스템 복구 테스트
        print(f"\n🔄 시스템 복구 테스트:")
        try:
            # 정상 데이터로 복구 확인
            normal_data = self.demo_data[0]
            result = await system.process_crawling_task(normal_data)
            
            if result['success']:
                print(f"   ✅ 시스템 정상 복구 확인")
            else:
                print(f"   ⚠️ 시스템 복구 실패")
                
        except Exception as e:
            print(f"   ❌ 복구 테스트 중 예외: {str(e)}")
        
        system.stop_system()
    
    async def _demo_final_analysis(self):
        """최종 결과 분석"""
        print("\n📋 6. 최종 결과 분석")
        print("-" * 40)
        
        if not self.results:
            print("❌ 분석할 결과가 없습니다.")
            return
        
        # 종합 통계
        total_orgs = len(self.demo_data)
        successful_orgs = len(self.results)
        
        # 데이터 품질 분석
        total_contacts = 0
        total_validations = 0
        high_quality_count = 0
        
        for result in self.results:
            final_data = result['final_data']
            
            # 연락처 정보 집계
            total_contacts += len(final_data.get('phone_numbers', []))
            total_contacts += len(final_data.get('email_addresses', []))
            total_contacts += len(final_data.get('websites', []))
            
            # 검증 점수 집계
            validation_score = final_data.get('validation_score', 0)
            total_validations += validation_score
            
            # 고품질 데이터 카운트
            if final_data.get('quality_grade', 'F') in ['A', 'B']:
                high_quality_count += 1
        
        avg_validation_score = total_validations / successful_orgs if successful_orgs > 0 else 0
        
        print(f"🎯 종합 결과:")
        print(f"   📊 처리 현황: {successful_orgs}/{total_orgs} ({successful_orgs/total_orgs*100:.1f}%)")
        print(f"   📞 수집된 연락처: {total_contacts}개")
        print(f"   📈 평균 검증 점수: {avg_validation_score:.2f}")
        print(f"   🏆 고품질 데이터: {high_quality_count}개 ({high_quality_count/successful_orgs*100:.1f}%)")
        
        # 카테고리별 분석
        category_stats = {}
        for i, result in enumerate(self.results):
            if i < len(self.demo_data):
                category = self.demo_data[i]['category']
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'total_confidence': 0}
                
                category_stats[category]['count'] += 1
                category_stats[category]['total_confidence'] += result['overall_confidence']
        
        print(f"\n📊 카테고리별 성능:")
        for category, stats in category_stats.items():
            avg_confidence = stats['total_confidence'] / stats['count']
            print(f"   {category}: {stats['count']}건, 평균 신뢰도 {avg_confidence:.1%}")
        
        # 권장사항 생성
        print(f"\n💡 권장사항:")
        
        if avg_validation_score < 0.7:
            print(f"   🔧 데이터 검증 로직 개선 필요")
        
        if high_quality_count / successful_orgs < 0.5:
            print(f"   📈 데이터 품질 향상 방안 검토 필요")
        
        if successful_orgs / total_orgs < 0.8:
            print(f"   🚀 처리 성공률 개선 방안 필요")
        
        print(f"   ✅ 전반적으로 안정적인 시스템 성능 확인")

async def run_advanced_demo():
    """고급 데모 실행 함수"""
    demo = AdvancedDemoExample()
    await demo.run_comprehensive_demo()

def run_demo_sync():
    """동기 방식으로 데모 실행"""
    asyncio.run(run_advanced_demo())

if __name__ == "__main__":
    # 직접 실행 시 데모 시작
    print("🤖 AI 에이전트 시스템 - 고급 데모")
    print("이 데모는 실제 크롤링 시나리오를 시뮬레이션합니다.")
    print("Gemini API 키가 설정되어 있어야 정상 동작합니다.")
    print()
    
    try:
        run_demo_sync()
    except KeyboardInterrupt:
        print("\n\n⏹️ 데모가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 데모 실행 중 오류 발생: {str(e)}")
        print("Gemini API 키 설정을 확인해주세요.") 
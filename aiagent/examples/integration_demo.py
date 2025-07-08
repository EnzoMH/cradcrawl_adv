#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 기존 크롤링 시스템 통합 데모
centercrawling.py와의 연동 예제
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aiagent.core.agent_system import AIAgentSystem
from aiagent.agents import create_agent

class CrawlingIntegrationDemo:
    """크롤링 시스템 통합 데모"""
    
    def __init__(self):
        self.ai_system = None
        
    async def setup_ai_system(self):
        """AI 시스템 초기화"""
        print("🤖 AI 에이전트 시스템 초기화...")
        
        self.ai_system = AIAgentSystem(config_preset='production')
        self.ai_system.start_system()
        
        # 시스템 상태 확인
        health = await self.ai_system.health_check()
        print(f"✅ 시스템 상태: {health['overall_health']}")
        
        return self.ai_system
    
    async def process_organization_with_ai(self, org_data):
        """AI 에이전트를 활용한 조직 데이터 처리"""
        if not self.ai_system:
            await self.setup_ai_system()
        
        print(f"\n🏢 처리 중: {org_data.get('organization_name', 'Unknown')}")
        
        try:
            # AI 에이전트 시스템으로 처리
            result = await self.ai_system.process_crawling_task(org_data)
            
            if result['success']:
                print(f"✅ AI 처리 완료 (신뢰도: {result['overall_confidence']:.1%})")
                
                # 결과를 기존 크롤링 시스템 형식으로 변환
                converted_result = self._convert_ai_result_to_legacy_format(result)
                return converted_result
            else:
                print(f"❌ AI 처리 실패: {result.get('error', 'Unknown')}")
                return None
                
        except Exception as e:
            print(f"❌ AI 처리 중 예외: {str(e)}")
            return None
    
    def _convert_ai_result_to_legacy_format(self, ai_result):
        """AI 결과를 기존 시스템 형식으로 변환"""
        final_data = ai_result.get('final_data', {})
        
        # 기존 크롤링 시스템에서 기대하는 형식으로 변환
        legacy_format = {
            'homepage_url': ai_result.get('results', {}).get('homepage_search', {}).get('data', {}).get('homepage_url', ''),
            'phone_numbers': final_data.get('phone_numbers', []),
            'fax_numbers': final_data.get('fax_numbers', []),
            'email_addresses': final_data.get('email_addresses', []),
            'websites': final_data.get('websites', []),
            'addresses': final_data.get('addresses', []),
            'quality_score': final_data.get('validation_score', 0.0),
            'quality_grade': final_data.get('quality_grade', 'F'),
            'ai_confidence': ai_result.get('overall_confidence', 0.0),
            'processing_metadata': {
                'task_id': ai_result.get('task_id'),
                'timestamp': ai_result.get('timestamp'),
                'ai_enhanced': True
            }
        }
        
        return legacy_format
    
    async def enhanced_crawling_workflow(self, organizations_list):
        """향상된 크롤링 워크플로우"""
        print("🚀 AI 강화 크롤링 워크플로우 시작")
        print("=" * 50)
        
        results = []
        
        for i, org_data in enumerate(organizations_list, 1):
            print(f"\n📋 [{i}/{len(organizations_list)}] 처리 중...")
            
            # AI 에이전트로 처리
            ai_result = await self.process_organization_with_ai(org_data)
            
            if ai_result:
                # 결과 검증 및 후처리
                validated_result = self._validate_and_enhance_result(org_data, ai_result)
                results.append(validated_result)
                
                # 진행 상황 출력
                self._print_processing_summary(validated_result)
            else:
                print(f"⚠️ {org_data.get('organization_name', 'Unknown')} 처리 실패")
        
        # 최종 결과 요약
        self._print_final_summary(results)
        
        return results
    
    def _validate_and_enhance_result(self, original_data, ai_result):
        """결과 검증 및 강화"""
        enhanced_result = ai_result.copy()
        
        # 원본 데이터와 비교 검증
        enhanced_result['original_data'] = original_data
        enhanced_result['validation_notes'] = []
        
        # 전화번호 일치성 검사
        original_phone = original_data.get('phone', '')
        ai_phones = ai_result.get('phone_numbers', [])
        
        if original_phone and original_phone not in ai_phones:
            enhanced_result['validation_notes'].append(f"원본 전화번호 불일치: {original_phone}")
        
        # 주소 정보 일치성 검사
        original_address = original_data.get('address', '')
        ai_addresses = ai_result.get('addresses', [])
        
        if original_address and not any(original_address in addr for addr in ai_addresses):
            enhanced_result['validation_notes'].append(f"주소 정보 검증 필요")
        
        # 품질 점수 조정
        if enhanced_result['validation_notes']:
            enhanced_result['quality_score'] *= 0.9  # 검증 이슈가 있으면 점수 조정
        
        return enhanced_result
    
    def _print_processing_summary(self, result):
        """처리 결과 요약 출력"""
        print(f"   📞 전화: {len(result.get('phone_numbers', []))}개")
        print(f"   📧 이메일: {len(result.get('email_addresses', []))}개")
        print(f"   🌐 웹사이트: {len(result.get('websites', []))}개")
        print(f"   🏆 품질: {result.get('quality_grade', 'N/A')}급 ({result.get('quality_score', 0):.2f})")
        
        if result.get('validation_notes'):
            print(f"   ⚠️ 검증 이슈: {len(result['validation_notes'])}건")
    
    def _print_final_summary(self, results):
        """최종 결과 요약"""
        print(f"\n📊 최종 처리 결과")
        print("=" * 50)
        
        if not results:
            print("❌ 처리된 결과가 없습니다.")
            return
        
        total_contacts = sum(
            len(r.get('phone_numbers', [])) + 
            len(r.get('email_addresses', [])) + 
            len(r.get('websites', []))
            for r in results
        )
        
        quality_grades = [r.get('quality_grade', 'F') for r in results]
        grade_counts = {grade: quality_grades.count(grade) for grade in set(quality_grades)}
        
        avg_confidence = sum(r.get('ai_confidence', 0) for r in results) / len(results)
        
        print(f"✅ 처리 완료: {len(results)}개 조직")
        print(f"📞 총 연락처: {total_contacts}개")
        print(f"🎯 평균 AI 신뢰도: {avg_confidence:.1%}")
        print(f"🏆 품질 등급 분포:")
        for grade, count in sorted(grade_counts.items()):
            print(f"   {grade}급: {count}개")
    
    async def cleanup(self):
        """리소스 정리"""
        if self.ai_system:
            self.ai_system.stop_system()
            print("🔄 AI 시스템 정리 완료")

async def run_integration_demo():
    """통합 데모 실행"""
    demo = CrawlingIntegrationDemo()
    
    # 샘플 조직 데이터 (기존 크롤링 시스템 형식)
    sample_organizations = [
        {
            'organization_name': '서울대학교병원',
            'address': '서울특별시 종로구 대학로 101',
            'phone': '02-2072-2114'
        },
        {
            'organization_name': '부산시립미술관',
            'address': '부산광역시 해운대구 APEC로 58',
            'phone': '051-744-2602'
        },
        {
            'organization_name': '경기도립중앙도서관',
            'address': '경기도 수원시 영통구 월드컵로 310',
            'phone': '031-249-2300'
        }
    ]
    
    try:
        # AI 강화 크롤링 실행
        results = await demo.enhanced_crawling_workflow(sample_organizations)
        
        # 결과를 JSON으로 저장 (선택사항)
        if results:
            import json
            output_file = project_root / 'ai_enhanced_results.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 결과 저장: {output_file}")
        
    except Exception as e:
        print(f"❌ 데모 실행 중 오류: {str(e)}")
    
    finally:
        await demo.cleanup()

def main():
    """메인 함수"""
    print("🔗 AI 에이전트 시스템 - 크롤링 통합 데모")
    print("기존 크롤링 시스템과 AI 에이전트의 연동을 시연합니다.")
    print()
    
    try:
        asyncio.run(run_integration_demo())
    except KeyboardInterrupt:
        print("\n⏹️ 데모가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
레거시 시스템 통합 레이어
기존 crawler/ 및 test/ 폴더의 구현체들을 AI 에이전트 시스템과 통합
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

# 프로젝트 루트 경로 설정
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 기존 구현체들 import
try:
    from cralwer.url_extractor import HomepageParser
    from cralwer.phone_extractor import search_phone_number, extract_phone_numbers, setup_driver
    from cralwer.fax_extractor import GoogleContactCrawler
    from test.data_processor import DataProcessor
    LEGACY_AVAILABLE = True
    print("✅ 레거시 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ 레거시 모듈 로드 실패: {e}")
    LEGACY_AVAILABLE = False

# AI 에이전트 시스템 import
try:
    from aiagent.core.enhanced_agent_system import (
        SearchStrategyAgent, ValidationAgent, ResourceManager, 
        CrawlingResult, DataQualityGrade
    )
    from aiagent.config.gcp_optimization import GCPOptimizer
    AI_AGENT_AVAILABLE = True
    print("✅ AI 에이전트 시스템 로드 성공")
except ImportError as e:
    print(f"⚠️ AI 에이전트 시스템 로드 실패: {e}")
    AI_AGENT_AVAILABLE = False

@dataclass
class IntegrationConfig:
    """통합 설정"""
    use_ai_primary: bool = True  # AI 우선 사용
    use_legacy_fallback: bool = True  # 레거시 fallback
    hybrid_validation: bool = True  # 하이브리드 검증
    performance_comparison: bool = True  # 성능 비교
    data_quality_threshold: float = 0.7  # 데이터 품질 임계값

class LegacyIntegrationManager:
    """레거시 시스템 통합 관리자"""
    
    def __init__(self, config: IntegrationConfig = None):
        self.config = config or IntegrationConfig()
        self.logger = self._setup_logger()
        
        # 시스템 초기화
        self.ai_agents = {}
        self.legacy_crawlers = {}
        self.data_processor = None
        self.gcp_optimizer = None
        
        self._initialize_systems()
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('legacy_integration')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_systems(self):
        """시스템 초기화"""
        self.logger.info("🔄 통합 시스템 초기화 시작")
        
        # AI 에이전트 시스템 초기화
        if AI_AGENT_AVAILABLE:
            try:
                self.ai_agents['search'] = SearchStrategyAgent()
                self.ai_agents['validation'] = ValidationAgent()
                self.ai_agents['resource'] = ResourceManager()
                self.gcp_optimizer = GCPOptimizer()
                self.logger.info("✅ AI 에이전트 시스템 초기화 완료")
            except Exception as e:
                self.logger.error(f"❌ AI 에이전트 시스템 초기화 실패: {e}")
        
        # 레거시 시스템 초기화
        if LEGACY_AVAILABLE:
            try:
                self.legacy_crawlers['homepage'] = HomepageParser(headless=True)
                self.legacy_crawlers['contact'] = GoogleContactCrawler()
                self.data_processor = DataProcessor()
                self.logger.info("✅ 레거시 시스템 초기화 완료")
            except Exception as e:
                self.logger.error(f"❌ 레거시 시스템 초기화 실패: {e}")
    
    def integrated_crawl(self, organization: Dict[str, Any]) -> CrawlingResult:
        """통합 크롤링 수행"""
        self.logger.info(f"🔍 통합 크롤링 시작: {organization.get('name', 'Unknown')}")
        
        # AI 우선 시도
        if self.config.use_ai_primary and AI_AGENT_AVAILABLE:
            try:
                result = self._ai_crawl(organization)
                if self._is_result_satisfactory(result):
                    self.logger.info("✅ AI 크롤링 성공")
                    return result
                else:
                    self.logger.warning("⚠️ AI 크롤링 품질 부족 - 레거시 fallback")
            except Exception as e:
                self.logger.error(f"❌ AI 크롤링 실패: {e}")
        
        # 레거시 fallback
        if self.config.use_legacy_fallback and LEGACY_AVAILABLE:
            try:
                result = self._legacy_crawl(organization)
                self.logger.info("✅ 레거시 크롤링 완료")
                return result
            except Exception as e:
                self.logger.error(f"❌ 레거시 크롤링 실패: {e}")
        
        # 최소한의 결과 반환
        return CrawlingResult(
            organization_name=organization.get('name', ''),
            address=organization.get('address', ''),
            phone='',
            fax='',
            email='',
            homepage='',
            quality_grade=DataQualityGrade.F,
            confidence_score=0.0,
            processing_time=0.0,
            data_sources=['minimal']
        )
    
    def _ai_crawl(self, organization: Dict[str, Any]) -> CrawlingResult:
        """AI 에이전트 기반 크롤링"""
        # 검색 전략 생성
        search_agent = self.ai_agents['search']
        search_queries = search_agent.generate_search_queries(
            organization.get('name', ''),
            organization.get('address', ''),
            organization.get('phone', ''),
            organization.get('category', '')
        )
        
        # 크롤링 수행 (간단한 구현)
        result_data = {
            'organization_name': organization.get('name', ''),
            'address': organization.get('address', ''),
            'phone': organization.get('phone', ''),
            'fax': '',
            'email': '',
            'homepage': '',
            'quality_grade': DataQualityGrade.C,
            'confidence_score': 0.8,
            'processing_time': 2.0,
            'data_sources': ['ai_agent']
        }
        
        return CrawlingResult(**result_data)
    
    def _legacy_crawl(self, organization: Dict[str, Any]) -> CrawlingResult:
        """레거시 시스템 기반 크롤링"""
        org_name = organization.get('name', '')
        
        # 전화번호 추출
        phone_numbers = []
        if 'contact' in self.legacy_crawlers:
            try:
                phone_result = self.legacy_crawlers['contact'].search_phone_number(org_name)
                if phone_result:
                    phone_numbers = phone_result.get('phone_numbers', [])
            except Exception as e:
                self.logger.error(f"전화번호 추출 실패: {e}")
        
        # 팩스번호 추출
        fax_numbers = []
        if 'contact' in self.legacy_crawlers:
            try:
                fax_result = self.legacy_crawlers['contact'].search_fax_number(org_name)
                if fax_result:
                    fax_numbers = fax_result.get('fax_numbers', [])
            except Exception as e:
                self.logger.error(f"팩스번호 추출 실패: {e}")
        
        # 홈페이지 추출
        homepage_info = {}
        if 'homepage' in self.legacy_crawlers:
            try:
                homepage_result = self.legacy_crawlers['homepage'].extract_page_content(
                    f"https://www.google.com/search?q={org_name}"
                )
                if homepage_result:
                    homepage_info = homepage_result
            except Exception as e:
                self.logger.error(f"홈페이지 추출 실패: {e}")
        
        # 데이터 품질 평가
        quality_grade = self._evaluate_legacy_quality(
            phone_numbers, fax_numbers, homepage_info
        )
        
        result_data = {
            'organization_name': org_name,
            'address': organization.get('address', ''),
            'phone': phone_numbers[0] if phone_numbers else '',
            'fax': fax_numbers[0] if fax_numbers else '',
            'email': homepage_info.get('email', ''),
            'homepage': homepage_info.get('url', ''),
            'quality_grade': quality_grade,
            'confidence_score': 0.6,
            'processing_time': 5.0,
            'data_sources': ['legacy_crawler']
        }
        
        return CrawlingResult(**result_data)
    
    def _is_result_satisfactory(self, result: CrawlingResult) -> bool:
        """결과가 만족스러운지 확인"""
        if not result:
            return False
        
        # 품질 등급 확인
        quality_threshold = {
            DataQualityGrade.A: 1.0,
            DataQualityGrade.B: 0.8,
            DataQualityGrade.C: 0.6,
            DataQualityGrade.D: 0.4,
            DataQualityGrade.E: 0.2,
            DataQualityGrade.F: 0.0
        }
        
        return quality_threshold.get(result.quality_grade, 0.0) >= self.config.data_quality_threshold
    
    def _evaluate_legacy_quality(self, phone_numbers: List[str], 
                                fax_numbers: List[str], 
                                homepage_info: Dict) -> DataQualityGrade:
        """레거시 결과의 품질 평가"""
        score = 0
        
        # 전화번호 (30점)
        if phone_numbers:
            score += 30
        
        # 팩스번호 (20점)
        if fax_numbers:
            score += 20
        
        # 홈페이지 (25점)
        if homepage_info.get('url'):
            score += 25
        
        # 이메일 (15점)
        if homepage_info.get('email'):
            score += 15
        
        # 기타 정보 (10점)
        if homepage_info.get('content'):
            score += 10
        
        # 등급 결정
        if score >= 90:
            return DataQualityGrade.A
        elif score >= 70:
            return DataQualityGrade.B
        elif score >= 50:
            return DataQualityGrade.C
        elif score >= 30:
            return DataQualityGrade.D
        elif score >= 10:
            return DataQualityGrade.E
        else:
            return DataQualityGrade.F
    
    def hybrid_validation(self, ai_result: CrawlingResult, 
                         legacy_result: CrawlingResult) -> CrawlingResult:
        """하이브리드 검증 수행"""
        if not self.config.hybrid_validation:
            return ai_result
        
        self.logger.info("🔍 하이브리드 검증 시작")
        
        # 최고 품질 결과 선택
        if ai_result.quality_grade.value < legacy_result.quality_grade.value:
            best_result = ai_result
            backup_result = legacy_result
        else:
            best_result = legacy_result
            backup_result = ai_result
        
        # 필드별 보완
        validated_data = {
            'organization_name': best_result.organization_name,
            'address': best_result.address,
            'phone': best_result.phone or backup_result.phone,
            'fax': best_result.fax or backup_result.fax,
            'email': best_result.email or backup_result.email,
            'homepage': best_result.homepage or backup_result.homepage,
            'quality_grade': best_result.quality_grade,
            'confidence_score': max(best_result.confidence_score, backup_result.confidence_score),
            'processing_time': best_result.processing_time + backup_result.processing_time,
            'data_sources': best_result.data_sources + backup_result.data_sources
        }
        
        return CrawlingResult(**validated_data)
    
    def process_batch(self, organizations: List[Dict[str, Any]], 
                     output_file: str = None) -> List[CrawlingResult]:
        """배치 처리"""
        self.logger.info(f"📊 배치 처리 시작: {len(organizations)}개 조직")
        
        results = []
        
        for i, org in enumerate(organizations, 1):
            self.logger.info(f"처리 중 ({i}/{len(organizations)}): {org.get('name', 'Unknown')}")
            
            try:
                result = self.integrated_crawl(org)
                results.append(result)
                
                # 진행률 출력
                if i % 10 == 0:
                    self.logger.info(f"진행률: {i}/{len(organizations)} ({i/len(organizations)*100:.1f}%)")
                    
            except Exception as e:
                self.logger.error(f"처리 실패: {org.get('name', 'Unknown')} - {e}")
                continue
        
        # 결과 저장
        if output_file and self.data_processor:
            try:
                self._save_results(results, output_file)
                self.logger.info(f"✅ 결과 저장 완료: {output_file}")
            except Exception as e:
                self.logger.error(f"❌ 결과 저장 실패: {e}")
        
        self.logger.info(f"✅ 배치 처리 완료: {len(results)}개 결과")
        return results
    
    def _save_results(self, results: List[CrawlingResult], output_file: str):
        """결과 저장"""
        # CrawlingResult를 dict로 변환
        results_dict = []
        for result in results:
            result_dict = {
                'organization_name': result.organization_name,
                'address': result.address,
                'phone': result.phone,
                'fax': result.fax,
                'email': result.email,
                'homepage': result.homepage,
                'quality_grade': result.quality_grade.name,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'data_sources': result.data_sources
            }
            results_dict.append(result_dict)
        
        # 파일 형식에 따라 저장
        if output_file.endswith('.json'):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)
        elif output_file.endswith(('.xlsx', '.xls')):
            if self.data_processor:
                # 임시 JSON 파일로 저장 후 Excel로 변환
                temp_json = output_file.replace('.xlsx', '_temp.json').replace('.xls', '_temp.json')
                with open(temp_json, 'w', encoding='utf-8') as f:
                    json.dump(results_dict, f, ensure_ascii=False, indent=2)
                
                self.data_processor.json_to_excel(temp_json, output_file)
                os.remove(temp_json)  # 임시 파일 삭제
    
    def performance_comparison(self, organization: Dict[str, Any]) -> Dict[str, Any]:
        """성능 비교 분석"""
        if not self.config.performance_comparison:
            return {}
        
        self.logger.info("📊 성능 비교 분석 시작")
        
        comparison_results = {
            'organization': organization.get('name', ''),
            'ai_result': None,
            'legacy_result': None,
            'comparison': {}
        }
        
        # AI 시스템 테스트
        if AI_AGENT_AVAILABLE:
            try:
                import time
                start_time = time.time()
                ai_result = self._ai_crawl(organization)
                ai_time = time.time() - start_time
                
                comparison_results['ai_result'] = {
                    'quality_grade': ai_result.quality_grade.name,
                    'confidence_score': ai_result.confidence_score,
                    'processing_time': ai_time,
                    'data_completeness': self._calculate_completeness(ai_result)
                }
            except Exception as e:
                self.logger.error(f"AI 시스템 테스트 실패: {e}")
        
        # 레거시 시스템 테스트
        if LEGACY_AVAILABLE:
            try:
                import time
                start_time = time.time()
                legacy_result = self._legacy_crawl(organization)
                legacy_time = time.time() - start_time
                
                comparison_results['legacy_result'] = {
                    'quality_grade': legacy_result.quality_grade.name,
                    'confidence_score': legacy_result.confidence_score,
                    'processing_time': legacy_time,
                    'data_completeness': self._calculate_completeness(legacy_result)
                }
            except Exception as e:
                self.logger.error(f"레거시 시스템 테스트 실패: {e}")
        
        # 비교 분석
        if comparison_results['ai_result'] and comparison_results['legacy_result']:
            ai_res = comparison_results['ai_result']
            legacy_res = comparison_results['legacy_result']
            
            comparison_results['comparison'] = {
                'speed_winner': 'AI' if ai_res['processing_time'] < legacy_res['processing_time'] else 'Legacy',
                'quality_winner': 'AI' if ai_res['quality_grade'] < legacy_res['quality_grade'] else 'Legacy',
                'completeness_winner': 'AI' if ai_res['data_completeness'] > legacy_res['data_completeness'] else 'Legacy',
                'confidence_winner': 'AI' if ai_res['confidence_score'] > legacy_res['confidence_score'] else 'Legacy'
            }
        
        return comparison_results
    
    def _calculate_completeness(self, result: CrawlingResult) -> float:
        """데이터 완전성 계산"""
        fields = ['phone', 'fax', 'email', 'homepage']
        filled_fields = sum(1 for field in fields if getattr(result, field, ''))
        return filled_fields / len(fields)
    
    def cleanup(self):
        """리소스 정리"""
        self.logger.info("🧹 리소스 정리 시작")
        
        # 레거시 크롤러 정리
        for name, crawler in self.legacy_crawlers.items():
            try:
                if hasattr(crawler, 'close'):
                    crawler.close()
                elif hasattr(crawler, 'close_driver'):
                    crawler.close_driver()
            except Exception as e:
                self.logger.error(f"크롤러 정리 실패 ({name}): {e}")
        
        self.logger.info("✅ 리소스 정리 완료")

# 사용 예제
def main():
    """메인 함수"""
    print("🔄 레거시 통합 시스템 테스트")
    
    # 설정
    config = IntegrationConfig(
        use_ai_primary=True,
        use_legacy_fallback=True,
        hybrid_validation=True,
        performance_comparison=True
    )
    
    # 통합 관리자 초기화
    manager = LegacyIntegrationManager(config)
    
    # 테스트 데이터
    test_organizations = [
        {
            'name': '서울시립어린이집',
            'address': '서울시 강남구',
            'category': '어린이집'
        },
        {
            'name': '부산아동센터',
            'address': '부산시 해운대구',
            'category': '아동센터'
        }
    ]
    
    try:
        # 배치 처리
        results = manager.process_batch(
            test_organizations,
            output_file='integration_test_results.json'
        )
        
        # 성능 비교
        if results:
            comparison = manager.performance_comparison(test_organizations[0])
            print(f"성능 비교 결과: {comparison}")
        
    finally:
        # 리소스 정리
        manager.cleanup()

if __name__ == "__main__":
    main() 
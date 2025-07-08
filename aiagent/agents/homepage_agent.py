#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
홈페이지 검색 전문 에이전트
최적의 검색 전략을 수립하고 홈페이지를 찾는 AI 에이전트
"""

import re
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

from ..core.agent_base import BaseAgent, AgentTask, AgentResult
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class HomepageAgent(BaseAgent):
    """홈페이지 검색 전문 에이전트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("homepage_agent", config)
        self.search_strategies = [
            "direct_search",
            "keyword_combination",
            "location_based_search",
            "organization_type_search"
        ]
        
    def get_system_prompt(self) -> str:
        """홈페이지 검색 전문 시스템 프롬프트"""
        return """
당신은 홈페이지 검색 전문가입니다. 주어진 조직 정보를 바탕으로 최적의 검색 전략을 수립하고 정확한 홈페이지를 찾아주세요.

**전문 영역:**
1. 검색 키워드 최적화
2. 검색 결과 분석 및 필터링
3. 홈페이지 진위 판별
4. 검색 전략 수립

**분석 기준:**
- 조직명과 홈페이지 내용의 일치도
- 주소 정보 일치 여부
- 연락처 정보 일치 여부
- 도메인 신뢰도
- 웹사이트 활성도

**응답 형식:**
반드시 JSON 형식으로 응답해주세요.
"""
    
    def process_task(self, task: AgentTask) -> AgentResult:
        """홈페이지 검색 작업 처리"""
        try:
            data = task.data
            org_name = data.get('organization_name', '')
            org_address = data.get('address', '')
            org_phone = data.get('phone', '')
            
            if not org_name:
                return AgentResult(
                    task_id=task.task_id,
                    success=False,
                    data={},
                    error_message="조직명이 제공되지 않았습니다."
                )
            
            # 1. 검색 전략 수립
            search_strategy = self._develop_search_strategy(org_name, org_address, org_phone)
            
            # 2. 홈페이지 검색 실행
            search_results = self._execute_search(search_strategy)
            
            # 3. 결과 분석 및 검증
            validated_results = self._validate_search_results(
                search_results, org_name, org_address, org_phone
            )
            
            # 4. 최종 홈페이지 선택
            final_homepage = self._select_best_homepage(validated_results)
            
            return AgentResult(
                task_id=task.task_id,
                success=bool(final_homepage),
                data={
                    'homepage_url': final_homepage.get('url', ''),
                    'confidence_score': final_homepage.get('confidence', 0.0),
                    'search_strategy': search_strategy,
                    'total_candidates': len(search_results),
                    'validated_candidates': len(validated_results),
                    'analysis_details': final_homepage.get('analysis', {})
                },
                confidence_score=final_homepage.get('confidence', 0.0)
            )
            
        except Exception as e:
            logger.error(f"홈페이지 검색 중 오류: {str(e)}")
            return AgentResult(
                task_id=task.task_id,
                success=False,
                data={},
                error_message=str(e)
            )
    
    def _develop_search_strategy(self, org_name: str, org_address: str, org_phone: str) -> Dict[str, Any]:
        """검색 전략 수립"""
        try:
            prompt = f"""
다음 조직의 홈페이지를 찾기 위한 최적의 검색 전략을 수립해주세요:

조직명: {org_name}
주소: {org_address}
전화번호: {org_phone}

검색 전략을 JSON 형식으로 제공해주세요:
{{
    "primary_keywords": ["주요 키워드1", "주요 키워드2"],
    "secondary_keywords": ["보조 키워드1", "보조 키워드2"],
    "search_queries": ["검색어1", "검색어2", "검색어3"],
    "expected_domains": ["예상 도메인1", "예상 도메인2"],
    "verification_criteria": ["검증 기준1", "검증 기준2"],
    "confidence_factors": ["신뢰도 요소1", "신뢰도 요소2"]
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                import json
                try:
                    strategy = json.loads(response['content'])
                    return strategy
                except json.JSONDecodeError:
                    # 기본 전략 반환
                    return self._get_default_strategy(org_name, org_address)
            else:
                return self._get_default_strategy(org_name, org_address)
                
        except Exception as e:
            logger.error(f"검색 전략 수립 실패: {str(e)}")
            return self._get_default_strategy(org_name, org_address)
    
    def _get_default_strategy(self, org_name: str, org_address: str) -> Dict[str, Any]:
        """기본 검색 전략"""
        return {
            "primary_keywords": [org_name],
            "secondary_keywords": [org_address.split()[0] if org_address else ""],
            "search_queries": [
                f"{org_name} 홈페이지",
                f"{org_name} 공식 사이트",
                f"{org_name} 웹사이트"
            ],
            "expected_domains": [f"{org_name.replace(' ', '')}.co.kr"],
            "verification_criteria": ["조직명 일치", "주소 정보 포함"],
            "confidence_factors": ["도메인 신뢰도", "내용 일치도"]
        }
    
    def _execute_search(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """검색 실행 (시뮬레이션)"""
        # 실제 구현에서는 Google Search API나 다른 검색 엔진 사용
        search_results = []
        
        for query in strategy.get('search_queries', []):
            # 시뮬레이션된 검색 결과
            mock_results = [
                {
                    'url': f'http://example-{i}.co.kr',
                    'title': f'{query} 관련 사이트 {i}',
                    'snippet': f'{query}에 대한 정보를 제공하는 사이트입니다.',
                    'search_query': query
                }
                for i in range(1, 4)
            ]
            search_results.extend(mock_results)
        
        return search_results
    
    def _validate_search_results(self, search_results: List[Dict[str, Any]], 
                                org_name: str, org_address: str, org_phone: str) -> List[Dict[str, Any]]:
        """검색 결과 검증"""
        validated_results = []
        
        for result in search_results:
            try:
                # AI를 통한 결과 검증
                validation_result = self._validate_single_result(
                    result, org_name, org_address, org_phone
                )
                
                if validation_result['is_valid']:
                    validated_results.append({
                        **result,
                        'validation': validation_result,
                        'confidence': validation_result.get('confidence', 0.5)
                    })
                    
            except Exception as e:
                logger.error(f"결과 검증 중 오류: {str(e)}")
                continue
        
        return validated_results
    
    def _validate_single_result(self, result: Dict[str, Any], 
                               org_name: str, org_address: str, org_phone: str) -> Dict[str, Any]:
        """단일 검색 결과 검증"""
        try:
            prompt = f"""
다음 검색 결과가 해당 조직의 공식 홈페이지인지 검증해주세요:

조직 정보:
- 조직명: {org_name}
- 주소: {org_address}
- 전화번호: {org_phone}

검색 결과:
- URL: {result.get('url', '')}
- 제목: {result.get('title', '')}
- 설명: {result.get('snippet', '')}

검증 결과를 JSON 형식으로 제공해주세요:
{{
    "is_valid": true/false,
    "confidence": 0.8,
    "matching_factors": ["일치 요소1", "일치 요소2"],
    "concerns": ["우려사항1", "우려사항2"],
    "recommendation": "추천 여부 및 이유"
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                import json
                try:
                    return json.loads(response['content'])
                except json.JSONDecodeError:
                    return {'is_valid': False, 'confidence': 0.0}
            else:
                return {'is_valid': False, 'confidence': 0.0}
                
        except Exception as e:
            logger.error(f"단일 결과 검증 실패: {str(e)}")
            return {'is_valid': False, 'confidence': 0.0}
    
    def _select_best_homepage(self, validated_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """최적의 홈페이지 선택"""
        if not validated_results:
            return {}
        
        # 신뢰도 기준으로 정렬
        sorted_results = sorted(
            validated_results, 
            key=lambda x: x.get('confidence', 0.0), 
            reverse=True
        )
        
        best_result = sorted_results[0]
        
        # 최종 분석 수행
        final_analysis = self._perform_final_analysis(best_result)
        
        return {
            'url': best_result.get('url', ''),
            'confidence': best_result.get('confidence', 0.0),
            'analysis': final_analysis,
            'validation_details': best_result.get('validation', {})
        }
    
    def _perform_final_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 분석 수행"""
        try:
            prompt = f"""
선택된 홈페이지에 대한 최종 분석을 수행해주세요:

홈페이지 정보:
- URL: {result.get('url', '')}
- 제목: {result.get('title', '')}
- 검증 결과: {result.get('validation', {})}

최종 분석 결과를 JSON 형식으로 제공해주세요:
{{
    "overall_assessment": "전반적 평가",
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1", "약점2"],
    "recommendation_score": 0.85,
    "next_steps": ["다음 단계1", "다음 단계2"]
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                import json
                try:
                    return json.loads(response['content'])
                except json.JSONDecodeError:
                    return {'overall_assessment': '분석 실패'}
            else:
                return {'overall_assessment': '분석 실패'}
                
        except Exception as e:
            logger.error(f"최종 분석 실패: {str(e)}")
            return {'overall_assessment': '분석 실패'}
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """검색 통계 반환"""
        stats = self.get_performance_stats()
        return {
            'total_searches': stats.get('total_tasks', 0),
            'successful_searches': stats.get('successful_tasks', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'average_confidence': stats.get('average_confidence', 0.0),
            'average_search_time': stats.get('average_duration', 0.0)
        } 
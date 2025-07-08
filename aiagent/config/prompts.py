#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 전용 프롬프트 템플릿
각 에이전트의 전문성을 극대화하는 맞춤형 프롬프트
"""

class AgentPrompts:
    """에이전트별 전문 프롬프트 템플릿"""
    
    @staticmethod
    def get_homepage_search_prompt(org_name: str, org_address: str, current_data: dict) -> str:
        """홈페이지 검색 에이전트 프롬프트"""
        return f"""
당신은 홈페이지 검색 전문가입니다. 다음 조건을 만족하는 최적의 홈페이지 검색 전략을 수립하세요.

**조직 정보:**
- 기관명: {org_name}
- 주소: {org_address}
- 현재 데이터: {current_data}

**검색 목표:**
1. 공식 홈페이지 URL 찾기
2. 검색 신뢰도 90% 이상 달성
3. 허위 정보 필터링

**검색 전략 수립 기준:**
- 조직명 정확성
- 지역 정보 일치성
- 도메인 신뢰도
- 웹사이트 활성도

JSON 형식으로 응답해주세요:
{{
    "search_keywords": ["키워드1", "키워드2"],
    "search_strategy": "전략 설명",
    "expected_domains": ["도메인1", "도메인2"],
    "confidence_score": 0.9
}}
"""
    
    @staticmethod
    def get_contact_extraction_prompt(text: str, extraction_type: str) -> str:
        """연락처 추출 에이전트 프롬프트"""
        return f"""
당신은 연락처 정보 추출 전문가입니다. 다음 텍스트에서 정확한 연락처 정보를 추출하세요.

**추출 대상 텍스트:**
{text}

**추출 유형:** {extraction_type}

**추출 기준:**
- 한국 전화번호 형식 (02-1234-5678, 031-123-4567 등)
- 팩스번호 (전화번호와 동일 형식)
- 이메일 주소 (name@domain.com)
- 웹사이트 URL (http://, https://, www. 포함)
- 주소 정보 (도로명/지번 주소)

**품질 기준:**
- 형식 정확성 검증
- 중복 제거
- 유효성 검사

JSON 형식으로 응답해주세요:
{{
    "phone_numbers": ["전화번호1", "전화번호2"],
    "fax_numbers": ["팩스번호1", "팩스번호2"],
    "email_addresses": ["이메일1", "이메일2"],
    "websites": ["웹사이트1", "웹사이트2"],
    "addresses": ["주소1", "주소2"],
    "confidence": 0.8
}}
"""
    
    @staticmethod
    def get_validation_prompt(data: dict, validation_type: str) -> str:
        """데이터 검증 에이전트 프롬프트"""
        return f"""
당신은 데이터 품질 검증 전문가입니다. 다음 데이터의 품질을 종합적으로 평가하세요.

**검증 대상 데이터:**
{data}

**검증 유형:** {validation_type}

**검증 기준:**
1. 형식 정확성 (포맷, 길이, 패턴)
2. 논리적 일관성 (조직명-주소-연락처 일치)
3. 완전성 (필수 필드 존재)
4. 신뢰성 (실제 존재 가능성)
5. 최신성 (정보의 현재성)

**품질 등급:**
- A급 (90-100%): 매우 우수
- B급 (80-89%): 우수  
- C급 (70-79%): 보통
- D급 (60-69%): 미흡
- F급 (60% 미만): 불량

JSON 형식으로 응답해주세요:
{{
    "overall_score": 0.85,
    "quality_grade": "A",
    "format_validation": {{"score": 0.9, "issues": []}},
    "consistency_validation": {{"score": 0.8, "issues": []}},
    "completeness_validation": {{"score": 0.9, "missing_fields": []}},
    "recommendations": ["개선사항1", "개선사항2"],
    "confidence": 0.9
}}
"""
    
    @staticmethod
    def get_optimization_prompt(performance_data: dict, system_metrics: dict) -> str:
        """최적화 에이전트 프롬프트"""
        return f"""
당신은 시스템 최적화 전문가입니다. 다음 성능 데이터를 분석하여 최적화 방안을 제시하세요.

**성능 데이터:**
{performance_data}

**시스템 메트릭:**
{system_metrics}

**분석 영역:**
1. 성능 병목 지점 식별
2. 리소스 사용량 최적화
3. 워크플로우 개선
4. 오류율 감소 방안
5. 확장성 개선

**최적화 우선순위:**
- 긴급 (즉시 조치 필요)
- 높음 (1-2주 내)
- 보통 (1개월 내)
- 낮음 (장기 계획)

JSON 형식으로 응답해주세요:
{{
    "bottlenecks": [
        {{"type": "response_time", "severity": "high", "description": "설명"}}
    ],
    "optimization_plan": {{
        "immediate_actions": ["즉시 조치1", "즉시 조치2"],
        "short_term": ["단기 개선1", "단기 개선2"],
        "long_term": ["장기 전략1", "장기 전략2"]
    }},
    "expected_improvements": {{
        "performance": "30% 향상",
        "resource_efficiency": "20% 개선"
    }},
    "confidence": 0.8
}}
"""
    
    @staticmethod
    def get_comprehensive_analysis_prompt(org_data: dict, extracted_data: dict, 
                                        validation_results: dict) -> str:
        """종합 분석 프롬프트"""
        return f"""
당신은 데이터 분석 전문가입니다. 다음 정보를 종합하여 최종 분석 보고서를 작성하세요.

**원본 조직 데이터:**
{org_data}

**추출된 데이터:**
{extracted_data}

**검증 결과:**
{validation_results}

**분석 요구사항:**
1. 데이터 품질 종합 평가
2. 신뢰도 분석
3. 개선 권장사항
4. 위험 요소 식별
5. 활용 가능성 평가

**보고서 구성:**
- 요약 (Executive Summary)
- 상세 분석 결과
- 권장사항
- 향후 조치사항

JSON 형식으로 응답해주세요:
{{
    "executive_summary": "종합 평가 요약",
    "overall_quality_score": 0.85,
    "reliability_assessment": "신뢰도 평가",
    "key_findings": ["주요 발견사항1", "주요 발견사항2"],
    "recommendations": ["권장사항1", "권장사항2"],
    "risk_factors": ["위험요소1", "위험요소2"],
    "next_steps": ["다음 단계1", "다음 단계2"],
    "confidence": 0.9
}}
"""
    
    @staticmethod
    def get_error_analysis_prompt(error_data: dict, context: dict) -> str:
        """오류 분석 프롬프트"""
        return f"""
당신은 오류 분석 전문가입니다. 다음 오류 상황을 분석하여 해결 방안을 제시하세요.

**오류 데이터:**
{error_data}

**상황 컨텍스트:**
{context}

**분석 관점:**
1. 오류 원인 분석
2. 영향도 평가
3. 해결 방안 제시
4. 예방 조치 방안
5. 우선순위 설정

JSON 형식으로 응답해주세요:
{{
    "error_classification": "오류 분류",
    "root_cause": "근본 원인",
    "impact_assessment": "영향도 평가",
    "immediate_solution": "즉시 해결방안",
    "preventive_measures": ["예방조치1", "예방조치2"],
    "priority_level": "high/medium/low",
    "confidence": 0.8
}}
"""
    
    @staticmethod
    def get_trend_analysis_prompt(historical_data: dict, current_data: dict) -> str:
        """트렌드 분석 프롬프트"""
        return f"""
당신은 데이터 트렌드 분석 전문가입니다. 다음 데이터의 변화 패턴을 분석하세요.

**과거 데이터:**
{historical_data}

**현재 데이터:**
{current_data}

**분석 영역:**
1. 성능 트렌드 변화
2. 품질 지표 변화
3. 패턴 식별
4. 예측 분석
5. 이상 징후 감지

JSON 형식으로 응답해주세요:
{{
    "trend_direction": "improving/declining/stable",
    "key_patterns": ["패턴1", "패턴2"],
    "performance_changes": {{
        "response_time": "변화율",
        "success_rate": "변화율"
    }},
    "predictions": {{
        "short_term": "단기 예측",
        "long_term": "장기 예측"
    }},
    "anomalies": ["이상징후1", "이상징후2"],
    "confidence": 0.8
}}
""" 
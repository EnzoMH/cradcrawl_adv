#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화 전문 에이전트
시스템 성능을 분석하고 최적화 방안을 제안하는 AI 에이전트
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from ..core.agent_base import BaseAgent, AgentTask, AgentResult
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class OptimizerAgent(BaseAgent):
    """최적화 전문 에이전트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("optimizer_agent", config)
        
        self.optimization_areas = [
            'performance',
            'accuracy',
            'resource_usage',
            'workflow',
            'error_reduction'
        ]
    
    def get_system_prompt(self) -> str:
        """최적화 전문 시스템 프롬프트"""
        return """
당신은 시스템 최적화 전문가입니다. 성능 데이터를 분석하고 효율성 개선 방안을 제안해주세요.

**전문 영역:**
1. 성능 병목 지점 식별
2. 리소스 사용량 최적화
3. 워크플로우 개선
4. 오류율 감소 방안
5. 확장성 개선

**분석 기준:**
- 처리 속도 및 응답 시간
- 메모리 및 CPU 사용량
- 성공률 및 오류율
- 사용자 경험
- 비용 효율성

**응답 형식:**
반드시 JSON 형식으로 응답해주세요.
"""
    
    def process_task(self, task: AgentTask) -> AgentResult:
        """최적화 작업 처리"""
        try:
            data = task.data
            optimization_type = data.get('optimization_type', 'comprehensive')
            performance_data = data.get('performance_data', {})
            system_metrics = data.get('system_metrics', {})
            
            # 1. 성능 분석
            performance_analysis = self._analyze_performance(performance_data)
            
            # 2. 병목 지점 식별
            bottlenecks = self._identify_bottlenecks(performance_data, system_metrics)
            
            # 3. 최적화 방안 생성
            optimization_plan = self._generate_optimization_plan(
                performance_analysis, bottlenecks, optimization_type
            )
            
            # 4. AI 기반 고급 분석
            ai_insights = self._get_ai_insights(performance_data, system_metrics)
            
            # 5. 최종 최적화 보고서 생성
            final_report = self._generate_final_report(
                performance_analysis, bottlenecks, optimization_plan, ai_insights
            )
            
            return AgentResult(
                task_id=task.task_id,
                success=True,
                data=final_report,
                confidence_score=final_report.get('confidence', 0.0)
            )
            
        except Exception as e:
            logger.error(f"최적화 분석 중 오류: {str(e)}")
            return AgentResult(
                task_id=task.task_id,
                success=False,
                data={},
                error_message=str(e)
            )
    
    def _analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """성능 분석"""
        analysis = {
            'response_time_analysis': {},
            'success_rate_analysis': {},
            'throughput_analysis': {},
            'trend_analysis': {}
        }
        
        try:
            # 응답 시간 분석
            if 'avg_durations' in performance_data:
                durations = performance_data['avg_durations']
                analysis['response_time_analysis'] = {
                    'average': sum(durations) / len(durations) if durations else 0,
                    'max': max(durations) if durations else 0,
                    'min': min(durations) if durations else 0,
                    'trend': 'increasing' if len(durations) > 1 and durations[-1] > durations[0] else 'stable'
                }
            
            # 성공률 분석
            if 'success_rates' in performance_data:
                success_rates = performance_data['success_rates']
                analysis['success_rate_analysis'] = {
                    'average': sum(success_rates) / len(success_rates) if success_rates else 0,
                    'current': success_rates[-1] if success_rates else 0,
                    'trend': 'improving' if len(success_rates) > 1 and success_rates[-1] > success_rates[0] else 'stable'
                }
            
        except Exception as e:
            logger.error(f"성능 분석 중 오류: {str(e)}")
        
        return analysis
    
    def _identify_bottlenecks(self, performance_data: Dict[str, Any], 
                            system_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """병목 지점 식별"""
        bottlenecks = []
        
        try:
            # 응답 시간 병목
            if performance_data.get('avg_durations', []):
                avg_duration = sum(performance_data['avg_durations']) / len(performance_data['avg_durations'])
                if avg_duration > 5.0:  # 5초 이상
                    bottlenecks.append({
                        'type': 'response_time',
                        'severity': 'high' if avg_duration > 10 else 'medium',
                        'description': f'평균 응답 시간이 {avg_duration:.2f}초로 느립니다.',
                        'impact': 'user_experience'
                    })
            
            # 성공률 병목
            if performance_data.get('success_rates', []):
                avg_success_rate = sum(performance_data['success_rates']) / len(performance_data['success_rates'])
                if avg_success_rate < 0.9:  # 90% 미만
                    bottlenecks.append({
                        'type': 'success_rate',
                        'severity': 'high' if avg_success_rate < 0.7 else 'medium',
                        'description': f'성공률이 {avg_success_rate:.2%}로 낮습니다.',
                        'impact': 'reliability'
                    })
            
            # 리소스 사용량 병목
            if system_metrics.get('cpu_usage', 0) > 80:
                bottlenecks.append({
                    'type': 'cpu_usage',
                    'severity': 'high',
                    'description': f'CPU 사용률이 {system_metrics["cpu_usage"]}%로 높습니다.',
                    'impact': 'performance'
                })
            
            if system_metrics.get('memory_usage', 0) > 80:
                bottlenecks.append({
                    'type': 'memory_usage',
                    'severity': 'high',
                    'description': f'메모리 사용률이 {system_metrics["memory_usage"]}%로 높습니다.',
                    'impact': 'stability'
                })
            
        except Exception as e:
            logger.error(f"병목 지점 식별 중 오류: {str(e)}")
        
        return bottlenecks
    
    def _generate_optimization_plan(self, performance_analysis: Dict[str, Any], 
                                  bottlenecks: List[Dict[str, Any]], 
                                  optimization_type: str) -> Dict[str, Any]:
        """최적화 계획 생성"""
        plan = {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_strategies': [],
            'priority_ranking': []
        }
        
        try:
            # 병목 지점 기반 즉시 조치사항
            for bottleneck in bottlenecks:
                if bottleneck['severity'] == 'high':
                    if bottleneck['type'] == 'response_time':
                        plan['immediate_actions'].append({
                            'action': '병렬 처리 워커 수 증가',
                            'target': 'response_time',
                            'expected_improvement': '30-50% 성능 향상'
                        })
                    elif bottleneck['type'] == 'success_rate':
                        plan['immediate_actions'].append({
                            'action': '재시도 로직 강화',
                            'target': 'success_rate',
                            'expected_improvement': '10-20% 성공률 향상'
                        })
                    elif bottleneck['type'] == 'cpu_usage':
                        plan['immediate_actions'].append({
                            'action': 'CPU 집약적 작업 최적화',
                            'target': 'cpu_usage',
                            'expected_improvement': '20-30% CPU 사용량 감소'
                        })
            
            # 단기 개선사항
            plan['short_term_improvements'] = [
                {
                    'improvement': '캐싱 시스템 도입',
                    'timeline': '1-2주',
                    'expected_benefit': '응답 시간 50% 단축'
                },
                {
                    'improvement': '데이터베이스 쿼리 최적화',
                    'timeline': '2-3주',
                    'expected_benefit': '전체 성능 20% 향상'
                }
            ]
            
            # 장기 전략
            plan['long_term_strategies'] = [
                {
                    'strategy': '마이크로서비스 아키텍처 도입',
                    'timeline': '2-3개월',
                    'expected_benefit': '확장성 및 유지보수성 대폭 개선'
                },
                {
                    'strategy': 'AI 기반 자동 최적화 시스템',
                    'timeline': '3-6개월',
                    'expected_benefit': '지속적인 성능 개선'
                }
            ]
            
        except Exception as e:
            logger.error(f"최적화 계획 생성 중 오류: {str(e)}")
        
        return plan
    
    def _get_ai_insights(self, performance_data: Dict[str, Any], 
                        system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """AI 기반 인사이트"""
        try:
            prompt = f"""
다음 성능 데이터를 분석하여 최적화 인사이트를 제공해주세요:

성능 데이터: {json.dumps(performance_data, ensure_ascii=False, indent=2)}
시스템 메트릭: {json.dumps(system_metrics, ensure_ascii=False, indent=2)}

다음 관점에서 분석해주세요:
1. 숨겨진 성능 패턴
2. 예측 가능한 문제점
3. 혁신적인 최적화 방안
4. 비용 효율성 개선

분석 결과를 JSON 형식으로 제공해주세요:
{{
    "hidden_patterns": ["패턴1", "패턴2"],
    "predicted_issues": ["예상 문제1", "예상 문제2"],
    "innovative_solutions": ["혁신 방안1", "혁신 방안2"],
    "cost_optimization": ["비용 절감 방안1", "비용 절감 방안2"],
    "performance_forecast": "향후 성능 예측",
    "confidence": 0.8
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                try:
                    return json.loads(response['content'])
                except json.JSONDecodeError:
                    return {'confidence': 0.0}
            else:
                return {'confidence': 0.0}
                
        except Exception as e:
            logger.error(f"AI 인사이트 생성 중 오류: {str(e)}")
            return {'confidence': 0.0}
    
    def _generate_final_report(self, performance_analysis: Dict[str, Any],
                             bottlenecks: List[Dict[str, Any]],
                             optimization_plan: Dict[str, Any],
                             ai_insights: Dict[str, Any]) -> Dict[str, Any]:
        """최종 최적화 보고서 생성"""
        
        # 전체 우선순위 계산
        priority_score = self._calculate_priority_score(bottlenecks, ai_insights)
        
        final_report = {
            'report_timestamp': datetime.now().isoformat(),
            'executive_summary': self._generate_executive_summary(bottlenecks, priority_score),
            'performance_analysis': performance_analysis,
            'identified_bottlenecks': bottlenecks,
            'optimization_plan': optimization_plan,
            'ai_insights': ai_insights,
            'priority_score': priority_score,
            'implementation_roadmap': self._create_implementation_roadmap(optimization_plan),
            'success_metrics': self._define_success_metrics(),
            'confidence': ai_insights.get('confidence', 0.7)
        }
        
        return final_report
    
    def _calculate_priority_score(self, bottlenecks: List[Dict[str, Any]], 
                                ai_insights: Dict[str, Any]) -> float:
        """우선순위 점수 계산"""
        if not bottlenecks:
            return 0.5
        
        high_severity_count = sum(1 for b in bottlenecks if b.get('severity') == 'high')
        total_bottlenecks = len(bottlenecks)
        
        base_score = high_severity_count / total_bottlenecks if total_bottlenecks > 0 else 0
        ai_confidence = ai_insights.get('confidence', 0.5)
        
        return (base_score * 0.7) + (ai_confidence * 0.3)
    
    def _generate_executive_summary(self, bottlenecks: List[Dict[str, Any]], 
                                  priority_score: float) -> str:
        """경영진 요약 생성"""
        high_severity_count = sum(1 for b in bottlenecks if b.get('severity') == 'high')
        
        if priority_score > 0.8:
            urgency = "긴급"
        elif priority_score > 0.6:
            urgency = "높음"
        elif priority_score > 0.4:
            urgency = "보통"
        else:
            urgency = "낮음"
        
        return f"""
시스템 최적화 분석 결과, 총 {len(bottlenecks)}개의 개선점이 식별되었습니다.
이 중 {high_severity_count}개는 높은 우선순위로 즉시 조치가 필요합니다.
전체 우선순위 점수는 {priority_score:.2f}로 '{urgency}' 수준의 대응이 권장됩니다.
"""
    
    def _create_implementation_roadmap(self, optimization_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """구현 로드맵 생성"""
        roadmap = []
        
        # 즉시 조치사항
        for action in optimization_plan.get('immediate_actions', []):
            roadmap.append({
                'phase': '즉시 조치',
                'timeline': '1주 이내',
                'action': action.get('action', ''),
                'priority': 'high'
            })
        
        # 단기 개선사항
        for improvement in optimization_plan.get('short_term_improvements', []):
            roadmap.append({
                'phase': '단기 개선',
                'timeline': improvement.get('timeline', ''),
                'action': improvement.get('improvement', ''),
                'priority': 'medium'
            })
        
        # 장기 전략
        for strategy in optimization_plan.get('long_term_strategies', []):
            roadmap.append({
                'phase': '장기 전략',
                'timeline': strategy.get('timeline', ''),
                'action': strategy.get('strategy', ''),
                'priority': 'low'
            })
        
        return roadmap
    
    def _define_success_metrics(self) -> Dict[str, Any]:
        """성공 지표 정의"""
        return {
            'performance_metrics': {
                'response_time_improvement': '30% 단축',
                'success_rate_improvement': '95% 이상',
                'throughput_increase': '50% 증가'
            },
            'resource_metrics': {
                'cpu_usage_reduction': '20% 감소',
                'memory_optimization': '15% 효율화',
                'cost_reduction': '25% 절감'
            },
            'quality_metrics': {
                'error_rate_reduction': '50% 감소',
                'user_satisfaction': '90% 이상',
                'system_reliability': '99.9% 가동률'
            }
        }
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """최적화 통계 반환"""
        stats = self.get_performance_stats()
        return {
            'total_optimizations': stats.get('total_tasks', 0),
            'successful_optimizations': stats.get('successful_tasks', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'average_confidence': stats.get('average_confidence', 0.0),
            'average_analysis_time': stats.get('average_duration', 0.0)
        } 
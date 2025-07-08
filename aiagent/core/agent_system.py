#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 메인 시스템
모든 에이전트들을 통합 관리하는 중앙 시스템
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import uuid

from .agent_base import BaseAgent, AgentTask, AgentResult, AgentStatus
from .coordinator import AgentCoordinator
from ..agents import AGENT_REGISTRY, create_agent
from ..config.agent_config import AgentConfig, ConfigPresets
from ..metrics.performance import PerformanceTracker
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class AIAgentSystem:
    """AI 에이전트 시스템 - 메인 클래스"""
    
    def __init__(self, config_preset: str = 'development'):
        """
        AI 에이전트 시스템 초기화
        
        Args:
            config_preset: 설정 프리셋 ('development', 'production', 'high_performance')
        """
        self.system_id = str(uuid.uuid4())
        self.config_preset = config_preset
        self.agents: Dict[str, BaseAgent] = {}
        self.coordinator = AgentCoordinator()
        self.performance_tracker = PerformanceTracker()
        self.gemini_client = GeminiClient()
        
        # 설정 로드
        self._load_configuration()
        
        # 에이전트 초기화
        self._initialize_agents()
        
        # 시스템 상태
        self.is_running = False
        self.system_stats = {
            'start_time': None,
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'active_agents': 0
        }
        
        logger.info(f"AI 에이전트 시스템 초기화 완료 (ID: {self.system_id})")
    
    def _load_configuration(self):
        """설정 로드"""
        try:
            if self.config_preset == 'development':
                self.agent_configs = ConfigPresets.get_development_config()
            elif self.config_preset == 'production':
                self.agent_configs = ConfigPresets.get_production_config()
            elif self.config_preset == 'high_performance':
                self.agent_configs = ConfigPresets.get_high_performance_config()
            else:
                logger.warning(f"Unknown config preset: {self.config_preset}, using development")
                self.agent_configs = ConfigPresets.get_development_config()
                
            logger.info(f"설정 로드 완료: {self.config_preset}")
            
        except Exception as e:
            logger.error(f"설정 로드 실패: {str(e)}")
            self.agent_configs = ConfigPresets.get_development_config()
    
    def _initialize_agents(self):
        """에이전트 초기화"""
        try:
            for agent_name, config in self.agent_configs.items():
                if config.enabled:
                    agent = create_agent(agent_name, config)
                    self.agents[agent_name] = agent
                    logger.info(f"에이전트 초기화 완료: {agent_name}")
                else:
                    logger.info(f"에이전트 비활성화: {agent_name}")
            
            self.system_stats['active_agents'] = len(self.agents)
            logger.info(f"총 {len(self.agents)}개 에이전트 초기화 완료")
            
        except Exception as e:
            logger.error(f"에이전트 초기화 실패: {str(e)}")
            raise
    
    def start_system(self):
        """시스템 시작"""
        try:
            self.is_running = True
            self.system_stats['start_time'] = datetime.now()
            
            # 에이전트 상태 확인
            for agent_name, agent in self.agents.items():
                agent.status = AgentStatus.READY
                logger.info(f"에이전트 시작: {agent_name}")
            
            logger.info("AI 에이전트 시스템 시작 완료")
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {str(e)}")
            self.is_running = False
            raise
    
    def stop_system(self):
        """시스템 중지"""
        try:
            self.is_running = False
            
            # 에이전트 중지
            for agent_name, agent in self.agents.items():
                agent.status = AgentStatus.STOPPED
                logger.info(f"에이전트 중지: {agent_name}")
            
            logger.info("AI 에이전트 시스템 중지 완료")
            
        except Exception as e:
            logger.error(f"시스템 중지 실패: {str(e)}")
    
    async def process_crawling_task(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        크롤링 작업 처리 - 멀티 에이전트 워크플로우
        
        Args:
            organization_data: 조직 데이터 (이름, 주소 등)
            
        Returns:
            Dict: 처리 결과
        """
        if not self.is_running:
            raise RuntimeError("시스템이 실행 중이 아닙니다.")
        
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            logger.info(f"크롤링 작업 시작: {task_id}")
            
            # 1. 홈페이지 검색
            homepage_result = await self._execute_homepage_search(task_id, organization_data)
            
            # 2. 연락처 추출
            contact_result = await self._execute_contact_extraction(task_id, homepage_result)
            
            # 3. 데이터 검증
            validation_result = await self._execute_data_validation(task_id, contact_result)
            
            # 4. 최적화 분석 (선택적)
            optimization_result = await self._execute_optimization_analysis(task_id, {
                'homepage_result': homepage_result,
                'contact_result': contact_result,
                'validation_result': validation_result
            })
            
            # 5. 최종 결과 통합
            final_result = self._integrate_results(
                task_id, organization_data, homepage_result, 
                contact_result, validation_result, optimization_result
            )
            
            # 통계 업데이트
            self.system_stats['total_tasks'] += 1
            self.system_stats['successful_tasks'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"크롤링 작업 완료: {task_id} (처리시간: {processing_time:.2f}초)")
            
            return final_result
            
        except Exception as e:
            logger.error(f"크롤링 작업 실패: {task_id} - {str(e)}")
            self.system_stats['total_tasks'] += 1
            self.system_stats['failed_tasks'] += 1
            
            return {
                'task_id': task_id,
                'success': False,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_homepage_search(self, task_id: str, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """홈페이지 검색 실행"""
        if 'homepage_agent' not in self.agents:
            return {'success': False, 'error': 'Homepage agent not available'}
        
        agent = self.agents['homepage_agent']
        task = AgentTask(
            task_id=f"{task_id}_homepage",
            agent_name="homepage_agent",
            task_type="homepage_search",
            data=organization_data
        )
        
        result = await asyncio.to_thread(agent.process_task, task)
        return result.to_dict()
    
    async def _execute_contact_extraction(self, task_id: str, homepage_result: Dict[str, Any]) -> Dict[str, Any]:
        """연락처 추출 실행"""
        if 'contact_agent' not in self.agents:
            return {'success': False, 'error': 'Contact agent not available'}
        
        agent = self.agents['contact_agent']
        
        # 홈페이지 콘텐츠에서 연락처 추출
        text_content = homepage_result.get('data', {}).get('homepage_content', '')
        if not text_content:
            # 시뮬레이션 텍스트 (실제로는 홈페이지 크롤링 결과)
            text_content = f"조직: {homepage_result.get('organization_name', '')} 연락처 정보"
        
        task = AgentTask(
            task_id=f"{task_id}_contact",
            agent_name="contact_agent",
            task_type="contact_extraction",
            data={
                'text': text_content,
                'extraction_type': 'all'
            }
        )
        
        result = await asyncio.to_thread(agent.process_task, task)
        return result.to_dict()
    
    async def _execute_data_validation(self, task_id: str, contact_result: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 검증 실행"""
        if 'validation_agent' not in self.agents:
            return {'success': False, 'error': 'Validation agent not available'}
        
        agent = self.agents['validation_agent']
        task = AgentTask(
            task_id=f"{task_id}_validation",
            agent_name="validation_agent",
            task_type="data_validation",
            data={
                'validation_type': 'comprehensive',
                'target_data': contact_result.get('data', {})
            }
        )
        
        result = await asyncio.to_thread(agent.process_task, task)
        return result.to_dict()
    
    async def _execute_optimization_analysis(self, task_id: str, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """최적화 분석 실행"""
        if 'optimizer_agent' not in self.agents:
            return {'success': False, 'error': 'Optimizer agent not available'}
        
        agent = self.agents['optimizer_agent']
        
        # 성능 데이터 수집
        performance_data = self.performance_tracker.get_recent_metrics()
        system_metrics = self._get_system_metrics()
        
        task = AgentTask(
            task_id=f"{task_id}_optimization",
            agent_name="optimizer_agent",
            task_type="optimization_analysis",
            data={
                'optimization_type': 'comprehensive',
                'performance_data': performance_data,
                'system_metrics': system_metrics
            }
        )
        
        result = await asyncio.to_thread(agent.process_task, task)
        return result.to_dict()
    
    def _integrate_results(self, task_id: str, organization_data: Dict[str, Any],
                          homepage_result: Dict[str, Any], contact_result: Dict[str, Any],
                          validation_result: Dict[str, Any], optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """결과 통합"""
        
        # 신뢰도 점수 계산
        confidence_scores = [
            homepage_result.get('confidence_score', 0.0),
            contact_result.get('confidence_score', 0.0),
            validation_result.get('confidence_score', 0.0)
        ]
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # 최종 결과 구성
        integrated_result = {
            'task_id': task_id,
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'organization_info': organization_data,
            'overall_confidence': overall_confidence,
            'results': {
                'homepage_search': homepage_result,
                'contact_extraction': contact_result,
                'data_validation': validation_result,
                'optimization_analysis': optimization_result
            },
            'final_data': self._extract_final_data(contact_result, validation_result),
            'quality_assessment': self._assess_quality(validation_result),
            'recommendations': self._generate_recommendations(optimization_result)
        }
        
        return integrated_result
    
    def _extract_final_data(self, contact_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 데이터 추출"""
        contact_data = contact_result.get('data', {})
        validation_data = validation_result.get('data', {})
        
        return {
            'phone_numbers': contact_data.get('phone_numbers', []),
            'fax_numbers': contact_data.get('fax_numbers', []),
            'email_addresses': contact_data.get('email_addresses', []),
            'websites': contact_data.get('websites', []),
            'addresses': contact_data.get('addresses', []),
            'quality_grade': validation_data.get('quality_grade', 'F'),
            'validation_score': validation_data.get('overall_score', 0.0)
        }
    
    def _assess_quality(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """품질 평가"""
        validation_data = validation_result.get('data', {})
        
        return {
            'overall_grade': validation_data.get('quality_grade', 'F'),
            'overall_score': validation_data.get('overall_score', 0.0),
            'detailed_scores': validation_data.get('detailed_scores', {}),
            'summary': validation_data.get('summary', '품질 평가 실패')
        }
    
    def _generate_recommendations(self, optimization_result: Dict[str, Any]) -> List[str]:
        """권장사항 생성"""
        optimization_data = optimization_result.get('data', {})
        return optimization_data.get('recommendations', [])
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집"""
        return {
            'active_agents': len(self.agents),
            'total_tasks': self.system_stats['total_tasks'],
            'success_rate': (self.system_stats['successful_tasks'] / max(1, self.system_stats['total_tasks'])) * 100,
            'cpu_usage': 50,  # 실제로는 psutil 등으로 측정
            'memory_usage': 60,  # 실제로는 psutil 등으로 측정
            'uptime': (datetime.now() - self.system_stats['start_time']).total_seconds() if self.system_stats['start_time'] else 0
        }
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        if agent_name:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                return {
                    'name': agent_name,
                    'status': agent.status.value,
                    'performance': agent.get_performance_stats()
                }
            else:
                return {'error': f'Agent {agent_name} not found'}
        else:
            return {
                agent_name: {
                    'status': agent.status.value,
                    'performance': agent.get_performance_stats()
                }
                for agent_name, agent in self.agents.items()
            }
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        return {
            'system_id': self.system_id,
            'config_preset': self.config_preset,
            'is_running': self.is_running,
            'system_stats': self.system_stats,
            'agents': {
                agent_name: agent.get_performance_stats()
                for agent_name, agent in self.agents.items()
            },
            'performance_metrics': self.performance_tracker.get_recent_metrics()
        }
    
    def add_agent(self, agent_name: str, agent_config: AgentConfig):
        """에이전트 추가"""
        try:
            if agent_name in self.agents:
                logger.warning(f"에이전트 {agent_name}이 이미 존재합니다.")
                return False
            
            agent = create_agent(agent_name, agent_config)
            self.agents[agent_name] = agent
            self.system_stats['active_agents'] = len(self.agents)
            
            logger.info(f"에이전트 추가 완료: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"에이전트 추가 실패: {agent_name} - {str(e)}")
            return False
    
    def remove_agent(self, agent_name: str):
        """에이전트 제거"""
        try:
            if agent_name in self.agents:
                del self.agents[agent_name]
                self.system_stats['active_agents'] = len(self.agents)
                logger.info(f"에이전트 제거 완료: {agent_name}")
                return True
            else:
                logger.warning(f"에이전트 {agent_name}을 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"에이전트 제거 실패: {agent_name} - {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """시스템 헬스체크"""
        health_status = {
            'system_status': 'healthy' if self.is_running else 'stopped',
            'agents': {},
            'overall_health': 'healthy'
        }
        
        unhealthy_agents = 0
        
        for agent_name, agent in self.agents.items():
            try:
                # 간단한 테스트 작업 실행
                test_task = AgentTask(
                    task_id=f"health_check_{agent_name}",
                    agent_name=agent_name,
                    task_type="health_check",
                    data={'test': True}
                )
                
                # 타임아웃 설정 (5초)
                result = await asyncio.wait_for(
                    asyncio.to_thread(agent.process_task, test_task),
                    timeout=5.0
                )
                
                health_status['agents'][agent_name] = {
                    'status': 'healthy',
                    'response_time': result.processing_time if hasattr(result, 'processing_time') else 0
                }
                
            except asyncio.TimeoutError:
                health_status['agents'][agent_name] = {
                    'status': 'timeout',
                    'error': 'Health check timeout'
                }
                unhealthy_agents += 1
                
            except Exception as e:
                health_status['agents'][agent_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                unhealthy_agents += 1
        
        # 전체 헬스 상태 결정
        if unhealthy_agents > len(self.agents) / 2:
            health_status['overall_health'] = 'unhealthy'
        elif unhealthy_agents > 0:
            health_status['overall_health'] = 'degraded'
        
        return health_status 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 기본 에이전트 클래스
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..utils.gemini_client import GeminiClient
from ..metrics.performance import PerformanceTracker, PerformanceMetric

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class AgentTask:
    """에이전트 작업"""
    task_id: str
    task_type: str
    data: Dict[str, Any]
    priority: int = 1
    max_retries: int = 3
    timeout_seconds: float = 60.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AgentResult:
    """에이전트 결과"""
    task_id: str
    success: bool
    data: Dict[str, Any]
    confidence_score: float = 0.0
    error_message: str = ""
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseAgent(ABC):
    """기본 에이전트 클래스"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.gemini_client = GeminiClient()
        self.performance_tracker = PerformanceTracker()
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # 에이전트별 설정
        self.max_retries = self.config.get('max_retries', 3)
        self.timeout_seconds = self.config.get('timeout_seconds', 60.0)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        self.logger.info(f"에이전트 '{name}' 초기화 완료")
    
    @abstractmethod
    def process_task(self, task: AgentTask) -> AgentResult:
        """작업 처리 (구현 필요)"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """시스템 프롬프트 반환 (구현 필요)"""
        pass
    
    def execute_task(self, task: AgentTask) -> AgentResult:
        """작업 실행 (재시도 로직 포함)"""
        self.logger.info(f"작업 시작: {task.task_id}")
        self.status = AgentStatus.WORKING
        
        # 성능 추적 시작
        metric = PerformanceMetric(
            agent_name=self.name,
            task_type=task.task_type,
            start_time=datetime.now()
        )
        
        for attempt in range(task.max_retries + 1):
            try:
                start_time = time.time()
                
                # 실제 작업 처리
                result = self.process_task(task)
                
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                
                # 성공 시 메트릭 업데이트
                metric.end_time = datetime.now()
                metric.success = result.success
                metric.confidence_score = result.confidence_score
                metric.metadata = result.metadata
                
                self.performance_tracker.add_metric(metric)
                
                if result.success:
                    self.status = AgentStatus.COMPLETED
                    self.logger.info(f"작업 완료: {task.task_id} (시도: {attempt + 1})")
                    return result
                else:
                    self.logger.warning(f"작업 실패: {task.task_id} (시도: {attempt + 1}) - {result.error_message}")
                    
            except Exception as e:
                error_msg = f"작업 처리 중 오류: {str(e)}"
                self.logger.error(error_msg)
                
                if attempt == task.max_retries:
                    # 최종 실패
                    metric.end_time = datetime.now()
                    metric.success = False
                    metric.error_message = error_msg
                    self.performance_tracker.add_metric(metric)
                    
                    self.status = AgentStatus.ERROR
                    return AgentResult(
                        task_id=task.task_id,
                        success=False,
                        data={},
                        error_message=error_msg,
                        processing_time=time.time() - start_time
                    )
                
                # 재시도 전 대기
                time.sleep(min(2 ** attempt, 10))  # 지수 백오프
        
        # 모든 재시도 실패
        self.status = AgentStatus.ERROR
        return AgentResult(
            task_id=task.task_id,
            success=False,
            data={},
            error_message="모든 재시도 실패",
            processing_time=0.0
        )
    
    def query_gemini(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gemini API 호출"""
        try:
            system_prompt = self.get_system_prompt()
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            if context:
                full_prompt += f"\n\n컨텍스트:\n{context}"
            
            response = self.gemini_client.generate_content(full_prompt)
            
            return {
                'success': True,
                'content': response,
                'confidence': self._calculate_confidence(response)
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API 호출 실패: {str(e)}")
            return {
                'success': False,
                'content': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_confidence(self, response: str) -> float:
        """응답의 신뢰도 계산"""
        if not response:
            return 0.0
        
        # 간단한 신뢰도 계산 로직
        confidence = 0.5  # 기본값
        
        # 응답 길이에 따른 가중치
        if len(response) > 100:
            confidence += 0.1
        if len(response) > 500:
            confidence += 0.1
        
        # 특정 키워드 포함 여부
        positive_keywords = ['확실', '명확', '정확', '신뢰할 수 있는']
        negative_keywords = ['불확실', '애매', '추측', '확실하지 않은']
        
        for keyword in positive_keywords:
            if keyword in response:
                confidence += 0.1
        
        for keyword in negative_keywords:
            if keyword in response:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.performance_tracker.get_agent_stats(self.name)
    
    def reset_status(self):
        """상태 초기화"""
        self.status = AgentStatus.IDLE
        self.logger.info(f"에이전트 '{self.name}' 상태 초기화")
    
    def __str__(self):
        return f"Agent({self.name}, status={self.status.value})"
    
    def __repr__(self):
        return f"Agent(name='{self.name}', status='{self.status.value}', config={self.config})" 
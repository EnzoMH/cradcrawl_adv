#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 조정자 (Agent Coordinator)
여러 에이전트 간의 작업 조정 및 워크플로우 관리
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dataclasses import dataclass, field

from .agent_base import BaseAgent, AgentTask, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """워크플로우 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class WorkflowTask:
    """워크플로우 작업"""
    task_id: str
    agent_name: str
    task_type: str
    data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 60.0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[AgentResult] = None
    error: Optional[str] = None
    retry_count: int = 0

@dataclass
class Workflow:
    """워크플로우"""
    workflow_id: str
    name: str
    tasks: List[WorkflowTask]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentCoordinator:
    """에이전트 조정자"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """
        에이전트 조정자 초기화
        
        Args:
            max_concurrent_tasks: 최대 동시 작업 수
        """
        self.coordinator_id = str(uuid.uuid4())
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_workflows: Dict[str, Workflow] = {}
        self.completed_workflows: Dict[str, Workflow] = {}
        self.task_queue: List[WorkflowTask] = []
        self.running_tasks: Dict[str, WorkflowTask] = {}
        
        # 통계
        self.stats = {
            'total_workflows': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_workflow_time': 0.0,
            'average_task_time': 0.0
        }
        
        logger.info(f"에이전트 조정자 초기화 완료 (ID: {self.coordinator_id})")
    
    def create_workflow(self, name: str, tasks: List[Dict[str, Any]], 
                       metadata: Dict[str, Any] = None) -> str:
        """
        워크플로우 생성
        
        Args:
            name: 워크플로우 이름
            tasks: 작업 목록
            metadata: 메타데이터
            
        Returns:
            str: 워크플로우 ID
        """
        workflow_id = str(uuid.uuid4())
        
        # 작업 객체 생성
        workflow_tasks = []
        for task_data in tasks:
            task = WorkflowTask(
                task_id=str(uuid.uuid4()),
                agent_name=task_data['agent_name'],
                task_type=task_data['task_type'],
                data=task_data['data'],
                priority=TaskPriority(task_data.get('priority', TaskPriority.MEDIUM.value)),
                dependencies=task_data.get('dependencies', []),
                timeout=task_data.get('timeout', 60.0),
                max_retries=task_data.get('max_retries', 3)
            )
            workflow_tasks.append(task)
        
        # 워크플로우 생성
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            tasks=workflow_tasks,
            metadata=metadata or {}
        )
        
        self.active_workflows[workflow_id] = workflow
        self.stats['total_workflows'] += 1
        
        logger.info(f"워크플로우 생성: {name} (ID: {workflow_id})")
        return workflow_id
    
    def create_crawling_workflow(self, organization_data: Dict[str, Any]) -> str:
        """
        크롤링 워크플로우 생성
        
        Args:
            organization_data: 조직 데이터
            
        Returns:
            str: 워크플로우 ID
        """
        tasks = [
            {
                'agent_name': 'homepage_agent',
                'task_type': 'homepage_search',
                'data': organization_data,
                'priority': TaskPriority.HIGH.value,
                'dependencies': [],
                'timeout': 120.0
            },
            {
                'agent_name': 'contact_agent',
                'task_type': 'contact_extraction',
                'data': {'text': '', 'extraction_type': 'all'},
                'priority': TaskPriority.HIGH.value,
                'dependencies': ['homepage_search'],
                'timeout': 90.0
            },
            {
                'agent_name': 'validation_agent',
                'task_type': 'data_validation',
                'data': {'validation_type': 'comprehensive', 'target_data': {}},
                'priority': TaskPriority.MEDIUM.value,
                'dependencies': ['contact_extraction'],
                'timeout': 60.0
            },
            {
                'agent_name': 'optimizer_agent',
                'task_type': 'optimization_analysis',
                'data': {'optimization_type': 'comprehensive'},
                'priority': TaskPriority.LOW.value,
                'dependencies': ['data_validation'],
                'timeout': 180.0
            }
        ]
        
        return self.create_workflow(
            name=f"크롤링 워크플로우 - {organization_data.get('organization_name', 'Unknown')}",
            tasks=tasks,
            metadata={'organization_data': organization_data}
        )
    
    async def execute_workflow(self, workflow_id: str, agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """
        워크플로우 실행
        
        Args:
            workflow_id: 워크플로우 ID
            agents: 에이전트 딕셔너리
            
        Returns:
            Dict: 실행 결과
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"워크플로우를 찾을 수 없습니다: {workflow_id}")
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        try:
            logger.info(f"워크플로우 실행 시작: {workflow.name} (ID: {workflow_id})")
            
            # 의존성 그래프 생성
            dependency_graph = self._build_dependency_graph(workflow.tasks)
            
            # 작업 실행
            results = await self._execute_tasks(workflow, dependency_graph, agents)
            
            # 워크플로우 완료
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            
            # 통계 업데이트
            self.stats['successful_workflows'] += 1
            execution_time = (workflow.completed_at - workflow.started_at).total_seconds()
            self._update_average_workflow_time(execution_time)
            
            # 완료된 워크플로우 이동
            self.completed_workflows[workflow_id] = workflow
            del self.active_workflows[workflow_id]
            
            logger.info(f"워크플로우 실행 완료: {workflow.name} (처리시간: {execution_time:.2f}초)")
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'results': results,
                'execution_time': execution_time,
                'task_count': len(workflow.tasks)
            }
            
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {workflow.name} - {str(e)}")
            
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            self.stats['failed_workflows'] += 1
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': (workflow.completed_at - workflow.started_at).total_seconds() if workflow.started_at else 0
            }
    
    def _build_dependency_graph(self, tasks: List[WorkflowTask]) -> Dict[str, List[str]]:
        """의존성 그래프 구축"""
        graph = {}
        task_map = {task.task_type: task.task_id for task in tasks}
        
        for task in tasks:
            dependencies = []
            for dep in task.dependencies:
                if dep in task_map:
                    dependencies.append(task_map[dep])
            graph[task.task_id] = dependencies
        
        return graph
    
    async def _execute_tasks(self, workflow: Workflow, dependency_graph: Dict[str, List[str]], 
                           agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """작업 실행"""
        task_map = {task.task_id: task for task in workflow.tasks}
        completed_tasks = set()
        results = {}
        
        # 실행 가능한 작업 찾기
        while len(completed_tasks) < len(workflow.tasks):
            ready_tasks = []
            
            for task_id, dependencies in dependency_graph.items():
                if task_id not in completed_tasks and all(dep in completed_tasks for dep in dependencies):
                    ready_tasks.append(task_map[task_id])
            
            if not ready_tasks:
                raise RuntimeError("순환 의존성 또는 해결할 수 없는 의존성이 있습니다.")
            
            # 우선순위 정렬
            ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
            
            # 동시 실행 (최대 동시 작업 수 제한)
            batch_size = min(len(ready_tasks), self.max_concurrent_tasks)
            batch_tasks = ready_tasks[:batch_size]
            
            # 작업 실행
            batch_results = await asyncio.gather(
                *[self._execute_single_task(task, agents, results) for task in batch_tasks],
                return_exceptions=True
            )
            
            # 결과 처리
            for task, result in zip(batch_tasks, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"작업 실행 실패: {task.task_id} - {str(result)}")
                    task.status = WorkflowStatus.FAILED
                    task.error = str(result)
                    self.stats['failed_tasks'] += 1
                else:
                    task.status = WorkflowStatus.COMPLETED
                    task.result = result
                    results[task.task_id] = result
                    completed_tasks.add(task.task_id)
                    self.stats['successful_tasks'] += 1
                
                self.stats['total_tasks'] += 1
        
        return results
    
    async def _execute_single_task(self, task: WorkflowTask, agents: Dict[str, BaseAgent], 
                                 previous_results: Dict[str, Any]) -> AgentResult:
        """단일 작업 실행"""
        if task.agent_name not in agents:
            raise ValueError(f"에이전트를 찾을 수 없습니다: {task.agent_name}")
        
        agent = agents[task.agent_name]
        
        # 이전 결과를 현재 작업 데이터에 통합
        task_data = self._prepare_task_data(task, previous_results)
        
        # 에이전트 작업 생성
        agent_task = AgentTask(
            task_id=task.task_id,
            agent_name=task.agent_name,
            task_type=task.task_type,
            data=task_data
        )
        
        # 재시도 로직
        for attempt in range(task.max_retries + 1):
            try:
                task.retry_count = attempt
                
                # 타임아웃 설정
                result = await asyncio.wait_for(
                    asyncio.to_thread(agent.process_task, agent_task),
                    timeout=task.timeout
                )
                
                if result.success:
                    return result
                else:
                    logger.warning(f"작업 실패 (시도 {attempt + 1}/{task.max_retries + 1}): {task.task_id}")
                    if attempt == task.max_retries:
                        raise RuntimeError(f"작업 실패: {result.error_message}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"작업 타임아웃 (시도 {attempt + 1}/{task.max_retries + 1}): {task.task_id}")
                if attempt == task.max_retries:
                    raise RuntimeError(f"작업 타임아웃: {task.timeout}초")
                    
            except Exception as e:
                logger.warning(f"작업 오류 (시도 {attempt + 1}/{task.max_retries + 1}): {task.task_id} - {str(e)}")
                if attempt == task.max_retries:
                    raise
                
            # 재시도 전 대기
            await asyncio.sleep(min(2 ** attempt, 10))  # 지수 백오프
        
        raise RuntimeError("모든 재시도 실패")
    
    def _prepare_task_data(self, task: WorkflowTask, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """작업 데이터 준비"""
        task_data = task.data.copy()
        
        # 작업 타입별 데이터 준비
        if task.task_type == 'contact_extraction':
            # 홈페이지 검색 결과에서 텍스트 추출
            homepage_results = [r for r in previous_results.values() if hasattr(r, 'data') and 'homepage_url' in r.data]
            if homepage_results:
                # 시뮬레이션: 실제로는 홈페이지 콘텐츠 크롤링
                task_data['text'] = f"홈페이지 콘텐츠 시뮬레이션 - {homepage_results[0].data.get('homepage_url', '')}"
        
        elif task.task_type == 'data_validation':
            # 연락처 추출 결과 사용
            contact_results = [r for r in previous_results.values() if hasattr(r, 'data') and 'phone_numbers' in r.data]
            if contact_results:
                task_data['target_data'] = contact_results[0].data
        
        elif task.task_type == 'optimization_analysis':
            # 모든 이전 결과 사용
            task_data['all_results'] = {
                result_id: result.data if hasattr(result, 'data') else result
                for result_id, result in previous_results.items()
            }
        
        return task_data
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        workflow = self.active_workflows.get(workflow_id) or self.completed_workflows.get(workflow_id)
        
        if not workflow:
            return {'error': f'워크플로우를 찾을 수 없습니다: {workflow_id}'}
        
        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'task_count': len(workflow.tasks),
            'completed_tasks': len([t for t in workflow.tasks if t.status == WorkflowStatus.COMPLETED]),
            'failed_tasks': len([t for t in workflow.tasks if t.status == WorkflowStatus.FAILED]),
            'tasks': [
                {
                    'task_id': task.task_id,
                    'agent_name': task.agent_name,
                    'task_type': task.task_type,
                    'status': task.status.value,
                    'priority': task.priority.value,
                    'retry_count': task.retry_count,
                    'error': task.error
                }
                for task in workflow.tasks
            ]
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """워크플로우 취소"""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now()
        
        # 실행 중인 작업들 취소
        for task in workflow.tasks:
            if task.status == WorkflowStatus.RUNNING:
                task.status = WorkflowStatus.CANCELLED
        
        logger.info(f"워크플로우 취소: {workflow.name} (ID: {workflow_id})")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """조정자 통계 조회"""
        return {
            'coordinator_id': self.coordinator_id,
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.completed_workflows),
            'running_tasks': len(self.running_tasks),
            'stats': self.stats,
            'performance': {
                'success_rate': (self.stats['successful_workflows'] / max(1, self.stats['total_workflows'])) * 100,
                'task_success_rate': (self.stats['successful_tasks'] / max(1, self.stats['total_tasks'])) * 100,
                'average_workflow_time': self.stats['average_workflow_time'],
                'average_task_time': self.stats['average_task_time']
            }
        }
    
    def _update_average_workflow_time(self, execution_time: float):
        """평균 워크플로우 시간 업데이트"""
        total_workflows = self.stats['successful_workflows']
        if total_workflows == 1:
            self.stats['average_workflow_time'] = execution_time
        else:
            current_avg = self.stats['average_workflow_time']
            self.stats['average_workflow_time'] = ((current_avg * (total_workflows - 1)) + execution_time) / total_workflows
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """완료된 워크플로우 정리"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for workflow_id, workflow in self.completed_workflows.items():
            if workflow.completed_at and workflow.completed_at < cutoff_time:
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.completed_workflows[workflow_id]
        
        logger.info(f"완료된 워크플로우 정리: {len(to_remove)}개 제거")
        return len(to_remove) 
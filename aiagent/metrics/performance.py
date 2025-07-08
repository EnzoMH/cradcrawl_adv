#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 성능 측정 및 모니터링 시스템
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import psutil
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """성능 지표"""
    agent_name: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    confidence_score: float = 0.0
    error_message: str = ""
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """작업 소요 시간 (초)"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'agent_name': self.agent_name,
            'task_type': self.task_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'success': self.success,
            'confidence_score': self.confidence_score,
            'error_message': self.error_message,
            'resource_usage': self.resource_usage,
            'metadata': self.metadata
        }

class PerformanceTracker:
    """성능 추적기"""
    
    def __init__(self, max_metrics: int = 10000):
        """
        성능 추적기 초기화
        
        Args:
            max_metrics: 저장할 최대 메트릭 수
        """
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.agent_stats: Dict[str, Dict] = defaultdict(lambda: {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_duration': 0.0,
            'average_confidence': 0.0,
            'total_duration': 0.0,
            'last_activity': None
        })
        self.lock = threading.Lock()
        
        logger.info("성능 추적기 초기화 완료")
    
    def add_metric(self, metric: PerformanceMetric):
        """메트릭 추가"""
        with self.lock:
            self.metrics.append(metric)
            self._update_agent_stats(metric)
    
    def _update_agent_stats(self, metric: PerformanceMetric):
        """에이전트 통계 업데이트"""
        stats = self.agent_stats[metric.agent_name]
        
        stats['total_tasks'] += 1
        stats['last_activity'] = metric.end_time or metric.start_time
        
        if metric.success:
            stats['successful_tasks'] += 1
        else:
            stats['failed_tasks'] += 1
        
        if metric.duration > 0:
            stats['total_duration'] += metric.duration
            stats['average_duration'] = stats['total_duration'] / stats['total_tasks']
        
        if metric.confidence_score > 0:
            # 누적 평균 계산
            current_avg = stats['average_confidence']
            total_tasks = stats['total_tasks']
            stats['average_confidence'] = (current_avg * (total_tasks - 1) + metric.confidence_score) / total_tasks
    
    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """특정 에이전트 통계 반환"""
        with self.lock:
            stats = self.agent_stats.get(agent_name, {})
            if stats:
                stats = dict(stats)  # 복사본 반환
                stats['success_rate'] = (
                    stats['successful_tasks'] / stats['total_tasks'] 
                    if stats['total_tasks'] > 0 else 0.0
                )
                stats['failure_rate'] = (
                    stats['failed_tasks'] / stats['total_tasks'] 
                    if stats['total_tasks'] > 0 else 0.0
                )
            return stats
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 에이전트 통계 반환"""
        with self.lock:
            all_stats = {}
            for agent_name in self.agent_stats:
                all_stats[agent_name] = self.get_agent_stats(agent_name)
            return all_stats
    
    def get_recent_metrics(self, minutes: int = 60) -> List[PerformanceMetric]:
        """최근 메트릭 반환"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            recent_metrics = []
            for metric in reversed(self.metrics):
                if metric.start_time >= cutoff_time:
                    recent_metrics.append(metric)
                else:
                    break
            
            return list(reversed(recent_metrics))
    
    def get_task_type_stats(self, task_type: str) -> Dict[str, Any]:
        """작업 유형별 통계"""
        with self.lock:
            matching_metrics = [m for m in self.metrics if m.task_type == task_type]
            
            if not matching_metrics:
                return {}
            
            successful = [m for m in matching_metrics if m.success]
            failed = [m for m in matching_metrics if not m.success]
            
            durations = [m.duration for m in matching_metrics if m.duration > 0]
            confidences = [m.confidence_score for m in matching_metrics if m.confidence_score > 0]
            
            return {
                'task_type': task_type,
                'total_tasks': len(matching_metrics),
                'successful_tasks': len(successful),
                'failed_tasks': len(failed),
                'success_rate': len(successful) / len(matching_metrics) if matching_metrics else 0.0,
                'average_duration': statistics.mean(durations) if durations else 0.0,
                'median_duration': statistics.median(durations) if durations else 0.0,
                'min_duration': min(durations) if durations else 0.0,
                'max_duration': max(durations) if durations else 0.0,
                'average_confidence': statistics.mean(confidences) if confidences else 0.0,
                'median_confidence': statistics.median(confidences) if confidences else 0.0
            }
    
    def generate_performance_report(self, format: str = "dict") -> Any:
        """성능 리포트 생성"""
        with self.lock:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'total_metrics': len(self.metrics),
                'agent_stats': self.get_all_stats(),
                'task_type_stats': {},
                'system_overview': self._get_system_overview()
            }
            
            # 작업 유형별 통계
            task_types = set(m.task_type for m in self.metrics)
            for task_type in task_types:
                report_data['task_type_stats'][task_type] = self.get_task_type_stats(task_type)
            
            if format == "dict":
                return report_data
            elif format == "json":
                return json.dumps(report_data, indent=2, ensure_ascii=False)
            elif format == "dataframe":
                return self._to_dataframe()
            else:
                raise ValueError(f"지원하지 않는 형식: {format}")
    
    def _get_system_overview(self) -> Dict[str, Any]:
        """시스템 개요"""
        if not self.metrics:
            return {}
        
        recent_metrics = self.get_recent_metrics(60)  # 최근 1시간
        
        total_tasks = len(self.metrics)
        successful_tasks = sum(1 for m in self.metrics if m.success)
        
        durations = [m.duration for m in self.metrics if m.duration > 0]
        confidences = [m.confidence_score for m in self.metrics if m.confidence_score > 0]
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': total_tasks - successful_tasks,
            'overall_success_rate': successful_tasks / total_tasks if total_tasks > 0 else 0.0,
            'recent_tasks_count': len(recent_metrics),
            'average_duration': statistics.mean(durations) if durations else 0.0,
            'average_confidence': statistics.mean(confidences) if confidences else 0.0,
            'active_agents': len(self.agent_stats),
            'unique_task_types': len(set(m.task_type for m in self.metrics))
        }
    
    def _to_dataframe(self) -> pd.DataFrame:
        """DataFrame으로 변환"""
        if not self.metrics:
            return pd.DataFrame()
        
        data = [metric.to_dict() for metric in self.metrics]
        df = pd.DataFrame(data)
        
        # 시간 컬럼 변환
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        
        return df
    
    def export_to_file(self, filepath: str, format: str = "json"):
        """파일로 내보내기"""
        try:
            if format == "json":
                report = self.generate_performance_report("json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report)
            elif format == "csv":
                df = self._to_dataframe()
                df.to_csv(filepath, index=False, encoding='utf-8')
            elif format == "excel":
                df = self._to_dataframe()
                df.to_excel(filepath, index=False, engine='openpyxl')
            else:
                raise ValueError(f"지원하지 않는 형식: {format}")
            
            logger.info(f"성능 리포트 저장 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"성능 리포트 저장 실패: {str(e)}")
            raise
    
    def clear_metrics(self):
        """메트릭 초기화"""
        with self.lock:
            self.metrics.clear()
            self.agent_stats.clear()
            logger.info("성능 메트릭 초기화 완료")
    
    def get_top_performing_agents(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """성능 상위 에이전트 반환"""
        all_stats = self.get_all_stats()
        
        # 성공률과 평균 신뢰도로 정렬
        sorted_agents = sorted(
            all_stats.items(),
            key=lambda x: (x[1].get('success_rate', 0), x[1].get('average_confidence', 0)),
            reverse=True
        )
        
        return [
            {'agent_name': name, **stats}
            for name, stats in sorted_agents[:top_n]
        ]
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List]:
        """성능 트렌드 데이터"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [m for m in self.metrics if m.start_time >= cutoff_time]
            
            # 시간대별 그룹화 (1시간 단위)
            hourly_data = defaultdict(lambda: {'success': 0, 'failure': 0, 'total_duration': 0.0, 'count': 0})
            
            for metric in recent_metrics:
                hour_key = metric.start_time.strftime('%Y-%m-%d %H:00')
                hourly_data[hour_key]['count'] += 1
                hourly_data[hour_key]['total_duration'] += metric.duration
                
                if metric.success:
                    hourly_data[hour_key]['success'] += 1
                else:
                    hourly_data[hour_key]['failure'] += 1
            
            # 결과 정리
            times = sorted(hourly_data.keys())
            success_rates = []
            avg_durations = []
            task_counts = []
            
            for time_key in times:
                data = hourly_data[time_key]
                success_rate = data['success'] / data['count'] if data['count'] > 0 else 0.0
                avg_duration = data['total_duration'] / data['count'] if data['count'] > 0 else 0.0
                
                success_rates.append(success_rate)
                avg_durations.append(avg_duration)
                task_counts.append(data['count'])
            
            return {
                'times': times,
                'success_rates': success_rates,
                'avg_durations': avg_durations,
                'task_counts': task_counts
            } 
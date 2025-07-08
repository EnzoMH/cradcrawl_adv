#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - 시스템 모니터링
실시간 시스템 상태 모니터링 및 알림 기능
"""

import asyncio
import time
import os
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """시스템 건강 상태"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_agents: int
    pending_tasks: int
    error_count: int
    response_time: float
    overall_status: str = "healthy"  # healthy, warning, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_io': self.network_io,
            'active_agents': self.active_agents,
            'pending_tasks': self.pending_tasks,
            'error_count': self.error_count,
            'response_time': self.response_time,
            'overall_status': self.overall_status
        }

@dataclass
class AlertRule:
    """알림 규칙"""
    name: str
    condition: Callable[[SystemHealth], bool]
    severity: str  # info, warning, critical
    message_template: str
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, health: SystemHealth) -> bool:
        """알림 발생 조건 확인"""
        if not self.condition(health):
            return False
        
        # 쿨다운 시간 확인
        if self.last_triggered:
            cooldown_delta = timedelta(minutes=self.cooldown_minutes)
            if datetime.now() - self.last_triggered < cooldown_delta:
                return False
        
        return True
    
    def trigger(self, health: SystemHealth) -> str:
        """알림 발생"""
        self.last_triggered = datetime.now()
        return self.message_template.format(
            cpu=health.cpu_usage,
            memory=health.memory_usage,
            disk=health.disk_usage,
            agents=health.active_agents,
            tasks=health.pending_tasks,
            errors=health.error_count,
            response_time=health.response_time
        )

class SystemMonitor:
    """시스템 모니터링 클래스"""
    
    def __init__(self, 
                 check_interval: float = 30.0,
                 history_size: int = 100,
                 enable_alerts: bool = True):
        """
        시스템 모니터 초기화
        
        Args:
            check_interval: 모니터링 간격 (초)
            history_size: 히스토리 보관 개수
            enable_alerts: 알림 활성화 여부
        """
        self.check_interval = check_interval
        self.history_size = history_size
        self.enable_alerts = enable_alerts
        
        # 상태 히스토리
        self.health_history: deque = deque(maxlen=history_size)
        
        # 에이전트 상태 추적
        self.agent_stats: Dict[str, Dict] = defaultdict(dict)
        self.task_stats: Dict[str, Any] = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'average_response_time': 0.0
        }
        
        # 알림 규칙
        self.alert_rules: List[AlertRule] = []
        self.alert_callbacks: List[Callable] = []
        
        # 모니터링 제어
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 기본 알림 규칙 설정
        self._setup_default_alert_rules()
    
    def _setup_default_alert_rules(self):
        """기본 알림 규칙 설정"""
        self.alert_rules = [
            AlertRule(
                name="high_cpu_usage",
                condition=lambda h: h.cpu_usage > 80.0,
                severity="warning",
                message_template="⚠️ CPU 사용률 높음: {cpu:.1f}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_memory_usage",
                condition=lambda h: h.memory_usage > 85.0,
                severity="warning",
                message_template="⚠️ 메모리 사용률 높음: {memory:.1f}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="critical_cpu_usage",
                condition=lambda h: h.cpu_usage > 95.0,
                severity="critical",
                message_template="🚨 CPU 사용률 위험: {cpu:.1f}%",
                cooldown_minutes=2
            ),
            AlertRule(
                name="critical_memory_usage",
                condition=lambda h: h.memory_usage > 95.0,
                severity="critical",
                message_template="🚨 메모리 사용률 위험: {memory:.1f}%",
                cooldown_minutes=2
            ),
            AlertRule(
                name="high_error_rate",
                condition=lambda h: h.error_count > 10,
                severity="warning",
                message_template="⚠️ 오류 발생 증가: {errors}개",
                cooldown_minutes=10
            ),
            AlertRule(
                name="slow_response_time",
                condition=lambda h: h.response_time > 5.0,
                severity="warning",
                message_template="⚠️ 응답 시간 지연: {response_time:.2f}초",
                cooldown_minutes=5
            ),
            AlertRule(
                name="no_active_agents",
                condition=lambda h: h.active_agents == 0,
                severity="critical",
                message_template="🚨 활성 에이전트 없음",
                cooldown_minutes=1
            )
        ]
    
    def add_alert_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        self.alert_rules.append(rule)
        logger.info(f"알림 규칙 추가: {rule.name}")
    
    def add_alert_callback(self, callback: Callable[[str, str, str], None]):
        """
        알림 콜백 추가
        
        Args:
            callback: (rule_name, severity, message) -> None
        """
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            logger.warning("모니터링이 이미 실행 중입니다.")
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("시스템 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("시스템 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while not self.stop_event.wait(self.check_interval):
            try:
                health = self._collect_system_health()
                self.health_history.append(health)
                
                # 알림 확인
                if self.enable_alerts:
                    self._check_alerts(health)
                
                # 로그 기록
                self._log_health_status(health)
                
            except Exception as e:
                logger.error(f"모니터링 중 오류 발생: {str(e)}")
    
    def _collect_system_health(self) -> SystemHealth:
        """시스템 건강 상태 수집"""
        # CPU 사용률
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 디스크 사용률 (Windows 호환)
        try:
            disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
            disk_usage = disk.percent
        except:
            disk_usage = 0.0
        
        # 네트워크 I/O
        network_io = psutil.net_io_counters()
        network_data = {
            'bytes_sent': network_io.bytes_sent,
            'bytes_recv': network_io.bytes_recv,
            'packets_sent': network_io.packets_sent,
            'packets_recv': network_io.packets_recv
        }
        
        # 에이전트 상태
        active_agents = len([stats for stats in self.agent_stats.values() 
                           if stats.get('status') == 'active'])
        
        # 작업 상태
        pending_tasks = sum(stats.get('pending_tasks', 0) 
                          for stats in self.agent_stats.values())
        
        # 오류 카운트
        error_count = self.task_stats.get('error_count', 0)
        
        # 응답 시간
        response_time = self.task_stats.get('average_response_time', 0.0)
        
        # 전체 상태 판단
        overall_status = self._determine_overall_status(
            cpu_usage, memory_usage, disk_usage, error_count, response_time
        )
        
        return SystemHealth(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_data,
            active_agents=active_agents,
            pending_tasks=pending_tasks,
            error_count=error_count,
            response_time=response_time,
            overall_status=overall_status
        )
    
    def _determine_overall_status(self, cpu: float, memory: float, 
                                disk: float, errors: int, response_time: float) -> str:
        """전체 상태 판단"""
        # 위험 상태
        if cpu > 95 or memory > 95 or disk > 95:
            return "critical"
        
        # 경고 상태
        if cpu > 80 or memory > 80 or disk > 80 or errors > 10 or response_time > 5:
            return "warning"
        
        # 정상 상태
        return "healthy"
    
    def _check_alerts(self, health: SystemHealth):
        """알림 확인 및 발송"""
        for rule in self.alert_rules:
            if rule.should_trigger(health):
                message = rule.trigger(health)
                
                # 콜백 호출
                for callback in self.alert_callbacks:
                    try:
                        callback(rule.name, rule.severity, message)
                    except Exception as e:
                        logger.error(f"알림 콜백 오류: {str(e)}")
                
                # 로그 기록
                logger.warning(f"알림 발생 [{rule.severity}]: {message}")
    
    def _log_health_status(self, health: SystemHealth):
        """건강 상태 로그 기록"""
        if health.overall_status == "critical":
            logger.error(f"시스템 상태 위험: CPU {health.cpu_usage:.1f}%, "
                        f"메모리 {health.memory_usage:.1f}%, "
                        f"오류 {health.error_count}개")
        elif health.overall_status == "warning":
            logger.warning(f"시스템 상태 경고: CPU {health.cpu_usage:.1f}%, "
                          f"메모리 {health.memory_usage:.1f}%")
        else:
            logger.debug(f"시스템 정상: CPU {health.cpu_usage:.1f}%, "
                        f"메모리 {health.memory_usage:.1f}%")
    
    def update_agent_stats(self, agent_id: str, stats: Dict[str, Any]):
        """에이전트 상태 업데이트"""
        self.agent_stats[agent_id].update(stats)
        self.agent_stats[agent_id]['last_update'] = datetime.now()
    
    def update_task_stats(self, stats: Dict[str, Any]):
        """작업 통계 업데이트"""
        self.task_stats.update(stats)
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """현재 건강 상태 반환"""
        if not self.health_history:
            return None
        return self.health_history[-1]
    
    def get_health_history(self, minutes: int = 60) -> List[SystemHealth]:
        """지정된 시간 동안의 건강 상태 히스토리 반환"""
        if not self.health_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [health for health in self.health_history 
                if health.timestamp >= cutoff_time]
    
    def get_system_summary(self) -> Dict[str, Any]:
        """시스템 요약 정보 반환"""
        current = self.get_current_health()
        if not current:
            return {'status': 'no_data'}
        
        history = self.get_health_history(60)  # 최근 1시간
        
        # 평균 계산
        avg_cpu = sum(h.cpu_usage for h in history) / len(history) if history else 0
        avg_memory = sum(h.memory_usage for h in history) / len(history) if history else 0
        avg_response = sum(h.response_time for h in history) / len(history) if history else 0
        
        return {
            'current_status': current.overall_status,
            'current_cpu': current.cpu_usage,
            'current_memory': current.memory_usage,
            'current_disk': current.disk_usage,
            'active_agents': current.active_agents,
            'pending_tasks': current.pending_tasks,
            'error_count': current.error_count,
            'avg_cpu_1h': avg_cpu,
            'avg_memory_1h': avg_memory,
            'avg_response_time_1h': avg_response,
            'total_processed': self.task_stats.get('total_processed', 0),
            'success_rate': self._calculate_success_rate(),
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_success_rate(self) -> float:
        """성공률 계산"""
        total = self.task_stats.get('total_processed', 0)
        if total == 0:
            return 0.0
        
        success = self.task_stats.get('success_count', 0)
        return (success / total) * 100
    
    def _calculate_uptime(self) -> str:
        """업타임 계산"""
        if not self.health_history:
            return "0분"
        
        first_record = self.health_history[0]
        uptime_delta = datetime.now() - first_record.timestamp
        
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        
        if uptime_delta.days > 0:
            return f"{uptime_delta.days}일 {hours}시간 {minutes}분"
        elif hours > 0:
            return f"{hours}시간 {minutes}분"
        else:
            return f"{minutes}분"
    
    def generate_health_report(self) -> str:
        """건강 상태 리포트 생성"""
        summary = self.get_system_summary()
        current = self.get_current_health()
        
        if not current:
            return "📊 시스템 모니터링 데이터 없음"
        
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🚨'
        }
        
        report = f"""
📊 시스템 건강 상태 리포트
{'='*50}

🔍 현재 상태: {status_emoji.get(current.overall_status, '❓')} {current.overall_status.upper()}
📅 마지막 업데이트: {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

💻 시스템 리소스:
   CPU 사용률: {current.cpu_usage:.1f}% (평균: {summary['avg_cpu_1h']:.1f}%)
   메모리 사용률: {current.memory_usage:.1f}% (평균: {summary['avg_memory_1h']:.1f}%)
   디스크 사용률: {current.disk_usage:.1f}%

🤖 에이전트 상태:
   활성 에이전트: {current.active_agents}개
   대기 중인 작업: {current.pending_tasks}개
   오류 발생: {current.error_count}개

📈 성능 지표:
   평균 응답 시간: {current.response_time:.2f}초 (1시간 평균: {summary['avg_response_time_1h']:.2f}초)
   총 처리 건수: {summary['total_processed']}건
   성공률: {summary['success_rate']:.1f}%

⏰ 운영 시간: {summary['uptime']}

🌐 네트워크 I/O:
   송신: {current.network_io['bytes_sent']:,} bytes
   수신: {current.network_io['bytes_recv']:,} bytes
        """
        
        return report.strip()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_monitoring()

# 전역 모니터 인스턴스
_global_monitor: Optional[SystemMonitor] = None

def get_system_monitor() -> SystemMonitor:
    """전역 시스템 모니터 인스턴스 반환"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = SystemMonitor()
    return _global_monitor

def start_global_monitoring():
    """전역 모니터링 시작"""
    monitor = get_system_monitor()
    monitor.start_monitoring()
    return monitor

def stop_global_monitoring():
    """전역 모니터링 중지"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()

# 편의 함수들
def log_alert(rule_name: str, severity: str, message: str):
    """기본 알림 로깅 함수"""
    level_map = {
        'info': logging.INFO,
        'warning': logging.WARNING,
        'critical': logging.ERROR
    }
    
    level = level_map.get(severity, logging.INFO)
    logger.log(level, f"[{rule_name}] {message}")

def print_alert(rule_name: str, severity: str, message: str):
    """콘솔 알림 출력 함수"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

if __name__ == "__main__":
    # 테스트 실행
    print("🔍 시스템 모니터링 테스트 시작...")
    
    # 알림 콜백 설정
    monitor = SystemMonitor(check_interval=5.0)
    monitor.add_alert_callback(print_alert)
    
    try:
        with monitor:
            print("✅ 모니터링 시작됨")
            print("📊 10초 후 현재 상태 출력...")
            time.sleep(10)
            
            # 현재 상태 출력
            print(monitor.generate_health_report())
            
            print("\n⏳ 추가로 10초 대기...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n⏹️ 모니터링 중단됨")
    
    print("✅ 테스트 완료") 
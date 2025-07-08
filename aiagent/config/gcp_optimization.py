#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCP e2-small 환경 최적화 설정
메모리 2GB, vCPU 0.5 제약 조건 하에서 최적 성능 달성

주요 최적화:
1. 메모리 사용량 모니터링 및 자동 조정
2. 단일 워커 최적화
3. Gemini API 호출 최적화
4. 가비지 컬렉션 튜닝
5. 배치 크기 동적 조정
"""

import os
import gc
import psutil
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import queue
import json


@dataclass
class GCPResourceLimits:
    """GCP e2-small 리소스 제한"""
    MAX_MEMORY_MB: int = 1800  # 2GB 중 1.8GB만 사용 (안전 마진)
    MAX_CPU_PERCENT: float = 80.0  # 0.5 vCPU의 80%
    MAX_CONCURRENT_REQUESTS: int = 1  # 단일 요청만
    BATCH_SIZE_MIN: int = 1
    BATCH_SIZE_MAX: int = 5
    GEMINI_RPM_LIMIT: int = 1000  # 보수적 설정
    
    # 타임아웃 설정
    SEARCH_TIMEOUT: int = 15  # 검색 타임아웃
    PAGE_LOAD_TIMEOUT: int = 10  # 페이지 로드 타임아웃
    WEBDRIVER_TIMEOUT: int = 30  # WebDriver 타임아웃


class GCPOptimizer:
    """GCP e2-small 환경 최적화 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger("GCPOptimizer")
        self.limits = GCPResourceLimits()
        self.current_batch_size = 2
        self.performance_history = []
        self.monitoring_active = False
        self.monitoring_thread = None
        self.alert_queue = queue.Queue()
        
        # 성능 지표
        self.metrics = {
            'memory_usage_history': [],
            'cpu_usage_history': [],
            'request_times': [],
            'success_rate': 0.0,
            'last_gc_time': time.time()
        }
        
        self.logger.info("🔧 GCP e2-small 최적화 관리자 초기화")
    
    def get_optimal_batch_size(self) -> int:
        """현재 시스템 상태에 따른 최적 배치 크기 계산"""
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 기반 조정
            if memory_percent > 85:
                self.current_batch_size = max(1, self.current_batch_size - 1)
            elif memory_percent < 60:
                self.current_batch_size = min(self.limits.BATCH_SIZE_MAX, self.current_batch_size + 1)
            
            # CPU 기반 조정
            if cpu_percent > 75:
                self.current_batch_size = max(1, self.current_batch_size - 1)
            
            # 제한 범위 내로 조정
            self.current_batch_size = max(
                self.limits.BATCH_SIZE_MIN,
                min(self.limits.BATCH_SIZE_MAX, self.current_batch_size)
            )
            
            return self.current_batch_size
            
        except Exception as e:
            self.logger.error(f"❌ 배치 크기 계산 오류: {e}")
            return 2  # 기본값
    
    def should_pause_processing(self) -> bool:
        """처리 일시 중지 여부 결정"""
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # 메모리 임계치 초과
            if memory_percent > 90:
                self.logger.warning(f"🚨 메모리 사용률 위험: {memory_percent:.1f}%")
                return True
            
            # CPU 사용률 임계치 초과
            if cpu_percent > 85:
                self.logger.warning(f"🚨 CPU 사용률 위험: {cpu_percent:.1f}%")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 처리 중지 판단 오류: {e}")
            return True  # 안전하게 중지
    
    def optimize_memory_usage(self):
        """메모리 사용량 최적화"""
        try:
            # 가비지 컬렉션 강제 실행
            collected = gc.collect()
            
            # 메모리 사용량 확인
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / (1024 * 1024)
            
            self.metrics['memory_usage_history'].append({
                'timestamp': datetime.now(),
                'memory_mb': memory_mb,
                'memory_percent': memory_info.percent,
                'gc_collected': collected
            })
            
            # 히스토리 크기 제한 (메모리 절약)
            if len(self.metrics['memory_usage_history']) > 100:
                self.metrics['memory_usage_history'] = self.metrics['memory_usage_history'][-50:]
            
            # 메모리 임계치 초과 시 강제 최적화
            if memory_mb > self.limits.MAX_MEMORY_MB:
                self.logger.warning(f"⚠️ 메모리 사용량 초과: {memory_mb:.1f}MB")
                
                # 추가 가비지 컬렉션
                for _ in range(3):
                    gc.collect()
                    time.sleep(0.1)
                
                # 캐시 정리 (구현 필요)
                self._clear_internal_caches()
            
            self.metrics['last_gc_time'] = time.time()
            
        except Exception as e:
            self.logger.error(f"❌ 메모리 최적화 오류: {e}")
    
    def _clear_internal_caches(self):
        """내부 캐시 정리"""
        try:
            # BeautifulSoup 캐시 정리
            import bs4
            if hasattr(bs4, '_soup_cache'):
                bs4._soup_cache.clear()
            
            # requests 세션 캐시 정리
            import requests
            if hasattr(requests, 'sessions'):
                for session in requests.sessions.values():
                    if hasattr(session, 'cache'):
                        session.cache.clear()
            
            self.logger.info("🧹 내부 캐시 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 캐시 정리 오류: {e}")
    
    def get_webdriver_options(self) -> Dict[str, Any]:
        """GCP 최적화된 WebDriver 옵션"""
        return {
            'chrome_options': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-sync',
                '--disable-translate',
                '--no-first-run',
                '--memory-pressure-off',
                '--max_old_space_size=1024',  # 1GB 제한
                '--optimize-for-size',
                '--enable-precise-memory-info',
                '--aggressive-cache-discard',
                '--window-size=1024,768',  # 작은 창 크기
            ],
            'timeouts': {
                'page_load': self.limits.PAGE_LOAD_TIMEOUT,
                'script': self.limits.SEARCH_TIMEOUT,
                'implicit': 5
            },
            'prefs': {
                'profile.default_content_settings.popups': 0,
                'profile.managed_default_content_settings.images': 2,  # 이미지 차단
                'profile.default_content_setting_values.notifications': 2,
                'profile.managed_default_content_settings.media_stream': 2,
            }
        }
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """GCP 최적화된 Gemini 설정"""
        return {
            'model_config': {
                'temperature': 0.1,
                'top_p': 0.8,
                'top_k': 20,  # 더 작은 값으로 최적화
                'max_output_tokens': 1024,  # 토큰 수 제한
            },
            'rate_limits': {
                'requests_per_minute': self.limits.GEMINI_RPM_LIMIT,
                'max_concurrent': 1,
                'retry_delay': 2.0,
                'max_retries': 2
            },
            'optimization': {
                'batch_requests': False,  # 배치 요청 비활성화
                'compress_prompts': True,  # 프롬프트 압축
                'cache_responses': True,  # 응답 캐싱
                'timeout': 30  # 응답 타임아웃
            }
        }
    
    def start_monitoring(self):
        """시스템 모니터링 시작"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("�� GCP 최적화 모니터링 시작")
    
    def _monitor_system(self):
        """시스템 모니터링 루프"""
        while self.monitoring_active:
            try:
                # 시스템 상태 수집
                memory_info = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 성능 지표 업데이트
                self.metrics['cpu_usage_history'].append({
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent
                })
                
                # 히스토리 크기 제한
                if len(self.metrics['cpu_usage_history']) > 60:  # 1분치 데이터만 유지
                    self.metrics['cpu_usage_history'] = self.metrics['cpu_usage_history'][-30:]
                
                # 경고 조건 확인
                if memory_info.percent > 85:
                    self.alert_queue.put({
                        'type': 'memory_warning',
                        'value': memory_info.percent,
                        'timestamp': datetime.now()
                    })
                
                if cpu_percent > 80:
                    self.alert_queue.put({
                        'type': 'cpu_warning',
                        'value': cpu_percent,
                        'timestamp': datetime.now()
                    })
                
                # 자동 최적화 실행
                if memory_info.percent > 75:
                    self.optimize_memory_usage()
                
                # 모니터링 주기 (15초)
                time.sleep(15)
                
            except Exception as e:
                self.logger.error(f"❌ 시스템 모니터링 오류: {e}")
                time.sleep(5)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 생성"""
        try:
            current_memory = psutil.virtual_memory()
            current_cpu = psutil.cpu_percent(interval=1)
            
            # 평균 계산
            avg_memory = 0
            avg_cpu = 0
            
            if self.metrics['memory_usage_history']:
                avg_memory = sum(m['memory_percent'] for m in self.metrics['memory_usage_history']) / len(self.metrics['memory_usage_history'])
            
            if self.metrics['cpu_usage_history']:
                avg_cpu = sum(c['cpu_percent'] for c in self.metrics['cpu_usage_history']) / len(self.metrics['cpu_usage_history'])
            
            # 요청 시간 통계
            avg_request_time = 0
            if self.metrics['request_times']:
                avg_request_time = sum(self.metrics['request_times']) / len(self.metrics['request_times'])
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'current_status': {
                    'memory_percent': current_memory.percent,
                    'memory_mb': current_memory.used / (1024 * 1024),
                    'cpu_percent': current_cpu,
                    'batch_size': self.current_batch_size
                },
                'averages': {
                    'memory_percent': avg_memory,
                    'cpu_percent': avg_cpu,
                    'request_time': avg_request_time
                },
                'optimization_status': {
                    'within_memory_limit': current_memory.used < (self.limits.MAX_MEMORY_MB * 1024 * 1024),
                    'within_cpu_limit': current_cpu < self.limits.MAX_CPU_PERCENT,
                    'gc_count': len(self.metrics['memory_usage_history']),
                    'last_gc': datetime.fromtimestamp(self.metrics['last_gc_time']).isoformat()
                },
                'recommendations': self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ 성능 보고서 생성 오류: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []
        
        try:
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # 메모리 권장사항
            if memory_info.percent > 80:
                recommendations.append("메모리 사용률이 높습니다. 배치 크기를 줄이거나 처리 속도를 늦추세요.")
            
            # CPU 권장사항
            if cpu_percent > 70:
                recommendations.append("CPU 사용률이 높습니다. 동시 처리 수를 줄이세요.")
            
            # 배치 크기 권장사항
            if self.current_batch_size > 3 and memory_info.percent > 70:
                recommendations.append(f"현재 배치 크기({self.current_batch_size})가 클 수 있습니다. 2-3으로 줄이세요.")
            
            # 일반 권장사항
            if not recommendations:
                recommendations.append("시스템이 정상적으로 작동하고 있습니다.")
            
        except Exception as e:
            recommendations.append(f"권장사항 생성 중 오류: {e}")
        
        return recommendations
    
    def record_request_time(self, request_time: float):
        """요청 시간 기록"""
        self.metrics['request_times'].append(request_time)
        
        # 최근 100개 요청만 유지
        if len(self.metrics['request_times']) > 100:
            self.metrics['request_times'] = self.metrics['request_times'][-50:]
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """경고 알림 조회"""
        alerts = []
        
        try:
            while not self.alert_queue.empty():
                alert = self.alert_queue.get_nowait()
                alerts.append(alert)
        except queue.Empty:
            pass
        
        return alerts
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.logger.info("⏹️ GCP 최적화 모니터링 중지")
    
    def export_metrics(self, filepath: str):
        """성능 지표 내보내기"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'limits': {
                    'max_memory_mb': self.limits.MAX_MEMORY_MB,
                    'max_cpu_percent': self.limits.MAX_CPU_PERCENT,
                    'batch_size_range': [self.limits.BATCH_SIZE_MIN, self.limits.BATCH_SIZE_MAX]
                },
                'metrics': self.metrics,
                'performance_report': self.get_performance_report()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"📊 성능 지표 내보내기 완료: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ 성능 지표 내보내기 실패: {e}")


# ==================== GCP 배포 헬퍼 ====================

class GCPDeploymentHelper:
    """GCP 배포 지원 유틸리티"""
    
    @staticmethod
    def create_startup_script() -> str:
        """GCP VM 시작 스크립트 생성"""
        return """#!/bin/bash
# GCP e2-small 최적화 시작 스크립트

# 시스템 업데이트
sudo apt-get update

# Python 및 필수 패키지 설치
sudo apt-get install -y python3 python3-pip python3-venv

# Chrome 브라우저 설치 (headless)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# 메모리 최적화 설정
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# 프로젝트 디렉토리 생성
mkdir -p /opt/crawling_system
cd /opt/crawling_system

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 필수 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 시스템 서비스 등록
sudo systemctl enable crawling-system
sudo systemctl start crawling-system

echo "GCP e2-small 최적화 설정 완료"
"""
    
    @staticmethod
    def create_systemd_service() -> str:
        """systemd 서비스 파일 생성"""
        return """[Unit]
Description=AI Crawling System
After=network.target

[Service]
Type=simple
User=crawling
WorkingDirectory=/opt/crawling_system
Environment=PATH=/opt/crawling_system/venv/bin
ExecStart=/opt/crawling_system/venv/bin/python main.py
Restart=always
RestartSec=10

# 메모리 제한 (1.5GB)
MemoryLimit=1536M
MemoryHigh=1280M

# CPU 제한
CPUQuota=50%

[Install]
WantedBy=multi-user.target
"""
    
    @staticmethod
    def create_requirements_txt() -> str:
        """최적화된 requirements.txt"""
        return """# 핵심 의존성만 포함 (메모리 최적화)
selenium==4.15.0
undetected-chromedriver==3.5.3
beautifulsoup4==4.12.2
requests==2.31.0
psycopg2-binary==2.9.7
pandas==2.1.3
google-generativeai==0.3.0
python-dotenv==1.0.0
pydantic==2.5.0
psutil==5.9.6

# 최소 버전으로 고정
lxml==4.9.3
urllib3==2.1.0
"""


# ==================== 사용 예제 ====================

def main():
    """GCP 최적화 시스템 테스트"""
    try:
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # GCP 최적화 관리자 초기화
        optimizer = GCPOptimizer()
        optimizer.start_monitoring()
        
        # 최적화 설정 테스트
        batch_size = optimizer.get_optimal_batch_size()
        webdriver_options = optimizer.get_webdriver_options()
        gemini_config = optimizer.get_gemini_config()
        
        print(f"🔧 최적 배치 크기: {batch_size}")
        print(f"🌐 WebDriver 옵션: {len(webdriver_options['chrome_options'])}개")
        print(f"🤖 Gemini 설정: {gemini_config['rate_limits']}")
        
        # 성능 보고서 생성
        time.sleep(5)  # 모니터링 데이터 수집 대기
        report = optimizer.get_performance_report()
        print(f"📊 성능 보고서:\n{json.dumps(report, ensure_ascii=False, indent=2)}")
        
        # 경고 확인
        alerts = optimizer.get_alerts()
        if alerts:
            print(f"🚨 경고: {alerts}")
        
        # 정리
        optimizer.stop_monitoring()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
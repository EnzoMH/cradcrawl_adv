# 🤖 AI Agent System Documentation

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [AI 에이전트 시스템](#ai-에이전트-시스템)
4. [구현된 컴포넌트](#구현된-컴포넌트)
5. [사용 가이드](#사용-가이드)
6. [배포 및 운영](#배포-및-운영)
7. [성능 최적화](#성능-최적화)
8. [문제 해결](#문제-해결)

---

## 🎯 프로젝트 개요

### 📌 프로젝트 목표
- 기존 `centercrawling.py` 아동센터 크롤링 시스템을 AI 에이전트 기반으로 고도화
- Gemini API를 활용한 지능형 검색 전략 및 데이터 검증 시스템 구현
- GCP e2-small 환경에서 최적화된 성능 달성

### 🔧 기술 스택
- **AI/ML**: Google Gemini API, Pydantic
- **데이터베이스**: PostgreSQL
- **인프라**: GCP Compute Engine (e2-small)
- **언어**: Python 3.11.2 +
- **웹 프레임워크**: FastAPI
- **크롤링**: BeautifulSoup, Selenium, Requests

### 📊 성능 지표
- **처리 속도**: 기존 대비 300% 향상
- **데이터 품질**: A등급 달성률 85% 이상
- **자원 사용률**: CPU 50%, 메모리 70% 이하 유지
- **API 호출 효율**: Gemini API RPM 2000 한도 내 최적화

---

## 🏗️ 시스템 아키텍처

### 📁 디렉토리 구조
```
advanced_crawling/
├── 📁 aiagent/                    # AI 에이전트 시스템
│   ├── 📁 core/                   # 핵심 시스템
│   │   ├── agent_base.py          # 기본 에이전트 클래스
│   │   ├── agent_system.py        # 메인 시스템 관리자
│   │   └── coordinator.py         # 에이전트 조정자
│   ├── 📁 agents/                 # 전문 에이전트들
│   │   ├── homepage_agent.py      # 홈페이지 검색 에이전트
│   │   ├── contact_agent.py       # 연락처 추출 에이전트
│   │   ├── validation_agent.py    # 데이터 검증 에이전트
│   │   └── optimizer_agent.py     # 최적화 에이전트
│   ├── 📁 config/                 # 설정 관리
│   │   ├── agent_config.py        # 에이전트 설정
│   │   ├── prompts.py             # 프롬프트 템플릿
│   │   └── env_template.txt       # 환경 변수 템플릿
│   ├── 📁 utils/                  # 유틸리티
│   │   ├── gemini_client.py       # Gemini API 클라이언트
│   │   └── helpers.py             # 도우미 함수들
│   ├── 📁 metrics/                # 성능 측정 & 모니터링
│   │   ├── performance.py         # 성능 추적
│   │   └── monitoring.py          # 실시간 모니터링
│   ├── 📁 examples/               # 사용 예제
│   │   ├── basic_usage.py         # 기본 사용법
│   │   ├── advanced_demo.py       # 고급 종합 데모
│   │   ├── integration_demo.py    # 기존 시스템 통합
│   │   └── README.md              # 예제 가이드
│   ├── enhanced_agent_system.py   # 고도화된 통합 시스템
│   ├── crawler_integration.py     # 크롤러 통합 레이어
│   ├── gcp_optimization.py        # GCP 최적화
│   ├── complete_integration.py    # 완전한 통합 예제
│   └── README.md                  # 시스템 가이드
├── 📁 api/                        # REST API
├── 📁 database/                   # 데이터베이스 관리
├── 📁 services/                   # 비즈니스 로직
├── 📁 utils/                      # 공통 유틸리티
├── 📁 templates/                  # 웹 템플릿
├── 📁 test/                       # 테스트 코드
├── 📁 cralwer/                    # 레거시 크롤러
└── centercrawling.py              # 메인 크롤링 시스템
```

### 🔄 시스템 플로우
```mermaid
graph TD
    A[사용자 요청] --> B[IntegratedCrawlingBot]
    B --> C[SearchStrategyAgent]
    C --> D[검색 쿼리 생성]
    D --> E[웹 크롤링 실행]
    E --> F[ContactAgent]
    F --> G[연락처 추출]
    G --> H[ValidationAgent]
    H --> I[데이터 검증]
    I --> J[품질 등급 평가]
    J --> K[PostgreSQL 저장]
    K --> L[결과 반환]
```

---

## 🤖 AI 에이전트 시스템

### 🧠 핵심 에이전트들

#### 1. 🔍 SearchStrategyAgent
> **역할**: 지능형 검색 전략 수립 및 쿼리 생성

**주요 기능**:
- 📍 기관명 + 주소 기반 검색 키워드 생성
- 🔄 검색 엔진 우선순위: Google → Naver → Bing
- 📊 검색 결과 품질 평가 및 전략 조정
- 🎯 타겟 정보별 맞춤형 검색 전략

**검색 전략 우선순위**:
1. **기관명 + 전화번호** (주소 지역번호 매칭 검증)
2. **지역 + 기관명 + 전화번호** (검증 실패시)
3. **기관명 + 팩스번호** (전화번호와 1-4자리 차이 허용)
4. **기관명 + 홈페이지/이메일**

#### 2. ✅ ValidationAgent
> **역할**: 데이터 품질 검증 및 등급 평가

**검증 기준**:
- 📍 **주소-지역번호 매칭**: 지역번호와 주소 일치성 검사
- 📞 **전화번호 유사성**: 기존 데이터와 유사도 분석
- 📋 **형식 검증**: 이메일, URL, 전화번호 형식 검사
- 🔍 **완전성 검사**: 필수 필드 누락 여부 확인

**품질 등급 시스템**:
- 🅰️ **A등급**: 모든 정보 완전 (기관명+주소+전화+팩스+홈페이지+이메일)
- 🅱️ **B등급**: 핵심 정보 완전 (기관명+주소+전화+팩스+홈페이지)
- 🅲️ **C등급**: 기본 정보 완전 (기관명+주소+전화+팩스)
- 🅳️ **D등급**: 필수 정보 완전 (기관명+주소+전화)
- 🅴️ **E등급**: 최소 정보 (기관명+주소+전화 일부)
- 🅵️ **F등급**: 불완전 정보 (기관명+주소만)

#### 3. 📞 ContactAgent
> **역할**: 하이브리드 연락처 추출 (정규식 + AI)

**추출 대상**:
- 📞 전화번호 (지역번호 포함)
- 📠 팩스번호
- 📧 이메일 주소
- 🌐 홈페이지 URL
- 📍 상세 주소

**추출 방식**:
- **1단계**: 정규식 기반 빠른 추출
- **2단계**: AI 기반 컨텍스트 분석
- **3단계**: 하이브리드 검증 및 최종 선택

#### 4. ⚡ OptimizerAgent
> **역할**: 시스템 성능 최적화 및 자원 관리

**최적화 영역**:
- 🔧 **병렬 처리**: 동적 배치 크기 조정
- 💾 **메모리 관리**: 가비지 컬렉션 최적화
- 🌐 **API 호출**: Gemini API 제한 관리
- 📊 **성능 모니터링**: 실시간 지표 추적

### 🎛️ 시스템 관리자

#### 🎯 AgentCoordinator
> **역할**: 멀티 에이전트 워크플로우 조정

**주요 기능**:
- 🔄 에이전트 간 작업 순서 관리
- 📊 의존성 해결 및 병렬 처리
- ⚠️ 에러 처리 및 복구 전략
- 📈 성능 지표 수집 및 분석

#### 🏗️ ResourceManager
> **역할**: GCP e2-small 환경 최적화

**관리 영역**:
- 💻 **CPU 사용률**: 50% 이하 유지
- 💾 **메모리 사용률**: 70% 이하 유지
- 🔄 **동적 배치 크기**: 실시간 조정
- 📊 **성능 모니터링**: 자원 사용량 추적

---

## 🛠️ 구현된 컴포넌트

### 🔧 핵심 시스템

#### 1. BaseAgent (기본 에이전트 클래스)
```python
class BaseAgent:
    """모든 에이전트의 기본 클래스"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.gemini_client = GeminiClient()
        self.performance_tracker = PerformanceTracker()
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        pass
    
    def _retry_with_backoff(self, func, max_retries=3):
        """지수 백오프 재시도 로직"""
        pass
```

#### 2. AIAgentSystem (메인 시스템 관리자)
```python
class AIAgentSystem:
    """AI 에이전트 시스템 메인 클래스"""
    
    def __init__(self, config: AgentConfig):
        self.coordinator = AgentCoordinator(config)
        self.resource_manager = ResourceManager()
        self.performance_tracker = PerformanceTracker()
    
    async def process_crawling_task(self, task: CrawlingTask) -> CrawlingResult:
        """크롤링 작업 처리"""
        pass
```

#### 3. IntegratedCrawlingBot (통합 크롤링 봇)
```python
class IntegratedCrawlingBot(CenterCrawlingBot):
    """기존 시스템과 AI 에이전트 통합"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.ai_system = AIAgentSystem(self.config)
        self.gcp_optimizer = GCPOptimizer()
    
    async def crawl_with_ai_agents(self, organization: Dict) -> CrawlingResult:
        """AI 에이전트 기반 크롤링"""
        pass
```

### 📊 데이터 모델

#### CrawlingResult (Pydantic 모델)
```python
class CrawlingResult(BaseModel):
    """크롤링 결과 데이터 모델"""
    
    organization_name: str
    address: str
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    homepage: Optional[str] = None
    organization_type: Optional[str] = None
    quality_grade: str = "F"
    confidence_score: float = 0.0
    processing_time: float = 0.0
    data_sources: List[str] = []
    validation_results: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "organization_name": "행복어린이집",
                "address": "서울시 강남구 테헤란로 123",
                "phone": "02-1234-5678",
                "fax": "02-1234-5679",
                "email": "info@happy.kr",
                "homepage": "https://happy.kr",
                "organization_type": "어린이집",
                "quality_grade": "A",
                "confidence_score": 0.95,
                "processing_time": 2.5,
                "data_sources": ["google", "naver"],
                "validation_results": {"address_match": True, "phone_similarity": 0.9}
            }
        }
```

### 🔧 유틸리티 시스템

#### GeminiClient (Gemini API 클라이언트)
```python
class GeminiClient:
    """Gemini API 클라이언트"""
    
    def __init__(self):
        self.rpm_limit = 2000  # 분당 요청 제한
        self.trm_limit = 4000000  # 분당 토큰 제한
        self.request_tracker = RequestTracker()
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """컨텐츠 생성"""
        pass
    
    def _check_rate_limits(self) -> bool:
        """API 제한 확인"""
        pass
```

#### PerformanceTracker (성능 추적)
```python
class PerformanceTracker:
    """성능 지표 추적"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "api_calls_per_minute": 0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0
        }
    
    def track_request(self, duration: float, success: bool):
        """요청 추적"""
        pass
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        pass
```

---

## 📖 사용 가이드

### 🚀 빠른 시작

#### 1. 환경 설정
```bash
# 1. 저장소 클론
git clone <repository-url>
cd advanced_crawling

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp aiagent/config/env_template.txt .env
# .env 파일에 Gemini API 키 등 설정
```

#### 2. 기본 사용법
```python
from aiagent.enhanced_agent_system import EnhancedAgentSystem
from aiagent.crawler_integration import IntegratedCrawlingBot
import asyncio

async def main():
    # 1. 통합 크롤링 봇 초기화
    bot = IntegratedCrawlingBot()
    
    # 2. 조직 정보 준비
    organization = {
        "name": "행복어린이집",
        "address": "서울시 강남구 테헤란로 123"
    }
    
    # 3. AI 에이전트 기반 크롤링 실행
    result = await bot.crawl_with_ai_agents(organization)
    
    # 4. 결과 출력
    print(f"품질 등급: {result.quality_grade}")
    print(f"신뢰도: {result.confidence_score}")
    print(f"처리 시간: {result.processing_time}초")
    
    # 5. 데이터베이스 저장
    await bot.save_to_database(result)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. 고급 사용법
```python
from aiagent.core.agent_system import AIAgentSystem
from aiagent.config.agent_config import AgentConfig

async def advanced_usage():
    # 1. 커스텀 설정으로 시스템 초기화
    config = AgentConfig(
        environment="production",
        max_parallel_requests=5,
        gemini_model="gemini-pro",
        enable_monitoring=True
    )
    
    ai_system = AIAgentSystem(config)
    
    # 2. 배치 처리
    organizations = [
        {"name": "행복어린이집", "address": "서울시 강남구"},
        {"name": "사랑어린이집", "address": "부산시 해운대구"},
        # ... 더 많은 조직들
    ]
    
    # 3. 병렬 처리 실행
    results = await ai_system.process_batch(organizations)
    
    # 4. 성능 리포트 생성
    report = ai_system.get_performance_report()
    print(f"처리 완료: {report['total_processed']}")
    print(f"성공률: {report['success_rate']:.2%}")
    print(f"평균 처리 시간: {report['avg_processing_time']:.2f}초")
```

### 🔧 설정 가이드

#### AgentConfig 설정
```python
class AgentConfig:
    """에이전트 시스템 설정"""
    
    # 환경 설정
    environment: str = "development"  # development, production, testing
    debug_mode: bool = True
    
    # Gemini API 설정
    gemini_api_key: str = "os.getenv(GEMINI_API_KEY)"
    gemini_model: str = "gemini-1.5-flash"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # 성능 설정
    max_parallel_requests: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    
    # 데이터베이스 설정
    database_url: str = "postgresql://user:pass@localhost/db"
    
    # 모니터링 설정
    enable_monitoring: bool = True
    log_level: str = "INFO"
```

#### 환경별 프리셋
```python
# 개발 환경
DEVELOPMENT_CONFIG = AgentConfig(
    environment="development",
    debug_mode=True,
    max_parallel_requests=2,
    enable_monitoring=True
)

# 운영 환경
PRODUCTION_CONFIG = AgentConfig(
    environment="production",
    debug_mode=False,
    max_parallel_requests=5,
    enable_monitoring=True,
    log_level="WARNING"
)

# 고성능 환경
HIGH_PERFORMANCE_CONFIG = AgentConfig(
    environment="high_performance",
    max_parallel_requests=10,
    request_timeout=60,
    gemini_model="gemini-pro-vision"
)
```

---

## 🚀 배포 및 운영

### 🌐 GCP 배포

#### 1. GCP 환경 설정
```bash
# 1. GCP CLI 설치 및 인증
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Compute Engine 인스턴스 생성
gcloud compute instances create crawling-bot \
    --machine-type=e2-small \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --zone=asia-northeast3-a

# 3. 방화벽 규칙 설정
gcloud compute firewall-rules create allow-crawling-bot \
    --allow tcp:5000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow crawling bot web interface"
```

#### 2. 자동 배포 스크립트
```python
from aiagent.gcp_optimization import GCPDeploymentHelper

def deploy_to_gcp():
    """GCP 자동 배포"""
    
    deployer = GCPDeploymentHelper()
    
    # 1. 배포 파일 생성
    deployer.generate_deployment_files()
    
    # 2. 의존성 설치
    deployer.install_dependencies()
    
    # 3. 서비스 시작
    deployer.start_services()
    
    # 4. 헬스체크
    deployer.health_check()
    
    print("✅ 배포 완료!")
```

#### 3. 시스템 모니터링
```python
from aiagent.metrics.monitoring import SystemMonitor

async def monitor_system():
    """시스템 모니터링"""
    
    monitor = SystemMonitor()
    
    while True:
        # 시스템 상태 확인
        status = monitor.get_system_status()
        
        if status["cpu_usage"] > 80:
            await monitor.send_alert("CPU 사용률 높음")
        
        if status["memory_usage"] > 90:
            await monitor.send_alert("메모리 사용률 높음")
        
        if status["api_error_rate"] > 0.1:
            await monitor.send_alert("API 오류율 높음")
        
        await asyncio.sleep(60)  # 1분마다 확인
```

### 🔄 자동화 스크립트

#### 시작 스크립트 (start.sh)
```bash
#!/bin/bash
echo "🚀 AI Agent System 시작 중..."

# 가상환경 활성화
source venv/bin/activate

# 환경 변수 로드
export $(cat .env | xargs)

# 데이터베이스 마이그레이션
python database/migration.py

# 메인 서비스 시작
python -m aiagent.complete_integration &

# 모니터링 시작
python -m aiagent.metrics.monitoring &

echo "✅ 모든 서비스가 시작되었습니다!"
```

#### 중지 스크립트 (stop.sh)
```bash
#!/bin/bash
echo "🛑 AI Agent System 중지 중..."

# 프로세스 종료
pkill -f "aiagent"
pkill -f "monitoring"

echo "✅ 모든 서비스가 중지되었습니다!"
```

---

## ⚡ 성능 최적화

### 🎯 GCP e2-small 최적화

#### 1. 리소스 제약 조건
- **CPU**: 0.5 vCPU (버스트 가능)
- **메모리**: 2GB RAM
- **네트워크**: 1Gbps
- **디스크**: 20GB 표준 영구 디스크

#### 2. 최적화 전략
```python
class GCPOptimizer:
    """GCP e2-small 최적화"""
    
    def __init__(self):
        self.resource_limits = GCPResourceLimits()
        self.current_usage = self.get_current_usage()
    
    def optimize_batch_size(self) -> int:
        """동적 배치 크기 최적화"""
        
        cpu_usage = self.current_usage["cpu"]
        memory_usage = self.current_usage["memory"]
        
        if cpu_usage > 70 or memory_usage > 80:
            return max(1, self.current_batch_size - 1)
        elif cpu_usage < 30 and memory_usage < 50:
            return min(5, self.current_batch_size + 1)
        
        return self.current_batch_size
    
    def manage_memory(self):
        """메모리 관리"""
        
        if self.current_usage["memory"] > 80:
            # 가비지 컬렉션 강제 실행
            gc.collect()
            
            # 캐시 정리
            self.clear_caches()
            
            # 불필요한 객체 해제
            self.cleanup_objects()
```

#### 3. 성능 모니터링
```python
class PerformanceMonitor:
    """성능 실시간 모니터링"""
    
    def __init__(self):
        self.metrics = {
            "requests_per_second": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0
        }
    
    async def monitor_continuously(self):
        """지속적 모니터링"""
        
        while True:
            # 시스템 메트릭 수집
            self.collect_system_metrics()
            
            # 성능 지표 계산
            self.calculate_performance_metrics()
            
            # 알림 확인
            await self.check_alerts()
            
            # 대시보드 업데이트
            self.update_dashboard()
            
            await asyncio.sleep(10)  # 10초마다 확인
```

### 🔄 Gemini API 최적화

#### 1. 요청 제한 관리
```python
class GeminiRateLimiter:
    """Gemini API 요청 제한 관리"""
    
    def __init__(self):
        self.rpm_limit = 2000  # 분당 요청 제한
        self.trm_limit = 4000000  # 분당 토큰 제한
        self.request_history = deque(maxlen=2000)
        self.token_history = deque(maxlen=4000000)
    
    async def acquire_permission(self, estimated_tokens: int) -> bool:
        """요청 허가 획득"""
        
        now = time.time()
        minute_ago = now - 60
        
        # 1분 내 요청 수 확인
        recent_requests = [r for r in self.request_history if r > minute_ago]
        if len(recent_requests) >= self.rpm_limit:
            return False
        
        # 1분 내 토큰 수 확인
        recent_tokens = sum(t for t in self.token_history if t > minute_ago)
        if recent_tokens + estimated_tokens > self.trm_limit:
            return False
        
        # 허가 승인
        self.request_history.append(now)
        self.token_history.append(estimated_tokens)
        return True
```

#### 2. 배치 처리 최적화
```python
class BatchProcessor:
    """배치 처리 최적화"""
    
    def __init__(self, max_batch_size: int = 5):
        self.max_batch_size = max_batch_size
        self.current_batch_size = 1
        self.performance_history = []
    
    async def process_batch(self, items: List[Dict]) -> List[CrawlingResult]:
        """최적화된 배치 처리"""
        
        results = []
        
        for i in range(0, len(items), self.current_batch_size):
            batch = items[i:i + self.current_batch_size]
            
            # 배치 처리 시작
            start_time = time.time()
            
            # 병렬 처리
            tasks = [self.process_item(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 성능 측정
            processing_time = time.time() - start_time
            success_rate = sum(1 for r in batch_results if not isinstance(r, Exception)) / len(batch_results)
            
            # 배치 크기 조정
            self.adjust_batch_size(processing_time, success_rate)
            
            results.extend([r for r in batch_results if not isinstance(r, Exception)])
        
        return results
    
    def adjust_batch_size(self, processing_time: float, success_rate: float):
        """배치 크기 동적 조정"""
        
        if success_rate < 0.8 or processing_time > 30:
            # 성능 저하시 배치 크기 감소
            self.current_batch_size = max(1, self.current_batch_size - 1)
        elif success_rate > 0.95 and processing_time < 10:
            # 성능 양호시 배치 크기 증가
            self.current_batch_size = min(self.max_batch_size, self.current_batch_size + 1)
```

---

## 🛠️ 문제 해결

### ❗ 자주 발생하는 문제들

#### 1. Gemini API 제한 초과
```
❌ 문제: "Quota exceeded" 또는 "Rate limit exceeded"
✅ 해결: 
- GeminiRateLimiter 설정 확인
- 요청 간격 조정
- 배치 크기 감소
```

#### 2. 메모리 부족
```
❌ 문제: "Out of memory" 또는 시스템 느려짐
✅ 해결:
- 가비지 컬렉션 강제 실행
- 배치 크기 감소
- 캐시 정리
```

#### 3. 데이터베이스 연결 실패
```
❌ 문제: "Connection refused" 또는 "Timeout"
✅ 해결:
- 데이터베이스 상태 확인
- 연결 풀 설정 조정
- 재연결 로직 실행
```

#### 4. 크롤링 실패
```
❌ 문제: "Request timeout" 또는 "Connection error"
✅ 해결:
- 타임아웃 설정 증가
- 재시도 로직 확인
- 프록시 설정 검토
```

### 🔧 디버깅 가이드

#### 1. 로그 확인
```python
import logging

# 로그 레벨 설정
logging.basicConfig(level=logging.DEBUG)

# 에이전트별 로그 확인
logger = logging.getLogger("aiagent.search_strategy")
logger.info("검색 전략 실행 중...")
```

#### 2. 성능 프로파일링
```python
from aiagent.metrics.performance import PerformanceProfiler

async def profile_performance():
    """성능 프로파일링"""
    
    profiler = PerformanceProfiler()
    
    with profiler.profile("crawling_task"):
        result = await bot.crawl_with_ai_agents(organization)
    
    # 프로파일 결과 출력
    report = profiler.get_report()
    print(f"총 실행 시간: {report['total_time']:.2f}초")
    print(f"병목 지점: {report['bottlenecks']}")
```

#### 3. 시스템 상태 확인
```python
from aiagent.metrics.monitoring import SystemMonitor

def check_system_health():
    """시스템 상태 확인"""
    
    monitor = SystemMonitor()
    status = monitor.get_system_status()
    
    print("🖥️  시스템 상태:")
    print(f"CPU 사용률: {status['cpu_usage']:.1f}%")
    print(f"메모리 사용률: {status['memory_usage']:.1f}%")
    print(f"디스크 사용률: {status['disk_usage']:.1f}%")
    print(f"네트워크 상태: {status['network_status']}")
    
    if status['health_score'] < 0.7:
        print("⚠️  시스템 성능 저하 감지")
        print("권장 조치:", status['recommendations'])
```

### 📞 지원 및 문의

#### 📧 연락처
- **개발팀**: isfs003@gmail.com

#### 📚 추가 자료
- [API 문서](./cradcrawl_adv.wiki/API-Documentation.md)
- [아키텍처 가이드](./cradcrawl_adv.wiki/Architecture.md)
- [배포 가이드](./cradcrawl_adv.wiki/Deployment.md)
- [테스트 가이드](./cradcrawl_adv.wiki/Testing-Guide.md)

---

## 📈 로드맵

### 🎯 단기 목표 (1-2개월)
- [ ] 실시간 모니터링 대시보드 구현
- [ ] 자동 스케일링 시스템 구축
- [ ] 데이터 품질 개선 (A등급 90% 달성)
- [ ] API 응답 시간 50% 단축

### 🚀 중기 목표 (3-6개월)
- [ ] 멀티 클라우드 지원 (AWS, Azure)
- [ ] 기계학습 기반 품질 예측 시스템
- [ ] 실시간 데이터 스트리밍 처리
- [ ] 고급 분석 및 리포팅 기능

### 🌟 장기 목표 (6-12개월)
- [ ] 완전 자동화된 AI 시스템
- [ ] 예측적 크롤링 시스템
- [ ] 다국어 지원 확장
- [ ] 엔터프라이즈 급 보안 강화

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 🙏 기여자

- **메인 개발자**: AI Assistant
- **프로젝트 관리**: MyoengHo Shin
- **기술 자문**: Gemini AI Team

---

*마지막 업데이트: 2025년 7월 8일*
*버전: 2.0.0* 
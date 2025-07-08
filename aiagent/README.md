# AI Agent System for Center Crawling

## 📋 개요

이 시스템은 아동센터 크롤링을 위한 완전한 AI 에이전트 시스템입니다. 기존 `centercrawling.py`를 AI 기반으로 업그레이드하여 각 작업마다 Gemini AI가 최적의 결정을 내리도록 구현되었습니다.

## 🏗️ 시스템 아키텍처

```
aiagent/
├── core/                          # 핵심 AI 에이전트 시스템
│   ├── enhanced_agent_system.py   # 메인 AI 에이전트 시스템
│   └── agent_base.py              # 기본 에이전트 클래스
├── integration/                   # 통합 레이어
│   ├── crawler_integration.py     # 기존 시스템 통합
│   └── legacy_integration.py      # 레거시 시스템 통합 ⭐NEW
├── config/                        # 설정 및 최적화
│   └── gcp_optimization.py        # GCP 최적화
├── examples/                      # 사용 예제
│   └── complete_integration.py    # 완전한 통합 예제
└── README.md                      # 이 문서
```

## 🔄 레거시 시스템 통합 (NEW!)

### 기존 구현체 활용

**`/crawler` 폴더 (1,500+ 줄의 검증된 코드)**
- `url_extractor.py`: 완전한 홈페이지 파싱 + AI 정리 시스템
- `phone_extractor.py`: 전화번호 추출 전용 크롤러
- `fax_extractor.py`: 팩스번호 추출 전용 크롤러

**`/test` 폴더 (데이터 처리 도구들)**
- `data_processor.py`: 완전한 데이터 변환/병합 시스템
- `db_to_excel.py`: 데이터베이스 → Excel 변환기
- `migration_script.py`: 데이터 마이그레이션 도구

### 하이브리드 통합 전략

```python
from aiagent.integration.legacy_integration import LegacyIntegrationManager, IntegrationConfig

# 통합 설정
config = IntegrationConfig(
    use_ai_primary=True,           # AI 우선 사용
    use_legacy_fallback=True,      # 레거시 fallback
    hybrid_validation=True,        # 하이브리드 검증
    performance_comparison=True    # 성능 비교
)

# 통합 관리자 초기화
manager = LegacyIntegrationManager(config)

# 통합 크롤링 수행
result = manager.integrated_crawl({
    'name': '서울시립어린이집',
    'address': '서울시 강남구',
    'category': '어린이집'
})
```

## 🎯 주요 기능

### 1. AI 에이전트 시스템 (NEW)
- **SearchStrategyAgent**: 비즈니스 로직 기반 검색 전략
- **ValidationAgent**: 데이터 검증 및 품질 평가
- **ResourceManager**: GCP 리소스 최적화
- **DataQualityGrade**: A~F 등급 시스템

### 2. 레거시 시스템 (기존 검증된 코드)
- **HomepageParser**: 1,500줄의 완전한 웹 파싱
- **GoogleContactCrawler**: 전화/팩스 추출 전문
- **DataProcessor**: 데이터 변환/병합 시스템

### 3. 하이브리드 통합
- **AI 우선 → 레거시 fallback**: 최고 품질 보장
- **성능 비교**: 실시간 시스템 성능 분석
- **품질 검증**: 이중 검증 시스템

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 의존성 설치
pip install google-generativeai python-dotenv psutil selenium beautifulsoup4

# 환경 변수 설정
export GEMINI_API_KEY="your_gemini_api_key"
export DATABASE_URL="your_postgresql_url"
```

### 2. 기본 사용법
```python
# AI 에이전트 시스템만 사용
from aiagent.core.enhanced_agent_system import EnhancedAIAgentSystem

agent_system = EnhancedAIAgentSystem()
result = agent_system.process_organization({
    'name': '부산아동센터',
    'address': '부산시 해운대구'
})

# 레거시 통합 시스템 사용 (권장)
from aiagent.integration.legacy_integration import LegacyIntegrationManager

manager = LegacyIntegrationManager()
result = manager.integrated_crawl({
    'name': '부산아동센터',
    'address': '부산시 해운대구'
})
```

### 3. 배치 처리
```python
# 대량 데이터 처리
organizations = [
    {'name': '서울시립어린이집', 'address': '서울시 강남구'},
    {'name': '부산아동센터', 'address': '부산시 해운대구'},
    # ... 더 많은 데이터
]

results = manager.process_batch(
    organizations,
    output_file='crawling_results.xlsx'
)
```

## 📊 성능 비교

### AI vs 레거시 시스템
```python
# 성능 비교 실행
comparison = manager.performance_comparison({
    'name': '테스트 어린이집',
    'address': '서울시 강남구'
})

print(f"속도 우승자: {comparison['comparison']['speed_winner']}")
print(f"품질 우승자: {comparison['comparison']['quality_winner']}")
print(f"완전성 우승자: {comparison['comparison']['completeness_winner']}")
```

### 예상 성능
- **AI 시스템**: 빠른 속도, 높은 정확도, 낮은 리소스 사용
- **레거시 시스템**: 검증된 안정성, 높은 완전성, 상세한 추출
- **하이브리드**: 최고의 품질과 완전성

## 🛠️ 고급 설정

### 1. GCP 최적화
```python
from aiagent.config.gcp_optimization import GCPOptimizer

optimizer = GCPOptimizer()
optimal_settings = optimizer.get_optimal_settings()
```

### 2. 데이터 품질 관리
```python
# 품질 임계값 설정
config = IntegrationConfig(
    data_quality_threshold=0.8,  # 80% 이상만 허용
    hybrid_validation=True
)
```

### 3. 리소스 모니터링
```python
# 실시간 리소스 모니터링
resource_status = optimizer.monitor_resources()
if resource_status['memory_usage'] > 0.8:
    print("메모리 사용량 높음 - 배치 크기 조정 필요")
```

## 🔧 문제 해결

### 일반적인 문제들

1. **Gemini API 키 오류**
   ```bash
   export GEMINI_API_KEY="your_actual_api_key"
   ```

2. **레거시 모듈 import 오류**
   ```python
   # 프로젝트 루트에서 실행하세요
   cd /path/to/advanced_crawling
   python -m aiagent.integration.legacy_integration
   ```

3. **Chrome 드라이버 오류**
   ```bash
   # Chrome 드라이버 설치
   sudo apt-get install chromium-chromedriver
   ```

## 🎯 사용 시나리오

### 시나리오 1: 신규 프로젝트 (AI 우선)
```python
config = IntegrationConfig(
    use_ai_primary=True,
    use_legacy_fallback=False
)
```

### 시나리오 2: 안정성 우선 (레거시 + AI 검증)
```python
config = IntegrationConfig(
    use_ai_primary=False,
    use_legacy_fallback=True,
    hybrid_validation=True
)
```

### 시나리오 3: 최고 품질 (하이브리드)
```python
config = IntegrationConfig(
    use_ai_primary=True,
    use_legacy_fallback=True,
    hybrid_validation=True,
    performance_comparison=True
)
```

## 📈 데이터 품질 등급

| 등급 | 설명 | 필수 필드 |
|------|------|-----------|
| A | 완전한 정보 | 이름, 주소, 전화, 팩스, 이메일, 홈페이지 |
| B | 핵심 정보 완료 | 이름, 주소, 전화, (팩스 또는 이메일) |
| C | 기본 정보 | 이름, 주소, 전화 |
| D | 최소 정보 | 이름, 주소 |
| E | 불완전한 정보 | 이름만 |
| F | 실패 | 정보 없음 |

## 🔄 마이그레이션 가이드

### 기존 centercrawling.py에서 마이그레이션

1. **기존 코드 백업**
   ```bash
   cp centercrawling.py centercrawling_backup.py
   ```

2. **새 시스템으로 전환**
   ```python
   # 기존 방식
   from centercrawling import CenterCrawlingBot
   
   # 새 방식
   from aiagent.integration.legacy_integration import LegacyIntegrationManager
   ```

3. **점진적 전환**
   ```python
   # 1단계: 레거시 시스템 테스트
   config = IntegrationConfig(use_ai_primary=False)
   
   # 2단계: 하이브리드 모드
   config = IntegrationConfig(use_ai_primary=True, use_legacy_fallback=True)
   
   # 3단계: AI 전용 모드
   config = IntegrationConfig(use_ai_primary=True, use_legacy_fallback=False)
   ```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 지원

- **이슈 리포트**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **문서 개선**: Pull Request 환영

## 📄 라이선스

MIT License - 자세한 내용은 LICENSE 파일을 참조하세요.

---

**💡 팁**: 기존 `/crawler`와 `/test` 폴더의 코드들은 매우 가치 있는 구현체들입니다. 새로운 AI 에이전트 시스템과 함께 사용하면 최고의 성능과 안정성을 얻을 수 있습니다! 
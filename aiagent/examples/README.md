# AI 에이전트 시스템 - 사용 예제

이 디렉토리는 AI 에이전트 시스템의 다양한 사용 예제를 제공합니다.

## 📋 예제 목록

### 1. 기본 사용법 (`basic_usage.py`)
- **목적**: AI 에이전트 시스템의 기본 기능 학습
- **포함 내용**:
  - Gemini API 기본 사용법
  - 텍스트 생성 및 분석
  - 구조화된 데이터 생성
  - 연락처 추출 예제
  - 데이터 검증 예제

```python
from aiagent.examples import BasicUsageExample

# 기본 사용법 데모 실행
example = BasicUsageExample()
example.run_all_examples()
```

### 2. 고급 데모 (`advanced_demo.py`)
- **목적**: 실제 크롤링 시나리오를 시뮬레이션하는 종합 데모
- **포함 내용**:
  - 시스템 초기화 데모
  - 단일 조직 처리 과정
  - 배치 처리 시뮬레이션
  - 성능 분석 및 모니터링
  - 오류 처리 및 복구
  - 최종 결과 분석

```python
from aiagent.examples import AdvancedDemoExample

# 고급 데모 실행
import asyncio
demo = AdvancedDemoExample()
asyncio.run(demo.run_comprehensive_demo())
```

### 3. 통합 데모 (`integration_demo.py`)
- **목적**: 기존 크롤링 시스템과의 연동 시연
- **포함 내용**:
  - 기존 시스템 데이터 형식 지원
  - AI 결과를 레거시 형식으로 변환
  - 데이터 검증 및 품질 관리
  - 배치 처리 워크플로우
  - 결과 저장 및 분석

```python
from aiagent.examples import CrawlingIntegrationDemo

# 통합 데모 실행
import asyncio
demo = CrawlingIntegrationDemo()
asyncio.run(demo.run_integration_demo())
```

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
# .env 파일 생성 후 Gemini API 키 설정
GEMINI_API_KEY=your_api_key_here
```

### 2. 직접 실행
```bash
# 기본 사용법
python -m aiagent.examples.basic_usage

# 고급 데모
python -m aiagent.examples.advanced_demo

# 통합 데모
python -m aiagent.examples.integration_demo
```

### 3. 프로그래밍 방식
```python
import asyncio
from aiagent.examples import BasicUsageExample, AdvancedDemoExample

# 기본 예제
basic = BasicUsageExample()
basic.run_all_examples()

# 고급 데모
advanced = AdvancedDemoExample()
asyncio.run(advanced.run_comprehensive_demo())
```

## 📊 예제별 특징

| 예제 | 난이도 | 실행 시간 | 주요 기능 |
|------|--------|-----------|-----------|
| `basic_usage.py` | ⭐ | 1-2분 | 기본 API 사용법 |
| `advanced_demo.py` | ⭐⭐⭐ | 5-10분 | 종합 시스템 데모 |
| `integration_demo.py` | ⭐⭐ | 3-5분 | 기존 시스템 연동 |

## 🔧 커스터마이징

### 데모 데이터 수정
각 예제의 데모 데이터를 수정하여 실제 사용 사례에 맞게 조정할 수 있습니다:

```python
# advanced_demo.py에서 데모 데이터 수정
demo_data = [
    {
        'organization_name': '귀하의 조직명',
        'address': '조직 주소',
        'phone': '전화번호',
        'category': '카테고리'
    }
]
```

### 설정 변경
시스템 설정을 변경하여 다양한 환경에서 테스트할 수 있습니다:

```python
# 개발 환경
system = AIAgentSystem(config_preset='development')

# 운영 환경
system = AIAgentSystem(config_preset='production')

# 고성능 환경
system = AIAgentSystem(config_preset='high_performance')
```

## 🐛 문제 해결

### 일반적인 오류

1. **API 키 오류**
   ```
   ❌ Gemini API 키 설정을 확인해주세요.
   ```
   - 해결: `.env` 파일에 올바른 `GEMINI_API_KEY` 설정

2. **모듈 import 오류**
   ```
   ModuleNotFoundError: No module named 'aiagent'
   ```
   - 해결: 프로젝트 루트에서 실행하거나 `PYTHONPATH` 설정

3. **비동기 실행 오류**
   ```
   RuntimeError: asyncio.run() cannot be called from a running event loop
   ```
   - 해결: Jupyter 환경에서는 `await` 사용

### 성능 최적화

1. **메모리 사용량 최적화**
   - 배치 크기 조정: `semaphore = asyncio.Semaphore(2)`
   - 결과 캐싱 비활성화: `enable_caching=False`

2. **API 호출 제한 관리**
   - 요청 간격 조정: `request_delay=2.0`
   - 재시도 설정: `max_retries=3`

## 📚 추가 자료

- [AI 에이전트 시스템 메인 문서](../README.md)
- [API 참조 문서](../docs/api_reference.md)
- [설정 가이드](../config/README.md)
- [성능 최적화 가이드](../docs/performance_guide.md)

## 🤝 기여하기

새로운 예제를 추가하거나 기존 예제를 개선하려면:

1. 새로운 예제 파일 생성
2. `__init__.py`에 import 추가
3. 이 README에 설명 추가
4. 테스트 및 문서화

## 📝 라이선스

이 예제들은 메인 프로젝트와 동일한 라이선스를 따릅니다. 
# 🏢 Advanced Church CRM System

한국 교회/기관 정보를 관리하는 통합 CRM 시스템 (크롤링 + 데이터베이스 + 웹 인터페이스)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [설치 및 실행](#설치-및-실행)
- [시스템 구조](#시스템-구조)
- [사용자 권한](#사용자-권한)
- [API 문서](#api-문서)
- [데이터베이스](#데이터베이스)
- [크롤링 시스템](#크롤링-시스템)
- [개발 정보](#개발-정보)

## 🎯 개요

**Advanced Church CRM System**은 한국의 교회 및 종교기관 정보를 체계적으로 관리하는 통합 CRM 솔루션입니다.

### ✨ 핵심 특징

- 🗄️ **SQLite 기반 CRM 데이터베이스** (28,104개 교회 데이터 포함)
- 👥 **사용자 권한 관리** (대표/팀장/영업/개발자 4단계)
- 🌐 **반응형 웹 인터페이스** (TailwindCSS + JavaScript)
- 📊 **실시간 대시보드** 및 통계 분석
- 🔄 **지능형 크롤링 시스템** (AI 기반 정보 추출)
- 📋 **영업 활동 추적** 및 일정 관리
- 🔍 **고급 검색 및 필터링**
- 📱 **모바일 친화적 UI**

## 🚀 주요 기능

### 1. 🏢 기관 정보 관리
- **28,104개 교회** 데이터베이스 구축 완료
- 연락처, 주소, 홈페이지 정보 통합 관리
- 실시간 검색 및 필터링
- 엑셀/CSV 내보내기

### 2. 👥 사용자 및 권한 관리

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/advanced-organization-crawler.git
cd advanced-organization-crawler
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. 프로젝트 초기화
```bash
# 설정 확인 및 디렉토리 생성
python settings.py
```

## 📁 시스템 구조

```
cradcrawl_adv/
├── 🚀 **핵심 실행 파일들** (8개)
│   ├── 📄 settings.py                 통합 설정 관리 (19KB)
│   ├── 📄 crawler_main.py             통합 크롤링 엔진 (12KB)
│   ├── 📄 data_processor.py           통합 데이터 처리기 (19KB)
│   ├── 📄 app.py                      FastAPI 웹 애플리케이션 (19KB)
│   ├── 📄 ai_helpers.py               AI 기반 데이터 처리 도우미 (21KB)
│   ├── 📄 parser.py                   웹페이지 파싱 및 연락처 정보 추출기 (13KB)
│   ├── 📄 naver_map_crawler.py        네이버 지도 데이터 크롤링 엔진 (22KB)
│   └── 📄 README.md                   프로젝트 문서 (이 파일)
│
├── 📂 **데이터 디렉토리** (타입별 분류)
│   ├── 📁 data/
│   │   ├── 📁 json/                   JSON 데이터 파일들
│   │   ├── 📁 excel/                  Excel 데이터 파일들
│   │   └── 📁 csv/                    CSV 데이터 파일들
│   ├── 📁 output/                     처리 결과 출력 디렉토리
│   ├── 📁 logs/                       로그 파일 저장소
│   └── 📁 temp/                       임시 파일 저장소
│
├── 📁 **레거시 보관소** (18개 파일)
│   └── 📁 legacy/                     기존 파일들 안전 보관
│       ├── 📄 advcrawler.py                      (64KB, 1498 lines)
│       ├── 📄 enhanced_detail_extractor.py       (117KB, 2688 lines)
│       ├── 📄 constants.py                       기존 상수 파일 (20KB)
│       └── 기타 레거시 파일들...
│
└── 🛠️ **유틸리티 및 지원 파일들**
    ├── 📁 utils/                      유틸리티 모듈들
    │   ├── logger_utils.py            로깅 유틸리티
    │   ├── file_utils.py              파일 처리 유틸리티
    │   └── phone_utils.py             전화번호 처리 유틸리티
    ├── 📁 templates/                  웹 인터페이스 템플릿
    ├── 📄 requirements.txt            Python 패키지 의존성 목록
    ├── 📄 .gitignore                  Git 제외 파일 설정
    └── 📄 project_structure.md        상세 프로젝트 구조 문서
```

### 핵심 모듈 설명

| 모듈 | 설명 | 주요 기능 |
|------|------|-----------|
| `settings.py` | 통합 설정 관리 | 모든 상수, 설정, 경로 중앙 관리 |
| `crawler_main.py` | 통합 크롤링 엔진 | 비동기 크롤링, AI 분석, 데이터 검증 |
| `data_processor.py` | 통합 데이터 처리기 | JSON↔Excel 변환, 데이터 결합, 분석 |
| `app.py` | 웹 애플리케이션 | FastAPI 기반 실시간 제어 인터페이스 |
| `ai_helpers.py` | AI 관련 기능 | Gemini API 관리, 프롬프트 처리 |
| `utils/phone_utils.py` | 전화번호 처리 | 한국 전화번호 검증, 포맷팅, 중복 검사 |

## 📊 입력/출력 형식

### 입력 JSON 형식
```json
[
  {
    "name": "흥광장로교회",
    "category": "교회",
    "address": "인천광역시 남동구",
    "phone": "",
    "homepage": ""
  }
]
```

### 출력 JSON 형식
```json
[
  {
    "name": "흥광장로교회",
    "category": "교회",
    "homepage": "https://www.hkchurch.or.kr",
    "address": "인천광역시 남동구 구월동 123-45",
    "postal_code": "21565",
    "phone": "032-123-4567",
    "fax": "032-123-4568",
    "email": "info@hkchurch.or.kr",
    "extraction_method": "homepage_crawling",
    "processing_status": "success"
  }
]
```

## ⚙️ 설정 옵션

### AI 모델 설정 (`settings.py`)
```python
AI_MODEL_CONFIG = {
    'temperature': 0.1,      # 창의성 낮음 (정확성 우선)
    'top_p': 0.8,
    'top_k': 10,
    'max_output_tokens': 1000,
}

TPM_LIMITS = {
    'requests_per_minute': 6,  # 분당 6회 (무료 제한)
    'max_wait_time': 30       # 최대 대기 시간
}
```

### 크롤링 설정
```python
CRAWLING_CONFIG = {
    "default_delay": 2,          # 기본 딜레이
    "max_retries": 3,            # 최대 재시도
    "timeout": 30,               # 요청 타임아웃
    "headless_mode": True,       # 헤드리스 모드
    "max_concurrent": 5,         # 최대 동시 처리
    "save_interval": 50          # 저장 간격
}
```

### 데이터 변환 설정
```python
CONVERSION_CONFIG = {
    "exclude_fields": [          # 제외할 필드들
        "processing_error", "validation_errors", 
        "extraction_timestamp", "source_url"
    ],
    "priority_columns": [        # 우선순위 컬럼
        "name", "category", "homepage", 
        "phone", "fax", "email", "address"
    ]
}
```

## 🔍 예제

### 1. 통합 크롤링 예제

```python
import asyncio
from crawler_main import UnifiedCrawler

async def main():
    # 크롤러 초기화
    crawler = UnifiedCrawler()
    
    # 조직 데이터 준비
    organizations = [
        {"name": "삼성교회", "category": "교회"},
        {"name": "태권도장", "category": "체육시설"}
    ]
    
    # 크롤링 실행
    results = await crawler.process_organizations(organizations)
    
    print(f"✅ 처리 완료: {len(results)}개 기관")

# 실행
asyncio.run(main())
```

### 2. 데이터 처리 예제

```python
from data_processor import DataProcessor

# 데이터 처리기 초기화
processor = DataProcessor()

# JSON을 Excel로 변환
excel_file = processor.json_to_excel(
    json_file="data/json/raw_data.json",
    exclude_fields=["processing_error"]
)

# 여러 파일 결합
combined_file = processor.combine_datasets([
    "data/json/file1.json",
    "data/json/file2.json"
])

# 데이터 분석
analysis = processor.analyze_data("data/json/combined.json")
print(f"총 레코드: {analysis['basic_stats']['total_records']}")
```

### 3. 설정 관리 예제

```python
from settings import *

# 프로젝트 초기화
initialize_project()

# 설정 검증
if validate_config():
    print("✅ 설정이 올바릅니다")

# 런타임 정보 확인
info = get_runtime_info()
print(f"API 키 설정: {info['api_key_configured']}")
print(f"최신 파일: {info['latest_input_file']}")
```

## 📈 성능 최적화

### 1. TPM 제한 관리
- Gemini 1.5-flash 무료 버전: 분당 6회 제한
- 자동 대기 및 재시도 로직

### 2. 비동기 처리
- 동시 처리 수 제한 (기본 5개)
- 메모리 효율적인 청크 처리

### 3. 중간 저장
- 50개 단위로 중간 저장
- 실패 시 복구 가능

## 🐛 문제 해결

### 자주 발생하는 오류

#### 1. 설정 파일 오류
```bash
# 설정 확인
python settings.py

# 환경변수 확인
echo $GEMINI_API_KEY  # Linux/Mac
echo %GEMINI_API_KEY% # Windows
```

#### 2. 의존성 오류
```bash
# 의존성 재설치
pip install -r requirements.txt --upgrade
```

#### 3. 메모리 부족
```python
# 처리 수 제한
CRAWLING_CONFIG["max_concurrent"] = 3
```

#### 4. API 제한 오류
```python
# TPM 제한 조정
TPM_LIMITS["requests_per_minute"] = 4
```

## 📋 요구사항

### Python 버전
- Python 3.8 이상

### 주요 의존성
```
selenium>=4.0.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
google-generativeai>=0.3.0
requests>=2.28.0
openpyxl>=3.0.0
python-dotenv>=0.19.0
fastapi>=0.68.0
uvicorn>=0.15.0
```

## 🤝 기여하기

1. 이 저장소를 Fork합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

### 개발 가이드라인
- 코드 스타일: PEP 8 준수
- 문서화: 함수별 docstring 작성
- 테스트: 새 기능 추가시 테스트 코드 포함
- 설정: 모든 설정은 `settings.py`에 추가

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **Google Gemini API**: AI 기반 웹 분석 기능
- **Selenium**: 브라우저 자동화
- **BeautifulSoup**: HTML 파싱
- **FastAPI**: 웹 애플리케이션 프레임워크
- **네이버**: 검색 엔진 API

## 📞 문의

- 이슈: [GitHub Issues](https://github.com/your-username/advanced-organization-crawler/issues)
- 이메일: isfs003@gmail.com

---

## 🎉 리팩토링 완료 상태

- **1단계**: 파일 정리 및 디렉토리 구조화 ✅
- **2단계**: 핵심 모듈 통합 (crawler_main.py, data_processor.py) ✅
- **3단계**: 설정 파일 통합 (settings.py) ✅
- **최종**: 문서 업데이트 및 테스트 준비 ✅

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

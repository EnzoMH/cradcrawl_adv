# 🚀 Advanced Crawling 프로젝트 구조 (리팩토링 완료)

## 📁 프로젝트 디렉토리 구조

```
cradcrawl_adv/
├── 🚀 **핵심 실행 파일들** (8개)
│   ├── 📄 crawler_main.py             통합 크롤링 엔진 (12KB)
│   ├── 📄 data_processor.py           통합 데이터 처리기 (19KB)
│   ├── 📄 settings.py                 통합 설정 관리 (19KB)
│   ├── 📄 app.py                      FastAPI 웹 애플리케이션 (19KB)
│   ├── 📄 ai_helpers.py               AI 기반 데이터 처리 도우미 (21KB)
│   ├── 📄 parser.py                   웹페이지 파싱 및 연락처 정보 추출기 (13KB)
│   ├── 📄 naver_map_crawler.py        네이버 지도 데이터 크롤링 엔진 (22KB)
│   └── 📄 README.md                   프로젝트 문서 (10KB)
│
├── 📂 **데이터 디렉토리** (타입별 분류)
│   ├── 📁 data/
│   │   ├── 📁 json/                   JSON 데이터 파일들
│   │   ├── 📁 excel/                  Excel 데이터 파일들
│   │   └── 📁 csv/                    CSV 데이터 파일들
│   │
│   ├── 📁 output/                     처리 결과 출력 디렉토리
│   ├── 📁 logs/                       로그 파일 저장소
│   └── 📁 temp/                       임시 파일 저장소
│
├── 📁 **레거시 보관소** (15+ 파일)
│   └── 📁 legacy/                     기존 파일들 안전 보관
│       ├── 📄 advcrawler.py                      (64KB, 1498 lines)
│       ├── 📄 enhanced_detail_extractor.py       (117KB, 2688 lines)
│       ├── 📄 validator.py                       (29KB, 764 lines)
│       ├── 📄 jsontoexcel.py                     (22KB)
│       ├── 📄 constants.py                       기존 상수 파일 (20KB)
│       ├── 📄 config.py                          기존 설정 파일 (6KB)
│       └── 기타 레거시 파일들...
│
└── 🛠️ **유틸리티 및 지원 파일들**
    ├── 📁 utils/                      유틸리티 모듈들
    ├── 📁 templates/                  웹 인터페이스 템플릿
    ├── 📄 requirements.txt            Python 패키지 의존성 목록
    ├── 📄 .gitignore                  Git 제외 파일 설정
    └── 📄 project_structure.md        프로젝트 구조 문서 (이 파일)
```

## 🎯 리팩토링 주요 성과

### 📊 파일 구조 개선
- ✅ 30+ 분산 파일 → 8개 핵심 파일로 통합
- ✅ 중복 기능 제거 및 모듈화
- ✅ 타입별 데이터 디렉토리 분류 (JSON/Excel/CSV)
- ✅ 레거시 파일 안전 보관

## 🔧 핵심 모듈별 기능

### 🚀 crawler_main.py - 통합 크롤링 엔진
- 기존 advcrawler.py + enhanced_detail_extractor.py 통합
- 비동기 크롤링 처리
- 홈페이지 검색 및 상세 정보 추출
- 구글 검색으로 누락 정보 보완
- 데이터 검증 및 정리
- 중간 저장 및 통계 출력

### 📊 data_processor.py - 통합 데이터 처리기
- 기존 jsontoexcel.py + exceltojson.py + combined.py 통합
- JSON ↔ Excel 양방향 변환
- 여러 데이터셋 결합 및 병합
- 데이터 분석 및 품질 지표 계산
- 통계 시트 자동 생성
- 중복 제거 및 검증 병합

### ⚙️ settings.py - 통합 설정 관리
- 기존 constants.py + constants_extended.py + config.py 통합
- 모든 상수, 설정, 경로 중앙 관리
- API 설정 및 크롤링 설정
- 정규식 패턴 및 검증 규칙
- 유틸리티 함수들

## 💻 기술 스택
- **웹 크롤링**: Selenium, BeautifulSoup4, Requests
- **웹 프레임워크**: FastAPI, Uvicorn, Jinja2
- **데이터 처리**: Pandas, OpenPyXL
- **AI/ML**: Google Gemini API, Pydantic
- **프론트엔드**: HTML5, CSS3, JavaScript

## 🎯 주요 워크플로우
1. **데이터 입력**: JSON 파일 또는 웹 인터페이스를 통한 데이터 입력
2. **크롤링 실행**: `crawler_main.py`를 통한 통합 크롤링
3. **데이터 처리**: `data_processor.py`를 통한 변환 및 분석
4. **결과 출력**: Excel, CSV 등 다양한 형식으로 출력
5. **웹 모니터링**: `app.py`를 통한 실시간 모니터링

## 🎉 리팩토링 완료 상태
- **1단계**: 파일 정리 및 디렉토리 구조화 ✅
- **2단계**: 핵심 모듈 통합 (crawler_main.py, data_processor.py) ✅
- **3단계**: 설정 파일 통합 (settings.py) ✅
- **최종**: 문서 업데이트 및 테스트 준비 ✅

## 🚀 사용 방법

### 기본 실행
```bash
# 통합 크롤링 실행
python crawler_main.py

# 데이터 처리 실행
python data_processor.py

# 웹 애플리케이션 실행
python app.py
```

### 설정 확인
```bash
# 프로젝트 설정 초기화 및 확인
python settings.py
``` 
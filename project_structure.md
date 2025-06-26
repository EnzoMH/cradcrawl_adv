# 🚀 Advanced Crawling CRM 프로젝트 구조 (React 리팩토링 완료)

## 📁 프로젝트 디렉토리 구조

```
advanced_crawling/
├── 🚀 **핵심 애플리케이션 파일들**
│   ├── 📄 crm_app.py                  🎯 FastAPI CRM 메인 애플리케이션 (32KB, 796줄)
│   ├── 📄 app.py                      🔄 레거시 웹 애플리케이션 (17KB, 431줄)
│   ├── 📄 crawler_main.py             🎯 통합 크롤링 메인 모듈 (UnifiedCrawler)
│   ├── 📄 additionalplan.py           추가 계획 및 기능 개발
│   ├── 📄 test_crm.py                 🧪 CRM 시스템 테스트 스크립트
│   └── 📄 cleanup_logs.py             로그 정리 유틸리티
│
├── 🗄️ **데이터베이스 시스템**
│   └── 📁 database/
│       ├── 📄 __init__.py             패키지 초기화
│       ├── 📄 database.py             🎯 SQLite CRM 메인 모듈 (38KB, 900줄)
│       ├── 📄 models.py               🎯 데이터 모델 정의 (17KB, 474줄)
│       ├── 📄 migration.py            🎯 JSON → DB 마이그레이션 (14KB, 361줄)
│       ├── 📄 churches_crm.db         🎯 SQLite 데이터베이스 파일 (80MB+)
│       ├── 📄 churches_crm.db-shm     SQLite 공유 메모리 파일
│       ├── 📄 churches_crm.db-wal     SQLite 쓰기 전용 로그 파일
│       └── 📄 churches_crm_backup.db  백업 데이터베이스
│
├── 🔧 **서비스 레이어** (NEW!)
│   └── 📁 services/
│       ├── 📄 __init__.py             패키지 초기화
│       ├── 📄 organization_service.py 🎯 기관 관리 서비스 (고급 검색, 필터링)
│       └── 📄 contact_enrichment_service.py 🎯 연락처 보강 서비스 (자동 크롤링)
│
├── 🌐 **API 레이어** (NEW!)
│   └── 📁 api/
│       ├── 📄 __init__.py             패키지 초기화
│       ├── 📄 organization_api.py     🎯 기관 관리 API (CRUD, 검색, 필터링)
│       └── 📄 enrichment_api.py       🎯 연락처 보강 API (단일/일괄/자동 보강)
│
├── 🔧 **유틸리티 모듈**
│   └── 📁 utils/
│       ├── 📄 __init__.py             패키지 초기화
│       ├── 📄 settings.py             🎯 통합 애플리케이션 설정 (상수, 설정값)
│       ├── 📄 ai_helpers.py           AI 도움 기능 (Gemini API)
│       ├── 📄 converter.py            데이터 변환 도구
│       ├── 📄 crawler_utils.py        크롤링 유틸리티
│       ├── 📄 file_utils.py           파일 처리 유틸리티
│       ├── 📄 logger_utils.py         로깅 유틸리티
│       ├── 📄 naver_map_crawler.py    네이버 지도 크롤러
│       ├── 📄 parser.py               데이터 파싱 모듈
│       ├── 📄 phone_utils.py          전화번호 처리 도구
│       └── 📄 validator.py            데이터 검증 도구
│
├── 🌐 **웹 애플리케이션 템플릿** (React 기반 CRM 시스템)
│   └── 📁 templates/
│       ├── 📁 html/                   🎯 HTML 템플릿 파일들
│       │   ├── 📄 index.html         🎯 CRM 랜딩 페이지 (정적 + 시스템 상태)
│       │   ├── 📄 dashboard.html     🎯 대시보드 페이지 (React 기반)
│       │   ├── 📄 organizations.html 🎯 기관 관리 페이지 (React 기반)
│       │   ├── 📄 enrichment.html    🎯 연락처 보강 페이지 (React 기반)
│       │   ├── 📄 login.html         🎯 로그인 페이지
│       │   ├── 📄 shared-navigation.html 🆕 공통 네비게이션 컴포넌트
│       │   ├── 📄 404.html           404 에러 페이지
│       │   └── 📄 500.html           500 에러 페이지
│       ├── 📁 css/
│       │   └── 📄 style.css          🎯 TailwindCSS 보완 스타일시트 (개선됨)
│       └── 📁 js/                    🎯 JavaScript 모듈 (React + 통합 API)
│           ├── 📄 utils.js           🆕 공통 유틸리티 함수 (포맷팅, 검증, DOM 조작)
│           ├── 📄 api.js             🆕 통합 API 클래스 (모든 API 호출 중앙 관리)
│           ├── 📄 main.js            🔄 CRM 시스템 메인 로직 (단순화됨, 15KB, 568줄)
│           ├── 📄 ui.js              🔄 UI 렌더링 모듈 (기존 유지, 52KB, 1146줄)
│           ├── 📄 dashboard.js       🎯 대시보드 React 컴포넌트 (통합 API 사용)
│           ├── 📄 organizations.js   🎯 기관 관리 React 컴포넌트 (37KB, 1108줄)
│           └── 📄 enrichment.js      🎯 연락처 보강 React 컴포넌트 (16KB, 474줄)
│
├── 📂 **데이터 저장소**
│   └── 📁 data/
│       ├── 📁 json/                   JSON 데이터 파일들
│       │   ├── 📄 merged_church_data_20250618_174032.json 🎯 메인 병합 데이터 (28,104개)
│       │   ├── 📄 parsed_homepages_20250617_192102.json   홈페이지 파싱 결과
│       │   ├── 📄 church_data_converted_20250617_202219.json 교회 데이터 변환
│       │   └── 📄 (기타 JSON 파일들...)
│       ├── 📁 excel/                  Excel 데이터 파일들
│       └── 📁 csv/                    CSV 데이터 파일들
│
├── 🧪 **테스트 및 실험 파일들**
│   └── 📁 test/
│       ├── 📄 data_processor.py       🎯 데이터 처리기 (수정됨)
│       ├── 📄 db_to_excel.py          DB → Excel 내보내기
│       ├── 📄 faxextractor.py         🎯 팩스 번호 추출기 (통합됨, 8.6KB, 224줄)
│       ├── 📄 migration_script.py     마이그레이션 스크립트
│       ├── 📄 phoneextractor.py       전화번호 추출기 (5.9KB, 160줄)
│       └── 📄 urlextractor_2.py       🎯 URL 추출기 v2 (수정됨, 60KB, 1362줄)
│
├── 🗂️ **레거시 파일들**
│   ├── 📁 legacy/
│   │   ├── 📄 data_statistics.py     🎯 데이터 통계 분석 (수정됨)
│   │   └── 📁 legacy2/               추가 레거시 파일들
│   └── 📁 logs/                      애플리케이션 로그 파일들
│
└── 🛠️ **지원 파일들**
    ├── 📄 requirements.txt            Python 패키지 의존성 목록
    ├── 📄 README.md                   프로젝트 설명서
    ├── 📄 directory.txt               프로젝트 구조 문서
    ├── 📄 project_structure.md        프로젝트 구조 상세 문서 (이 파일)
    ├── 📄 SaaS 추가개발 계획안.txt     SaaS 확장 계획서
    └── 📄 .gitignore                  Git 제외 파일 설정
```

## 🎯 리팩토링 주요 성과 (2025-06-18 20:45)

### 📊 아키텍처 개선
- ✅ **React 기반 프론트엔드**: 모듈화된 컴포넌트 시스템
- ✅ **서비스 레이어 구축**: 비즈니스 로직 분리
- ✅ **API 레이어 구축**: RESTful API 완전 문서화
- ✅ **통합 API 클래스**: 모든 API 호출 중앙 관리
- ✅ **공통 유틸리티 모듈**: 코드 재사용성 극대화

### 🗄️ 데이터베이스 현황
- **총 기관 수**: 218,039개 (교회 중심 → 확장됨)
- **데이터베이스 크기**: 80MB+ (SQLite WAL 모드)
- **마이그레이션 완료**: JSON → SQLite 완전 이전
- **인덱싱 최적화**: 검색 성능 향상

## 🔧 핵심 모듈별 기능

### 🚀 crm_app.py - FastAPI CRM 메인 애플리케이션
- **RESTful API**: 완전한 CRUD 작업 지원
- **사용자 인증**: 세션 기반 인증 시스템
- **실시간 모니터링**: 크롤링 진행 상황 추적
- **자동 문서화**: FastAPI 기반 API 문서 자동 생성
- **에러 처리**: 포괄적인 예외 처리 및 로깅

### 🌐 React 기반 프론트엔드 시스템
#### JavaScript 모듈 구조
```
templates/js/
├── utils.js          # 공통 유틸리티 (전역)
├── api.js            # 통합 API 클래스 (전역)
├── main.js           # CRM 시스템 메인 로직 (단순화)
├── ui.js             # UI 렌더링 (기존 유지)
├── dashboard.js      # 대시보드 React 컴포넌트
├── organizations.js  # 기관 관리 React 컴포넌트
└── enrichment.js     # 연락처 보강 React 컴포넌트
```

#### 의존성 로드 순서
```html
1. utils.js       → 공통 유틸리티 함수
2. api.js         → 통합 API 클래스
3. [페이지].js    → 페이지별 React 컴포넌트
```

### 🔧 서비스 레이어
#### OrganizationService
- **고급 검색**: 복합 조건 검색 및 필터링
- **데이터 분석**: 연락처 완성도 통계
- **보강 우선순위**: 누락 데이터 기반 우선순위 계산
- **활동 추적**: 사용자 활동 이력 관리

#### ContactEnrichmentService
- **자동 보강**: 누락된 연락처 정보 자동 탐지 및 보강
- **배치 처리**: 대량 데이터 일괄 보강
- **실시간 모니터링**: 보강 진행 상황 실시간 추적
- **AI 통합**: Gemini API 기반 데이터 추출

### 🌐 API 레이어
#### 기관 관리 API
- `GET /api/organizations` - 기관 목록 조회 (페이징, 검색, 필터링)
- `GET /api/organizations/{id}` - 기관 상세 조회
- `POST /api/organizations` - 새 기관 생성
- `PUT /api/organizations/{id}` - 기관 정보 수정
- `DELETE /api/organizations/{id}` - 기관 삭제

#### 연락처 보강 API
- `POST /api/enrichment/single/{id}` - 단일 기관 보강
- `POST /api/enrichment/batch` - 다중 기관 일괄 보강
- `POST /api/enrichment/auto` - 자동 보강 시작
- `GET /api/organizations/enrichment-candidates` - 보강 후보 조회

#### 통계 API
- `GET /api/statistics` - 기본 통계
- `GET /api/stats/summary` - 요약 통계
- `GET /api/stats/dashboard-data` - 대시보드 차트용 데이터

### 🎯 crawler_main.py - 통합 크롤링 엔진
- **UnifiedCrawler**: 통합 크롤링 클래스
- **AI 기반 추출**: Gemini API 활용 데이터 추출
- **구글 검색 통합**: 누락 정보 자동 검색
- **실시간 콜백**: 진행 상황 실시간 업데이트
- **배치 처리**: 대량 데이터 효율적 처리

## 💻 기술 스택

### 백엔드
- **웹 프레임워크**: FastAPI + Uvicorn
- **데이터베이스**: SQLite (WAL 모드)
- **ORM**: 순수 SQL (최적화된 쿼리)
- **인증**: 세션 기반 인증
- **API 문서**: FastAPI 자동 생성 (Swagger UI)

### 프론트엔드
- **JavaScript**: React 18 + Vanilla JavaScript
- **CSS 프레임워크**: TailwindCSS
- **차트**: Chart.js
- **아이콘**: Lucide Icons
- **반응형**: Mobile-first 디자인

### 크롤링 & AI
- **웹 크롤링**: Selenium + BeautifulSoup4
- **HTTP 클라이언트**: Requests + aiohttp
- **AI**: Google Gemini API
- **데이터 처리**: Pandas + OpenPyXL

## 🎯 주요 워크플로우

### 1. 데이터 관리 워크플로우
```
데이터 입력 → 검증 → 저장 → 인덱싱 → 검색/필터링
```

### 2. 연락처 보강 워크플로우
```
누락 탐지 → 크롤링 → AI 추출 → 검증 → 업데이트 → 통계 갱신
```

### 3. 사용자 인터페이스 워크플로우
```
로그인 → 대시보드 → 기관 관리/보강 → 실시간 모니터링 → 결과 확인
```

## 🌐 웹 페이지 구조

### 홈 (`/`)
- CRM 시스템 소개
- 빠른 네비게이션
- 시스템 상태 표시
- 로그인 링크

### 대시보드 (`/dashboard`)
- React 기반 실시간 통계
- 차트 및 그래프
- 최근 활동 이력
- 빠른 액션 버튼

### 기관 관리 (`/organizations`)
- React 기반 CRUD 인터페이스
- 고급 검색 및 필터링
- 대량 작업 지원
- 실시간 테이블 업데이트

### 연락처 보강 (`/enrichment`)
- React 기반 보강 인터페이스
- 진행 상황 실시간 모니터링
- 배치 작업 관리
- 결과 분석 및 통계

## 📈 성능 최적화

### 데이터베이스 최적화
- ✅ SQLite WAL 모드 사용
- ✅ 인덱싱 최적화 (검색 필드)
- ✅ 페이징 처리 (50개씩)
- ✅ 쿼리 최적화 (JOIN 최소화)

### 프론트엔드 최적화
- ✅ React 컴포넌트 최적화
- ✅ API 응답 캐싱
- ✅ 지연 로딩 (Lazy Loading)
- ✅ 번들 크기 최적화

### 크롤링 최적화
- ✅ 비동기 처리
- ✅ 배치 처리 (100개씩)
- ✅ 재시도 로직
- ✅ 중복 방지

## 🔐 보안 기능

- ✅ **사용자 인증**: 세션 기반 인증 시스템
- ✅ **권한 관리**: 역할 기반 접근 제어
- ✅ **비밀번호 보안**: PBKDF2 해시화
- ✅ **세션 관리**: 안전한 세션 토큰 관리
- ✅ **입력 검증**: 모든 입력 데이터 검증
- ✅ **SQL 인젝션 방지**: 매개변수화된 쿼리

## 🎉 프로젝트 완성도: 98%

### ✅ 완료된 기능
- 🗄️ SQLite CRM 데이터베이스 시스템 완성
- 🏢 기관/교회 정보 관리 (218,039개 데이터)
- 📊 React 기반 대시보드 (실시간 차트, 통계)
- 🌐 React 기반 웹 인터페이스 (모듈화된 컴포넌트)
- 🔄 실시간 크롤링 모니터링
- 🔍 고급 검색 및 필터링
- 📱 반응형 웹 디자인
- 🤖 자동 연락처 보강 시스템
- 📋 영업 활동 추적 및 관리
- 🔐 사용자 인증 및 권한 관리
- ✅ RESTful API 완성 (문서화)
- ✅ 서비스 레이어 구축
- ✅ 통합 API 클래스
- ✅ 공통 유틸리티 모듈

### 🔄 진행 중
- SaaS 확장 계획 수립
- 추가 데이터 소스 통합
- 고급 분석 기능 개발

## 🚀 사용 방법

### 기본 실행
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 데이터베이스 마이그레이션 (선택사항)
python database/migration.py

# 3. CRM 애플리케이션 실행 (권장)
python crm_app.py

# 4. 또는 레거시 애플리케이션 실행
python app.py

# 5. 브라우저에서 접속
http://localhost:8000

# 6. API 문서 확인
http://localhost:8000/docs
```

### 개발 모드 실행
```bash
# 개발 서버 실행 (자동 재시작)
uvicorn crm_app:app --reload --host 0.0.0.0 --port 8000
```

### 테스트 실행
```bash
# CRM 시스템 테스트
python test_crm.py

# 크롤링 테스트
python crawler_main.py --test-mode
```

---

## 📝 변경 이력

### 2025-06-18 20:45 - React 리팩토링 완료
- React 기반 프론트엔드 시스템 구축
- 서비스 레이어 및 API 레이어 분리
- 통합 API 클래스 및 공통 유틸리티 모듈 구축
- 218,039개 데이터로 확장
- 성능 최적화 및 보안 강화

### 2025-06-18 19:30 - CRM 시스템 완성
- SQLite 기반 CRM 데이터베이스 구축
- 28,104개 데이터 마이그레이션 완료
- 웹 기반 사용자 인터페이스 구축
- 실시간 크롤링 모니터링 시스템

### 2025-06-17 - 초기 리팩토링
- 파일 구조 정리 및 모듈화
- 통합 크롤링 엔진 구축
- 데이터 처리 파이프라인 구축 
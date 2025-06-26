# 🏢 Advanced Church CRM System

한국 교회/기관 정보를 관리하는 통합 CRM 시스템 (React + FastAPI + SQLite + AI 크롤링)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [최신 업데이트](#최신-업데이트)
- [설치 및 실행](#설치-및-실행)
- [시스템 구조](#시스템-구조)
- [React 기반 프론트엔드](#react-기반-프론트엔드)
- [API 문서](#api-문서)
- [데이터베이스](#데이터베이스)
- [크롤링 시스템](#크롤링-시스템)
- [개발 정보](#개발-정보)

## 🎯 개요

**Advanced Church CRM System**은 한국의 교회 및 종교기관 정보를 체계적으로 관리하는 통합 CRM 솔루션입니다.

### ✨ 핵심 특징

- 🗄️ **SQLite CRM 데이터베이스** (218,039개 기관 데이터 포함)
- ⚛️ **React 기반 프론트엔드** (모듈화된 컴포넌트 시스템)
- 🌐 **FastAPI + RESTful API** (완전한 문서화)
- 👥 **사용자 권한 관리** (세션 기반 인증)
- 📊 **실시간 대시보드** 및 통계 분석
- 🔄 **지능형 크롤링 시스템** (AI 기반 정보 추출)
- 🔧 **서비스 레이어 아키텍처** (비즈니스 로직 분리)
- 📱 **반응형 웹 디자인** (TailwindCSS)
- 🤖 **AI 기반 연락처 자동 보강**

## 🚀 주요 기능

### 1. 🏢 기관 정보 관리
- **218,039개 기관** 데이터베이스 구축 완료
- React 기반 CRUD 인터페이스
- 고급 검색 및 필터링 (실시간)
- 대량 작업 지원 (일괄 수정/삭제)
- 엑셀/CSV 내보내기

### 2. ⚛️ React 기반 프론트엔드 시스템
- **모듈화된 컴포넌트**: 재사용 가능한 React 컴포넌트
- **통합 API 클래스**: 모든 API 호출 중앙 관리
- **공통 유틸리티**: 포맷팅, 검증, DOM 조작 함수
- **실시간 업데이트**: 데이터 변경 시 즉시 반영
- **반응형 디자인**: 모바일/데스크톱 최적화

### 3. 🌐 RESTful API 시스템
- **완전한 CRUD**: 기관 정보 생성/조회/수정/삭제
- **고급 검색**: 복합 조건 검색 및 필터링
- **연락처 보강**: 단일/일괄/자동 보강 API
- **실시간 통계**: 대시보드용 데이터 API
- **자동 문서화**: FastAPI Swagger UI

### 4. 🤖 AI 기반 연락처 보강 시스템
- **자동 탐지**: 누락된 연락처 정보 자동 감지
- **배치 처리**: 대량 데이터 일괄 보강
- **실시간 모니터링**: 보강 진행 상황 추적
- **AI 통합**: Gemini API 기반 데이터 추출

### 5. 👥 사용자 및 권한 관리
- **세션 기반 인증**: 안전한 로그인 시스템
- **권한 기반 접근 제어**: 역할별 기능 제한
- **활동 이력 추적**: 사용자 행동 로깅
- **비밀번호 보안**: PBKDF2 해시화

## 🔥 최신 업데이트 (2025.06.18)

### 📊 React 리팩토링 완료
새로운 아키텍처로 완전히 전환되었습니다:

#### ⚛️ JavaScript 모듈 구조
```
templates/js/
├── utils.js          # 공통 유틸리티 (전역)
├── api.js            # 통합 API 클래스 (전역)
├── main.js           # CRM 시스템 메인 로직 (단순화)
├── ui.js             # UI 렌더링 (기존 유지)
├── dashboard.js      # 대시보드 React 컴포넌트
├── organizations.js  # 기관 관리 React 컴포넌트 (37KB, 1108줄)
└── enrichment.js     # 연락처 보강 React 컴포넌트 (16KB, 474줄)
```

#### 🔧 서비스 레이어 구축
```python
# OrganizationService - 기관 관리 서비스
class OrganizationService:
    def search_organizations(self, filters, pagination)
    def get_enrichment_candidates(self, criteria)
    def calculate_completeness_score(self, organization)
    def track_user_activity(self, user_id, action)

# ContactEnrichmentService - 연락처 보강 서비스
class ContactEnrichmentService:
    def enrich_single_organization(self, org_id, callback)
    def enrich_batch_organizations(self, org_ids, callback)
    def auto_enrich_missing_contacts(self, criteria, callback)
    def get_enrichment_statistics(self)
```

#### 🌐 API 레이어 구축
```python
# RESTful API 엔드포인트
@app.get("/api/organizations")           # 기관 목록 조회 (페이징, 검색, 필터링)
@app.get("/api/organizations/{id}")      # 기관 상세 조회
@app.post("/api/organizations")          # 새 기관 생성
@app.put("/api/organizations/{id}")      # 기관 정보 수정
@app.delete("/api/organizations/{id}")   # 기관 삭제

@app.post("/api/enrichment/single/{id}") # 단일 기관 보강
@app.post("/api/enrichment/batch")       # 다중 기관 일괄 보강
@app.post("/api/enrichment/auto")        # 자동 보강 시작
```

### 🗄️ 데이터베이스 확장
- **총 기관 수**: 28,104개 → **218,039개**로 확장
- **데이터베이스 크기**: 80MB+ (SQLite WAL 모드)
- **인덱싱 최적화**: 검색 성능 향상
- **백업 시스템**: 자동 백업 및 복구

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/advanced-church-crm.git
cd advanced-church-crm
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
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///./churches_crm.db
```

### 5. 애플리케이션 실행
```bash
# CRM 애플리케이션 실행 (권장)
python crm_app.py

# 또는 레거시 애플리케이션 실행
python app.py

# 브라우저에서 접속
http://localhost:8000

# API 문서 확인
http://localhost:8000/docs
```

### 6. 개발 모드 실행
```bash
# 개발 서버 실행 (자동 재시작)
uvicorn crm_app:app --reload --host 0.0.0.0 --port 8000
```

## 📁 시스템 구조

```
advanced_crawling/
├── 🚀 **핵심 애플리케이션 파일들**
│   ├── 📄 crm_app.py                  🎯 FastAPI CRM 메인 애플리케이션 (32KB, 796줄)
│   ├── 📄 app.py                      🔄 레거시 웹 애플리케이션 (17KB, 431줄)
│   ├── 📄 crawler_main.py             🎯 통합 크롤링 메인 모듈 (UnifiedCrawler)
│   ├── 📄 additionalplan.py           추가 계획 및 기능 개발
│   └── 📄 cleanup_logs.py             로그 정리 유틸리티
│
├── 🗄️ **데이터베이스 시스템**
│   └── 📁 database/
│       ├── 📄 database.py             🎯 SQLite CRM 메인 모듈 (38KB, 900줄)
│       ├── 📄 models.py               🎯 데이터 모델 정의 (17KB, 474줄)
│       ├── 📄 migration.py            🎯 JSON → DB 마이그레이션 (14KB, 361줄)
│       └── 📄 churches_crm.db         🎯 SQLite 데이터베이스 파일 (80MB+)
│
├── 🔧 **서비스 레이어** (NEW!)
│   └── 📁 services/
│       ├── 📄 organization_service.py 🎯 기관 관리 서비스 (고급 검색, 필터링)
│       └── 📄 contact_enrichment_service.py 🎯 연락처 보강 서비스 (자동 크롤링)
│
├── 🌐 **API 레이어** (NEW!)
│   └── 📁 api/
│       ├── 📄 organization_api.py     🎯 기관 관리 API (CRUD, 검색, 필터링)
│       └── 📄 enrichment_api.py       🎯 연락처 보강 API (단일/일괄/자동 보강)
│
├── 🔧 **유틸리티 모듈**
│   └── 📁 utils/
│       ├── 📄 settings.py             🎯 통합 애플리케이션 설정 (상수, 설정값)
│       ├── 📄 ai_helpers.py           AI 도움 기능 (Gemini API)
│       ├── 📄 crawler_utils.py        크롤링 유틸리티
│       ├── 📄 parser.py               데이터 파싱 모듈
│       └── 📄 validator.py            데이터 검증 도구
│
└── 🌐 **웹 애플리케이션 템플릿** (React 기반 CRM 시스템)
    └── 📁 templates/
        ├── 📁 html/                   🎯 HTML 템플릿 파일들
        │   ├── 📄 index.html         🎯 CRM 랜딩 페이지
        │   ├── 📄 dashboard.html     🎯 대시보드 페이지 (React 기반)
        │   ├── 📄 organizations.html 🎯 기관 관리 페이지 (React 기반)
        │   ├── 📄 enrichment.html    🎯 연락처 보강 페이지 (React 기반)
        │   └── 📄 login.html         🎯 로그인 페이지
        ├── 📁 css/
        │   └── 📄 style.css          🎯 TailwindCSS 보완 스타일시트
        └── 📁 js/                    🎯 JavaScript 모듈 (React + 통합 API)
            ├── 📄 utils.js           🆕 공통 유틸리티 함수
            ├── 📄 api.js             🆕 통합 API 클래스
            ├── 📄 main.js            🔄 CRM 시스템 메인 로직
            ├── 📄 ui.js              🔄 UI 렌더링 모듈
            ├── 📄 dashboard.js       🎯 대시보드 React 컴포넌트
            ├── 📄 organizations.js   🎯 기관 관리 React 컴포넌트
            └── 📄 enrichment.js      🎯 연락처 보강 React 컴포넌트
```

## ⚛️ React 기반 프론트엔드

### 🎯 컴포넌트 구조

#### 1. 대시보드 컴포넌트 (`dashboard.js`)
```javascript
class DashboardApp {
    constructor() {
        this.api = new CRMApi();
        this.charts = {};
        this.init();
    }
    
    async loadDashboardData() {
        const data = await this.api.get('/api/stats/dashboard-data');
        this.renderCharts(data);
        this.renderRecentActivity(data.recent_activity);
    }
    
    renderCharts(data) {
        // Chart.js 기반 실시간 차트 렌더링
        this.renderOrganizationChart(data.organization_stats);
        this.renderEnrichmentChart(data.enrichment_stats);
        this.renderActivityChart(data.activity_stats);
    }
}
```

#### 2. 기관 관리 컴포넌트 (`organizations.js`)
```javascript
class OrganizationsApp {
    constructor() {
        this.api = new CRMApi();
        this.currentPage = 1;
        this.pageSize = 50;
        this.filters = {};
        this.init();
    }
    
    async loadOrganizations() {
        const params = {
            page: this.currentPage,
            page_size: this.pageSize,
            ...this.filters
        };
        
        const response = await this.api.get('/api/organizations', params);
        this.renderOrganizationsTable(response.data);
        this.renderPagination(response.pagination);
    }
    
    async handleBulkAction(action, selectedIds) {
        switch(action) {
            case 'delete':
                await this.bulkDelete(selectedIds);
                break;
            case 'enrich':
                await this.bulkEnrich(selectedIds);
                break;
        }
        this.loadOrganizations();
    }
}
```

#### 3. 연락처 보강 컴포넌트 (`enrichment.js`)
```javascript
class EnrichmentApp {
    constructor() {
        this.api = new CRMApi();
        this.enrichmentProgress = {};
        this.init();
    }
    
    async startAutoEnrichment() {
        const response = await this.api.post('/api/enrichment/auto');
        this.monitorProgress(response.task_id);
    }
    
    monitorProgress(taskId) {
        const interval = setInterval(async () => {
            const progress = await this.api.get(`/api/enrichment/progress/${taskId}`);
            this.updateProgressBar(progress);
            
            if (progress.status === 'completed') {
                clearInterval(interval);
                this.showCompletionSummary(progress.results);
            }
        }, 1000);
    }
}
```

### 🔧 통합 API 클래스 (`api.js`)
```javascript
class CRMApi {
    constructor() {
        this.baseURL = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    async get(endpoint, params = {}) {
        const url = new URL(endpoint, window.location.origin);
        Object.keys(params).forEach(key => 
            url.searchParams.append(key, params[key])
        );
        
        const response = await fetch(url, {
            method: 'GET',
            headers: this.defaultHeaders
        });
        
        return this.handleResponse(response);
    }
    
    async post(endpoint, data = {}) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: this.defaultHeaders,
            body: JSON.stringify(data)
        });
        
        return this.handleResponse(response);
    }
    
    async handleResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}
```

### 🛠️ 공통 유틸리티 (`utils.js`)
```javascript
const Utils = {
    // 날짜 포맷팅
    formatDate(date, format = 'YYYY-MM-DD') {
        return new Date(date).toLocaleDateString('ko-KR');
    },
    
    // 전화번호 포맷팅
    formatPhone(phone) {
        if (!phone) return '';
        return phone.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');
    },
    
    // 숫자 포맷팅 (천 단위 구분)
    formatNumber(number) {
        return new Intl.NumberFormat('ko-KR').format(number);
    },
    
    // DOM 조작
    createElement(tag, className = '', content = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (content) element.textContent = content;
        return element;
    },
    
    // 디바운스 함수
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
```

## 🌐 API 문서

### 기관 관리 API

#### 기관 목록 조회
```http
GET /api/organizations?page=1&page_size=50&search=교회&category=교회
```

**응답:**
```json
{
    "data": [
        {
            "id": 1,
            "name": "삼성교회",
            "category": "교회",
            "address": "서울시 강남구",
            "phone": "02-123-4567",
            "homepage": "https://samsung.church",
            "completeness_score": 85,
            "created_at": "2025-06-18T10:00:00Z",
            "updated_at": "2025-06-18T15:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 50,
        "total": 218039,
        "total_pages": 4361
    }
}
```

#### 기관 상세 조회
```http
GET /api/organizations/1
```

#### 새 기관 생성
```http
POST /api/organizations
Content-Type: application/json

{
    "name": "새로운교회",
    "category": "교회",
    "address": "서울시 서초구",
    "phone": "02-987-6543"
}
```

### 연락처 보강 API

#### 단일 기관 보강
```http
POST /api/enrichment/single/1
```

#### 일괄 보강
```http
POST /api/enrichment/batch
Content-Type: application/json

{
    "organization_ids": [1, 2, 3, 4, 5]
}
```

#### 자동 보강 시작
```http
POST /api/enrichment/auto
Content-Type: application/json

{
    "criteria": {
        "missing_phone": true,
        "missing_homepage": true,
        "limit": 100
    }
}
```

### 통계 API

#### 대시보드 데이터
```http
GET /api/stats/dashboard-data
```

**응답:**
```json
{
    "organization_stats": {
        "total": 218039,
        "by_category": {
            "교회": 180000,
            "학원": 25000,
            "기타": 13039
        }
    },
    "enrichment_stats": {
        "completed": 150000,
        "in_progress": 1500,
        "pending": 66539
    },
    "recent_activity": [
        {
            "id": 1,
            "action": "enrichment_completed",
            "organization_name": "삼성교회",
            "timestamp": "2025-06-18T15:30:00Z"
        }
    ]
}
```

## 🗄️ 데이터베이스

### 스키마 구조

#### organizations 테이블
```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    address TEXT,
    phone TEXT,
    mobile TEXT,
    fax TEXT,
    email TEXT,
    homepage TEXT,
    postal_code TEXT,
    region TEXT,
    completeness_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_category ON organizations(category);
CREATE INDEX idx_organizations_region ON organizations(region);
CREATE INDEX idx_organizations_completeness ON organizations(completeness_score);
```

#### user_activities 테이블
```sql
CREATE TABLE user_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT,
    organization_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations (id)
);
```

#### enrichment_logs 테이블
```sql
CREATE TABLE enrichment_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    enrichment_type TEXT,
    status TEXT,
    results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations (id)
);
```

### 데이터베이스 최적화

#### WAL 모드 설정
```python
# database/database.py
def setup_database():
    conn = sqlite3.connect('churches_crm.db')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=10000')
    conn.execute('PRAGMA temp_store=MEMORY')
    return conn
```

#### 성능 최적화
- **인덱싱**: 검색 필드에 복합 인덱스 적용
- **페이징**: LIMIT/OFFSET 최적화
- **캐싱**: 자주 사용되는 쿼리 결과 캐싱
- **배치 처리**: 대량 작업 시 트랜잭션 단위 처리

## 🤖 크롤링 시스템

### UnifiedCrawler 클래스

```python
from crawler_main import UnifiedCrawler

class UnifiedCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.ai_client = GeminiClient()
        self.parser = Parser()
        self.validator = Validator()
    
    async def process_organization(self, org_data, callback=None):
        """단일 기관 정보 크롤링 및 보강"""
        try:
            # 1. 홈페이지 검색
            homepage = await self.search_homepage(org_data['name'])
            
            # 2. 상세 정보 추출
            if homepage:
                details = await self.extract_details(homepage)
                org_data.update(details)
            
            # 3. AI 기반 추가 정보 추출
            ai_results = await self.ai_extract_info(org_data)
            org_data.update(ai_results)
            
            # 4. 데이터 검증
            validated_data = self.validator.validate(org_data)
            
            # 5. 콜백 호출 (진행 상황 업데이트)
            if callback:
                callback(validated_data)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"크롤링 오류: {e}")
            return org_data
    
    async def batch_process(self, organizations, callback=None):
        """배치 처리"""
        results = []
        for i, org in enumerate(organizations):
            result = await self.process_organization(org)
            results.append(result)
            
            # 진행 상황 콜백
            if callback:
                callback({
                    'current': i + 1,
                    'total': len(organizations),
                    'progress': (i + 1) / len(organizations) * 100,
                    'current_org': org['name']
                })
        
        return results
```

### AI 기반 정보 추출

```python
from utils.ai_helpers import GeminiClient

class GeminiClient:
    def __init__(self):
        self.client = genai.GenerativeModel('gemini-1.5-flash')
    
    async def extract_contact_info(self, webpage_content, org_name):
        """웹페이지에서 연락처 정보 추출"""
        prompt = f"""
        다음 웹페이지 내용에서 '{org_name}'의 연락처 정보를 추출해주세요:
        
        {webpage_content[:2000]}
        
        다음 JSON 형식으로 응답해주세요:
        {{
            "phone": "전화번호",
            "fax": "팩스번호", 
            "email": "이메일주소",
            "address": "주소"
        }}
        """
        
        response = await self.client.generate_content_async(prompt)
        return self.parse_ai_response(response.text)
```

## 📈 성능 최적화

### 1. 데이터베이스 최적화
- **SQLite WAL 모드**: 동시 읽기/쓰기 성능 향상
- **인덱싱**: 검색 필드에 복합 인덱스 적용
- **페이징**: 50개씩 페이징 처리
- **쿼리 최적화**: JOIN 최소화, 서브쿼리 최적화

### 2. 프론트엔드 최적화
- **React 컴포넌트**: 메모화 및 최적화
- **API 캐싱**: 자주 사용되는 데이터 캐싱
- **지연 로딩**: 필요시에만 데이터 로드
- **번들 최적화**: JavaScript 파일 크기 최적화

### 3. 크롤링 최적화
- **비동기 처리**: asyncio 기반 동시 처리
- **배치 처리**: 100개씩 배치 단위 처리
- **재시도 로직**: 실패 시 자동 재시도
- **중복 방지**: URL 기반 중복 처리 방지

## 🔐 보안 기능

### 1. 인증 및 권한
```python
# 세션 기반 인증
@app.post("/login")
async def login(request: Request, username: str, password: str):
    user = authenticate_user(username, password)
    if user:
        request.session['user_id'] = user.id
        request.session['role'] = user.role
        return {"status": "success"}
    return {"status": "error", "message": "Invalid credentials"}

# 권한 확인 데코레이터
def require_auth(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if 'user_id' not in request.session:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return await func(request, *args, **kwargs)
    return wrapper
```

### 2. 데이터 보호
- **비밀번호 해시화**: PBKDF2 알고리즘 사용
- **세션 보안**: 안전한 세션 토큰 관리
- **입력 검증**: 모든 입력 데이터 검증
- **SQL 인젝션 방지**: 매개변수화된 쿼리 사용

## 🔍 사용 예제

### 1. 기본 사용법

```python
# CRM 애플리케이션 실행
python crm_app.py

# 브라우저에서 접속
# http://localhost:8000

# 로그인 (기본 계정)
# Username: admin
# Password: admin123
```

### 2. API 사용 예제

```python
import requests

# API 클라이언트
api_base = "http://localhost:8000/api"

# 기관 목록 조회
response = requests.get(f"{api_base}/organizations", params={
    "page": 1,
    "page_size": 50,
    "search": "교회",
    "category": "교회"
})

organizations = response.json()
print(f"총 {organizations['pagination']['total']}개 기관")

# 단일 기관 보강
response = requests.post(f"{api_base}/enrichment/single/1")
result = response.json()
print(f"보강 결과: {result}")
```

### 3. 크롤링 사용 예제

```python
from crawler_main import UnifiedCrawler
import asyncio

async def crawl_example():
    crawler = UnifiedCrawler()
    
    # 단일 기관 크롤링
    org_data = {
        "name": "삼성교회",
        "category": "교회",
        "address": "서울시 강남구"
    }
    
    def progress_callback(data):
        print(f"처리 중: {data}")
    
    result = await crawler.process_organization(org_data, progress_callback)
    print(f"크롤링 결과: {result}")

# 실행
asyncio.run(crawl_example())
```

## 📋 요구사항

### Python 버전
- Python 3.8 이상

### 주요 의존성
```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlite3>=3.40.0
selenium>=4.15.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
google-generativeai>=0.3.0
requests>=2.31.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
jinja2>=3.1.0
python-multipart>=0.0.6
aiofiles>=23.0.0
```

### 시스템 요구사항
- **메모리**: 최소 4GB RAM (8GB 권장)
- **저장공간**: 최소 1GB (데이터베이스 포함)
- **브라우저**: Chrome/Firefox/Safari 최신 버전

## 🤝 기여하기

1. 이 저장소를 Fork합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

### 개발 가이드라인
- **코드 스타일**: PEP 8 준수
- **문서화**: 함수별 docstring 작성
- **테스트**: 새 기능 추가시 테스트 코드 포함
- **설정**: 모든 설정은 `utils/settings.py`에 추가
- **React 컴포넌트**: ES6+ 문법 사용, 모듈화 원칙 준수

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **Google Gemini API**: AI 기반 웹 분석 기능
- **FastAPI**: 고성능 웹 프레임워크
- **React**: 사용자 인터페이스 라이브러리
- **TailwindCSS**: 유틸리티 우선 CSS 프레임워크
- **Chart.js**: 데이터 시각화 라이브러리
- **Selenium**: 브라우저 자동화
- **SQLite**: 경량 데이터베이스

## 📞 문의

- **이슈**: [GitHub Issues](https://github.com/your-username/advanced-church-crm/issues)
- **이메일**: isfs003@gmail.com
- **문서**: [프로젝트 위키](https://github.com/your-username/advanced-church-crm/wiki)

---

## 🎉 개발 현황

### ✅ 완료된 기능 (98%)
- **React 기반 프론트엔드**: 모듈화된 컴포넌트 시스템 ✅
- **서비스 레이어**: 비즈니스 로직 분리 ✅
- **API 레이어**: RESTful API 완전 문서화 ✅
- **통합 API 클래스**: 모든 API 호출 중앙 관리 ✅
- **공통 유틸리티**: 코드 재사용성 극대화 ✅
- **SQLite CRM 데이터베이스**: 218,039개 데이터 ✅
- **사용자 인증**: 세션 기반 보안 시스템 ✅
- **실시간 크롤링**: AI 기반 자동 보강 ✅
- **반응형 웹 디자인**: 모바일/데스크톱 최적화 ✅

### 🔄 진행 중 (2%)
- **SaaS 확장**: 멀티 테넌시 아키텍처
- **고급 분석**: 비즈니스 인텔리전스 기능
- **모바일 앱**: React Native 기반 모바일 앱

### 🔥 최신 개발 (2025.06.26)
- ⚛️ **React 리팩토링 완료**: 모든 페이지 React 컴포넌트화
- 🔧 **서비스/API 레이어 구축**: 아키텍처 현대화
- 📊 **데이터베이스 확장**: 218,039개 기관 데이터
- 🌐 **통합 API 시스템**: 완전한 RESTful API
- 🎯 **성능 최적화**: WAL 모드, 인덱싱, 캐싱

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

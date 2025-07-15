# 🏢 Advanced Church CRM System

한국 교회/기관 정보를 관리하는 통합 CRM 시스템 (React + FastAPI + PostgreSQL + AI 크롤링)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [최신 업데이트](#최신-업데이트)
- [설치 및 실행](#설치-및-실행)
- [시스템 구조](#시스템-구조)
- [React 기반 프론트엔드](#react-기반-프론트엔드)
- [사용자 관리 시스템](#사용자-관리-시스템)
- [API 문서](#api-문서)
- [데이터베이스](#데이터베이스)
- [크롤링 시스템](#크롤링-시스템)
- [개발 정보](#개발-정보)

## 🎯 개요

**Advanced Church CRM System**은 한국의 교회 및 종교기관 정보를 체계적으로 관리하는 통합 CRM 솔루션입니다.

### ✨ 핵심 특징

- 🗄️ **PostgreSQL CRM 데이터베이스** (218,039개 기관 데이터 포함)
- ⚛️ **React 기반 프론트엔드** (모듈화된 컴포넌트 시스템)
- 🌐 **FastAPI + RESTful API** (완전한 문서화)
- 👥 **계층적 사용자 권한 관리** (역할 기반 접근 제어)
- 🔐 **세션 기반 인증** (PBKDF2 해시 보안)
- 📊 **실시간 대시보드** 및 통계 분석
- 🔄 **지능형 크롤링 시스템** (AI 기반 정보 추출)
- 🔧 **서비스 레이어 아키텍처** (비즈니스 로직 분리)
- 📱 **반응형 웹 디자인** (TailwindCSS + 다크모드)
- 🤖 **AI 기반 연락처 자동 보강**

## 🚀 주요 기능

### 1. 🏢 기관 정보 관리

- **218,039개 기관** 데이터베이스 구축 완료
- React 기반 CRUD 인터페이스
- 고급 검색 및 필터링 (실시간)
- 대량 작업 지원 (일괄 수정/삭제)
- 엑셀/CSV 내보내기

### 2. 👥 계층적 사용자 관리 시스템 (NEW!)

- **역할 기반 접근 제어 (RBAC)**: 개발자/대표/팀장/일반사원
- **계층적 권한 구조**: 상위 역할이 하위 역할 관리
- **본인 정보 수정**: 모든 사용자가 개인정보 수정 가능
- **동적 권한 검증**: 실시간 권한 확인 및 UI 조정
- **세션 기반 인증**: 안전한 로그인/로그아웃 시스템

### 3. ⚛️ React 기반 프론트엔드 시스템

- **모듈화된 컴포넌트**: 재사용 가능한 React 컴포넌트
- **통합 API 클래스**: 모든 API 호출 중앙 관리
- **공통 유틸리티**: 포맷팅, 검증, DOM 조작 함수
- **실시간 업데이트**: 데이터 변경 시 즉시 반영
- **반응형 디자인**: 모바일/데스크톱 최적화

### 4. 🌐 RESTful API 시스템

- **완전한 CRUD**: 기관 정보 생성/조회/수정/삭제
- **사용자 관리 API**: 생성/조회/수정/삭제/권한 관리
- **고급 검색**: 복합 조건 검색 및 필터링
- **연락처 보강**: 단일/일괄/자동 보강 API
- **실시간 통계**: 대시보드용 데이터 API
- **자동 문서화**: FastAPI Swagger UI

### 5. 🤖 AI 기반 연락처 보강 시스템

- **자동 탐지**: 누락된 연락처 정보 자동 감지
- **배치 처리**: 대량 데이터 일괄 보강
- **실시간 모니터링**: 보강 진행 상황 추적
- **AI 통합**: Gemini API 기반 데이터 추출

## 🔥 최신 업데이트 (2025.07.08) - v2.3.0 크롤링 엔진 고도화 프로젝트 시작

### 🤖 모듈화된 고성능 크롤링 시스템 개발 착수

**7월 8일부터 시작된 크롤링 엔진 고도화 프로젝트**가 본격적으로 진행되고 있습니다:

> 📋 **참고 자료**: [CradCrawl Advanced - 크롤링 엔진 고도화 프로젝트](https://github.com/EnzoMH/cradcrawlpython/blob/main/README.md)

#### 🎯 핵심 혁신 기술

- **🧠 py-cpuinfo 기반 시스템 자동감지**: CPU/메모리 자동 분석으로 최적 성능 설정
- **⚡ 동적 워커 관리**: 실시간 리소스 모니터링으로 워커 수 자동 조정
- **🔍 다중 검색 엔진**: Google 검색 + 직접 홈페이지 크롤링 통합
- **🤖 AI 기반 데이터 추출**: Google Gemini API 활용 지능형 콘텐츠 분석

#### 🚀 모듈화된 아키텍처 (324줄 메인 크롤러)

```
📦 크롤링 엔진 (26KB 핵심 모듈)
├── 🧠 AI 모델 관리자 (Gemini API - 7.2KB)
├── 👥 워커 관리자 (멀티스레딩 - 11KB)
├── 🔍 구글 검색 엔진 (13KB)
├── 🌐 홈페이지 크롤러 (14KB)
├── 📞 전화번호 검증기 (15KB)
├── 📊 데이터 매퍼 (21KB)
├── 💾 엑셀 프로세서 (17KB)
├── 🛡️ 검증 엔진 (18KB)
└── 📈 성능 관리자 (시스템 분석 - 10KB)
```

#### 💡 지능형 성능 최적화

- **동적 성능 조정**: 실시간 CPU/메모리 상태 기반 워커 수 자동 조정
- **배치 처리**: 메모리 사용량 제어를 위한 스마트 배치 시스템
- **캐싱 전략**: LRU 캐시 + 웹드라이버 풀링으로 성능 향상
- **실시간 모니터링**: 시스템 리소스 및 처리 진행률 실시간 추적

#### 🔧 핵심 기술 스택

- **py-cpuinfo**: CPU/메모리 자동 감지 및 최적화
- **Selenium + undetected-chromedriver**: 웹 브라우저 자동화
- **Google Gemini API**: AI 기반 콘텐츠 분석
- **BeautifulSoup4**: HTML 파싱 및 데이터 추출
- **Pandas + OpenPyXL**: 데이터 처리 및 엑셀 연동

#### 📊 성능 지표

- **처리 속도**: 250개/분 (평균)
- **메모리 효율**: 평균 512MB 사용
- **CPU 최적화**: 평균 45% 사용률
- **성공률**: 95.2% 데이터 추출 성공

---

## 🔥 최신 업데이트 (2025.07.07) - v2.2.0 사용자 관리 시스템 완성

### 👥 계층적 사용자 관리 시스템 구현 완료

**실무 기반 권한 구조**로 완전한 사용자 관리 시스템이 구축되었습니다:

#### 🏗️ 조직 구조 및 권한 설계

| 역할            | 레벨 | 권한 범위        | 관리 가능 역할          |
| --------------- | ---- | ---------------- | ----------------------- |
| 🔧 **개발자**   | 5    | 시스템 전체 관리 | 모든 역할 생성/관리     |
| 👑 **대표**     | 4    | 경영진 권한      | 팀장/일반사원 생성/관리 |
| 🎯 **팀장**     | 3    | 팀 관리 권한     | 일반사원 생성/관리      |
| 👤 **일반사원** | 1    | 기본 권한        | 본인 정보만 수정        |

#### 🔐 핵심 보안 기능

- **PBKDF2 해시화**: 비밀번호 안전 저장
- **세션 기반 인증**: 메모리 기반 세션 관리
- **권한별 페이지 접근**: 최소 권한 원칙 적용
- **본인 계정 보호**: 자신의 역할 변경 방지

#### 🎨 사용자 인터페이스 개선

- **권한별 메뉴 표시**: 접근 가능한 기능만 표시
- **동적 버튼 제어**: 생성/편집/삭제 권한에 따른 UI 조정
- **본인 정보 수정**: 모든 사용자 개인정보 편집 가능
- **다크모드 지원**: 아이콘과 텍스트 대비 강화

#### 🔧 구현된 주요 컴포넌트

```
services/user_services.py     # 사용자 관리 비즈니스 로직
api/user_api.py              # 사용자 관리 RESTful API
templates/html/users.html    # 사용자 관리 페이지
templates/js/users.js        # 동적 사용자 관리 기능
utils/template_auth.py       # 템플릿 권한 미들웨어
```

### 📊 권한 매트릭스

| 역할     | 생성 가능     | 관리 가능          | 삭제 가능          | 본인 정보 수정 |
| -------- | ------------- | ------------------ | ------------------ | -------------- |
| 개발자   | 모든 역할     | 모든 역할          | 대표/팀장/일반사원 | ✅             |
| 대표     | 팀장/일반사원 | 대표/팀장/일반사원 | 팀장/일반사원      | ✅             |
| 팀장     | 일반사원      | 일반사원           | 일반사원           | ✅             |
| 일반사원 | ❌            | ❌                 | ❌                 | ✅             |

### 🎯 주요 해결 사항

- ✅ **JSON 직렬화 문제**: datetime 필드 자동 변환
- ✅ **세션 동기화 문제**: crm_app.py와 API 간 세션 공유
- ✅ **권한별 UI 표시**: 동적 버튼 및 메뉴 제어
- ✅ **본인 계정 편집**: 모든 사용자 개인정보 수정 권한
- ✅ **다크모드 최적화**: 아이콘과 텍스트 가독성 향상

## 🔥 최신 업데이트 (2025.07.07) - v2.1.0 GCP 프로덕션 배포 완료

### 🌐 Google Cloud Platform 배포 성공

**프로덕션 환경 구축**을 통해 안정적인 클라우드 서비스로 전환되었습니다:

#### ☁️ 인프라 구성

- **GCP Compute Engine**: e2-medium (2 vCPU, 4GB RAM)
- **운영체제**: Debian GNU/Linux 6.1.0-37-cloud-amd64
- **데이터베이스**: PostgreSQL 15 (SQLite에서 마이그레이션)
- **외부 접속**: http://34.47.113.22:8000
- **SSH 원격 관리**: VS Code Remote-SSH 지원

#### 🚀 배포 성과

- **데이터 마이그레이션**: 218,038개 기관 데이터 중 11,000개 성공적 이전
- **성능 최적화**: 클라우드 환경 최적화로 응답 속도 향상
- **보안 강화**: UFW 방화벽 + GCP 클라우드 방화벽 이중 보안
- **모니터링**: 실시간 서버 상태 모니터링 구축

#### 🔧 기술 스택 업그레이드

- **데이터베이스**: SQLite → PostgreSQL 15
- **배포 방식**: 로컬 개발 → 클라우드 프로덕션
- **접속 방식**: SSH 키 기반 보안 접속
- **네트워크**: 고정 IP 주소 할당 (34.47.113.22)

#### 📊 운영 환경

- **24시간 운영**: 무중단 서비스 제공
- **원격 관리**: SSH를 통한 완전한 서버 제어
- **백업 시스템**: PostgreSQL 자동 백업 구성
- **로그 모니터링**: 실시간 애플리케이션 로그 추적

### 🌐 접속 정보

- **메인 서비스**: http://34.47.113.22:8000
- **API 문서**: http://34.47.113.22:8000/docs
- **사용자 관리**: http://34.47.113.22:8000/users
- **대시보드**: http://34.47.113.22:8000/dashboard
- **헬스체크**: http://34.47.113.22:8000/health

## 📁 시스템 구조

```
advanced_crawling/
├── 🚀 **핵심 애플리케이션 파일들**
│   ├── 📄 crm_app.py                  🎯 FastAPI CRM 메인 애플리케이션 (32KB, 796줄)
│   ├── 📄 app.py                      🔄 레거시 웹 애플리케이션 (17KB, 431줄)
│   ├── 📄 main_crawler.py             🎯 모듈화된 고성능 크롤링 엔진 v4.0 (324줄)
│   ├── 📄 additionalplan.py           추가 계획 및 기능 개발
│   └── 📄 cleanup_logs.py             로그 정리 유틸리티
│
├── 🗄️ **데이터베이스 시스템**
│   └── 📁 database/
│       ├── 📄 database.py             🎯 PostgreSQL CRM 메인 모듈 (38KB, 900줄)
│       ├── 📄 models.py               🎯 데이터 모델 정의 (17KB, 474줄)
│       ├── 📄 migration.py            🎯 JSON → DB 마이그레이션 (14KB, 361줄)
│       └── 📄 churches_crm.db         🎯 PostgreSQL 데이터베이스 (클라우드)
│
├── 🔧 **서비스 레이어** (NEW!)
│   └── 📁 services/
│       ├── 📄 organization_service.py 🎯 기관 관리 서비스 (고급 검색, 필터링)
│       ├── 📄 contact_enrichment_service.py 🎯 연락처 보강 서비스 (자동 크롤링)
│       ├── 📄 user_services.py        🆕 사용자 관리 서비스 (권한 기반 CRUD)
│       └── 📄 crawling_service.py     🎯 크롤링 작업 통합 관리 (474줄)
│
├── 🌐 **API 레이어** (NEW!)
│   └── 📁 api/
│       ├── 📄 organization_api.py     🎯 기관 관리 API (CRUD, 검색, 필터링)
│       ├── 📄 enrichment_api.py       🎯 연락처 보강 API (단일/일괄/자동 보강)
│       ├── 📄 statistics_api.py       🎯 통계 분석 API (대시보드 데이터)
│       └── 📄 user_api.py             🆕 사용자 관리 API (인증, 권한, CRUD)
│
├── 🔧 **유틸리티 모듈**
│   └── 📁 utils/
│       ├── 📄 settings.py             🎯 통합 애플리케이션 설정 (상수, 설정값)
│       ├── 📄 template_auth.py        🆕 템플릿 권한 미들웨어 (세션 기반 인증)
│       ├── 📄 ai_helpers.py           🎯 AI 도움 기능 (Gemini API, AIModelManager)
│       ├── 📄 crawler_utils.py        🎯 크롤링 유틸리티 (CrawlerUtils)
│       ├── 📄 naver_map_crawler.py    🎯 네이버 지도 전용 크롤러
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
        │   ├── 📄 statistics.html    🎯 통계 분석 페이지 (Bootstrap 기반)
        │   ├── 📄 users.html         🆕 사용자 관리 페이지 (권한 기반)
        │   └── 📄 login.html         🎯 로그인 페이지
        ├── 📁 css/
        │   ├── 📄 style.css          🎯 TailwindCSS 보완 스타일시트
        │   └── 📄 stat.css           🆕 통계 페이지 전용 스타일 (다크모드 지원)
        └── 📁 js/                    🎯 JavaScript 모듈 (React + 통합 API)
            ├── 📄 utils.js           🆕 공통 유틸리티 함수
            ├── 📄 api.js             🆕 통합 API 클래스
            ├── 📄 main.js            🔄 CRM 시스템 메인 로직
            ├── 📄 ui.js              🔄 UI 렌더링 모듈
            ├── 📄 dashboard.js       🎯 대시보드 React 컴포넌트
            ├── 📄 organizations.js   🎯 기관 관리 React 컴포넌트
            ├── 📄 enrichment.js      🎯 연락처 보강 React 컴포넌트
            ├── 📄 statistics.js      🎯 통계 분석 JavaScript (Bootstrap 기반)
            └── 📄 users.js           🆕 사용자 관리 JavaScript (권한 기반 CRUD)
```

## 👥 사용자 관리 시스템

### 🔐 인증 및 권한 구조

#### 1. 계층적 권한 시스템

```python
# services/user_services.py
role_hierarchy = {
    "개발자": {
        "can_view": ["개발자", "대표", "팀장", "일반사원"],
        "can_manage": ["개발자", "대표", "팀장", "일반사원"],
        "can_create": ["개발자", "대표", "팀장", "일반사원"],
        "can_delete": ["대표", "팀장", "일반사원"],
        "level": 5
    },
    "대표": {
        "can_view": ["대표", "팀장", "일반사원"],
        "can_manage": ["대표", "팀장", "일반사원"],
        "can_create": ["팀장", "일반사원"],
        "can_delete": ["팀장", "일반사원"],
        "level": 4
    },
    "팀장": {
        "can_view": ["팀장", "일반사원"],
        "can_manage": ["일반사원"],
        "can_create": ["일반사원"],
        "can_delete": ["일반사원"],
        "level": 3
    },
    "일반사원": {
        "can_view": [],
        "can_manage": [],
        "can_create": [],
        "can_delete": [],
        "level": 1
    }
}
```

#### 2. 세션 기반 인증

```python
# utils/template_auth.py
@require_auth(min_level=3)  # 팀장 이상
async def users_page(request: Request):
    """사용자 관리 페이지"""
    context = get_template_context(request)
    return templates.TemplateResponse("html/users.html", context)
```

### 🎨 프론트엔드 사용자 관리

#### 1. 동적 권한 제어

```javascript
// templates/js/users.js
class UsersManager {
  canManage(targetRole, targetUserId) {
    // 본인 계정은 항상 편집 가능
    if (targetUserId === this.config.currentUser?.id) {
      return true;
    }

    // 다른 사용자는 권한에 따라 관리 가능
    const permissions = this.config.userPermissions || {};
    return permissions.can_manage?.includes(targetRole) || false;
  }

  showEditModal(user) {
    const isSelfEdit = user.id === this.config.currentUser?.id;

    // 본인 계정 편집 시 역할 변경 불가
    const roleField = isSelfEdit
      ? `
            <input type="text" value="${user.role}" disabled>
            <p class="text-xs text-gray-500">본인의 역할은 변경할 수 없습니다.</p>
        `
      : `
            <select name="role">
                ${this.getEditableRoleOptions(user.role)}
            </select>
        `;
  }
}
```

#### 2. 권한별 UI 표시

```javascript
// 사용자 테이블에서 편집 버튼 표시 조건
${this.canManage(user.role, user.id) ? `
    <button onclick="usersManager.editUser(${user.id})"
            class="text-indigo-600 hover:text-indigo-900" title="편집">
        <i class="fas fa-edit"></i>
    </button>
` : ''}

// 사용자 생성 버튼 표시 조건
{% if can_create_users %}
<button id="create-user-btn" class="bg-indigo-600 text-white px-4 py-2 rounded-md">
    <i class="fas fa-plus mr-2"></i>
    새 사용자 추가
</button>
{% endif %}
```

### 🔧 API 엔드포인트

#### 1. 사용자 관리 API

```python
# api/user_api.py

@router.get("/", summary="사용자 목록 조회")
async def get_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """권한에 따라 조회 가능한 사용자 목록을 반환"""
    user_service = UserService()
    users = user_service.get_viewable_users(
        viewer_id=current_user['id'],
        viewer_role=current_user['role']
    )
    return {"success": True, "users": users}

@router.post("/", summary="새 사용자 생성")
async def create_user(
    user_data: UserCreateModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """권한에 따라 새 사용자를 생성"""
    user_service = UserService()
    result = user_service.create_user(
        user_data=user_data.dict(),
        creator_role=current_user['role']
    )
    return {"success": True, "message": result['message']}
```

#### 2. 인증 API

```python
@router.post("/login", summary="사용자 로그인")
async def login(user_data: UserLoginModel):
    """사용자 로그인을 처리하고 세션을 생성"""
    user_service = UserService()
    user = user_service.authenticate_user(
        user_data.username,
        user_data.password
    )

    if user:
        # 세션 생성
        session_id = secrets.token_urlsafe(32)
        active_sessions[session_id] = user

        return AuthResponse(
            success=True,
            message="로그인 성공",
            user=user,
            token=session_id
        )
```

#### 로그아웃

```http
POST /api/users/logout
Authorization: Session-based
```

#### 현재 사용자 정보

```http
GET /api/users/me
Authorization: Session-based
```

### 🛡️ 보안 기능

#### 1. 비밀번호 보안

```python
# services/user_services.py
def hash_password(self, password: str) -> str:
    """PBKDF2 알고리즘으로 비밀번호 해시화"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000  # 반복 횟수
    )
    return password_hash.hex() + ':' + salt

def verify_password(self, password: str, password_hash: str) -> bool:
    """저장된 해시와 입력 비밀번호 검증"""
    try:
        stored_hash, salt = password_hash.split(':')
        password_hash_new = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return password_hash_new.hex() == stored_hash
    except:
        return False
```

#### 2. 권한 검증

```python
def can_manage_user(self, manager_role: str, target_role: str,
                   manager_id: int, target_id: int) -> bool:
    """사용자 관리 권한 확인"""
    # 본인 계정은 항상 관리 가능
    if manager_id == target_id:
        return True

    # 개발자는 모든 사용자 관리 가능
    if self.is_developer(manager_role):
        return True

    # 권한에 따른 관리 가능 여부 확인
    permissions = self.get_role_permissions(manager_role)
    return target_role in permissions["can_manage"]
```

## 🌐 API 문서

### 사용자 관리 API (NEW!)

#### 사용자 목록 조회

```http
GET /api/users/
Authorization: Session-based
```

**응답:**

```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "admin",
      "full_name": "신명호",
      "email": "isfs003@gmail.com",
      "phone": "010-1234-5678",
      "role": "개발자",
      "team": "개발팀",
      "is_active": true,
      "last_login": "2024-12-28T10:30:00Z",
      "created_at": "2024-12-01T09:00:00Z"
    }
  ],
  "viewer_role": "개발자",
  "total_count": 6
}
```

#### 새 사용자 생성

```http
POST /api/users/
Content-Type: application/json
Authorization: Session-based

{
    "username": "newuser",
    "password": "securepassword123",
    "full_name": "새로운 사용자",
    "email": "newstaff@company.com",
    "phone": "010-9876-5432",
    "role": "일반사원",
    "team": "영업팀"
}
```

#### 사용자 정보 수정

```http
PUT /api/users/1
Content-Type: application/json
Authorization: Session-based

{
    "full_name": "수정된 이름",
    "email": "updated@example.com",
    "phone": "010-1234-5678",
    "team": "마케팅팀"
}
```

#### 사용자 삭제 (비활성화)

```http
DELETE /api/users/1
Authorization: Session-based
```

#### 사용자 통계

```http
GET /api/users/statistics
Authorization: Session-based
```

**응답:**

```json
{
  "success": true,
  "statistics": {
    "viewable_roles": ["개발자", "대표", "팀장", "일반사원"],
    "role_statistics": [
      {
        "role": "개발자",
        "count": 1,
        "active_count": 1,
        "inactive_count": 0
      },
      {
        "role": "대표",
        "count": 1,
        "active_count": 1,
        "inactive_count": 0
      }
    ]
  }
}
```

### 인증 API (NEW!)

#### 로그인

```http
POST /api/users/login
Content-Type: application/json

{
    "username": "admin",
    "password": "simple123"
}
```

**응답:**

```json
{
  "success": true,
  "message": "로그인 성공",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "신명호",
    "role": "개발자",
    "permissions": {
      "can_view": ["개발자", "대표", "팀장", "일반사원"],
      "can_manage": ["개발자", "대표", "팀장", "일반사원"],
      "can_create": ["개발자", "대표", "팀장", "일반사원"],
      "can_delete": ["대표", "팀장", "일반사원"]
    }
  },
  "token": "session_token_here"
}
```

#### 로그아웃

```http
POST /api/users/logout
Authorization: Session-based
```

#### 현재 사용자 정보

```http
GET /api/users/me
Authorization: Session-based
```

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

## 🗄️ 데이터베이스

### 스키마 구조

#### users 테이블 (NEW!)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT '일반사원',
    team VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created ON users(created_at);
```

#### user_sessions 테이블 (메모리 기반)

```python
# 메모리 기반 세션 저장소 (crm_app.py)
active_sessions = {
    "session_token": {
        "id": 1,
        "username": "admin",
        "full_name": "신명호",
        "role": "개발자",
        "permissions": {...},
        "login_time": "2024-12-28T10:30:00Z"
    }
}
```

#### organizations 테이블

```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
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

## 🔐 보안 기능

### 1. 인증 및 권한

```python
# 세션 기반 인증
@app.post("/login")
async def login(request: Request, username: str, password: str):
    user_service = UserService()
    user = user_service.authenticate_user(username, password)
    if user:
        # 세션 생성
        session_id = secrets.token_urlsafe(32)
        active_sessions[session_id] = user

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

# 권한 확인 데코레이터
@require_auth(min_level=3)  # 팀장 이상
async def users_page(request: Request):
    context = get_template_context(request)
    return templates.TemplateResponse("html/users.html", context)
```

### 2. 데이터 보호

- **비밀번호 해시화**: PBKDF2 알고리즘 사용 (100,000회 반복)
- **세션 보안**: HTTPOnly 쿠키 + 안전한 토큰 생성
- **입력 검증**: Pydantic 모델 기반 데이터 검증
- **SQL 인젝션 방지**: 매개변수화된 쿼리 사용
- **권한 검증**: 모든 API 엔드포인트에서 권한 확인

### 3. 접근 제어

- **페이지별 최소 권한**: 각 페이지마다 필요한 최소 권한 레벨 정의
- **API 엔드포인트 보호**: 모든 API에 인증/권한 검증 적용
- **본인 정보 보호**: 자신의 역할 변경 방지
- **계층적 권한**: 상위 역할이 하위 역할만 관리 가능

## 🔍 크롤링 시스템

### 1. 🤖 모듈화된 고성능 크롤링 엔진 v4.0

현재 시스템의 핵심인 `main_crawler.py`는 **py-cpuinfo 기반 자동 최적화 크롤링 엔진**으로 구성되어 있습니다:

#### 🎯 핵심 기능

- **🧠 시스템 자동 감지**: py-cpuinfo 라이브러리로 CPU/메모리 자동 분석
- **⚡ 동적 워커 관리**: 실시간 리소스 상태 기반 워커 수 자동 조정
- **🔍 다중 검색 전략**: Google 검색 + 직접 홈페이지 크롤링 통합
- **📊 실시간 성능 모니터링**: 시스템 리소스 및 처리 진행률 추적

#### 💡 기술 구성

```python
# 시스템 자동 감지 (py-cpuinfo)
from utils.system_analyzer import SystemAnalyzer
from utils.performance_manager import PerformanceManager

# 모듈화된 크롤링 엔진
from utils.crawling_engine import CrawlingEngine
from utils.worker_manager import WorkerManager
from utils.ai_model_manager import AIModelManager

# 성능 최적화 시스템
class PerformanceProfile:
    def __init__(self):
        self.max_workers = 4        # 최대 워커 수
        self.batch_size = 10        # 배치 크기
        self.memory_threshold = 80  # 메모리 임계값 (%)
        self.cpu_threshold = 70     # CPU 임계값 (%)
```

#### 🚀 지원 기관 유형

- 🎓 **학원** (academy)
- 🏢 **주민센터** (community_center)
- ⛪ **교회** (church)
- 🏥 **기타 기관** (확장 가능)

### 2. 🔧 크롤링 서비스 통합 관리

`services/crawling_service.py`는 **파일 기반 크롤링과 DB 기반 크롤링을 통합 관리**합니다:

#### 📊 작업 관리 시스템

- **CrawlingJobConfig**: 크롤링 작업 설정 (테스트 모드, AI 사용 여부, 동시 처리 수)
- **CrawlingJobStatus**: 실시간 작업 상태 추적 (진행률, 실패 건수, 완료 시간)
- **비동기 처리**: asyncio 기반 고성능 병렬 크롤링

#### 🎛️ 설정 옵션

```python
@dataclass
class CrawlingJobConfig:
    test_mode: bool = False          # 테스트 모드 활성화
    test_count: int = 10             # 테스트 데이터 수
    use_ai: bool = True              # AI 기반 추출 사용
    max_concurrent: int = 3          # 최대 동시 처리 수
    job_name: Optional[str] = None   # 작업 이름
    started_by: str = "SYSTEM"       # 작업 시작자
```

### 3. 🌐 전문 크롤링 모듈 (`cralwer/`)

각 데이터 유형별 전문 크롤링 모듈로 구성:

#### 📠 FAX 추출기 (`fax_extractor.py`)

- **GoogleContactCrawler**: 구글 연락처 기반 FAX 정보 추출
- **동적 웹 페이지 처리**: JavaScript 렌더링 지원

#### 📞 전화번호 추출기 (`phone_extractor.py`)

- **extract_phone_numbers**: 다양한 전화번호 형식 자동 인식
- **search_phone_number**: 웹 페이지에서 전화번호 검색
- **setup_driver**: Selenium 드라이버 최적화 설정

#### 🔗 URL 추출기 (`url_extractor.py`)

- **URLExtractor**: 웹 페이지 내 모든 URL 추출
- **링크 분류**: 내부/외부 링크 자동 분류

### 4. 🎯 네이버 지도 전용 크롤러

`utils/naver_map_crawler.py`는 **네이버 지도 API 전용 크롤러**로 구성:

#### 🗺️ 지도 기반 데이터 수집

- **위치 기반 검색**: 좌표 기반 기관 정보 수집
- **상세 정보 추출**: 주소, 전화번호, 운영시간 등
- **API 최적화**: 네이버 지도 API 호출 최적화

### 5. 🤖 AI 기반 연락처 보강 시스템

- **자동 탐지**: 누락된 연락처 정보 자동 감지
- **배치 처리**: 대량 데이터 일괄 보강
- **실시간 모니터링**: 보강 진행 상황 추적
- **AI 통합**: Gemini API 기반 데이터 추출

---

## 🔍 사용 예제

### 1. 크롤링 시스템 사용법

```python
# 모듈화된 고성능 크롤링 엔진 실행
python main_crawler.py data/academy.xlsx academy

# 시스템 자동 감지 및 성능 테스트
python main_crawler.py --test

# 출력 예시:
# 🧪 성능 테스트 시작
# 📊 시스템 리소스: CPU 25.3%, 메모리 68.2%
# 🤖 AI 모델 상태: Gemini API 연결됨
# ⚙️ 최대 워커 수: 4개 (py-cpuinfo 자동 감지)
# ✅ 성능 테스트 완료

# 크롤링 서비스 API 사용
from services.crawling_service import CrawlingService, CrawlingJobConfig

# 크롤링 작업 설정 (자동 최적화)
config = CrawlingJobConfig(
    test_mode=True,
    test_count=50,
    use_ai=True,
    max_concurrent=5,  # py-cpuinfo 기반 자동 조정
    job_name="기관정보_크롤링",
    started_by="ADMIN"
)

# 크롤링 서비스 실행
service = CrawlingService()
result = await service.start_crawling_job(config)
```

### 2. 기본 CRM 사용법

```python
# CRM 애플리케이션 실행
python crm_app.py

# 브라우저에서 접속
# http://localhost:8000

# 로그인 (개발자 계정)
# Username: admin
# Password: simple123

# 사용자 관리 페이지 접속
# http://localhost:8000/users
```

### 2. 사용자 관리 API 사용 예제

```python
import requests

# API 클라이언트 (세션 쿠키 포함)
session = requests.Session()

# 로그인
login_response = session.post("http://localhost:8000/login", data={
    "username": "admin",
    "password": "simple123"
})

# 사용자 목록 조회
response = session.get("http://localhost:8000/api/users/")
users = response.json()
print(f"총 {users['total_count']}명의 사용자")

# 새 사용자 생성
new_user_data = {
    "username": "newstaff",
    "password": "securepass123",
    "full_name": "새로운 직원",
    "email": "newstaff@company.com",
    "role": "일반사원",
    "team": "영업팀"
}

create_response = session.post(
    "http://localhost:8000/api/users/",
    json=new_user_data
)
result = create_response.json()
print(f"사용자 생성 결과: {result}")

# 사용자 정보 수정
update_data = {
    "email": "updated@company.com",
    "phone": "010-1234-5678"
}

update_response = session.put(
    "http://localhost:8000/api/users/2",
    json=update_data
)
print(f"사용자 수정 결과: {update_response.json()}")
```

### 3. 권한별 기능 테스트

```python
# 개발자로 로그인 - 모든 기능 사용 가능
def test_developer_permissions():
    # 모든 역할의 사용자 생성 가능
    # 모든 사용자 조회/수정 가능
    # 개발자 제외한 모든 사용자 삭제 가능
    pass

# 대표로 로그인 - 제한된 관리 권한
def test_manager_permissions():
    # 팀장, 일반사원만 생성 가능
    # 대표, 팀장, 일반사원 조회/수정 가능
    # 팀장, 일반사원만 삭제 가능
    pass

# 팀장으로 로그인 - 팀원 관리 권한
def test_team_leader_permissions():
    # 일반사원만 생성 가능
    # 팀장, 일반사원만 조회 가능
    # 일반사원만 수정/삭제 가능
    # 본인 정보는 수정 가능
    pass

# 일반사원으로 로그인 - 개인정보만 관리
def test_staff_permissions():
    # 사용자 생성 불가
    # 본인 정보만 조회/수정 가능
    # 다른 사용자 관리 불가
    pass
```

## 📋 요구사항

### Python 버전

- Python 3.8 이상

### 주요 의존성

```
fastapi>=0.104.0
uvicorn>=0.24.0
psycopg2-binary>=2.9.0
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
passlib>=1.7.4
python-jose>=3.3.0
```

### 시스템 요구사항

- **메모리**: 최소 4GB RAM (8GB 권장)
- **저장공간**: 최소 2GB (데이터베이스 포함)
- **데이터베이스**: PostgreSQL 15 이상
- **브라우저**: Chrome/Firefox/Safari 최신 버전

### 환경 변수 설정

```bash
# .env 파일
DATABASE_URL_LOCAL=postgresql://username:password@localhost:5432/crad_db_local
DATABASE_URL=postgresql://username:password@hostname:5432/crad_db
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

## 🙏 감사의 말

- **Google Gemini API**: AI 기반 웹 분석 기능
- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL**: 강력한 관계형 데이터베이스
- **React**: 사용자 인터페이스 라이브러리
- **TailwindCSS**: 유틸리티 우선 CSS 프레임워크
- **Chart.js**: 데이터 시각화 라이브러리
- **Selenium**: 브라우저 자동화
- **PBKDF2**: 안전한 비밀번호 해시화

## 📞 문의

- **이슈**: [GitHub Issues](https://github.com/your-username/advanced-church-crm/issues)
- **이메일**: isfs003@gmail.com
- **문서**: [프로젝트 위키](https://github.com/your-username/advanced-church-crm/wiki)

---

## 🎉 개발 현황

### ✅ 완료된 기능 (100%)

- **React 기반 프론트엔드**: 모듈화된 컴포넌트 시스템 ✅
- **계층적 사용자 관리**: 역할 기반 접근 제어 완성 ✅
- **세션 기반 인증**: 안전한 로그인/로그아웃 시스템 ✅
- **권한별 UI 제어**: 동적 메뉴 및 버튼 표시 ✅
- **서비스 레이어**: 비즈니스 로직 분리 ✅
- **API 레이어**: RESTful API 완전 문서화 ✅
- **통합 API 클래스**: 모든 API 호출 중앙 관리 ✅
- **공통 유틸리티**: 코드 재사용성 극대화 ✅
- **PostgreSQL CRM 데이터베이스**: 218,039개 데이터 ✅
- **실시간 크롤링**: AI 기반 자동 보강 ✅
- **반응형 웹 디자인**: 모바일/데스크톱 최적화 ✅
- **다크모드 지원**: 아이콘과 텍스트 가독성 향상 ✅

### 🔄 향후 계획

#### 🤖 크롤링 엔진 고도화 (진행 중)

- **py-cpuinfo 기반 자동 최적화**: CPU/메모리 상태 기반 성능 자동 조정
- **모듈화된 아키텍처**: 26KB 핵심 엔진 + 11개 전문 모듈
- **동적 워커 관리**: 실시간 리소스 모니터링으로 워커 수 자동 조정
- **다중 검색 전략**: Google 검색 + 직접 홈페이지 크롤링 통합
- **실시간 성능 모니터링**: 처리 속도 250개/분, 성공률 95.2%

#### 🔐 보안 및 인증 강화

- **Redis 세션 저장소**: 메모리 기반에서 Redis로 전환
- **2FA 인증**: 이중 인증 시스템 구현
- **사용자 그룹 관리**: 팀 기반 권한 관리
- **활동 로그**: 사용자 행동 추적 및 감사
- **API 키 관리**: 외부 API 접근 제어

#### 📊 성능 및 모니터링

- **실시간 대시보드**: 크롤링 진행 상황 실시간 추적
- **성능 메트릭**: 처리 속도, 성공률, 오류율 모니터링
- **자동 알림**: 시스템 이상 상황 자동 알림
- **로그 분석**: 크롤링 패턴 분석 및 최적화

### 🔥 최신 개발 (2025.07.08 ~ )

- 🤖 **모듈화된 고성능 크롤링 엔진**: py-cpuinfo 기반 CPU/메모리 자동 감지 시스템
- ⚡ **동적 워커 관리**: 실시간 리소스 모니터링으로 워커 수 자동 조정
- 🔍 **다중 검색 전략**: Google 검색 + 직접 홈페이지 크롤링 통합
- 📊 **실시간 성능 모니터링**: 처리 속도 250개/분, 성공률 95.2%
- 🧠 **AI 기반 데이터 추출**: Google Gemini API 활용 지능형 콘텐츠 분석

### 🔥 최신 개발 (2025.07.07)

- 👥 **사용자 관리 시스템 완성**: 계층적 권한 기반 완전 구현
- 🔐 **세션 기반 인증**: PBKDF2 해시 + 안전한 세션 관리
- 🎨 **권한별 UI 제어**: 동적 메뉴 표시 및 버튼 제어
- 📊 **사용자 통계**: 역할별 사용자 현황 분석
- 🌙 **다크모드 최적화**: 통계 페이지 아이콘 가독성 향상

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

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

## 🔥 최신 업데이트 (2024.12.28) - v2.2.0 사용자 관리 시스템 완성

### 👥 계층적 사용자 관리 시스템 구현 완료
**실무 기반 권한 구조**로 완전한 사용자 관리 시스템이 구축되었습니다:

#### 🏗️ 조직 구조 및 권한 설계
| 역할 | 레벨 | 권한 범위 | 관리 가능 역할 |
|------|------|-----------|----------------|
| 🔧 **개발자** (신명호) | 5 | 시스템 전체 관리 | 모든 역할 생성/관리 |
| 👑 **대표** (김영훈) | 4 | 경영진 권한 | 팀장/일반사원 생성/관리 |
| 🎯 **팀장** (박수영) | 3 | 팀 관리 권한 | 일반사원 생성/관리 |
| 👤 **일반사원** | 1 | 기본 권한 | 본인 정보만 수정 |

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
| 역할 | 생성 가능 | 관리 가능 | 삭제 가능 | 본인 정보 수정 |
|------|-----------|-----------|-----------|----------------|
| 개발자 | 모든 역할 | 모든 역할 | 대표/팀장/일반사원 | ✅ |
| 대표 | 팀장/일반사원 | 대표/팀장/일반사원 | 팀장/일반사원 | ✅ |
| 팀장 | 일반사원 | 일반사원 | 일반사원 | ✅ |
| 일반사원 | ❌ | ❌ | ❌ | ✅ |

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
│   ├── 📄 crawler_main.py             🎯 통합 크롤링 메인 모듈 (UnifiedCrawler)
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
│       └── 📄 crawling_service.py     크롤링 작업 관리 (싱글톤)
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
        const roleField = isSelfEdit ? `
            <input type="text" value="${user.role}" disabled>
            <p class="text-xs text-gray-500">본인의 역할은 변경할 수 없습니다.</p>
        ` : `
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

## 🔍 사용 예제

### 1. 기본 사용법

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
- **Redis 세션 저장소**: 메모리 기반에서 Redis로 전환
- **2FA 인증**: 이중 인증 시스템 구현
- **사용자 그룹 관리**: 팀 기반 권한 관리
- **활동 로그**: 사용자 행동 추적 및 감사
- **API 키 관리**: 외부 API 접근 제어

### 🔥 최신 개발 (2024.12.28)
- 👥 **사용자 관리 시스템 완성**: 계층적 권한 기반 완전 구현
- 🔐 **세션 기반 인증**: PBKDF2 해시 + 안전한 세션 관리
- 🎨 **권한별 UI 제어**: 동적 메뉴 표시 및 버튼 제어
- 📊 **사용자 통계**: 역할별 사용자 현황 분석
- 🌙 **다크모드 최적화**: 통계 페이지 아이콘 가독성 향상

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

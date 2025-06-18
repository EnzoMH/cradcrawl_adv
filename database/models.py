#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM 시스템 데이터 모델 정의
타입 힌트, 데이터 검증, 비즈니스 로직 포함
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import re
import json

# ==================== Enums ====================

class UserRole(Enum):
    """사용자 권한 레벨"""
    ADMIN1 = "대표"          # 모든 권한
    ADMIN2 = "팀장"          # 팀 관리 + 모든 데이터 접근  
    SALES = "영업"           # 담당 데이터만 편집
    DEVELOPER = "개발자"      # 시스템 관리

class OrganizationType(Enum):
    """기관 유형"""
    CHURCH = "교회"
    ACADEMY = "학원"
    PUBLIC = "공공기관"
    SCHOOL = "학교"

class ContactStatus(Enum):
    """영업 상태"""
    NEW = "신규"
    CONTACTED = "접촉완료"
    INTERESTED = "관심있음"
    NEGOTIATING = "협상중"
    CLOSED_WON = "성사"
    CLOSED_LOST = "실패"
    FOLLOW_UP = "후속조치"

class Priority(Enum):
    """우선순위"""
    HIGH = "높음"
    MEDIUM = "보통"
    LOW = "낮음"

class ActivityType(Enum):
    """활동 유형"""
    CALL = "전화"
    EMAIL = "이메일"
    MEETING = "미팅"
    VISIT = "방문"
    NOTE = "메모"

class CrawlingStatus(Enum):
    """크롤링 상태"""
    RUNNING = "진행중"
    COMPLETED = "완료"
    STOPPED = "중단"
    ERROR = "오류"

# ==================== 유틸리티 함수 ====================

def validate_phone(phone: str) -> bool:
    """전화번호 형식 검증"""
    if not phone:
        return True  # 빈 값은 허용
    
    # 한국 전화번호 형식: 02-1234-5678, 031-123-4567, 010-1234-5678
    phone_pattern = r'^(\d{2,3})-(\d{3,4})-(\d{4})$'
    return bool(re.match(phone_pattern, phone.strip()))

def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    if not email:
        return True  # 빈 값은 허용
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))

def validate_homepage(homepage: str) -> bool:
    """홈페이지 URL 형식 검증"""
    if not homepage:
        return True  # 빈 값은 허용
    
    url_pattern = r'^https?://.+'
    return bool(re.match(url_pattern, homepage.strip()))

# ==================== 데이터 모델 클래스 ====================

@dataclass
class User:
    """사용자 데이터 모델"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = UserRole.SALES.value
    team: str = ""
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.username:
            raise ValueError("사용자명은 필수입니다")
        if not self.full_name:
            raise ValueError("실명은 필수입니다")
        if self.email and not validate_email(self.email):
            raise ValueError("이메일 형식이 올바르지 않습니다")
        if self.phone and not validate_phone(self.phone):
            raise ValueError("전화번호 형식이 올바르지 않습니다")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'team': self.team,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class Organization:
    """기관/조직 데이터 모델"""
    # 기본 정보
    id: Optional[int] = None
    name: str = ""
    type: str = OrganizationType.CHURCH.value
    category: str = "종교시설"
    
    # 연락처 정보
    homepage: str = ""
    phone: str = ""
    fax: str = ""
    email: str = ""
    mobile: str = ""
    postal_code: str = ""
    address: str = ""
    
    # 상세 정보
    organization_size: str = ""
    founding_year: Optional[int] = None
    member_count: Optional[int] = None
    denomination: str = ""  # 교단, 계열
    
    # CRM 정보
    contact_status: str = ContactStatus.NEW.value
    priority: str = Priority.MEDIUM.value
    assigned_to: str = ""
    lead_source: str = "DATABASE"
    estimated_value: int = 0
    
    # 영업 노트
    sales_notes: str = ""
    internal_notes: str = ""
    last_contact_date: Optional[date] = None
    next_follow_up_date: Optional[date] = None
    
    # 크롤링 데이터
    crawling_data: Dict[str, Any] = field(default_factory=dict)
    
    # 시스템 필드
    created_by: str = ""
    updated_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.name.strip():
            raise ValueError("기관명은 필수입니다")
        if self.email and not validate_email(self.email):
            raise ValueError("이메일 형식이 올바르지 않습니다")
        if self.phone and not validate_phone(self.phone):
            raise ValueError("전화번호 형식이 올바르지 않습니다")
        if self.homepage and not validate_homepage(self.homepage):
            raise ValueError("홈페이지 URL 형식이 올바르지 않습니다")
        if self.founding_year and (self.founding_year < 1800 or self.founding_year > datetime.now().year):
            raise ValueError("설립연도가 올바르지 않습니다")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'homepage': self.homepage,
            'phone': self.phone,
            'fax': self.fax,
            'email': self.email,
            'mobile': self.mobile,
            'postal_code': self.postal_code,
            'address': self.address,
            'organization_size': self.organization_size,
            'founding_year': self.founding_year,
            'member_count': self.member_count,
            'denomination': self.denomination,
            'contact_status': self.contact_status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'lead_source': self.lead_source,
            'estimated_value': self.estimated_value,
            'sales_notes': self.sales_notes,
            'internal_notes': self.internal_notes,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_follow_up_date': self.next_follow_up_date.isoformat() if self.next_follow_up_date else None,
            'crawling_data': self.crawling_data,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Organization':
        """딕셔너리에서 객체 생성"""
        # 날짜 필드 변환
        if isinstance(data.get('last_contact_date'), str):
            data['last_contact_date'] = datetime.fromisoformat(data['last_contact_date']).date()
        if isinstance(data.get('next_follow_up_date'), str):
            data['next_follow_up_date'] = datetime.fromisoformat(data['next_follow_up_date']).date()
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # JSON 문자열을 dict로 변환
        if isinstance(data.get('crawling_data'), str):
            try:
                data['crawling_data'] = json.loads(data['crawling_data'])
            except:
                data['crawling_data'] = {}
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class ContactActivity:
    """영업 활동 데이터 모델"""
    id: Optional[int] = None
    organization_id: int = 0
    activity_type: str = ActivityType.NOTE.value
    subject: str = ""
    description: str = ""
    contact_person: str = ""
    contact_method: str = ""
    result: str = ""
    next_action: str = ""
    created_by: str = ""
    created_at: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_completed: bool = False
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.subject.strip():
            raise ValueError("활동 제목은 필수입니다")
        if not self.created_by.strip():
            raise ValueError("작성자는 필수입니다")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'activity_type': self.activity_type,
            'subject': self.subject,
            'description': self.description,
            'contact_person': self.contact_person,
            'contact_method': self.contact_method,
            'result': self.result,
            'next_action': self.next_action,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_completed': self.is_completed
        }

@dataclass
class CrawlingJob:
    """크롤링 작업 데이터 모델"""
    id: Optional[int] = None
    job_name: str = ""
    status: str = CrawlingStatus.RUNNING.value
    total_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    started_by: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config_data: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.job_name.strip():
            raise ValueError("작업명은 필수입니다")
    
    @property
    def progress_percentage(self) -> float:
        """진행률 계산"""
        if self.total_count == 0:
            return 0.0
        return (self.processed_count / self.total_count) * 100
    
    @property
    def is_running(self) -> bool:
        """실행 중인지 확인"""
        return self.status == CrawlingStatus.RUNNING.value
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'job_name': self.job_name,
            'status': self.status,
            'total_count': self.total_count,
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'progress_percentage': self.progress_percentage,
            'started_by': self.started_by,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'config_data': self.config_data,
            'error_message': self.error_message,
            'is_running': self.is_running
        }

@dataclass
class DashboardStats:
    """대시보드 통계 데이터 모델"""
    total_organizations: int = 0
    total_users: int = 0
    status_counts: Dict[str, int] = field(default_factory=dict)
    follow_ups_this_week: int = 0
    recent_activities: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_organizations': self.total_organizations,
            'total_users': self.total_users,
            'status_counts': self.status_counts,
            'follow_ups_this_week': self.follow_ups_this_week,
            'recent_activities': self.recent_activities
        }

# ==================== 검증 함수 ====================

def validate_organization_data(data: Dict[str, Any]) -> List[str]:
    """기관 데이터 검증 및 오류 목록 반환"""
    errors = []
    
    # 필수 필드 체크
    if not data.get('name', '').strip():
        errors.append("기관명은 필수입니다")
    
    # 이메일 형식 체크
    if data.get('email') and not validate_email(data['email']):
        errors.append("이메일 형식이 올바르지 않습니다")
    
    # 전화번호 형식 체크
    if data.get('phone') and not validate_phone(data['phone']):
        errors.append("전화번호 형식이 올바르지 않습니다")
    
    # 홈페이지 URL 체크
    if data.get('homepage') and not validate_homepage(data['homepage']):
        errors.append("홈페이지 URL 형식이 올바르지 않습니다")
    
    return errors

def validate_user_data(data: Dict[str, Any]) -> List[str]:
    """사용자 데이터 검증 및 오류 목록 반환"""
    errors = []
    
    # 필수 필드 체크
    if not data.get('username', '').strip():
        errors.append("사용자명은 필수입니다")
    if not data.get('full_name', '').strip():
        errors.append("실명은 필수입니다")
    if not data.get('password', '').strip():
        errors.append("비밀번호는 필수입니다")
    
    # 이메일 형식 체크
    if data.get('email') and not validate_email(data['email']):
        errors.append("이메일 형식이 올바르지 않습니다")
    
    # 전화번호 형식 체크
    if data.get('phone') and not validate_phone(data['phone']):
        errors.append("전화번호 형식이 올바르지 않습니다")
    
    return errors

# ==================== 헬퍼 함수 ====================

def create_organization_from_json(json_data: Dict[str, Any]) -> Organization:
    """JSON 데이터에서 Organization 객체 생성"""
    # 크롤링 데이터 분리
    crawling_fields = [
        'homepage_parsed', 'page_title', 'page_content_length',
        'contact_info_extracted', 'meta_info', 'ai_summary',
        'parsing_timestamp', 'parsing_status'
    ]
    
    crawling_data = {k: v for k, v in json_data.items() if k in crawling_fields}
    
    return Organization(
        name=json_data.get('name', '').strip(),
        type=OrganizationType.CHURCH.value,
        category=json_data.get('category', '종교시설'),
        homepage=json_data.get('homepage', '').strip(),
        phone=json_data.get('phone', '').strip(),
        fax=json_data.get('fax', '').strip(),
        email=json_data.get('email', '').strip(),
        mobile=json_data.get('mobile', '').strip(),
        postal_code=json_data.get('postal_code', '').strip(),
        address=json_data.get('address', '').strip(),
        contact_status=ContactStatus.NEW.value,
        priority=Priority.MEDIUM.value,
        lead_source='DATABASE',
        crawling_data=crawling_data,
        created_by='MIGRATION'
    )

if __name__ == "__main__":
    # 테스트 실행
    print("🧪 모델 테스트 실행...")
    
    # Organization 테스트
    try:
        org = Organization(
            name="테스트 교회",
            phone="02-1234-5678",
            email="test@church.com",
            homepage="https://test-church.com"
        )
        print("✅ Organization 모델 생성 성공")
        print(f"📊 조직 정보: {org.name}")
        
    except ValueError as e:
        print(f"❌ Organization 모델 검증 실패: {e}")
    
    # User 테스트
    try:
        user = User(
            username="testuser",
            full_name="테스트 사용자",
            email="test@company.com",
            role=UserRole.SALES.value
        )
        print("✅ User 모델 생성 성공")
        print(f"👤 사용자 정보: {user.full_name} ({user.role})")
        
    except ValueError as e:
        print(f"❌ User 모델 검증 실패: {e}")
    
    print("🎉 모델 테스트 완료!")

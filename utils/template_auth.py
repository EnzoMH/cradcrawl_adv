#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿 권한 미들웨어
세션 기반 인증 및 역할별 접근 제어
"""

from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from services.user_services import UserService

class TemplateAuthManager:
    """템플릿 권한 관리자"""
    
    def __init__(self):
        self.user_service = UserService()
        
        # 페이지별 최소 권한 레벨 정의
        self.page_permissions = {
            # 공통 페이지 (모든 사용자)
            "/": 1,
            "/dashboard": 1,
            "/login": 0,  # 로그인 불필요
            
            # 기관 관리 (모든 사용자)
            "/organizations": 1,
            "/enrichment": 3,
            "/statistics": 3,
            
            # 사용자 관리 (팀장 이상)
            "/users": 3,
            "/users/create": 3,
            "/users/edit": 3,
            
            # 시스템 관리 (개발자만)
            "/admin": 5,
            "/system": 5,
            "/logs": 5,
        }
    
    def serialize_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """datetime 필드를 JSON 직렬화 가능한 형태로 변환"""
        if not data:
            return data
        
        serialized_data = data.copy()
        
        # datetime 필드들을 문자열로 변환
        datetime_fields = ['last_login', 'created_at', 'updated_at']
        
        for field in datetime_fields:
            if field in serialized_data and serialized_data[field] is not None:
                if isinstance(serialized_data[field], datetime):
                    serialized_data[field] = serialized_data[field].isoformat()
        
        return serialized_data
    
    def get_current_user_from_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """세션에서 현재 사용자 정보 조회"""
        try:
            # 쿠키에서 세션 ID 조회
            session_id = request.cookies.get("session_id")
            if not session_id:
                return None
            
            # crm_app의 active_sessions에서 사용자 정보 조회
            import crm_app
            active_sessions = getattr(crm_app, 'active_sessions', {})
            
            if session_id in active_sessions:
                return active_sessions[session_id]
            
            return None
            
        except Exception as e:
            print(f"세션 조회 오류: {e}")  # 디버그용
            return None
    
    def get_user_permission_level(self, user: Dict[str, Any]) -> int:
        """사용자 권한 레벨 조회"""
        if not user:
            return 0
        
        role = user.get('role', '')
        
        # 역할별 권한 레벨 매핑
        role_levels = {
            "개발자": 5,
            "DEVELOPER": 5,  # 기존 영문 코드 호환
            "대표": 4,
            "ADMIN1": 4,     # 기존 영문 코드 호환
            "팀장": 3,
            "ADMIN2": 3,     # 기존 영문 코드 호환
            "일반사원": 1,
            "SALES": 1,      # 기존 영문 코드 호환
            "영업": 1,       # 기존 한글 코드 호환
        }
        
        return role_levels.get(role, 0)
    
    def check_page_permission(self, request: Request, required_level: int = 1) -> bool:
        """페이지 접근 권한 확인"""
        user = self.get_current_user_from_session(request)
        
        if required_level == 0:  # 로그인 불필요
            return True
        
        if not user:  # 로그인 필요한데 사용자 없음
            return False
        
        user_level = self.get_user_permission_level(user)
        return user_level >= required_level
    
    def get_template_context(self, request: Request) -> Dict[str, Any]:
        """템플릿에서 사용할 컨텍스트 정보"""
        user = self.get_current_user_from_session(request)
        
        if not user:
            return {
                "is_authenticated": False,
                "current_user": None,
                "user_permissions": {},
                "template_access": "none"
            }
        
        # 사용자 권한 정보
        permissions = self.user_service.get_role_permissions(user.get('role', ''))
        template_access = self.user_service.get_template_access(user.get('role', ''))
        
        # current_user의 datetime 필드를 JSON 직렬화 가능한 형태로 변환
        serialized_user = self.serialize_datetime_fields(user)
        
        return {
            "is_authenticated": True,
            "current_user": serialized_user,
            "user_permissions": permissions,
            "template_access": template_access,
            "user_level": self.get_user_permission_level(user),
            
            # 페이지별 접근 권한
            "can_access_users": self.get_user_permission_level(user) >= 3,
            "can_access_admin": self.get_user_permission_level(user) >= 5,
            "can_create_users": user.get('role') in permissions.get('can_create', []),
            "can_manage_system": user.get('role') == '개발자',
        }

# 전역 인스턴스
auth_manager = TemplateAuthManager()

def require_auth(min_level: int = 1):
    """인증 필요 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not auth_manager.check_page_permission(request, min_level):
                # 로그인 페이지로 리다이렉트
                return RedirectResponse(url="/login", status_code=302)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(*allowed_roles):
    """특정 역할 필요 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = auth_manager.get_current_user_from_session(request)
            
            if not user or user.get('role') not in allowed_roles:
                raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_template_context(request: Request) -> Dict[str, Any]:
    """템플릿 컨텍스트 헬퍼 함수"""
    return auth_manager.get_template_context(request)
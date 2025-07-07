#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 관리 API 엔드포인트
실무 기반 계층적 권한 시스템
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from services.user_services import UserService
from utils.logger_utils import LoggerUtils

router = APIRouter(prefix="/api/users", tags=["사용자 관리"])
logger = LoggerUtils.setup_logger(name="user_api", file_logging=False)
security = HTTPBearer()

# Pydantic 모델들
class UserLoginModel(BaseModel):
    """사용자 로그인 모델"""
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호")

class UserCreateModel(BaseModel):
    """사용자 생성 모델"""
    username: str = Field(..., description="사용자명", min_length=3, max_length=50)
    password: str = Field(..., description="비밀번호", min_length=6)
    full_name: str = Field(..., description="성명", min_length=2, max_length=100)
    email: Optional[str] = Field(None, description="이메일")
    phone: Optional[str] = Field(None, description="전화번호")
    role: str = Field(..., description="역할 (개발자/대표/팀장/일반사원)")
    team: Optional[str] = Field(None, description="팀")

class UserUpdateModel(BaseModel):
    """사용자 수정 모델"""
    password: Optional[str] = Field(None, description="비밀번호", min_length=6)
    full_name: Optional[str] = Field(None, description="성명", min_length=2, max_length=100)
    email: Optional[str] = Field(None, description="이메일")
    phone: Optional[str] = Field(None, description="전화번호")
    role: Optional[str] = Field(None, description="역할 (개발자/대표/팀장/일반사원)")
    team: Optional[str] = Field(None, description="팀")

class AuthResponse(BaseModel):
    """인증 응답 모델"""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None

def get_current_user(request: Request) -> Dict[str, Any]:
    """현재 로그인된 사용자 정보 조회"""
    # crm_app의 active_sessions에서 사용자 정보 조회
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    # crm_app의 active_sessions 참조
    import crm_app
    active_sessions = getattr(crm_app, 'active_sessions', {})
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    
    return active_sessions[session_id]

# ==================== 인증 관련 엔드포인트 ====================

@router.post("/login", summary="사용자 로그인", response_model=AuthResponse)
async def login(user_data: UserLoginModel):
    """
    사용자 로그인을 처리합니다.
    
    - **username**: 사용자명
    - **password**: 비밀번호
    
    성공 시 사용자 정보와 권한을 반환합니다.
    """
    try:
        logger.info(f"🔐 로그인 시도: {user_data.username}")
        
        user_service = UserService()
        user = user_service.authenticate_user(user_data.username, user_data.password)
        
        if not user:
            logger.warning(f"❌ 로그인 실패: {user_data.username}")
            return AuthResponse(
                success=False,
                message="사용자명 또는 비밀번호가 올바르지 않습니다."
            )
        
        # 세션 생성 (crm_app의 active_sessions 사용)
        import secrets
        import crm_app
        session_id = secrets.token_urlsafe(32)
        active_sessions = getattr(crm_app, 'active_sessions', {})
        active_sessions[session_id] = user
        
        logger.info(f"✅ 로그인 성공: {user['full_name']} ({user['role']})")
        
        return AuthResponse(
            success=True,
            message="로그인 성공",
            user=user,
            token=session_id
        )
        
    except Exception as e:
        logger.error(f"❌ 로그인 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다.")

@router.post("/logout", summary="로그아웃")
async def logout(request: Request):
    """사용자 로그아웃"""
    try:
        session_id = request.cookies.get("session_id")
        if session_id:
            import crm_app
            active_sessions = getattr(crm_app, 'active_sessions', {})
            if session_id in active_sessions:
                user = active_sessions[session_id]
                del active_sessions[session_id]
                logger.info(f"👋 로그아웃: {user.get('full_name', 'Unknown')}")
        
        return {"success": True, "message": "로그아웃 되었습니다."}
        
    except Exception as e:
        logger.error(f"❌ 로그아웃 실패: {e}")
        return {"success": False, "message": "로그아웃 처리 중 오류가 발생했습니다."}

@router.get("/me", summary="현재 사용자 정보")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """현재 로그인된 사용자의 정보를 조회합니다."""
    return {
        "success": True,
        "user": current_user
    }

# ==================== 사용자 관리 엔드포인트 ====================

@router.get("/", summary="사용자 목록 조회")
async def get_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    권한에 따라 조회 가능한 사용자 목록을 반환합니다.
    
    - **개발자**: 모든 사용자 조회
    - **대표**: 개발자 제외한 모든 사용자 조회
    - **팀장**: 일반사원만 조회
    - **일반사원**: 본인만 조회
    """
    try:
        user_service = UserService()
        users = user_service.get_viewable_users(
            viewer_id=current_user['id'],
            viewer_role=current_user['role']
        )
        
        logger.info(f"👥 사용자 목록 조회: {len(users)}명 ({current_user['role']})")
        
        return {
            "success": True,
            "users": users,
            "viewer_role": current_user['role'],
            "total_count": len(users)
        }
        
    except Exception as e:
        logger.error(f"❌ 사용자 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.get("/{user_id}", summary="사용자 상세 조회")
async def get_user_detail(
    user_id: int = Path(..., description="사용자 ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """특정 사용자의 상세 정보를 조회합니다."""
    try:
        user_service = UserService()
        user = user_service.get_user_by_id(
            user_id=user_id,
            viewer_id=current_user['id'],
            viewer_role=current_user['role']
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        logger.info(f"👤 사용자 상세 조회: {user['full_name']}")
        
        return {
            "success": True,
            "user": user
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 사용자 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.post("/", summary="새 사용자 생성")
async def create_user(
    user_data: UserCreateModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    새 사용자를 생성합니다.
    
    - **개발자**: 모든 역할의 사용자 생성 가능
    - **대표**: 팀장, 일반사원 생성 가능
    - **팀장**: 일반사원만 생성 가능
    - **일반사원**: 생성 권한 없음
    """
    try:
        user_service = UserService()
        
        # 역할 유효성 검사
        valid_roles = ["개발자", "대표", "팀장", "일반사원"]
        if user_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 역할입니다. 가능한 역할: {', '.join(valid_roles)}")
        
        result = user_service.create_user(
            user_data=user_data.dict(),
            creator_role=current_user['role']
        )
        
        logger.info(f"👤 사용자 생성: {user_data.full_name} ({user_data.role})")
        
        return {
            "success": True,
            "message": result['message'],
            "user_id": result['user_id']
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 사용자 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"생성 실패: {str(e)}")

@router.put("/{user_id}", summary="사용자 정보 수정")
async def update_user(
    user_id: int = Path(..., description="사용자 ID"),
    user_data: UserUpdateModel = ...,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자 정보를 수정합니다.
    
    - **개발자**: 모든 사용자 수정 가능
    - **대표**: 개발자 제외한 모든 사용자 수정 가능
    - **팀장**: 일반사원만 수정 가능
    - **일반사원**: 본인만 수정 가능
    """
    try:
        user_service = UserService()
        
        # None이 아닌 필드만 업데이트 데이터에 포함
        update_data = {}
        for field, value in user_data.dict().items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다.")
        
        # 역할 변경 시 유효성 검사
        if "role" in update_data:
            valid_roles = ["개발자", "대표", "팀장", "일반사원"]
            if update_data["role"] not in valid_roles:
                raise HTTPException(status_code=400, detail=f"유효하지 않은 역할입니다. 가능한 역할: {', '.join(valid_roles)}")
        
        result = user_service.update_user(
            user_id=user_id,
            update_data=update_data,
            manager_id=current_user['id'],
            manager_role=current_user['role']
        )
        
        logger.info(f"✏️ 사용자 수정: ID {user_id}, 필드: {list(update_data.keys())}")
        
        return {
            "success": True,
            "message": result['message'],
            "updated_fields": result.get('updated_fields', [])
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 사용자 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")

@router.delete("/{user_id}", summary="사용자 삭제")
async def delete_user(
    user_id: int = Path(..., description="사용자 ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자를 삭제(비활성화)합니다.
    
    - **개발자**: 개발자 제외한 모든 사용자 삭제 가능
    - **대표**: 팀장, 일반사원 삭제 가능
    - **팀장**: 일반사원만 삭제 가능
    - **일반사원**: 삭제 권한 없음
    """
    try:
        user_service = UserService()
        
        result = user_service.delete_user(
            user_id=user_id,
            manager_role=current_user['role'],
            manager_id=current_user['id']
        )
        
        logger.info(f"🗑️ 사용자 삭제: ID {user_id}")
        
        return {
            "success": True,
            "message": result['message']
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 사용자 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

# ==================== 통계 및 관리 엔드포인트 ====================

@router.get("/statistics", summary="사용자 통계")
async def get_user_statistics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    사용자 역할별 통계를 조회합니다.
    권한에 따라 조회 가능한 통계만 반환됩니다.
    """
    try:
        user_service = UserService()
        stats = user_service.get_role_statistics(current_user['role'])
        
        logger.info(f"📊 사용자 통계 조회: {current_user['role']}")
        
        return {
            "success": True,
            "statistics": stats,
            "viewer_role": current_user['role']
        }
        
    except Exception as e:
        logger.error(f"❌ 사용자 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@router.get("/permissions", summary="권한 구조 조회")
async def get_permissions_structure(current_user: Dict[str, Any] = Depends(get_current_user)):
    """현재 사용자의 권한 구조를 조회합니다."""
    try:
        user_service = UserService()
        permissions = user_service.get_role_permissions(current_user['role'])
        
        return {
            "success": True,
            "role": current_user['role'],
            "permissions": permissions,
            "template_access": user_service.get_template_access(current_user['role'])
        }
        
    except Exception as e:
        logger.error(f"❌ 권한 구조 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"권한 조회 실패: {str(e)}")

# ==================== 개발자 전용 엔드포인트 ====================

@router.post("/developer/reset-password/{user_id}", summary="비밀번호 초기화 (개발자 전용)")
async def reset_user_password(
    user_id: int = Path(..., description="사용자 ID"),
    new_password: str = Query(..., description="새 비밀번호"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """개발자만 다른 사용자의 비밀번호를 초기화할 수 있습니다."""
    try:
        if current_user['role'] != "개발자":
            raise HTTPException(status_code=403, detail="개발자만 접근 가능합니다.")
        
        user_service = UserService()
        result = user_service.update_user(
            user_id=user_id,
            update_data={"password": new_password},
            manager_id=current_user['id'],
            manager_role=current_user['role']
        )
        
        logger.info(f"🔑 비밀번호 초기화: ID {user_id} by {current_user['full_name']}")
        
        return {
            "success": True,
            "message": "비밀번호가 초기화되었습니다."
        }
        
    except Exception as e:
        logger.error(f"❌ 비밀번호 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"초기화 실패: {str(e)}")

@router.get("/developer/sessions", summary="활성 세션 조회 (개발자 전용)")
async def get_active_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """개발자만 현재 활성 세션을 조회할 수 있습니다."""
    try:
        if current_user['role'] != "개발자":
            raise HTTPException(status_code=403, detail="개발자만 접근 가능합니다.")
        
        sessions = []
        for session_id, user_data in active_sessions.items():
            sessions.append({
                "session_id": session_id[:8] + "...",  # 보안을 위해 일부만 표시
                "user_id": user_data['id'],
                "username": user_data['username'],
                "full_name": user_data['full_name'],
                "role": user_data['role'],
                "last_login": user_data.get('last_login')
            })
        
        return {
            "success": True,
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"❌ 세션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"세션 조회 실패: {str(e)}")
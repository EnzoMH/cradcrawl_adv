#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실무 기반 사용자 관리 서비스
개발자 최고 권한 + 템플릿 CRUD 권한
"""

import hashlib
import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.database import get_database
from utils.logger_utils import LoggerUtils

class UserService:
    """실무 기반 사용자 관리 서비스"""
    
    def __init__(self):
        self.db = get_database()
        self.logger = LoggerUtils.setup_logger(name="user_service", file_logging=False)
        
        # 실무 기반 권한 구조
        self.role_hierarchy = {
            "개발자": {
                "can_view": ["개발자", "대표", "팀장", "일반사원"],
                "can_manage": ["개발자", "대표", "팀장", "일반사원"],
                "can_create": ["개발자", "대표", "팀장", "일반사원"],
                "can_delete": ["대표", "팀장", "일반사원"],  # 개발자는 개발자 삭제 불가
                "template_access": "full",  # 템플릿 모든 권한
                "level": 5,
                "description": "시스템 관리자 - 최고 권한"
            },
            "대표": {
                "can_view": ["대표", "팀장", "일반사원"],
                "can_manage": ["대표", "팀장", "일반사원"],
                "can_create": ["팀장", "일반사원"],
                "can_delete": ["팀장", "일반사원"],
                "template_access": "read_write",  # 템플릿 읽기/쓰기
                "level": 4,
                "description": "경영진 - 비즈니스 관리"
            },
            "팀장": {
                "can_view": ["팀장", "일반사원"],
                "can_manage": ["일반사원"],
                "can_create": ["일반사원"],
                "can_delete": ["일반사원"],
                "template_access": "read_write",  # 템플릿 읽기/쓰기
                "level": 3,
                "description": "중간 관리자 - 팀원 관리"
            },
            "일반사원": {
                "can_view": [],
                "can_manage": [],
                "can_create": [],
                "can_delete": [],
                "template_access": "read_only",  # 템플릿 읽기만
                "level": 1,
                "description": "일반 직원 - 제한적 권한"
            }
        }
        
        # 수정 가능한 필드
        self.editable_fields = [
            "password", "full_name", "email", "phone", "team"
        ]
    
    def get_role_permissions(self, role: str) -> Dict[str, Any]:
        """역할별 권한 조회"""
        return self.role_hierarchy.get(role, self.role_hierarchy["일반사원"])
    
    def is_developer(self, role: str) -> bool:
        """개발자 권한 확인"""
        return role == "개발자"
    
    def can_view_user(self, viewer_role: str, target_role: str, viewer_id: int, target_id: int) -> bool:
        """사용자 조회 권한 확인"""
        if viewer_id == target_id:
            return True
        
        if self.is_developer(viewer_role):
            return True
        
        permissions = self.get_role_permissions(viewer_role)
        return target_role in permissions["can_view"]
    
    def can_manage_user(self, manager_role: str, target_role: str, manager_id: int, target_id: int) -> bool:
        """사용자 관리 권한 확인"""
        if manager_id == target_id:
            return True
        
        if self.is_developer(manager_role):
            return True
        
        permissions = self.get_role_permissions(manager_role)
        return target_role in permissions["can_manage"]
    
    def can_create_user(self, creator_role: str, target_role: str) -> bool:
        """사용자 생성 권한 확인"""
        if self.is_developer(creator_role):
            return True
        
        permissions = self.get_role_permissions(creator_role)
        return target_role in permissions["can_create"]
    
    def can_delete_user(self, deleter_role: str, target_role: str) -> bool:
        """사용자 삭제 권한 확인"""
        if self.is_developer(deleter_role):
            return target_role != "개발자"  # 개발자는 개발자 삭제 불가
        
        permissions = self.get_role_permissions(deleter_role)
        return target_role in permissions["can_delete"]
    
    def get_template_access(self, role: str) -> str:
        """템플릿 접근 권한 확인"""
        permissions = self.get_role_permissions(role)
        return permissions.get("template_access", "read_only")
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex() + ':' + salt
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """비밀번호 검증"""
        # 임시: 단순 텍스트 비교 (테스트용)
        if password_hash == 'simple123':
            return password == 'simple123'
        
        # 기존 해시 검증
        try:
            stored_hash, salt = password_hash.split(':')
            password_hash_new = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_new.hex() == stored_hash
        except:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증"""
        try:
            user = self.db.execute_query(
                "SELECT * FROM users WHERE username = %s AND is_active = true",
                (username,),
                fetch_all=False
            )
            
            if not user:
                return None
            
            if self.verify_password(password, user['password_hash']):
                # 로그인 시간 업데이트
                self.db.execute_update(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                
                # 비밀번호 해시 제거 후 반환
                user_data = dict(user)
                del user_data['password_hash']
                
                # 권한 정보 추가
                permissions = self.get_role_permissions(user_data['role'])
                user_data['permissions'] = permissions
                user_data['template_access'] = self.get_template_access(user_data['role'])
                
                return user_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 인증 실패: {e}")
            return None
    
    def get_viewable_users(self, viewer_id: int, viewer_role: str) -> List[Dict[str, Any]]:
        """조회 가능한 사용자 목록"""
        permissions = self.get_role_permissions(viewer_role)
        viewable_roles = permissions["can_view"]
        
        if not viewable_roles:
            # 본인만 조회 가능
            users = self.db.execute_query("""
                SELECT id, username, full_name, email, phone, role, team, 
                       is_active, last_login, created_at, updated_at
                FROM users 
                WHERE id = %s
            """, (viewer_id,))
        else:
            # 권한에 따른 역할 필터링
            role_placeholders = ', '.join(['%s'] * len(viewable_roles))
            query = f"""
                SELECT id, username, full_name, email, phone, role, team, 
                       is_active, last_login, created_at, updated_at
                FROM users 
                WHERE role IN ({role_placeholders})
                ORDER BY 
                    CASE 
                        WHEN role = '개발자' THEN 5
                        WHEN role = '대표' THEN 4
                        WHEN role = '팀장' THEN 3
                        WHEN role = '일반사원' THEN 1
                        ELSE 0
                    END DESC,
                    created_at DESC
            """
            users = self.db.execute_query(query, tuple(viewable_roles))
        
        return users
    
    def get_user_by_id(self, user_id: int, viewer_id: int, viewer_role: str) -> Optional[Dict[str, Any]]:
        """사용자 상세 조회"""
        user = self.db.execute_query("""
            SELECT id, username, full_name, email, phone, role, team, 
                   is_active, last_login, created_at, updated_at
            FROM users 
            WHERE id = %s
        """, (user_id,), fetch_all=False)
        
        if not user:
            return None
        
        # 조회 권한 확인
        if not self.can_view_user(viewer_role, user['role'], viewer_id, user_id):
            raise PermissionError("해당 사용자 조회 권한이 없습니다.")
        
        return user
    
    def create_user(self, user_data: Dict[str, Any], creator_role: str) -> Dict[str, Any]:
        """새 사용자 생성"""
        # 생성 권한 확인
        if not self.can_create_user(creator_role, user_data["role"]):
            raise PermissionError(f"{creator_role}는 {user_data['role']} 역할의 사용자를 생성할 수 없습니다.")
        
        # 필수 필드 검증
        required_fields = ["username", "password", "full_name", "role"]
        for field in required_fields:
            if not user_data.get(field):
                raise ValueError(f"{field}는 필수 항목입니다.")
        
        # 사용자명 중복 확인
        existing = self.db.execute_query(
            "SELECT id FROM users WHERE username = %s",
            (user_data["username"],),
            fetch_all=False
        )
        
        if existing:
            raise ValueError("이미 존재하는 사용자명입니다.")
        
        # 비밀번호 해시화
        password_hash = self.hash_password(user_data["password"])
        
        # 사용자 생성
        user_id = self.db.execute_query("""
            INSERT INTO users (username, password_hash, full_name, email, phone, role, team)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_data["username"],
            password_hash,
            user_data["full_name"],
            user_data.get("email", ""),
            user_data.get("phone", ""),
            user_data["role"],
            user_data.get("team", "")
        ), fetch_all=False)["id"]
        
        self.logger.info(f"✅ 사용자 생성: {user_data['full_name']} ({user_data['username']})")
        
        return {"success": True, "user_id": user_id, "message": "사용자가 생성되었습니다."}
    
    def update_user(self, user_id: int, update_data: Dict[str, Any], 
                   manager_id: int, manager_role: str) -> Dict[str, Any]:
        """사용자 정보 수정"""
        # 대상 사용자 조회
        target_user = self.db.execute_query(
            "SELECT role FROM users WHERE id = %s",
            (user_id,),
            fetch_all=False
        )
        
        if not target_user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 관리 권한 확인
        if not self.can_manage_user(manager_role, target_user['role'], manager_id, user_id):
            raise PermissionError("해당 사용자 수정 권한이 없습니다.")
        
        # ID/사용자명 수정 차단
        if "id" in update_data or "username" in update_data:
            raise ValueError("ID와 사용자명은 수정할 수 없습니다.")
        
        # 역할 변경 권한 확인
        if "role" in update_data:
            new_role = update_data["role"]
            if not self.can_create_user(manager_role, new_role):
                raise PermissionError(f"{manager_role}는 사용자를 {new_role} 역할로 변경할 수 없습니다.")
        
        # 수정 가능한 필드만 필터링
        allowed_updates = {}
        for field, value in update_data.items():
            if field in self.editable_fields + ["role"] and value is not None:
                if field == "password":
                    allowed_updates["password_hash"] = self.hash_password(value)
                else:
                    allowed_updates[field] = value
        
        if not allowed_updates:
            raise ValueError("수정할 데이터가 없습니다.")
        
        # 업데이트 실행
        set_clauses = []
        params = []
        
        for field, value in allowed_updates.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)
        
        params.append(user_id)
        
        query = f"""
            UPDATE users 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        rows_affected = self.db.execute_update(query, tuple(params))
        
        if rows_affected > 0:
            self.logger.info(f"✅ 사용자 수정: ID {user_id}")
            return {
                "success": True, 
                "message": "사용자 정보가 수정되었습니다.",
                "updated_fields": list(update_data.keys())
            }
        else:
            return {"success": False, "message": "업데이트 실패"}
    
    def delete_user(self, user_id: int, manager_role: str, manager_id: int) -> Dict[str, Any]:
        """사용자 삭제 (비활성화)"""
        # 대상 사용자 조회
        target_user = self.db.execute_query(
            "SELECT role FROM users WHERE id = %s",
            (user_id,),
            fetch_all=False
        )
        
        if not target_user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 삭제 권한 확인
        if not self.can_delete_user(manager_role, target_user['role']):
            raise PermissionError("해당 사용자 삭제 권한이 없습니다.")
        
        # 본인 삭제 방지
        if manager_id == user_id:
            raise ValueError("본인 계정은 삭제할 수 없습니다.")
        
        # 소프트 삭제
        rows_affected = self.db.execute_update("""
            UPDATE users 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_active = true
        """, (user_id,))
        
        if rows_affected > 0:
            self.logger.info(f"✅ 사용자 삭제: ID {user_id}")
            return {"success": True, "message": "사용자가 비활성화되었습니다."}
        else:
            return {"success": False, "message": "사용자를 찾을 수 없거나 이미 비활성화되었습니다."}
    
    def get_role_statistics(self, viewer_role: str) -> Dict[str, Any]:
        """역할별 통계"""
        permissions = self.get_role_permissions(viewer_role)
        viewable_roles = permissions["can_view"]
        
        if not viewable_roles:
            return {"message": "개인 계정 정보만 조회 가능합니다."}
        
        # 권한에 따른 통계
        role_placeholders = ', '.join(['%s'] * len(viewable_roles))
        query = f"""
            SELECT 
                role,
                COUNT(*) as count,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_count
            FROM users 
            WHERE role IN ({role_placeholders})
            GROUP BY role
            ORDER BY 
                CASE 
                    WHEN role = '개발자' THEN 5
                    WHEN role = '대표' THEN 4
                    WHEN role = '팀장' THEN 3
                    WHEN role = '일반사원' THEN 1
                    ELSE 0
                END DESC
        """
        
        stats = self.db.execute_query(query, tuple(viewable_roles))
        
        return {
            "viewable_roles": viewable_roles,
            "role_statistics": stats,
            "viewer_permissions": permissions
        }
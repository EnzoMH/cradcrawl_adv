// 순수 JavaScript로 사용자 관리 구현
class UsersManager {
    constructor() {
        this.users = [];
        this.statistics = {};
        this.config = window.APP_CONFIG || {};
        this.init();
    }

    async init() {
        await this.loadUsers();
        await this.loadStatistics();
        this.setupEventListeners();
    }

    async loadUsers() {
        try {
            // 로딩 상태 표시
            this.showLoading();
            
            const response = await fetch('/api/users/', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('사용자 목록에 접근할 권한이 없습니다.');
                } else if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error('사용자 목록을 불러올 수 없습니다.');
            }
            
            const data = await response.json();
            this.users = data.users || [];
            this.renderUsers();
            
        } catch (error) {
            console.error('사용자 로드 실패:', error);
            this.showError(error.message);
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/users/statistics', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.statistics = data.statistics || {};
                this.renderStatistics();
            }
        } catch (error) {
            console.error('통계 로드 실패:', error);
        }
    }

    renderUsers() {
        const tbody = document.getElementById('users-table-body');
        const userCount = document.getElementById('user-count');
        
        userCount.textContent = `총 ${this.users.length}명의 사용자`;
        
        tbody.innerHTML = this.users.map(user => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center text-white ${this.getRoleColor(user.role)}">
                            <i class="fas ${this.getRoleIcon(user.role)}"></i>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">
                                ${user.full_name}
                                ${user.id === this.config.currentUser?.id ? '<span class="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">본인</span>' : ''}
                            </div>
                            <div class="text-sm text-gray-500">@${user.username}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getRoleBadgeColor(user.role)}">
                        ${user.role}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.team || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>${user.email || '-'}</div>
                    <div>${user.phone || '-'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${user.last_login ? new Date(user.last_login).toLocaleString('ko-KR') : '없음'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? '활성' : '비활성'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex items-center justify-end space-x-2">
                        ${this.canManage(user.role) ? `
                            <button onclick="usersManager.editUser(${user.id})" class="text-indigo-600 hover:text-indigo-900" title="편집">
                                <i class="fas fa-edit"></i>
                            </button>
                        ` : ''}
                        ${this.canDelete(user.role) && user.id !== this.config.currentUser?.id ? `
                            <button onclick="usersManager.deleteUser(${user.id})" class="text-red-600 hover:text-red-900 ml-2" title="삭제">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderStatistics() {
        const container = document.getElementById('statistics-container');
        const roleStats = this.statistics.role_statistics || [];
        
        container.innerHTML = roleStats.map(stat => `
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-md ${this.getRoleColor(stat.role)}">
                        <i class="fas ${this.getRoleIcon(stat.role)} text-white"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">${stat.role}</p>
                        <p class="text-2xl font-semibold text-gray-900">${stat.count}명</p>
                        <p class="text-xs text-gray-500">활성: ${stat.active_count} / 비활성: ${stat.inactive_count}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    setupEventListeners() {
        const createBtn = document.getElementById('create-user-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateModal());
        }
    }

    canManage(targetRole) {
        const permissions = this.config.userPermissions || {};
        return permissions.can_manage?.includes(targetRole) || false;
    }

    canDelete(targetRole) {
        const permissions = this.config.userPermissions || {};
        return permissions.can_delete?.includes(targetRole) || false;
    }

    async deleteUser(userId) {
        if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) {
            return;
        }

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '사용자 삭제에 실패했습니다.');
            }

            await this.loadUsers();
            await this.loadStatistics();
            this.showSuccessMessage('사용자가 삭제되었습니다.');
            
        } catch (error) {
            this.showErrorMessage(`삭제 실패: ${error.message}`);
        }
    }

    async editUser(userId) {
        try {
            // 사용자 정보 조회
            const response = await fetch(`/api/users/${userId}`, {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('사용자 정보를 불러올 수 없습니다.');
            }

            const data = await response.json();
            const user = data.user;

            this.showEditModal(user);

        } catch (error) {
            this.showErrorMessage(`편집 실패: ${error.message}`);
        }
    }

    showEditModal(user) {
        const modalHtml = `
            <div id="user-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium text-gray-900">사용자 편집</h3>
                            <button onclick="usersManager.closeModal()" class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <form id="edit-user-form" class="space-y-4">
                            <input type="hidden" name="user_id" value="${user.id}">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">사용자명</label>
                                <input type="text" name="username" value="${user.username}" disabled class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-100 text-gray-500">
                                <p class="text-xs text-gray-500 mt-1">사용자명은 변경할 수 없습니다.</p>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">새 비밀번호</label>
                                <input type="password" name="password" placeholder="변경하지 않으려면 비워두세요" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">성명</label>
                                <input type="text" name="full_name" value="${user.full_name}" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">이메일</label>
                                <input type="email" name="email" value="${user.email || ''}" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">전화번호</label>
                                <input type="tel" name="phone" value="${user.phone || ''}" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">역할</label>
                                <select name="role" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                                    ${this.getEditableRoleOptions(user.role)}
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">팀</label>
                                <input type="text" name="team" value="${user.team || ''}" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div class="flex justify-end space-x-3 pt-4">
                                <button type="button" onclick="usersManager.closeModal()" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">취소</button>
                                <button type="submit" class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">수정</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 폼 제출 이벤트 리스너
        document.getElementById('edit-user-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleEditUser(e.target);
        });
    }

    showCreateModal() {
        const modalHtml = `
            <div id="user-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium text-gray-900">새 사용자 추가</h3>
                            <button onclick="usersManager.closeModal()" class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <form id="create-user-form" class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">사용자명</label>
                                <input type="text" name="username" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">비밀번호</label>
                                <input type="password" name="password" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">성명</label>
                                <input type="text" name="full_name" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">이메일</label>
                                <input type="email" name="email" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">전화번호</label>
                                <input type="tel" name="phone" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">역할</label>
                                <select name="role" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                                    ${this.getAvailableRoleOptions()}
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">팀</label>
                                <input type="text" name="team" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                            </div>
                            <div class="flex justify-end space-x-3 pt-4">
                                <button type="button" onclick="usersManager.closeModal()" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">취소</button>
                                <button type="submit" class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">생성</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 폼 제출 이벤트 리스너
        document.getElementById('create-user-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreateUser(e.target);
        });
    }

    async handleCreateUser(form) {
        try {
            const formData = new FormData(form);
            const userData = {
                username: formData.get('username'),
                password: formData.get('password'),
                full_name: formData.get('full_name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                role: formData.get('role'),
                team: formData.get('team')
            };

            const response = await fetch('/api/users/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '사용자 생성에 실패했습니다.');
            }

            this.closeModal();
            await this.loadUsers();
            await this.loadStatistics();
            this.showSuccessMessage('새 사용자가 생성되었습니다.');

        } catch (error) {
            this.showErrorMessage(`생성 실패: ${error.message}`);
        }
    }

    async handleEditUser(form) {
        try {
            const formData = new FormData(form);
            const userId = formData.get('user_id');
            const userData = {
                full_name: formData.get('full_name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                role: formData.get('role'),
                team: formData.get('team')
            };

            // 비밀번호가 입력된 경우에만 포함
            const password = formData.get('password');
            if (password && password.trim()) {
                userData.password = password;
            }

            const response = await fetch(`/api/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '사용자 수정에 실패했습니다.');
            }

            this.closeModal();
            await this.loadUsers();
            await this.loadStatistics();
            this.showSuccessMessage('사용자 정보가 수정되었습니다.');

        } catch (error) {
            this.showErrorMessage(`수정 실패: ${error.message}`);
        }
    }

    closeModal() {
        const modal = document.getElementById('user-modal');
        if (modal) {
            modal.remove();
        }
    }

    getAvailableRoleOptions() {
        const permissions = this.config.userPermissions || {};
        const canCreate = permissions.can_create || [];
        
        return canCreate.map(role => `<option value="${role}">${role}</option>`).join('');
    }

    getEditableRoleOptions(currentRole) {
        const permissions = this.config.userPermissions || {};
        const canManage = permissions.can_manage || [];
        
        // 관리 가능한 역할 + 현재 역할 포함
        const availableRoles = [...new Set([...canManage, currentRole])];
        
        return availableRoles.map(role => 
            `<option value="${role}" ${role === currentRole ? 'selected' : ''}>${role}</option>`
        ).join('');
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg ${
            type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
            'bg-blue-100 text-blue-800 border border-blue-200'
        }`;
        messageDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                    type === 'success' ? 'fa-check-circle' :
                    type === 'error' ? 'fa-exclamation-circle' :
                    'fa-info-circle'
                } mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(messageDiv);
        
        // 3초 후 자동 제거
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }

    showError(message) {
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-red-600">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    ${message}
                </td>
            </tr>
        `;
    }

    showLoading() {
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center">
                    <div class="flex items-center justify-center">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        <span class="ml-3 text-gray-600">로딩 중...</span>
                    </div>
                </td>
            </tr>
        `;
    }

    getRoleColor(role) {
        const colors = {
            '개발자': 'bg-purple-500', 'DEVELOPER': 'bg-purple-500',
            '대표': 'bg-red-500', 'ADMIN1': 'bg-red-500',
            '팀장': 'bg-blue-500', 'ADMIN2': 'bg-blue-500',
            '일반사원': 'bg-green-500', 'SALES': 'bg-green-500', '영업': 'bg-green-500'
        };
        return colors[role] || 'bg-gray-500';
    }

    getRoleIcon(role) {
        const icons = {
            '개발자': 'fa-code', 'DEVELOPER': 'fa-code',
            '대표': 'fa-crown', 'ADMIN1': 'fa-crown',
            '팀장': 'fa-user-tie', 'ADMIN2': 'fa-user-tie',
            '일반사원': 'fa-user', 'SALES': 'fa-user', '영업': 'fa-user'
        };
        return icons[role] || 'fa-user';
    }

    getRoleBadgeColor(role) {
        const colors = {
            '개발자': 'bg-purple-100 text-purple-800', 'DEVELOPER': 'bg-purple-100 text-purple-800',
            '대표': 'bg-red-100 text-red-800', 'ADMIN1': 'bg-red-100 text-red-800',
            '팀장': 'bg-blue-100 text-blue-800', 'ADMIN2': 'bg-blue-100 text-blue-800',
            '일반사원': 'bg-green-100 text-green-800', 'SALES': 'bg-green-100 text-green-800', '영업': 'bg-green-100 text-green-800'
        };
        return colors[role] || 'bg-gray-100 text-gray-800';
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.usersManager = new UsersManager();
});
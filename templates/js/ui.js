// ===== UI 렌더링 및 상호작용 관리 =====

const UI = {
    // ===== 메인 앱 렌더링 =====
    renderApp(crmSystem) {
        console.log('🔄 UI 렌더링 시작');
        
        // 로딩 화면 숨기기
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            console.log('🔄 로딩 화면 숨기기');
            loadingScreen.style.display = 'none';
        }
        
        const appRoot = document.getElementById('app-root');
        if (!appRoot) {
            console.error('❌ app-root 요소를 찾을 수 없음');
            return;
        }
        
        console.log('🔄 앱 HTML 구조 생성');
        appRoot.innerHTML = `
            ${this.renderNavbar(crmSystem)}
            <div class="flex h-full">
                ${this.renderSidebar(crmSystem)}
                <main class="flex-1 overflow-hidden">
                    <div id="page-content" class="h-full overflow-y-auto">
                        <!-- 초기 콘텐츠는 비워둠 -->
                    </div>
                </main>
            </div>
            ${this.renderToastContainer()}
            ${this.renderModalContainer()}
        `;
        
        // DOM이 완전히 업데이트된 후 현재 페이지 렌더링
        setTimeout(() => {
            const pageContent = document.getElementById('page-content');
            if (pageContent) {
                console.log('🔄 페이지 콘텐츠 렌더링');
                pageContent.innerHTML = this.renderCurrentPage(crmSystem);
            }
            
            console.log('🔄 이벤트 바인딩');
            this.bindEvents(crmSystem);
            
            console.log('✅ UI 렌더링 완료');
        }, 0);
    },

    // ===== 네비게이션 바 =====
    renderNavbar(crmSystem) {
        return `
            <nav class="bg-white shadow-sm border-b border-gray-200 px-4 py-3">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <i class="fas fa-church text-blue-600 text-xl"></i>
                        <h1 class="text-xl font-bold text-gray-900">CRM 시스템</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center text-sm text-gray-700">
                            <i class="fas fa-user-circle text-lg mr-2"></i>
                            <span>${crmSystem.currentUser?.fullName || '사용자'}</span>
                        </div>
                        <button onclick="crmSystem.logout()" 
                                class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-sign-out-alt mr-1"></i>로그아웃
                        </button>
                    </div>
                </div>
            </nav>
        `;
    },

    // ===== 사이드바 =====
    renderSidebar(crmSystem) {
        const menuItems = [
            { id: 'dashboard', icon: 'chart-line', label: '대시보드' },
            { id: 'organizations', icon: 'building', label: '기관 관리' },
            { id: 'crawling', icon: 'spider', label: '데이터 크롤링' },
            { id: 'activities', icon: 'tasks', label: '영업 활동' },
            { id: 'statistics', icon: 'chart-pie', label: '통계 분석' }
        ];

        return `
            <aside class="w-64 bg-white shadow-sm border-r border-gray-200">
                <nav class="mt-4 px-2">
                    <div class="space-y-1">
                        ${menuItems.map(item => `
                            <button onclick="crmSystem.navigateTo('${item.id}')"
                                    class="nav-item w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                                        crmSystem.currentPage === item.id 
                                            ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600' 
                                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    }">
                                <i class="fas fa-${item.icon} mr-3 text-lg ${
                                    crmSystem.currentPage === item.id ? 'text-blue-600' : 'text-gray-400'
                                }"></i>
                                ${item.label}
                            </button>
                        `).join('')}
                    </div>
                </nav>
            </aside>
        `;
    },

    // ===== 현재 페이지 렌더링 =====
    renderCurrentPage(crmSystem) {
        const pages = {
            dashboard: () => this.renderDashboard(crmSystem),
            organizations: () => this.renderOrganizations(crmSystem),
            crawling: () => this.renderCrawling(crmSystem),
            activities: () => this.renderActivities(),
            statistics: () => this.renderStatistics()
        };

        const content = pages[crmSystem.currentPage]?.() || '<div>페이지를 찾을 수 없습니다.</div>';
        
        // 이 메서드가 직접 DOM을 업데이트하지 않고 HTML만 반환
        return content;
    },

    // ===== 대시보드 페이지 =====
    renderDashboard(crmSystem) {
        const stats = crmSystem.dashboardStats || {};
        
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-gray-900">대시보드</h2>
                    <p class="text-gray-600">전체 현황을 한눈에 확인하세요</p>
                </div>

                <!-- 통계 카드 -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${this.renderStatCard('building', '총 기관 수', stats.total_organizations || 0, 'blue')}
                    ${this.renderStatCard('phone', '연락한 기관', stats.total_users || 0, 'green')}
                    ${this.renderStatCard('handshake', '유망 고객', stats.recent_activities || 0, 'yellow')}
                    ${this.renderStatCard('won-sign', '성사된 계약', stats.crawling_jobs || 0, 'purple')}
                </div>

                <!-- 메인 콘텐츠 그리드 -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- 최근 활동 -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">최근 활동</h3>
                        <div id="recent-activities" class="space-y-3">
                            ${this.renderRecentActivities()}
                        </div>
                    </div>

                    <!-- 크롤링 상태 -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">크롤링 상태</h3>
                        <div id="crawling-status-card">
                            ${this.renderCrawlingStatusCard(crmSystem.crawlingStatus)}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    renderStatCard(icon, label, value, color) {
        const colors = {
            blue: 'bg-blue-100 text-blue-600',
            green: 'bg-green-100 text-green-600',
            yellow: 'bg-yellow-100 text-yellow-600',
            purple: 'bg-purple-100 text-purple-600'
        };

        return `
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full ${colors[color]}">
                        <i class="fas fa-${icon} text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-2xl font-bold text-gray-900">${Utils.formatNumber(value)}</h3>
                        <p class="text-gray-600">${label}</p>
                    </div>
                </div>
            </div>
        `;
    },

    // 기관 관리 페이지 수정
    renderOrganizations(crmSystem) {
        return `
            <div class="p-6 h-full flex flex-col">
                <!-- 헤더 -->
                <div class="mb-6 flex-shrink-0">
                    <div class="flex justify-between items-center">
                        <div>
                            <h2 class="text-2xl font-bold text-gray-900">기관 관리</h2>
                            <p class="text-gray-600">등록된 기관들을 관리하고 영업 활동을 추적하세요</p>
                        </div>
                        <div class="flex space-x-3">
                            <button onclick="this.exportOrganizations()" 
                                    class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors">
                                <i class="fas fa-download mr-2"></i>내보내기
                            </button>
                            <button onclick="this.showAddOrganizationModal()" 
                                    class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                                <i class="fas fa-plus mr-2"></i>새 기관 등록
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 검색 및 필터 -->
                <div class="flex-shrink-0 mb-6">
                    ${this.renderOrganizationFilters(crmSystem)}
                </div>

                <!-- 통계 정보 -->
                <div id="organizations-stats" class="flex-shrink-0 mb-4">
                    ${this.renderOrganizationsStats(crmSystem.organizations, crmSystem.pagination)}
                </div>

                <!-- 기관 목록 - 무한 스크롤 -->
                <div class="flex-1 bg-white rounded-lg shadow overflow-hidden">
                    <div id="organizations-table-container" class="h-full overflow-auto">
                        ${this.renderOrganizationsTable(crmSystem.organizations || [])}
                        ${crmSystem.isLoading ? this.renderLoadingIndicator() : ''}
                        ${!crmSystem.hasMore && crmSystem.organizations.length > 0 ? this.renderEndIndicator() : ''}
                    </div>
                </div>
            </div>
        `;
    },

    renderOrganizationsStats(organizations, pagination) {
        const total = pagination?.total_count || 0;
        const loaded = organizations?.length || 0;
        
        return `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="text-sm text-blue-700">
                            <i class="fas fa-building mr-1"></i>
                            <strong>${loaded.toLocaleString()}</strong>개 표시 중 / 
                            총 <strong>${total.toLocaleString()}</strong>개
                        </div>
                        ${loaded < total ? `
                            <div class="text-xs text-blue-600">
                                <i class="fas fa-arrow-down mr-1"></i>
                                스크롤하여 더 보기
                            </div>
                        ` : ''}
                    </div>
                    <div class="text-xs text-blue-600">
                        50개씩 자동 로드
                    </div>
                </div>
            </div>
        `;
    },
    
    renderLoadingIndicator() {
        return `
            <div class="flex justify-center items-center py-8">
                <div class="flex items-center space-x-2 text-gray-500">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span class="text-sm">더 많은 기관 로드 중...</span>
                </div>
            </div>
        `;
    },
    
    renderEndIndicator() {
        return `
            <div class="flex justify-center items-center py-8">
                <div class="text-sm text-gray-500">
                    <i class="fas fa-check-circle mr-2 text-green-500"></i>
                    모든 기관을 불러왔습니다
                </div>
            </div>
        `;
    },

    renderOrganizationFilters(crmSystem) {
        return `
            <div class="bg-white rounded-lg shadow mb-6 p-6">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="md:col-span-2">
                        <div class="relative">
                            <input type="text" id="search-input" placeholder="기관명, 주소, 전화번호 검색..." 
                                   value="${crmSystem.filters.search}"
                                   class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <i class="fas fa-search text-gray-400"></i>
                            </div>
                        </div>
                    </div>
                    <div>
                        <select id="category-filter" 
                                class="w-full py-2 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <option value="">전체 카테고리</option>
                            <option value="교회" ${crmSystem.filters.category === '교회' ? 'selected' : ''}>교회</option>
                            <option value="학원" ${crmSystem.filters.category === '학원' ? 'selected' : ''}>학원</option>
                            <option value="학교" ${crmSystem.filters.category === '학교' ? 'selected' : ''}>학교</option>
                            <option value="공공기관" ${crmSystem.filters.category === '공공기관' ? 'selected' : ''}>공공기관</option>
                        </select>
                    </div>
                    <div>
                        <select id="status-filter" 
                                class="w-full py-2 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <option value="">전체 상태</option>
                            <option value="신규" ${crmSystem.filters.status === '신규' ? 'selected' : ''}>신규</option>
                            <option value="접촉완료" ${crmSystem.filters.status === '접촉완료' ? 'selected' : ''}>접촉완료</option>
                            <option value="관심있음" ${crmSystem.filters.status === '관심있음' ? 'selected' : ''}>관심있음</option>
                            <option value="협상중" ${crmSystem.filters.status === '협상중' ? 'selected' : ''}>협상중</option>
                            <option value="성사" ${crmSystem.filters.status === '성사' ? 'selected' : ''}>성사</option>
                            <option value="실패" ${crmSystem.filters.status === '실패' ? 'selected' : ''}>실패</option>
                        </select>
                    </div>
                </div>
                <div class="mt-4 flex justify-between items-center">
                    <button onclick="this.searchOrganizations()" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors">
                        <i class="fas fa-search mr-2"></i>검색
                    </button>
                    <button onclick="crmSystem.resetFilters()" 
                            class="text-gray-500 hover:text-gray-700 px-4 py-2 rounded-lg transition-colors">
                        <i class="fas fa-undo mr-2"></i>초기화
                    </button>
                </div>
            </div>
        `;
    },

    // ===== 크롤링 페이지 =====
    renderCrawling(crmSystem) {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-gray-900">데이터 크롤링</h2>
                    <p class="text-gray-600">새로운 기관 정보를 자동으로 수집합니다</p>
                </div>

                <!-- 크롤링 설정 -->
                ${this.renderCrawlingSettings(crmSystem)}

                <!-- 크롤링 진행 상황 -->
                <div id="crawling-progress-section" class="${crmSystem.crawlingStatus?.isRunning ? '' : 'hidden'}">
                    ${this.renderCrawlingProgress(crmSystem.crawlingStatus)}
                </div>

                <!-- 실시간 결과 -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">실시간 결과</h3>
                    <div id="crawling-results" class="space-y-2 max-h-96 overflow-y-auto">
                        ${this.renderCrawlingResults([])}
                    </div>
                </div>
            </div>
        `;
    },

    // ===== 이벤트 바인딩 =====
    bindEvents(crmSystem) {
        // 검색 디바운스
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            const debouncedSearch = Utils.debounce(() => {
                crmSystem.updateFilters({ search: searchInput.value });
            }, 500);
            
            searchInput.addEventListener('input', debouncedSearch);
        }

        // 필터 변경
        const categoryFilter = document.getElementById('category-filter');
        const statusFilter = document.getElementById('status-filter');
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => {
                crmSystem.updateFilters({ category: categoryFilter.value });
            });
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                crmSystem.updateFilters({ status: statusFilter.value });
            });
        }
    },

    // ===== 알림 시스템 =====
    showSuccess(message) {
        this.showToast(message, 'success');
    },

    showError(message) {
        this.showToast(message, 'error');
    },

    showToast(message, type) {
        const toastContainer = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        };

        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `${colors[type]} text-white px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out translate-x-full`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'} mr-3"></i>
                <span>${message}</span>
                <button onclick="UI.removeToast('${toastId}')" class="ml-4 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        toastContainer.appendChild(toast);
        
        // 애니메이션
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);

        // 자동 제거
        setTimeout(() => {
            this.removeToast(toastId);
        }, 5000);
    },

    removeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }
    },

    // ===== 컨테이너 렌더링 =====
    renderToastContainer() {
        return `
            <div id="toast-container" 
                 class="fixed top-4 right-4 z-50 space-y-2">
            </div>
        `;
    },
    // renderToastContainer() 함수 뒤에 추가
    renderOrganizationsList(organizations, pagination) {
        console.log('🔄 기관 목록 업데이트:', organizations.length, '개');
        
        // 테이블 컨테이너 업데이트
        const tableContainer = document.getElementById('organizations-table-container');
        if (tableContainer) {
            tableContainer.innerHTML = this.renderOrganizationsTable(organizations);
        }
        
        // 페이지네이션 컨테이너 업데이트  
        const paginationContainer = document.getElementById('organizations-pagination');
        if (paginationContainer) {
            paginationContainer.innerHTML = this.renderPagination(pagination);
        }
    },

    renderModalContainer() {
        return `
            <div id="modal-container" class="hidden">
                <!-- 모달들이 여기에 동적으로 추가됨 -->
            </div>
        `;
    },
    renderOrganizationsTable(organizations) {
        if (!organizations || organizations.length === 0) {
            return `
                <div class="text-center py-12">
                    <i class="fas fa-building text-4xl text-gray-300 mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">등록된 기관이 없습니다</h3>
                    <p class="text-gray-500 mb-4">새로운 기관을 등록하거나 크롤링을 실행해보세요</p>
                    <button onclick="this.showAddOrganizationModal()" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                        <i class="fas fa-plus mr-2"></i>기관 등록
                    </button>
                </div>
            `;
        }

        return `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                #
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                기관정보
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                연락처
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                상태
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                담당자
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                작업
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${organizations.map((org, index) => this.renderOrganizationRow(org, index)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    renderOrganizationRow(org, index) {
        return `
            <tr class="hover:bg-gray-50 transition-colors cursor-pointer" 
                onclick="this.showOrganizationDetail(${org.id})">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${index + 1}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <i class="fas fa-${this.getOrgIcon(org.category)} text-blue-600"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${org.name || '이름 없음'}</div>
                            <div class="text-sm text-gray-500">${org.category || '미분류'}</div>
                            ${org.address ? `<div class="text-xs text-gray-400 max-w-xs truncate">${org.address}</div>` : ''}
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">
                        ${org.phone ? `<div><i class="fas fa-phone text-green-500 mr-1"></i>${org.phone}</div>` : ''}
                        ${org.fax ? `<div><i class="fas fa-fax text-blue-500 mr-1"></i>${org.fax}</div>` : ''}
                        ${org.email ? `<div><i class="fas fa-envelope text-purple-500 mr-1"></i>${org.email}</div>` : ''}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${Utils.getStatusClass(org.contact_status)}">
                        ${org.contact_status || '신규'}
                    </span>
                    ${org.priority ? `<div class="mt-1"><span class="text-xs ${this.getPriorityClass(org.priority)}">${org.priority}</span></div>` : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${org.assigned_to ? `
                        <div class="flex items-center">
                            <div class="h-6 w-6 rounded-full bg-gray-300 flex items-center justify-center mr-2">
                                <span class="text-xs font-medium text-gray-700">${org.assigned_to.charAt(0)}</span>
                            </div>
                            ${org.assigned_to}
                        </div>
                    ` : '<span class="text-gray-400">미배정</span>'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex space-x-2">
                        <button onclick="event.stopPropagation(); this.editOrganization(${org.id})" 
                                class="text-blue-600 hover:text-blue-900 transition-colors"
                                title="편집">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="event.stopPropagation(); this.addActivity(${org.id})" 
                                class="text-green-600 hover:text-green-900 transition-colors"
                                title="활동 추가">
                            <i class="fas fa-plus-circle"></i>
                        </button>
                        <button onclick="event.stopPropagation(); this.deleteOrganization(${org.id})" 
                                class="text-red-600 hover:text-red-900 transition-colors"
                                title="삭제">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    // ===== 페이지네이션 렌더링 =====
    renderPagination(pagination) {
        if (!pagination || !pagination.total_pages || pagination.total_pages <= 1) {
            return '';
        }

        const { current_page, total_pages, total_items, per_page } = pagination;
        const { start, end } = Utils.calculatePagination(current_page, total_pages);
        
        const startItem = (current_page - 1) * per_page + 1;
        const endItem = Math.min(current_page * per_page, total_items);

        return `
            <div class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
                <div class="flex items-center justify-between">
                    <div class="flex-1 flex justify-between sm:hidden">
                        <!-- 모바일 페이지네이션 -->
                        <button onclick="crmSystem.updateFilters({page: ${current_page - 1}})" 
                                ${current_page <= 1 ? 'disabled' : ''}
                                class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                            이전
                        </button>
                        <button onclick="crmSystem.updateFilters({page: ${current_page + 1}})" 
                                ${current_page >= total_pages ? 'disabled' : ''}
                                class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                            다음
                        </button>
                    </div>
                    <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                        <div>
                            <p class="text-sm text-gray-700">
                                <span class="font-medium">${startItem}</span>
                                -
                                <span class="font-medium">${endItem}</span>
                                /
                                <span class="font-medium">${total_items}</span>
                                개 결과
                            </p>
                        </div>
                        <div>
                            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                                <!-- 이전 버튼 -->
                                <button onclick="crmSystem.updateFilters({page: ${current_page - 1}})" 
                                        ${current_page <= 1 ? 'disabled' : ''}
                                        class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                                    <i class="fas fa-chevron-left"></i>
                                </button>
                                
                                <!-- 페이지 번호들 -->
                                ${this.renderPageNumbers(start, end, current_page)}
                                
                                <!-- 다음 버튼 -->
                                <button onclick="crmSystem.updateFilters({page: ${current_page + 1}})" 
                                        ${current_page >= total_pages ? 'disabled' : ''}
                                        class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                                    <i class="fas fa-chevron-right"></i>
                                </button>
                            </nav>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    renderPageNumbers(start, end, current) {
        let html = '';
        
        for (let i = start; i <= end; i++) {
            const isActive = i === current;
            html += `
                <button onclick="crmSystem.updateFilters({page: ${i}})" 
                        class="relative inline-flex items-center px-4 py-2 border text-sm font-medium transition-colors ${
                            isActive 
                                ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' 
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }">
                    ${i}
                </button>
            `;
        }
        
        return html;
    },

    // ===== 크롤링 설정 렌더링 =====
    renderCrawlingSettings(crmSystem) {
        const isRunning = crmSystem.crawlingStatus?.isRunning || false;
        
        return `
            <div class="bg-white rounded-lg shadow mb-6 p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">크롤링 설정</h3>
                <form id="crawling-form" class="space-y-6">
                    <!-- 기본 설정 -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="flex items-center space-x-2">
                                <input type="checkbox" id="test-mode" 
                                       class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                       ${isRunning ? 'disabled' : ''}>
                                <span class="text-sm font-medium text-gray-700">테스트 모드</span>
                            </label>
                            <p class="mt-1 text-xs text-gray-500">소량의 데이터로 테스트합니다</p>
                        </div>
                        
                        <div>
                            <label class="flex items-center space-x-2">
                                <input type="checkbox" id="use-ai" checked 
                                       class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                       ${isRunning ? 'disabled' : ''}>
                                <span class="text-sm font-medium text-gray-700">AI 분석 사용</span>
                            </label>
                            <p class="mt-1 text-xs text-gray-500">Gemini API를 사용한 고급 분석</p>
                        </div>
                    </div>

                    <!-- 테스트 모드 상세 설정 -->
                    <div id="test-options" class="hidden">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-sm font-medium text-gray-900 mb-3">테스트 모드 설정</h4>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 mb-1">테스트 개수</label>
                                    <input type="number" id="test-count" value="10" min="1" max="100" 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                           ${isRunning ? 'disabled' : ''}>
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 mb-1">처리 간격 (초)</label>
                                    <input type="number" id="crawl-delay" value="2" min="1" max="10" 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                           ${isRunning ? 'disabled' : ''}>
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 mb-1">카테고리 선택</label>
                                    <select id="test-category" 
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            ${isRunning ? 'disabled' : ''}>
                                        <option value="">모든 카테고리</option>
                                        <option value="교회">교회</option>
                                        <option value="학원">학원</option>
                                        <option value="학교">학교</option>
                                        <option value="공공기관">공공기관</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 고급 설정 -->
                    <div>
                        <h4 class="text-sm font-medium text-gray-900 mb-3">고급 설정</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" id="save-intermediate" checked 
                                           class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                           ${isRunning ? 'disabled' : ''}>
                                    <span class="text-sm text-gray-700">중간 결과 저장</span>
                                </label>
                            </div>
                            <div>
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" id="skip-existing" 
                                           class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                           ${isRunning ? 'disabled' : ''}>
                                    <span class="text-sm text-gray-700">기존 데이터 건너뛰기</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- 컨트롤 버튼 -->
                    <div class="flex space-x-3 pt-4 border-t border-gray-200">
                        <button type="button" onclick="this.startCrawling()" 
                                id="start-crawling-btn"
                                ${isRunning ? 'disabled' : ''}
                                class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <i class="fas fa-play mr-2"></i>
                            ${isRunning ? '크롤링 진행 중...' : '크롤링 시작'}
                        </button>
                        
                        <button type="button" onclick="crmSystem.stopCrawling()" 
                                id="stop-crawling-btn"
                                ${!isRunning ? 'disabled' : ''}
                                class="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <i class="fas fa-stop mr-2"></i>중지
                        </button>
                        
                        <button type="button" onclick="this.showCrawlingHistory()" 
                                class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <i class="fas fa-history mr-2"></i>이력 보기
                        </button>
                    </div>
                </form>
            </div>
        `;
    },

    // ===== 크롤링 진행 상황 렌더링 =====
    renderCrawlingProgress(crawlingStatus) {
        if (!crawlingStatus) return '';

        const progress = crawlingStatus.progress || {};
        const percentage = progress.percentage || 0;

        return `
            <div class="bg-white rounded-lg shadow mb-6 p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">크롤링 진행 상황</h3>
                
                <!-- 진행률 바 -->
                <div class="mb-6">
                    <div class="flex justify-between text-sm text-gray-600 mb-2">
                        <span id="current-org-name">${progress.current_organization || '준비 중...'}</span>
                        <span id="progress-text">${progress.processed_count || 0} / ${progress.total_count || 0}</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                        <div id="progress-bar" 
                             class="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500 progress-animated" 
                             style="width: ${percentage}%">
                        </div>
                    </div>
                    <div class="text-center mt-2">
                        <span class="text-lg font-bold text-blue-600">${Math.round(percentage)}%</span>
                    </div>
                </div>

                <!-- 통계 카드 -->
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="bg-green-50 rounded-lg p-4 text-center">
                        <div class="text-2xl font-bold text-green-600" id="success-count">
                            ${progress.successful_count || 0}
                        </div>
                        <div class="text-sm text-green-700">성공</div>
                    </div>
                    <div class="bg-red-50 rounded-lg p-4 text-center">
                        <div class="text-2xl font-bold text-red-600" id="failed-count">
                            ${progress.failed_count || 0}
                        </div>
                        <div class="text-sm text-red-700">실패</div>
                    </div>
                    <div class="bg-blue-50 rounded-lg p-4 text-center">
                        <div class="text-2xl font-bold text-blue-600" id="total-processed">
                            ${progress.processed_count || 0}
                        </div>
                        <div class="text-sm text-blue-700">처리됨</div>
                    </div>
                </div>

                <!-- 상태 정보 -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="font-medium text-gray-700">상태:</span>
                            <span class="ml-2 text-gray-600" id="crawling-status">${progress.status || '실행 중'}</span>
                        </div>
                        <div>
                            <span class="font-medium text-gray-700">시작 시간:</span>
                            <span class="ml-2 text-gray-600" id="start-time">
                                ${crawlingStatus.startTime ? Utils.formatDate(crawlingStatus.startTime) : '-'}
                            </span>
                        </div>
                        <div>
                            <span class="font-medium text-gray-700">예상 완료:</span>
                            <span class="ml-2 text-gray-600" id="estimated-completion">계산 중...</span>
                        </div>
                        <div>
                            <span class="font-medium text-gray-700">평균 속도:</span>
                            <span class="ml-2 text-gray-600" id="average-speed">계산 중...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // ===== 크롤링 결과 렌더링 =====
    renderCrawlingResults(results) {
        if (!results || results.length === 0) {
            return `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-clock text-3xl mb-2"></i>
                    <p>크롤링을 시작하면 결과가 여기에 표시됩니다</p>
                </div>
            `;
        }

        return results.map(result => this.renderCrawlingResultItem(result)).join('');
    },

    renderCrawlingResultItem(result) {
        const statusColors = {
            'COMPLETED': 'bg-green-100 text-green-800 border-green-200',
            'FAILED': 'bg-red-100 text-red-800 border-red-200',
            'PROCESSING': 'bg-yellow-100 text-yellow-800 border-yellow-200'
        };

        const statusColor = statusColors[result.status] || 'bg-gray-100 text-gray-800 border-gray-200';

        return `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                        <h4 class="font-medium text-gray-900">${result.organization_name || '알 수 없음'}</h4>
                        <p class="text-sm text-gray-600">${result.category || ''}</p>
                    </div>
                    <span class="px-2 py-1 text-xs font-medium rounded-full border ${statusColor}">
                        ${result.status === 'COMPLETED' ? '완료' : result.status === 'FAILED' ? '실패' : '처리중'}
                    </span>
                </div>
                
                ${result.status === 'COMPLETED' ? `
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-gray-600">
                        ${result.phone ? `<div><i class="fas fa-phone text-green-500 mr-1"></i>${result.phone}</div>` : ''}
                        ${result.fax ? `<div><i class="fas fa-fax text-blue-500 mr-1"></i>${result.fax}</div>` : ''}
                        ${result.email ? `<div><i class="fas fa-envelope text-purple-500 mr-1"></i>${result.email}</div>` : ''}
                    </div>
                ` : result.error_message ? `
                    <div class="text-sm text-red-600 mt-2">
                        <i class="fas fa-exclamation-triangle mr-1"></i>${result.error_message}
                    </div>
                ` : ''}
                
                <div class="flex justify-between items-center mt-3 text-xs text-gray-500">
                    <span>${result.current_step || ''}</span>
                    <span>${result.processing_time ? `${result.processing_time}초` : ''}</span>
                </div>
            </div>
        `;
    },

    // ===== 최근 활동 렌더링 =====
    renderRecentActivities() {
        // TODO: 실제 API에서 데이터 가져오기
        const activities = [
            { type: 'system', message: '시스템이 시작되었습니다', time: new Date() },
            { type: 'crawling', message: '마지막 크롤링: 28,104개 기관 처리', time: new Date(Date.now() - 3600000) }
        ];

        if (activities.length === 0) {
            return `
                <div class="text-center py-4 text-gray-500">
                    <i class="fas fa-clock text-2xl mb-2"></i>
                    <p>최근 활동이 없습니다</p>
                </div>
            `;
        }

        return activities.map(activity => `
            <div class="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div class="flex-shrink-0">
                    <i class="fas fa-${this.getActivityIcon(activity.type)} text-gray-400"></i>
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">${activity.message}</p>
                    <p class="text-xs text-gray-500">${Utils.formatDate(activity.time)}</p>
                </div>
            </div>
        `).join('');
    },

    // ===== 크롤링 상태 카드 렌더링 =====
    renderCrawlingStatusCard(crawlingStatus) {
        if (!crawlingStatus || !crawlingStatus.isRunning) {
            return `
                <div class="text-center py-6 text-gray-500">
                    <i class="fas fa-pause-circle text-3xl mb-2"></i>
                    <p class="font-medium">진행 중인 크롤링이 없습니다</p>
                    <button onclick="crmSystem.navigateTo('crawling')" 
                            class="mt-2 text-blue-600 hover:text-blue-800 text-sm underline">
                        크롤링 시작하기
                    </button>
                </div>
            `;
        }

        const progress = crawlingStatus.progress || {};
        const percentage = progress.percentage || 0;

        return `
            <div class="space-y-4">
                <div class="flex justify-between text-sm text-gray-600">
                    <span>${progress.current_organization || '처리 중...'}</span>
                    <span>${progress.processed_count || 0} / ${progress.total_count || 0}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                         style="width: ${percentage}%"></div>
                </div>
                <div class="flex justify-between text-xs text-gray-500">
                    <span>진행률: ${Math.round(percentage)}%</span>
                    <button onclick="crmSystem.navigateTo('crawling')" 
                            class="text-blue-600 hover:text-blue-800 underline">
                        상세 보기
                    </button>
                </div>
            </div>
        `;
    },

    // ===== 기타 페이지들 =====
    renderActivities() {
        return `
            <div class="p-6">
                <div class="text-center py-12">
                    <i class="fas fa-tasks text-4xl text-gray-300 mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">영업 활동 관리</h3>
                    <p class="text-gray-500 mb-4">영업 활동 추적 기능을 준비 중입니다</p>
                    <div class="space-y-2">
                        <p class="text-sm text-gray-400">• 통화 기록 관리</p>
                        <p class="text-sm text-gray-400">• 미팅 일정 관리</p>
                        <p class="text-sm text-gray-400">• 영업 진행 상황 추적</p>
                    </div>
                </div>
            </div>
        `;
    },

    renderStatistics() {
        return `
            <div class="p-6">
                <div class="text-center py-12">
                    <i class="fas fa-chart-pie text-4xl text-gray-300 mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">통계 분석</h3>
                    <p class="text-gray-500 mb-4">상세한 데이터 분석 기능을 준비 중입니다</p>
                    <div class="space-y-2">
                        <p class="text-sm text-gray-400">• 지역별 분포 차트</p>
                        <p class="text-sm text-gray-400">• 카테고리별 통계</p>
                        <p class="text-sm text-gray-400">• 영업 성과 분석</p>
                    </div>
                </div>
            </div>
        `;
    },

    // ===== 유틸리티 메서드들 =====
    getOrgIcon(category) {
        const icons = {
            '교회': 'church',
            '학원': 'graduation-cap',
            '학교': 'school',
            '공공기관': 'landmark'
        };
        return icons[category] || 'building';
    },

    getPriorityClass(priority) {
        const classes = {
            '높음': 'text-red-600 font-medium',
            '보통': 'text-yellow-600',
            '낮음': 'text-green-600'
        };
        return classes[priority] || 'text-gray-600';
    },

    getActivityIcon(type) {
        const icons = {
            'system': 'cog',
            'crawling': 'spider',
            'contact': 'phone',
            'meeting': 'calendar',
            'email': 'envelope'
        };
        return icons[type] || 'circle';
    },

    // ===== 업데이트 메서드들 =====
    updateDashboardStats(stats) {
        // 대시보드 통계 업데이트 로직
        if (crmSystem.currentPage === 'dashboard') {
            this.renderCurrentPage(crmSystem);
        }
    },

    updateCrawlingProgress(progress, results) {
        // 크롤링 진행 상황 업데이트
        if (document.getElementById('progress-bar')) {
            document.getElementById('progress-bar').style.width = `${progress.percentage || 0}%`;
        }
        
        if (document.getElementById('current-org-name')) {
            document.getElementById('current-org-name').textContent = progress.current_organization || '처리 중...';
        }
        
        // 결과 업데이트
        const resultsContainer = document.getElementById('crawling-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = this.renderCrawlingResults(results);
        }
    },

    updateCrawlingControls(isRunning) {
        const startBtn = document.getElementById('start-crawling-btn');
        const stopBtn = document.getElementById('stop-crawling-btn');
        
        if (startBtn) {
            startBtn.disabled = isRunning;
            startBtn.textContent = isRunning ? '크롤링 진행 중...' : '크롤링 시작';
        }
        
        if (stopBtn) {
            stopBtn.disabled = !isRunning;
        }
    },

    // ===== 모달 및 이벤트 핸들러들 =====
    async startCrawling() {
        const config = {
            test_mode: document.getElementById('test-mode')?.checked || false,
            test_count: parseInt(document.getElementById('test-count')?.value || '10'),
            use_ai: document.getElementById('use-ai')?.checked || true,
            save_intermediate: document.getElementById('save-intermediate')?.checked || true,
            skip_existing: document.getElementById('skip-existing')?.checked || false,
            crawl_delay: parseInt(document.getElementById('crawl-delay')?.value || '2'),
            category: document.getElementById('test-category')?.value || ''
        };

        await crmSystem.startCrawling(config);
    },

    async editOrganization(id) {
        // TODO: 기관 편집 모달 구현
        console.log('기관 편집:', id);
    },

    async deleteOrganization(id) {
        if (confirm('정말로 이 기관을 삭제하시겠습니까?')) {
            await crmSystem.deleteOrganization(id);
        }
    },

    showAddOrganizationModal() {
        // TODO: 기관 추가 모달 구현
        console.log('기관 추가 모달');
    },

    showOrganizationDetail(id) {
        // TODO: 기관 상세 정보 모달 구현
        console.log('기관 상세:', id);
    }
};

// 테스트 모드 체크박스 이벤트 바인딩
document.addEventListener('change', function(e) {
    if (e.target.id === 'test-mode') {
        const testOptions = document.getElementById('test-options');
        if (testOptions) {
            testOptions.classList.toggle('hidden', !e.target.checked);
        }
    }
});



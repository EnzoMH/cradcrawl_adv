// ===== CRM 시스템 메인 로직 =====

class CRMSystem {
    constructor() {
        this.currentUser = null;
        this.organizations = [];
        this.currentPage = 'dashboard';
        this.crawlingStatus = null;
        this.filters = {
            search: '',
            category: '',
            status: '',
            page: 1,
            perPage: 20
        };
        this.intervals = {
            crawling: null,
            dashboard: null
        };
    }

    // ===== 초기화 =====
    async init() {
        try {
            await this.checkAuth();
            await this.loadInitialData();
            UI.renderApp(this);
            this.startBackgroundTasks();
        } catch (error) {
            console.error('시스템 초기화 실패:', error);
            UI.showError('시스템을 시작할 수 없습니다.');
        }
    }

    // ===== 인증 관련 =====
    async checkAuth() {
        // TODO: 실제 인증 구현시 추가
        this.currentUser = {
            id: 1,
            username: 'admin',
            role: '관리자',
            fullName: '시스템 관리자'
        };
    }

    async logout() {
        try {
            // await this.api.logout();
            this.currentUser = null;
            window.location.reload();
        } catch (error) {
            console.error('로그아웃 실패:', error);
        }
    }

    // ===== 데이터 관리 =====
    async loadInitialData() {
        const promises = [
            this.loadDashboardStats(),
            this.checkCrawlingStatus()
        ];
        
        if (this.currentPage === 'organizations') {
            promises.push(this.loadOrganizations());
        }
        
        await Promise.allSettled(promises);
    }

    async loadDashboardStats() {
        try {
            console.log('🔄 대시보드 통계 로드 시작');
            const response = await fetch('/api/statistics');
            
            if (!response.ok) {
                throw new Error(`API 오류: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('🔄 API 데이터:', data);
            
            if (data.status === 'success') {
                this.dashboardStats = data.data;
            } else {
                throw new Error('API 응답 상태가 success가 아님');
            }
        } catch (error) {
            console.error('❌ 대시보드 통계 로드 실패:', error);
            
            // 기본값 설정
            this.dashboardStats = {
                total_organizations: 0,
                total_users: 0,
                recent_activities: 0,
                crawling_jobs: 0
            };
            console.log('📝 기본 통계값 설정됨');
        }
    }

    async loadOrganizations(resetPage = false) {
        try {
            if (resetPage) this.filters.page = 1;
            
            const params = new URLSearchParams({
                page: this.filters.page,
                per_page: this.filters.perPage
            });
            
            if (this.filters.search) params.append('search', this.filters.search);
            if (this.filters.category) params.append('category', this.filters.category);
            if (this.filters.status) params.append('status', this.filters.status);
            
            const response = await fetch(`/api/organizations?${params}`);
            const data = await response.json();
            
            if (response.ok) {
                this.organizations = data.organizations || [];
                this.pagination = data.pagination || {};
                UI.renderOrganizationsList(this.organizations, this.pagination);
            } else {
                throw new Error(data.message || '기관 목록 로드 실패');
            }
        } catch (error) {
            console.error('기관 목록 로드 실패:', error);
            UI.showError('기관 목록을 불러올 수 없습니다.');
        }
    }

    async getOrganizationDetail(id) {
        try {
            const response = await fetch(`/api/organizations/${id}`);
            const data = await response.json();
            
            if (response.ok) {
                return data.organization;
            } else {
                throw new Error(data.message || '기관 정보 로드 실패');
            }
        } catch (error) {
            console.error('기관 상세 정보 로드 실패:', error);
            UI.showError('기관 정보를 불러올 수 없습니다.');
    return null;
}
    }

    async updateOrganization(id, updates) {
        try {
            const response = await fetch(`/api/organizations/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                UI.showSuccess('기관 정보가 업데이트되었습니다.');
                await this.loadOrganizations();
                return true;
            } else {
                throw new Error(data.message || '업데이트 실패');
            }
        } catch (error) {
            console.error('기관 업데이트 실패:', error);
            UI.showError('기관 정보 업데이트에 실패했습니다.');
            return false;
        }
    }

    async deleteOrganization(id) {
        if (!confirm('정말로 이 기관을 삭제하시겠습니까?')) return false;
        
        try {
            const response = await fetch(`/api/organizations/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                UI.showSuccess('기관이 삭제되었습니다.');
                await this.loadOrganizations();
                return true;
            } else {
                throw new Error('삭제 실패');
            }
        } catch (error) {
            console.error('기관 삭제 실패:', error);
            UI.showError('기관 삭제에 실패했습니다.');
            return false;
        }
    }

    // ===== 크롤링 관련 =====
    async startCrawling(config) {
        try {
            const response = await fetch('/api/start-enhanced-crawling', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.crawlingStatus = {
                    jobId: data.job_id,
                    isRunning: true,
                    startTime: new Date()
                };
                
                this.startCrawlingMonitoring();
                UI.showSuccess('크롤링이 시작되었습니다!');
                UI.updateCrawlingControls(true);
                
                return true;
            } else {
                throw new Error(data.detail || '크롤링 시작 실패');
            }
        } catch (error) {
            console.error('크롤링 시작 실패:', error);
            UI.showError('크롤링을 시작할 수 없습니다.');
            return false;
        }
    }

    async stopCrawling() {
        try {
            const response = await fetch('/api/stop-crawling', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.stopCrawlingMonitoring();
                this.crawlingStatus = null;
                UI.showSuccess('크롤링이 중지되었습니다.');
                UI.updateCrawlingControls(false);
                return true;
            }
        } catch (error) {
            console.error('크롤링 중지 실패:', error);
            UI.showError('크롤링 중지에 실패했습니다.');
            return false;
        }
    }

    async checkCrawlingStatus() {
        try {
            const response = await fetch('/api/progress');
            const data = await response.json();
            
            if (data.status && data.status !== 'idle') {
                this.crawlingStatus = {
                    isRunning: true,
                    progress: data
                };
                this.startCrawlingMonitoring();
                UI.updateCrawlingControls(true);
            } else {
                this.crawlingStatus = null;
                UI.updateCrawlingControls(false);
            }
            
            return data;
        } catch (error) {
            console.error('크롤링 상태 확인 실패:', error);
            return null;
        }
    }

    startCrawlingMonitoring() {
        if (this.intervals.crawling) return;
        
        this.intervals.crawling = setInterval(async () => {
            try {
                const progress = await fetch('/api/progress').then(r => r.json());
                const results = await fetch('/api/real-time-results?limit=5').then(r => r.json());
                
                if (progress.status === 'completed' || progress.status === 'error') {
                    this.stopCrawlingMonitoring();
                    this.crawlingStatus = null;
                    UI.updateCrawlingControls(false);
                    
                    if (progress.status === 'completed') {
                        UI.showSuccess('크롤링이 완료되었습니다!');
                        await this.loadDashboardStats(); // 통계 갱신
                    } else {
                        UI.showError('크롤링 중 오류가 발생했습니다.');
                    }
                } else {
                    this.crawlingStatus.progress = progress;
                    UI.updateCrawlingProgress(progress, results.results || []);
                }
            } catch (error) {
                console.error('크롤링 모니터링 오류:', error);
            }
        }, 2000);
    }

    stopCrawlingMonitoring() {
        if (this.intervals.crawling) {
            clearInterval(this.intervals.crawling);
            this.intervals.crawling = null;
        }
    }

    // ===== 페이지 네비게이션 =====
    async navigateTo(page) {
        if (this.currentPage === page) return;
        
        this.currentPage = page;
        
        // 페이지별 데이터 로드
        switch(page) {
            case 'dashboard':
                await this.loadDashboardStats();
                break;
            case 'organizations':
                await this.loadOrganizations();
                break;
            case 'crawling':
                await this.checkCrawlingStatus();
                break;
        }
        
        UI.renderCurrentPage(this);
    }

    // ===== 검색 및 필터 =====
    updateFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
        this.loadOrganizations(true);
    }

    resetFilters() {
        this.filters = {
            search: '',
            category: '',
            status: '',
            page: 1,
            perPage: 20
        };
        this.loadOrganizations(true);
    }

    // ===== 백그라운드 작업 =====
    startBackgroundTasks() {
        // 대시보드 자동 갱신 (5분마다)
        this.intervals.dashboard = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardStats();
            }
        }, 5 * 60 * 1000);
    }

    // ===== 정리 =====
    destroy() {
        Object.values(this.intervals).forEach(interval => {
            if (interval) clearInterval(interval);
        });
    }
}

// ===== 전역 유틸리티 함수들 =====

const Utils = {
    // 날짜 포맷팅
    formatDate(date) {
        if (!date) return '-';
        return new Date(date).toLocaleString('ko-KR');
    },

    // 숫자 포맷팅
    formatNumber(num) {
        if (!num) return '0';
        return num.toLocaleString('ko-KR');
    },

    // 상태 클래스 반환
    getStatusClass(status) {
        const classes = {
            '신규': 'bg-gray-100 text-gray-800',
            '접촉완료': 'bg-blue-100 text-blue-800', 
            '관심있음': 'bg-yellow-100 text-yellow-800',
            '협상중': 'bg-orange-100 text-orange-800',
            '성사': 'bg-green-100 text-green-800',
            '실패': 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    },

    // 디바운스
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
    },

    // 페이지네이션 계산
    calculatePagination(current, total, visiblePages = 5) {
        const half = Math.floor(visiblePages / 2);
        let start = Math.max(current - half, 1);
        let end = Math.min(start + visiblePages - 1, total);
        
        if (end - start + 1 < visiblePages) {
            start = Math.max(end - visiblePages + 1, 1);
        }
        
        return { start, end };
    }
};

// ===== 전역 인스턴스 생성 =====
let crmSystem;

// ===== 초기화 =====
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔄 DOM 로드 완료');
    
    try {
        console.log('🔄 UI 객체 확인:', typeof UI);
        if (typeof UI === 'undefined') {
            throw new Error('UI 객체가 정의되지 않았습니다');
        }
        
        console.log('🔄 CRMSystem 인스턴스 생성');
        crmSystem = new CRMSystem();
        
        console.log('🔄 시스템 초기화 시작');
        await crmSystem.init();
        
        console.log('✅ 시스템 초기화 완료');
    } catch (error) {
        console.error('❌ CRM 시스템 초기화 실패:', error);
        document.getElementById('app-root').innerHTML = `
            <div class="h-screen flex items-center justify-center bg-red-50">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-6xl text-red-500 mb-4"></i>
                    <h1 class="text-2xl font-bold text-red-800 mb-2">시스템 오류</h1>
                    <p class="text-red-600 mb-4">CRM 시스템을 시작할 수 없습니다.</p>
                    <p class="text-red-500 mb-4 text-sm">오류: ${error.message}</p>
                    <button onclick="window.location.reload()" 
                            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded">
                        다시 시도
                    </button>
                </div>
            </div>
        `;
    }
});

// 페이지 언로드시 정리
window.addEventListener('beforeunload', () => {
    if (crmSystem) {
        crmSystem.destroy();
    }
}); 
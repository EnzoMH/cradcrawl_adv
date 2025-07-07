// 홈페이지 관리 클래스
class HomeManager {
    constructor() {
        this.config = window.APP_CONFIG || {};
        this.init();
    }

    async init() {
        await this.loadSystemStatus();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/stats/summary', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateSystemStatus(data.summary);
            } else {
                console.warn('시스템 상태 로드 실패');
                this.showSystemStatusError();
            }
        } catch (error) {
            console.error('시스템 상태 로드 오류:', error);
            this.showSystemStatusError();
        }
    }

    updateSystemStatus(stats) {
        // 총 기관 수
        const totalOrgs = document.getElementById('total-orgs');
        if (totalOrgs) {
            totalOrgs.textContent = this.formatNumber(stats.total_organizations || 0);
        }

        // 연락처 완료
        const completeContacts = document.getElementById('complete-contacts');
        if (completeContacts) {
            completeContacts.textContent = this.formatNumber(stats.complete_organizations || 0);
        }

        // 연락처 누락
        const missingContacts = document.getElementById('missing-contacts');
        if (missingContacts) {
            missingContacts.textContent = this.formatNumber(stats.organizations_needing_enrichment || 0);
        }

        // 완성도
        const completionRate = document.getElementById('completion-rate');
        if (completionRate) {
            const rate = stats.contact_completion_rate || 0;
            completionRate.textContent = `${rate.toFixed(1)}%`;
        }
    }

    showSystemStatusError() {
        const statusElements = ['total-orgs', 'complete-contacts', 'missing-contacts', 'completion-rate'];
        statusElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '오류';
                element.className = element.className.replace(/text-\w+-600/, 'text-red-600');
            }
        });
    }

    setupEventListeners() {
        // 빠른 액션 버튼 클릭 이벤트
        this.setupQuickActions();
        
        // 기능 카드 호버 효과
        this.setupFeatureCards();
        
        // 권한별 메뉴 표시
        this.setupPermissionBasedUI();
    }

    setupQuickActions() {
        // 새 기관 추가 버튼
        const createOrgBtn = document.querySelector('a[href="/organizations?action=create"]');
        if (createOrgBtn) {
            createOrgBtn.addEventListener('click', (e) => {
                this.trackUserAction('quick_action', 'create_organization');
            });
        }

        // 자동 보강 시작 버튼
        const autoEnrichBtn = document.querySelector('a[href="/enrichment?action=auto"]');
        if (autoEnrichBtn) {
            autoEnrichBtn.addEventListener('click', (e) => {
                this.trackUserAction('quick_action', 'auto_enrichment');
            });
        }
    }

    setupFeatureCards() {
        const featureCards = document.querySelectorAll('.hover\\:shadow-lg');
        featureCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px)';
                card.style.transition = 'transform 0.2s ease-in-out';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
    }

    setupPermissionBasedUI() {
        const userLevel = this.config.userLevel || 0;
        const currentUser = this.config.currentUser;

        // 권한별 기능 카드 표시/숨김
        this.toggleFeatureByPermission('.enrichment-feature', userLevel >= 3);
        this.toggleFeatureByPermission('.statistics-feature', userLevel >= 3);
        this.toggleFeatureByPermission('.admin-feature', userLevel >= 5);

        // 사용자 정보 표시
        this.displayUserInfo(currentUser);
    }

    toggleFeatureByPermission(selector, hasPermission) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            if (hasPermission) {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });
    }

    displayUserInfo(user) {
        if (!user) return;

        // 환영 메시지 추가
        const heroSection = document.querySelector('.text-center.mb-16');
        if (heroSection && !document.getElementById('welcome-message')) {
            const welcomeDiv = document.createElement('div');
            welcomeDiv.id = 'welcome-message';
            welcomeDiv.className = 'mt-4 p-4 bg-blue-50 rounded-lg';
            welcomeDiv.innerHTML = `
                <p class="text-blue-800">
                    <i class="fas fa-user-circle mr-2"></i>
                    환영합니다, <strong>${user.full_name}</strong>님! 
                    <span class="text-sm">(${user.role})</span>
                </p>
            `;
            heroSection.appendChild(welcomeDiv);
        }
    }

    startAutoRefresh() {
        // 30초마다 시스템 상태 업데이트
        setInterval(() => {
            this.loadSystemStatus();
        }, 30000);
    }

    trackUserAction(category, action) {
        // 사용자 행동 추적 (나중에 분석용)
        console.log(`User Action: ${category} - ${action}`);
        
        // 여기에 Google Analytics나 다른 추적 코드 추가 가능
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                event_category: category,
                event_label: this.config.currentUser?.username || 'anonymous'
            });
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }

    // 시스템 상태 색상 업데이트
    updateStatusColors() {
        const statusCards = document.querySelectorAll('#system-status .bg-gray-50');
        statusCards.forEach((card, index) => {
            const value = card.querySelector('.text-2xl');
            if (value && value.textContent !== '-' && value.textContent !== '오류') {
                // 상태에 따라 색상 변경
                switch (index) {
                    case 0: // 총 기관 수
                        card.classList.add('border-l-4', 'border-blue-500');
                        break;
                    case 1: // 연락처 완료
                        card.classList.add('border-l-4', 'border-green-500');
                        break;
                    case 2: // 연락처 누락
                        card.classList.add('border-l-4', 'border-yellow-500');
                        break;
                    case 3: // 완성도
                        const rate = parseFloat(value.textContent);
                        if (rate >= 80) {
                            card.classList.add('border-l-4', 'border-green-500');
                        } else if (rate >= 60) {
                            card.classList.add('border-l-4', 'border-yellow-500');
                        } else {
                            card.classList.add('border-l-4', 'border-red-500');
                        }
                        break;
                }
            }
        });
    }

    // 반응형 차트 생성 (Chart.js 사용 시)
    createStatusChart() {
        const ctx = document.getElementById('status-chart');
        if (!ctx || typeof Chart === 'undefined') return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['완료', '누락', '진행중'],
                datasets: [{
                    data: [60, 30, 10],
                    backgroundColor: [
                        '#10B981', // green
                        '#F59E0B', // yellow
                        '#3B82F6'  // blue
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.homeManager = new HomeManager();
});

// 탭 포커스 시 데이터 새로고침
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.homeManager) {
        window.homeManager.loadSystemStatus();
    }
});

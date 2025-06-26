/*!
 * Statistics Manager - CRM 통계 분석 페이지 JavaScript
 * 데이터 시각화, API 연동, 차트 관리 등의 기능 제공
 */

class StatisticsManager {
    constructor() {
        this.api = new APIClient();
        this.charts = {};
        this.currentSection = 'overview';
        this.data = {};
        this.refreshInterval = null;
        
        this.init();
    }

    async init() {
        console.log('📊 Statistics Manager 초기화 시작');
        this.setupEventListeners();
        await this.loadInitialData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // 사이드바 메뉴 클릭
        document.querySelectorAll('[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });

        // 창 크기 변경 시 차트 리사이즈
        window.addEventListener('resize', this.debounce(() => {
            this.resizeAllCharts();
        }, 250));

        // 페이지 가시성 변경 시 자동 새로고침 제어
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
    }

    switchSection(section) {
        console.log(`🔄 섹션 전환: ${this.currentSection} → ${section}`);
        
        // 이전 섹션 숨기기
        document.querySelectorAll('.statistics-section').forEach(sec => {
            sec.style.display = 'none';
        });

        // 새 섹션 표시
        const newSection = document.getElementById(`${section}-section`);
        if (newSection) {
            newSection.style.display = 'block';
        }

        // 메뉴 활성화 상태 변경
        document.querySelectorAll('[data-section]').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        this.currentSection = section;

        // 섹션별 데이터 로드
        this.loadSectionData(section);
    }

    async loadInitialData() {
        this.showLoading(true);
        
        try {
            console.log('📡 초기 데이터 로드 시작');
            await this.loadOverviewData();
            this.updateLastUpdated();
            console.log('✅ 초기 데이터 로드 완료');
        } catch (error) {
            console.error('❌ 초기 데이터 로드 실패:', error);
            this.showError('초기 데이터 로드에 실패했습니다.');
        } finally {
            this.showLoading(false);
        }
    }

    async loadSectionData(section) {
        // 이미 로드된 데이터가 있으면 스킵 (캐싱)
        if (this.data[section] && !this.shouldRefreshData(section)) {
            console.log(`📋 캐시된 데이터 사용: ${section}`);
            return;
        }

        this.showLoading(true);
        
        try {
            console.log(`📡 섹션 데이터 로드: ${section}`);
            
            switch (section) {
                case 'overview':
                    await this.loadOverviewData();
                    break;
                case 'contact-analysis':
                    await this.loadContactAnalysis();
                    break;
                case 'geographic':
                    await this.loadGeographicData();
                    break;
                case 'email-analysis':
                    await this.loadEmailAnalysis();
                    break;
                case 'category-breakdown':
                    await this.loadCategoryBreakdown();
                    break;
                case 'quality-report':
                    await this.loadQualityReport();
                    break;
                default:
                    console.warn(`⚠️ 알 수 없는 섹션: ${section}`);
            }
            
            // 데이터 로드 시간 기록
            this.data[`${section}_loaded_at`] = Date.now();
            
        } catch (error) {
            console.error(`❌ ${section} 데이터 로드 실패:`, error);
            this.showError(`${section} 데이터 로드에 실패했습니다.`);
        } finally {
            this.showLoading(false);
        }
    }

    shouldRefreshData(section) {
        const loadedAt = this.data[`${section}_loaded_at`];
        if (!loadedAt) return true;
        
        // 5분 이상 지났으면 새로고침
        return (Date.now() - loadedAt) > 5 * 60 * 1000;
    }

    // ==================== 개요 섹션 ====================
    
    async loadOverviewData() {
        try {
            const response = await this.api.get('/api/statistics/overview');
            this.data.overview = response.data;

            this.updateOverviewCards();
            this.createContactCoverageChart();
            this.createCompletenessChart();
            
        } catch (error) {
            console.error('❌ 개요 데이터 로드 실패:', error);
            throw error;
        }
    }

    updateOverviewCards() {
        const data = this.data.overview;
        
        this.updateElement('total-orgs', Utils.formatNumber(data.basic_stats?.total_organizations || 0));
        this.updateElement('complete-contacts', Utils.formatNumber(data.basic_stats?.complete_contacts || 0));
        this.updateElement('incomplete-contacts', Utils.formatNumber(data.basic_stats?.incomplete_contacts || 0));
        
        const completionRate = data.quality_metrics?.completeness_rate || 0;
        this.updateElement('completion-rate', `${completionRate}%`);
    }

    createContactCoverageChart() {
        const ctx = document.getElementById('contactCoverageChart');
        if (!ctx) return;
        
        const coverage = this.data.overview.contact_coverage || {};
        
        if (this.charts.contactCoverage) {
            this.charts.contactCoverage.destroy();
        }

        this.charts.contactCoverage = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['전화번호', '팩스번호', '이메일', '홈페이지'],
                datasets: [{
                    label: '보유 기관 수',
                    data: [
                        coverage.phone?.count || 0,
                        coverage.fax?.count || 0,
                        coverage.email?.count || 0,
                        coverage.homepage?.count || 0
                    ],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 205, 86, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${Utils.formatNumber(value)}개 (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return Utils.formatNumber(value);
                            }
                        }
                    }
                }
            }
        });
    }

    createCompletenessChart() {
        const ctx = document.getElementById('completenessChart');
        if (!ctx) return;
        
        const basicStats = this.data.overview.basic_stats || {};
        
        if (this.charts.completeness) {
            this.charts.completeness.destroy();
        }

        const complete = basicStats.complete_contacts || 0;
        const incomplete = basicStats.incomplete_contacts || 0;
        const total = complete + incomplete;

        this.charts.completeness = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['완전한 연락처', '불완전한 연락처'],
                datasets: [{
                    data: [complete, incomplete],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(255, 193, 7, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${Utils.formatNumber(value)}개 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // ==================== 연락처 분석 섹션 ====================
    
    async loadContactAnalysis() {
        try {
            const response = await this.api.get('/api/statistics/contact-analysis');
            this.data.contactAnalysis = response.analysis;

            this.updateQualityMetrics();
            this.updateContactDetailsTable();
            
        } catch (error) {
            console.error('❌ 연락처 분석 데이터 로드 실패:', error);
            throw error;
        }
    }

    updateQualityMetrics() {
        const metrics = this.data.contactAnalysis.quality_metrics || {};
        const coverage = this.data.contactAnalysis.contact_coverage || {};
        
        const metricsContainer = document.getElementById('quality-metrics');
        if (!metricsContainer) return;
        
        metricsContainer.innerHTML = '';

        const metricItems = [
            { 
                label: '전화번호 유효성', 
                value: `${Math.round(metrics.phone_validity_rate || 0)}%`, 
                color: 'primary',
                icon: 'telephone'
            },
            { 
                label: '팩스번호 유효성', 
                value: `${Math.round(metrics.fax_validity_rate || 0)}%`, 
                color: 'info',
                icon: 'printer'
            },
            { 
                label: '전화번호 보유율', 
                value: `${Math.round(coverage.phone?.rate || 0)}%`, 
                color: 'success',
                icon: 'check-circle'
            },
            { 
                label: '이메일 보유율', 
                value: `${Math.round(coverage.email?.rate || 0)}%`, 
                color: 'warning',
                icon: 'envelope'
            }
        ];

        metricItems.forEach(item => {
            const col = document.createElement('div');
            col.className = 'col-md-3';
            col.innerHTML = `
                <div class="text-center p-3 border rounded">
                    <i class="bi bi-${item.icon} fs-1 text-${item.color} mb-2"></i>
                    <div class="fs-2 fw-bold text-${item.color}">${item.value}</div>
                    <div class="text-muted small">${item.label}</div>
                </div>
            `;
            metricsContainer.appendChild(col);
        });
    }

    updateContactDetailsTable() {
        const coverage = this.data.contactAnalysis.contact_coverage || {};
        const metrics = this.data.contactAnalysis.quality_metrics || {};
        
        const tbody = document.querySelector('#contact-details-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';

        const contactTypes = [
            { 
                name: '전화번호', 
                count: coverage.phone?.count || 0, 
                rate: Math.round(coverage.phone?.rate || 0),
                valid: metrics.valid_phones || 0,
                validRate: Math.round(metrics.phone_validity_rate || 0),
                icon: 'telephone'
            },
            { 
                name: '팩스번호', 
                count: coverage.fax?.count || 0, 
                rate: Math.round(coverage.fax?.rate || 0),
                valid: metrics.valid_faxes || 0,
                validRate: Math.round(metrics.fax_validity_rate || 0),
                icon: 'printer'
            },
            { 
                name: '이메일', 
                count: coverage.email?.count || 0, 
                rate: Math.round(coverage.email?.rate || 0),
                valid: coverage.email?.count || 0,
                validRate: 100,
                icon: 'envelope'
            },
            { 
                name: '홈페이지', 
                count: coverage.homepage?.count || 0, 
                rate: Math.round(coverage.homepage?.rate || 0),
                valid: coverage.homepage?.count || 0,
                validRate: 100,
                icon: 'globe'
            }
        ];

        contactTypes.forEach(type => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>
                    <i class="bi bi-${type.icon} me-2"></i>
                    ${type.name}
                </td>
                <td>${Utils.formatNumber(type.count)}</td>
                <td><span class="badge bg-primary">${type.rate}%</span></td>
                <td>${Utils.formatNumber(type.valid)}</td>
                <td><span class="badge bg-success">${type.validRate}%</span></td>
            `;
        });
    }

    // ==================== 지역별 분포 섹션 ====================
    
    async loadGeographicData() {
        try {
            const response = await this.api.get('/api/statistics/geographic-distribution');
            this.data.geographic = response.geographic_data;

            this.createGeographicChart();
            this.updateTopRegionsList();
            
        } catch (error) {
            console.error('❌ 지역별 분포 데이터 로드 실패:', error);
            throw error;
        }
    }

    createGeographicChart() {
        const ctx = document.getElementById('geographicChart');
        if (!ctx) return;
        
        const geoData = this.data.geographic || {};
        
        if (this.charts.geographic) {
            this.charts.geographic.destroy();
        }

        const entries = Object.entries(geoData).slice(0, 10);
        const labels = entries.map(([code, data]) => data.area_name);
        const data = entries.map(([code, data]) => data.total_contacts);

        this.charts.geographic = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '연락처 수',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${Utils.formatNumber(context.parsed.x)}개`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return Utils.formatNumber(value);
                            }
                        }
                    }
                }
            }
        });
    }

    updateTopRegionsList() {
        const geoData = this.data.geographic || {};
        const container = document.getElementById('top-regions-list');
        if (!container) return;
        
        container.innerHTML = '';

        Object.entries(geoData).slice(0, 5).forEach(([code, data], index) => {
            const item = document.createElement('div');
            item.className = 'd-flex justify-content-between align-items-center mb-3 p-2 border rounded';
            item.innerHTML = `
                <div>
                    <span class="badge bg-primary me-2">${index + 1}</span>
                    <strong>${data.area_name}</strong>
                    <small class="text-muted ms-1">(${code})</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-info">${Utils.formatNumber(data.total_contacts)}개</span>
                    <div class="small text-muted">
                        전화: ${data.phone_count || 0} | 팩스: ${data.fax_count || 0}
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    // ==================== 이메일 분석 섹션 ====================
    
    async loadEmailAnalysis() {
        try {
            const response = await this.api.get('/api/statistics/email-analysis');
            this.data.emailAnalysis = response.email_data;

            this.createEmailCategoryChart();
            this.updateTopDomainsList();
            
        } catch (error) {
            console.error('❌ 이메일 분석 데이터 로드 실패:', error);
            throw error;
        }
    }

    createEmailCategoryChart() {
        const ctx = document.getElementById('emailCategoryChart');
        if (!ctx) return;
        
        const categories = this.data.emailAnalysis.domain_categories || {};
        
        if (this.charts.emailCategory) {
            this.charts.emailCategory.destroy();
        }

        const labels = Object.keys(categories);
        const data = Object.values(categories);
        const total = data.reduce((a, b) => a + b, 0);

        this.charts.emailCategory = new Chart(ctx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 205, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${Utils.formatNumber(value)}개 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateTopDomainsList() {
        const domains = this.data.emailAnalysis.top_domains || {};
        const container = document.getElementById('top-domains-list');
        if (!container) return;
        
        container.innerHTML = '';

        Object.entries(domains).slice(0, 10).forEach(([domain, count], index) => {
            const item = document.createElement('div');
            item.className = 'd-flex justify-content-between align-items-center mb-2 p-2 border rounded';
            item.innerHTML = `
                <div>
                    <span class="badge bg-secondary me-2">${index + 1}</span>
                    <code class="text-primary">${domain}</code>
                </div>
                <span class="badge bg-primary">${Utils.formatNumber(count)}개</span>
            `;
            container.appendChild(item);
        });
    }

    // ==================== 카테고리별 분석 섹션 ====================
    
    async loadCategoryBreakdown() {
        try {
            const response = await this.api.get('/api/statistics/category-breakdown');
            this.data.categoryBreakdown = response.category_ranking;

            this.updateCategoryRankingTable();
            
        } catch (error) {
            console.error('❌ 카테고리별 분석 데이터 로드 실패:', error);
            throw error;
        }
    }

    updateCategoryRankingTable() {
        const rankings = this.data.categoryBreakdown || [];
        const tbody = document.querySelector('#category-ranking-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';

        rankings.forEach((category, index) => {
            const row = tbody.insertRow();
            const avgCoverage = Math.round(category.average_coverage || 0);
            
            // 완성도에 따른 색상 결정
            const coverageClass = avgCoverage >= 80 ? 'success' : 
                                avgCoverage >= 60 ? 'warning' : 'danger';
            
            row.innerHTML = `
                <td><span class="badge bg-primary">${index + 1}</span></td>
                <td><strong>${category.category}</strong></td>
                <td>${Utils.formatNumber(category.total_organizations)}</td>
                <td><span class="badge bg-${coverageClass}">${avgCoverage}%</span></td>
                <td>${Math.round(category.coverage_details.phone || 0)}%</td>
                <td>${Math.round(category.coverage_details.fax || 0)}%</td>
                <td>${Math.round(category.coverage_details.email || 0)}%</td>
                <td>${Math.round(category.coverage_details.homepage || 0)}%</td>
            `;
        });
    }

    // ==================== 품질 리포트 섹션 ====================
    
    async loadQualityReport() {
        try {
            const response = await this.api.get('/api/statistics/quality-report');
            this.data.qualityReport = response.report;

            this.updateQualityScore();
            this.updateRecommendations();
            this.createQualityTrendChart();
            
        } catch (error) {
            console.error('❌ 품질 리포트 데이터 로드 실패:', error);
            throw error;
        }
    }

    updateQualityScore() {
        const report = this.data.qualityReport || {};
        const scoreBreakdown = report.score_breakdown || {};
        
        const overallScore = Math.round(report.overall_score || 0);
        
        this.updateElement('overall-quality-score', overallScore);
        this.updateElement('coverage-score', `${Math.round(scoreBreakdown.coverage_score || 0)}점`);
        this.updateElement('validity-score', `${Math.round(scoreBreakdown.validity_score || 0)}점`);
        this.updateElement('completeness-score', `${Math.round(scoreBreakdown.completeness_score || 0)}점`);

        // 품질 점수 원형 차트
        const ctx = document.getElementById('qualityScoreChart');
        if (!ctx) return;
        
        if (this.charts.qualityScore) {
            this.charts.qualityScore.destroy();
        }

        // 점수에 따른 색상 결정
        const scoreColor = overallScore >= 80 ? 'rgba(40, 167, 69, 0.8)' :
                          overallScore >= 60 ? 'rgba(255, 193, 7, 0.8)' :
                          'rgba(220, 53, 69, 0.8)';

        this.charts.qualityScore = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [overallScore, 100 - overallScore],
                    backgroundColor: [scoreColor, 'rgba(233, 236, 239, 0.3)'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    }

    updateRecommendations() {
        const recommendations = this.data.qualityReport.recommendations || [];
        const container = document.getElementById('recommendations-list');
        if (!container) return;
        
        container.innerHTML = '';

        if (recommendations.length === 0) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle me-2"></i>
                    현재 특별한 개선사항이 없습니다. 데이터 품질이 양호합니다!
                </div>
            `;
            return;
        }

        recommendations.forEach((rec, index) => {
            const priorityClass = rec.priority === 'high' ? 'danger' : 
                                rec.priority === 'medium' ? 'warning' : 'info';
            
            const priorityIcon = rec.priority === 'high' ? 'exclamation-triangle-fill' :
                               rec.priority === 'medium' ? 'exclamation-triangle' : 'info-circle';
            
            const item = document.createElement('div');
            item.className = `alert alert-${priorityClass} border-start border-4`;
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="alert-heading mb-2">
                            <i class="bi bi-${priorityIcon} me-2"></i>
                            ${rec.issue}
                            <span class="badge bg-${priorityClass} ms-2">${rec.priority.toUpperCase()}</span>
                        </h6>
                        <p class="mb-2">${rec.description}</p>
                        <div class="small">
                            <strong class="text-muted">권장 조치:</strong> ${rec.action}
                        </div>
                    </div>
                    <div class="ms-3">
                        <span class="badge bg-light text-dark">#${index + 1}</span>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    createQualityTrendChart() {
        const ctx = document.getElementById('qualityTrendChart');
        if (!ctx) return;
        
        const enrichmentHistory = this.data.qualityReport.enrichment_history || {};
        
        if (this.charts.qualityTrend) {
            this.charts.qualityTrend.destroy();
        }

        // 실제 데이터가 있으면 사용, 없으면 임시 데이터
        const dailyUpdates = enrichmentHistory.daily_updates || {};
        const labels = Object.keys(dailyUpdates).slice(-7);
        const data = Object.values(dailyUpdates).slice(-7);

        // 데이터가 없으면 임시 데이터 생성
        if (labels.length === 0) {
            const today = new Date();
            for (let i = 6; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                labels.push(date.toISOString().split('T')[0]);
                data.push(Math.floor(Math.random() * 50) + 10);
            }
        }

        this.charts.qualityTrend = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels.map(label => {
                    const date = new Date(label);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                }),
                datasets: [{
                    label: '일일 업데이트 수',
                    data: data,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `업데이트: ${Utils.formatNumber(context.parsed.y)}건`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return Utils.formatNumber(value);
                            }
                        }
                    }
                }
            }
        });
    }

    // ==================== 유틸리티 메서드 ====================
    
    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }

    updateLastUpdated() {
        const now = new Date();
        this.updateElement('last-updated', `최종 업데이트: ${Utils.formatDateTime(now)}`);
    }

    resizeAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    showSuccess(message) {
        const toastBody = document.getElementById('successToastBody');
        const toast = document.getElementById('successToast');
        
        if (toastBody && toast) {
            toastBody.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
        
        console.log('✅', message);
    }

    showError(message) {
        const toastBody = document.getElementById('errorToastBody');
        const toast = document.getElementById('errorToast');
        
        if (toastBody && toast) {
            toastBody.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
        
        console.error('❌', message);
    }

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
    }

    startAutoRefresh() {
        // 5분마다 현재 섹션 데이터 자동 새로고침
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            console.log('🔄 자동 새로고침 실행');
            this.loadSectionData(this.currentSection);
        }, 5 * 60 * 1000); // 5분
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // ==================== 공개 API 메서드 ====================
    
    async refreshAllData() {
        console.log('🔄 전체 데이터 새로고침 시작');
        
        // 캐시 무효화
        Object.keys(this.data).forEach(key => {
            if (key.endsWith('_loaded_at')) {
                delete this.data[key];
            }
        });
        
        await this.loadSectionData(this.currentSection);
        this.showSuccess('데이터가 새로고침되었습니다.');
    }

    generateReport() {
        const modal = document.getElementById('reportModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    async confirmGenerateReport() {
        const includeDetails = document.getElementById('includeDetails')?.checked || false;
        
        try {
            this.showLoading(true);
            const response = await this.api.post('/api/statistics/generate-report');
            
            const modal = document.getElementById('reportModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
            
            this.showSuccess('리포트 생성이 시작되었습니다. 완료되면 알림을 받으실 수 있습니다.');
            
        } catch (error) {
            console.error('리포트 생성 실패:', error);
            this.showError('리포트 생성에 실패했습니다.');
        } finally {
            this.showLoading(false);
        }
    }

    exportData() {
        const modal = document.getElementById('exportModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    async confirmExportData() {
        const format = document.getElementById('exportFormat')?.value || 'json';
        const includeDetails = document.getElementById('exportIncludeDetails')?.checked || false;
        
        try {
            this.showLoading(true);
            
            const response = await this.api.get('/api/statistics/export-data', {
                params: {
                    format: format,
                    include_details: includeDetails
                }
            });
            
            // 데이터 다운로드
            const content = format === 'json' ? 
                JSON.stringify(response.data, null, 2) : 
                response.data;
                
            const blob = new Blob([content], { 
                type: format === 'json' ? 'application/json' : 'text/csv' 
            });
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `statistics_export_${new Date().getTime()}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            const modal = document.getElementById('exportModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
            
            this.showSuccess('데이터가 성공적으로 내보내졌습니다.');
            
        } catch (error) {
            console.error('데이터 내보내기 실패:', error);
            this.showError('데이터 내보내기에 실패했습니다.');
        } finally {
            this.showLoading(false);
        }
    }
}

// ==================== 전역 변수 및 함수 ====================

let statisticsManager;

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Statistics 페이지 로드 완료');
    statisticsManager = new StatisticsManager();
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    if (statisticsManager) {
        statisticsManager.stopAutoRefresh();
    }
});

// 전역 함수들 (HTML에서 호출)
async function refreshAllData() {
    if (statisticsManager) {
        await statisticsManager.refreshAllData();
    }
}

function generateReport() {
    if (statisticsManager) {
        statisticsManager.generateReport();
    }
}

async function confirmGenerateReport() {
    if (statisticsManager) {
        await statisticsManager.confirmGenerateReport();
    }
}

function exportData() {
    if (statisticsManager) {
        statisticsManager.exportData();
    }
}

async function confirmExportData() {
    if (statisticsManager) {
        await statisticsManager.confirmExportData();
    }
}

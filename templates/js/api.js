// ===== 통합 API 클래스 =====
// 모든 API 호출을 중앙에서 관리

class API {
    static baseURL = '';
    
    // ===== 공통 요청 메서드 =====
    static async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(`${this.baseURL}${url}`, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API 요청 실패 [${url}]:`, error);
            throw error;
        }
    }

    static async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl);
    }

    static async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    // ===== 대시보드 API =====
    static async getDashboardStats() {
        return this.get('/api/statistics/overview');
    }

    static async getDashboardData() {
        return this.get('/api/statistics/basic-stats');
    }

    static async getRealTimeResults(limit = 5) {
        return this.get('/api/statistics/real-time-results', { limit });
    }

    // ===== 기관 관리 API =====
    static async getOrganizations(params = {}) {
        return this.get('/api/organizations', params);
    }

    static async getOrganization(id) {
        return this.get(`/api/organizations/${id}`);
    }

    static async createOrganization(data) {
        return this.post('/api/organizations', data);
    }

    static async updateOrganization(id, data) {
        return this.put(`/api/organizations/${id}`, data);
    }

    static async deleteOrganization(id) {
        return this.delete(`/api/organizations/${id}`);
    }

    static async getOrganizationActivities(id) {
        return this.get(`/api/organizations/${id}/activities`);
    }

    // ===== 연락처 보강 API =====
    static async getEnrichmentCandidates(params = {}) {
        // 기본 파라미터 설정
        const defaultParams = {
            limit: 20
        };
        
        const queryParams = { ...defaultParams, ...params };
        return this.get('/api/organizations/enrichment-candidates', queryParams);
    }

    static async enrichSingle(orgId) {
        return this.post(`/api/enrichment/single/${orgId}`);
    }

    static async enrichBatch(orgIds) {
        return this.post('/api/enrichment/batch', orgIds);
    }

    static async startAutoEnrichment(limit = 100) {
        // GET 파라미터로 전달하도록 수정
        return this.post(`/api/enrichment/auto?limit=${limit}`);
    }

    static async getEnrichmentStatus(jobId) {
        return this.get(`/api/enrichment/status/${jobId}`);
    }

    // ===== 크롤링 API =====
    static async startCrawling(config) {
        return this.post('/api/enrichment/start-file-crawling', config);
    }

    static async stopCrawling() {
        return this.post('/api/enrichment/stop-crawling');
    }

    static async getCrawlingStatus() {
        return this.get('/api/enrichment/crawling-progress');
    }

    static async getCrawlingResults() {
        return this.get('/api/enrichment/crawling-results');
    }

    // ===== 활동 관리 API =====
    static async getActivities(params = {}) {
        return this.get('/api/activities', params);
    }

    static async createActivity(data) {
        return this.post('/api/activities', data);
    }

    static async updateActivity(id, data) {
        return this.put(`/api/activities/${id}`, data);
    }

    static async deleteActivity(id) {
        return this.delete(`/api/activities/${id}`);
    }

    // ===== 통계 분석 API =====
    static async getStatisticsOverview() {
        return this.get('/api/statistics/overview');
    }

    static async getContactAnalysis() {
        return this.get('/api/statistics/contact-analysis');
    }

    static async getGeographicDistribution() {
        return this.get('/api/statistics/geographic-distribution');
    }

    static async getEmailAnalysis() {
        return this.get('/api/statistics/email-analysis');
    }

    static async getCategoryBreakdown() {
        return this.get('/api/statistics/category-breakdown');
    }

    static async getQualityReport() {
        return this.get('/api/statistics/quality-report');
    }

    static async getEnrichmentHistory(days = 30) {
        return this.get('/api/statistics/enrichment-history', { days });
    }

    static async generateStatisticsReport() {
        return this.post('/api/statistics/generate-report');
    }

    static async exportStatisticsData(format = 'json', includeDetails = true) {
        return this.get('/api/statistics/export-data', { 
            format, 
            include_details: includeDetails 
        });
    }

    // ===== 기존 통계 API (하위 호환성) =====
    static async getStatistics(type = 'all') {
        return this.get('/api/statistics/overview', { type });
    }

    static async exportData(format = 'excel', filters = {}) {
        const params = { format, ...filters };
        return this.get('/api/export', params);
    }
}

// ===== APIClient 클래스 (statistics.js 호환성) =====
class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(`${this.baseURL}${url}`, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error(`API 요청 실패 [${url}]:`, error);
            throw error;
        }
    }

    async get(url, options = {}) {
        const { params, ...otherOptions } = options;
        
        if (params) {
            const queryString = new URLSearchParams(params).toString();
            url = queryString ? `${url}?${queryString}` : url;
        }
        
        return this.request(url, { method: 'GET', ...otherOptions });
    }

    async post(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }

    async put(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }

    async delete(url, options = {}) {
        return this.request(url, { method: 'DELETE', ...options });
    }
}

// ===== 전역 접근 가능하도록 설정 =====
window.API = API;
window.APIClient = APIClient; 
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
        return this.get('/api/statistics');
    }

    static async getDashboardData() {
        return this.get('/api/stats/dashboard-data');
    }

    static async getRealTimeResults(limit = 5) {
        return this.get('/api/real-time-results', { limit });
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
    static async getEnrichmentCandidates() {
        return this.get('/api/organizations/enrichment-candidates');
    }

    static async enrichSingle(orgId) {
        return this.post(`/api/enrichment/single/${orgId}`);
    }

    static async enrichBatch(orgIds) {
        return this.post('/api/enrichment/batch', orgIds);
    }

    static async startAutoEnrichment(limit = 100) {
        return this.post(`/api/enrichment/auto?limit=${limit}`);
    }

    static async getEnrichmentStatus(jobId) {
        return this.get(`/api/enrichment/status/${jobId}`);
    }

    // ===== 크롤링 API =====
    static async startCrawling(config) {
        return this.post('/api/crawling/start', config);
    }

    static async stopCrawling() {
        return this.post('/api/crawling/stop');
    }

    static async getCrawlingStatus() {
        return this.get('/api/crawling/status');
    }

    static async getCrawlingResults() {
        return this.get('/api/crawling/results');
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

    // ===== 통계 API =====
    static async getStatistics(type = 'all') {
        return this.get('/api/statistics', { type });
    }

    static async exportData(format = 'excel', filters = {}) {
        const params = { format, ...filters };
        return this.get('/api/export', params);
    }
}

// ===== 전역 접근 가능하도록 설정 =====
window.API = API; 
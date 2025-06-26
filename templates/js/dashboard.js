// API 클래스
class DashboardAPI {
    static async getDashboardData() {
        const response = await fetch('/api/stats/dashboard-data');
        if (!response.ok) throw new Error('데이터 로드 실패');
        return response.json();
    }
    
    static async getEnrichmentCandidates() {
        const response = await fetch('/api/organizations/enrichment-candidates');
        if (!response.ok) throw new Error('보강 후보 로드 실패');
        return response.json();
    }
    
    static async enrichSingle(organizationId) {
        const response = await fetch(`/api/enrichment/single/${organizationId}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('보강 실패');
        return response.json();
    }
}

// 통계 카드 컴포넌트
const StatsCard = ({ icon, title, value, color }) => (
    <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-5">
            <div className="flex items-center">
                <div className="flex-shrink-0">
                    <i className={`fas ${icon} text-2xl ${color}`}></i>
                </div>
                <div className="ml-5 w-0 flex-1">
                    <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
                        <dd className="text-lg font-medium text-gray-900">{value}</dd>
                    </dl>
                </div>
            </div>
        </div>
    </div>
);

// 차트 컴포넌트
const ChartContainer = ({ title, children }) => (
    <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">{title}</h3>
            {children}
        </div>
    </div>
);

// 도넛 차트 컴포넌트
const CompletionChart = ({ completeContacts, missingContacts }) => {
    const chartRef = React.useRef(null);
    
    React.useEffect(() => {
        if (chartRef.current) {
            const ctx = chartRef.current.getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['완료', '누락'],
                    datasets: [{
                        data: [completeContacts, missingContacts],
                        backgroundColor: ['#10B981', '#F59E0B'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }, [completeContacts, missingContacts]);
    
    return <canvas ref={chartRef} width="400" height="200"></canvas>;
};

// 막대 차트 컴포넌트
const CategoryChart = ({ categories, categoryCounts }) => {
    const chartRef = React.useRef(null);
    
    React.useEffect(() => {
        if (chartRef.current && categories.length > 0) {
            const ctx = chartRef.current.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: categories,
                    datasets: [{
                        label: '기관 수',
                        data: categoryCounts,
                        backgroundColor: '#3B82F6',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }, [categories, categoryCounts]);
    
    return <canvas ref={chartRef} width="400" height="200"></canvas>;
};

// 보강 후보 테이블 컴포넌트
const EnrichmentTable = ({ candidates, onEnrich }) => {
    const getMissingFields = (candidate) => {
        const missing = [];
        if (!candidate.phone) missing.push('전화번호');
        if (!candidate.fax) missing.push('팩스');
        if (!candidate.email) missing.push('이메일');
        if (!candidate.homepage) missing.push('홈페이지');
        if (!candidate.address) missing.push('주소');
        return missing;
    };
    
    const getPriorityBadge = (missingCount) => {
        if (missingCount >= 4) {
            return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">높음</span>;
        } else if (missingCount >= 2) {
            return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">보통</span>;
        } else {
            return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">낮음</span>;
        }
    };
    
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">기관명</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">카테고리</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">누락 항목</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">우선순위</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {candidates.length > 0 ? candidates.map(candidate => {
                        const missingFields = getMissingFields(candidate);
                        return (
                            <tr key={candidate.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {candidate.name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {candidate.category || '미분류'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {missingFields.join(', ') || '없음'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {getPriorityBadge(missingFields.length)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <button 
                                        onClick={() => onEnrich(candidate.id)}
                                        className="text-blue-600 hover:text-blue-900 mr-2"
                                    >
                                        <i className="fas fa-search"></i>
                                    </button>
                                    <a href={`/api/organizations/${candidate.id}`} 
                                       className="text-gray-600 hover:text-gray-900">
                                        <i className="fas fa-eye"></i>
                                    </a>
                                </td>
                            </tr>
                        );
                    }) : (
                        <tr>
                            <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                                보강이 필요한 기관이 없습니다.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

// 메인 대시보드 컴포넌트
const Dashboard = () => {
    const [dashboardData, setDashboardData] = React.useState(null);
    const [candidates, setCandidates] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    
    // 데이터 로드
    const loadData = async () => {
        try {
            setLoading(true);
            const [data, candidatesData] = await Promise.all([
                DashboardAPI.getDashboardData(),
                DashboardAPI.getEnrichmentCandidates()
            ]);
            setDashboardData(data);
            setCandidates(candidatesData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    // 단일 보강 처리
    const handleEnrich = async (organizationId) => {
        try {
            const result = await DashboardAPI.enrichSingle(organizationId);
            alert(`보강 완료: ${result.enriched_fields.join(', ')}`);
            loadData(); // 데이터 새로고침
        } catch (err) {
            alert(`보강 실패: ${err.message}`);
        }
    };
    
    // 컴포넌트 마운트 시 데이터 로드
    React.useEffect(() => {
        loadData();
        
        // 30초마다 자동 새로고침
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, []);
    
    if (loading) {
        return (
            <div className="h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">대시보드 로딩 중...</p>
                </div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="h-screen flex items-center justify-center">
                <div className="text-center">
                    <i className="fas fa-exclamation-triangle text-6xl text-red-400 mb-4"></i>
                    <h1 className="text-2xl font-bold text-gray-800 mb-2">오류 발생</h1>
                    <p className="text-gray-500 mb-4">{error}</p>
                    <button 
                        onClick={loadData}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                    >
                        다시 시도
                    </button>
                </div>
            </div>
        );
    }
    
    return (
        <div className="min-h-screen bg-gray-50">
            {/* 네비게이션 */}
            <nav className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-semibold text-gray-900">
                                <i className="fas fa-chart-dashboard mr-2 text-blue-500"></i>
                                CRM 대시보드
                            </h1>
                        </div>
                        <div className="flex items-center space-x-4">
                            <a href="/" className="text-gray-600 hover:text-gray-900">
                                <i className="fas fa-home mr-1"></i>홈
                            </a>
                            <a href="/docs" className="text-gray-600 hover:text-gray-900">
                                <i className="fas fa-book mr-1"></i>API 문서
                            </a>
                        </div>
                    </div>
                </div>
            </nav>
            
            {/* 메인 컨텐츠 */}
            <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                {/* 통계 카드 */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <StatsCard 
                        icon="fa-building"
                        title="총 기관 수"
                        value={dashboardData?.total_organizations || 0}
                        color="text-blue-500"
                    />
                    <StatsCard 
                        icon="fa-phone"
                        title="연락처 완료"
                        value={dashboardData?.complete_contacts || 0}
                        color="text-green-500"
                    />
                    <StatsCard 
                        icon="fa-exclamation-triangle"
                        title="연락처 누락"
                        value={dashboardData?.missing_contacts || 0}
                        color="text-yellow-500"
                    />
                    <StatsCard 
                        icon="fa-percentage"
                        title="완성도"
                        value={`${(dashboardData?.completion_rate || 0).toFixed(1)}%`}
                        color="text-purple-500"
                    />
                </div>
                
                {/* 차트 영역 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <ChartContainer title="연락처 완성도">
                        <CompletionChart 
                            completeContacts={dashboardData?.complete_contacts || 0}
                            missingContacts={dashboardData?.missing_contacts || 0}
                        />
                    </ChartContainer>
                    
                    <ChartContainer title="카테고리별 분포">
                        <CategoryChart 
                            categories={dashboardData?.categories || []}
                            categoryCounts={dashboardData?.category_counts || []}
                        />
                    </ChartContainer>
                </div>
                
                {/* 보강 후보 테이블 */}
                <div className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg leading-6 font-medium text-gray-900">연락처 보강 후보</h3>
                            <a href="/enrichment" className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm">
                                <i className="fas fa-plus mr-1"></i>보강 시작
                            </a>
                        </div>
                        <EnrichmentTable 
                            candidates={candidates}
                            onEnrich={handleEnrich}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

// React 앱 렌더링
ReactDOM.render(<Dashboard />, document.getElementById('dashboard-root'));
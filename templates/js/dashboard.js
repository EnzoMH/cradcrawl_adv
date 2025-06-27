// 대시보드 React 애플리케이션
const { useState, useEffect } = React;

// API는 api.js에서 전역으로 로드됨

// 메인 대시보드 컴포넌트
function Dashboard() {
    const [dashboardData, setDashboardData] = useState(null);
    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 대시보드 데이터 로드
    const loadData = async () => {
        try {
            setLoading(true);
            
            // 대시보드 기본 데이터 로드
            console.log('대시보드 기본 데이터 로드 시작...');
            const data = await API.getDashboardData();
            console.log('대시보드 기본 데이터 응답:', data);
            setDashboardData(data);
            
            // 보강 후보 데이터 로드 (별도 처리)
            try {
                const candidatesData = await API.getEnrichmentCandidates();
                console.log('후보 데이터 응답:', candidatesData);
                
                // API 응답 구조 변경에 대응
                if (candidatesData && candidatesData.status === 'success' && candidatesData.candidates) {
                    setCandidates(Array.isArray(candidatesData.candidates) ? candidatesData.candidates : []);
                } else if (Array.isArray(candidatesData)) {
                    // 기존 형식도 지원 (하위 호환성)
                    setCandidates(candidatesData);
                } else {
                    console.warn('예상하지 못한 후보 데이터 형식:', candidatesData);
                    setCandidates([]);
                }
            } catch (candidatesErr) {
                console.error('보강 후보 로드 실패:', candidatesErr);
                setCandidates([]); // 후보 데이터만 실패해도 대시보드는 표시
            }
            
        } catch (err) {
            console.error('대시보드 데이터 로드 실패:', err);
            setError(err.message);
            setCandidates([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // 단일 보강 실행
    const handleQuickEnrich = async (organizationId) => {
        try {
            const result = await API.enrichSingle(organizationId);
            alert(`보강 완료: ${result.enriched_fields.join(', ')}`);
            loadData(); // 데이터 새로고침
        } catch (err) {
            alert(`보강 실패: ${err.message}`);
        }
    };

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
                    <i className="fas fa-exclamation-triangle text-6xl text-red-500 mb-4"></i>
                    <h1 className="text-2xl font-bold text-red-800 mb-2">데이터 로드 실패</h1>
                    <p className="text-red-600 mb-4">{error}</p>
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* 헤더 */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">CRM 대시보드</h1>
                <p className="text-gray-600 mt-1">교회/기관 관리 시스템 현황</p>
            </div>

            {/* 통계 카드 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard
                    title="총 기관 수"
                    value={dashboardData?.total_organizations || 0}
                    icon="fas fa-building"
                    color="blue"
                />
                <StatCard
                    title="연락처 완료"
                    value={dashboardData?.complete_contacts || 0}
                    icon="fas fa-check-circle"
                    color="green"
                />
                <StatCard
                    title="연락처 누락"
                    value={dashboardData?.missing_contacts || 0}
                    icon="fas fa-exclamation-circle"
                    color="red"
                />
                <StatCard
                    title="완성도"
                    value={`${(dashboardData?.completion_rate || 0).toFixed(1)}%`}
                    icon="fas fa-chart-pie"
                    color="purple"
                />
            </div>

            {/* 차트 섹션 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* 카테고리별 분포 */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                        <i className="fas fa-chart-bar mr-2 text-blue-600"></i>
                        카테고리별 분포
                    </h3>
                    <CategoryChart data={dashboardData} />
                </div>

                {/* 연락처 완성도 */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                        <i className="fas fa-chart-pie mr-2 text-green-600"></i>
                        연락처 완성도
                    </h3>
                    <CompletionChart data={dashboardData} />
                </div>
            </div>

            {/* 보강 후보 기관 */}
            <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-medium text-gray-900">
                            <i className="fas fa-magic mr-2 text-purple-600"></i>
                            연락처 보강 후보
                        </h3>
                        <a 
                            href="/enrichment" 
                            className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                        >
                            전체 보기 <i className="fas fa-arrow-right ml-1"></i>
                        </a>
                    </div>
                </div>
                
                {candidates.length === 0 ? (
                    <div className="p-8 text-center">
                        <i className="fas fa-check-circle text-4xl text-green-500 mb-4"></i>
                        <p className="text-gray-600">보강이 필요한 기관이 없습니다!</p>
                        <p className="text-sm text-gray-500 mt-2">모든 기관의 연락처 정보가 완성되었습니다.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {candidates.slice(0, 5).map((candidate) => (
                            <CandidateRow
                                key={candidate.id}
                                candidate={candidate}
                                onEnrich={handleQuickEnrich}
                            />
                        ))}
                        {candidates.length > 5 && (
                            <div className="p-4 text-center bg-gray-50">
                                <a 
                                    href="/enrichment" 
                                    className="text-purple-600 hover:text-purple-800 font-medium"
                                >
                                    +{candidates.length - 5}개 더 보기
                                </a>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// 통계 카드 컴포넌트
function StatCard({ title, value, icon, color }) {
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-600',
        green: 'bg-green-100 text-green-600',
        red: 'bg-red-100 text-red-600',
        purple: 'bg-purple-100 text-purple-600',
        yellow: 'bg-yellow-100 text-yellow-600'
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
                <div className={`p-3 rounded-full ${colorClasses[color]}`}>
                    <i className={`${icon} text-xl`}></i>
                </div>
                <div className="ml-4">
                    <h3 className="text-2xl font-bold text-gray-900">
                        {typeof value === 'number' ? value.toLocaleString() : value}
                    </h3>
                    <p className="text-gray-600">{title}</p>
                </div>
            </div>
        </div>
    );
}

// 카테고리 차트 컴포넌트 (간단한 바 차트)
function CategoryChart({ data }) {
    if (!data?.categories || !data?.category_counts) {
        return <div className="text-gray-500 text-center py-8">데이터가 없습니다.</div>;
    }

    const maxCount = Math.max(...data.category_counts);

    return (
        <div className="space-y-4">
            {data.categories.map((category, index) => (
                <div key={category} className="flex items-center">
                    <div className="w-20 text-sm text-gray-600 truncate">{category}</div>
                    <div className="flex-1 mx-4">
                        <div className="bg-gray-200 rounded-full h-4">
                            <div 
                                className="bg-blue-500 h-4 rounded-full transition-all duration-300"
                                style={{ width: `${(data.category_counts[index] / maxCount) * 100}%` }}
                            ></div>
                        </div>
                    </div>
                    <div className="w-12 text-sm text-gray-900 font-medium text-right">
                        {data.category_counts[index]}
                    </div>
                </div>
            ))}
        </div>
    );
}

// 완성도 차트 컴포넌트 (도넛 차트 스타일)
function CompletionChart({ data }) {
    const complete = data?.complete_contacts || 0;
    const missing = data?.missing_contacts || 0;
    const total = complete + missing;
    
    if (total === 0) {
        return <div className="text-gray-500 text-center py-8">데이터가 없습니다.</div>;
    }

    const completionRate = (complete / total) * 100;

    return (
        <div className="flex items-center justify-center">
            <div className="relative w-32 h-32">
                {/* 원형 프로그레스 바 */}
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                    <path
                        className="text-gray-200"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="transparent"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                        className="text-green-500"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="transparent"
                        strokeDasharray={`${completionRate}, 100`}
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl font-bold text-gray-900">
                        {completionRate.toFixed(1)}%
                    </span>
                </div>
            </div>
            <div className="ml-6 space-y-2">
                <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-600">완료: {complete.toLocaleString()}</span>
                </div>
                <div className="flex items-center">
                    <div className="w-3 h-3 bg-gray-300 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-600">누락: {missing.toLocaleString()}</span>
                </div>
            </div>
        </div>
    );
}

// 보강 후보 행 컴포넌트
function CandidateRow({ candidate, onEnrich }) {
    const getMissingFields = () => {
        const missing = [];
        if (!candidate.phone) missing.push('전화번호');
        if (!candidate.fax) missing.push('팩스');
        if (!candidate.email) missing.push('이메일');
        if (!candidate.homepage) missing.push('홈페이지');
        if (!candidate.address) missing.push('주소');
        return missing;
    };

    const missingFields = getMissingFields();

    return (
        <div className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <div className="flex items-center space-x-3">
                        <h4 className="text-sm font-medium text-gray-900">{candidate.name}</h4>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            {candidate.category || '미분류'}
                        </span>
                    </div>
                    <div className="mt-1 text-sm text-gray-500">{candidate.address || '주소 없음'}</div>
                    <div className="mt-2 flex flex-wrap gap-1">
                        {missingFields.map((field) => (
                            <span key={field} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                {field}
                            </span>
                        ))}
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => onEnrich(candidate.id)}
                        className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm transition-colors"
                    >
                        <i className="fas fa-magic mr-1"></i>
                        보강
                    </button>
                    <a 
                        href={`/organizations/${candidate.id}`} 
                        target="_blank"
                        className="text-gray-600 hover:text-gray-900 p-1 rounded transition-colors"
                        title="상세보기"
                    >
                        <i className="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
        </div>
    );
}

// React 앱 렌더링
ReactDOM.render(<Dashboard />, document.getElementById('dashboard-root'));
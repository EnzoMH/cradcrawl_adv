// 연락처 보강 React 애플리케이션
const { useState, useEffect, useCallback } = React;

// API는 api.js에서 전역으로 로드됨

// 메인 연락처 보강 컴포넌트
function EnrichmentApp() {
    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCandidates, setSelectedCandidates] = useState(new Set());
    const [enrichmentResults, setEnrichmentResults] = useState({});
    const [isEnriching, setIsEnriching] = useState(false);
    const [stats, setStats] = useState({
        total: 0,
        completed: 0,
        inProgress: 0,
        failed: 0
    });

    // 보강 후보 로드
    const loadCandidates = useCallback(async () => {
        try {
            setLoading(true);
            const result = await API.getEnrichmentCandidates();
            setCandidates(Array.isArray(result) ? result : []);
        } catch (error) {
            console.error('보강 후보 로드 실패:', error);
            alert('보강 후보를 불러올 수 없습니다.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadCandidates();
    }, [loadCandidates]);

    // 후보 선택
    const handleCandidateSelect = (orgId, checked) => {
        const newSelected = new Set(selectedCandidates);
        if (checked) {
            newSelected.add(orgId);
        } else {
            newSelected.delete(orgId);
        }
        setSelectedCandidates(newSelected);
    };

    // 전체 선택
    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedCandidates(new Set(candidates.map(c => c.id)));
        } else {
            setSelectedCandidates(new Set());
        }
    };

    // 단일 보강
    const handleSingleEnrichment = async (orgId) => {
        try {
            setIsEnriching(true);
            setEnrichmentResults(prev => ({
                ...prev,
                [orgId]: { status: 'in_progress', message: '보강 중...' }
            }));

            const result = await API.enrichSingle(orgId);
            
            setEnrichmentResults(prev => ({
                ...prev,
                [orgId]: {
                    status: result.status === 'success' ? 'completed' : 'failed',
                    message: result.message,
                    enriched_fields: result.enriched_fields || [],
                    found_data: result.found_data || {}
                }
            }));

            // 통계 업데이트
            setStats(prev => ({
                ...prev,
                completed: prev.completed + (result.status === 'success' ? 1 : 0),
                failed: prev.failed + (result.status === 'success' ? 0 : 1),
                inProgress: Math.max(0, prev.inProgress - 1)
            }));

        } catch (error) {
            console.error('단일 보강 실패:', error);
            setEnrichmentResults(prev => ({
                ...prev,
                [orgId]: { status: 'failed', message: '보강 실패: ' + error.message }
            }));
        } finally {
            setIsEnriching(false);
        }
    };

    // 선택된 기관들 일괄 보강
    const handleBatchEnrichment = async () => {
        if (selectedCandidates.size === 0) {
            alert('보강할 기관을 선택해주세요.');
            return;
        }

        if (!confirm(`선택된 ${selectedCandidates.size}개 기관을 보강하시겠습니까?`)) {
            return;
        }

        try {
            setIsEnriching(true);
            const orgIds = Array.from(selectedCandidates);
            
            // 진행 상태 초기화
            orgIds.forEach(id => {
                setEnrichmentResults(prev => ({
                    ...prev,
                    [id]: { status: 'in_progress', message: '보강 대기 중...' }
                }));
            });

            setStats(prev => ({
                ...prev,
                total: prev.total + orgIds.length,
                inProgress: prev.inProgress + orgIds.length
            }));

            const result = await API.enrichBatch(orgIds);
            alert(result.message);

            // 개별 결과 처리 (실제로는 백그라운드에서 처리되므로 주기적으로 상태 확인 필요)
            // 여기서는 간단히 성공으로 처리
            orgIds.forEach(id => {
                setTimeout(() => {
                    setEnrichmentResults(prev => ({
                        ...prev,
                        [id]: { 
                            status: 'completed', 
                            message: '보강 완료',
                            enriched_fields: ['phone', 'email'] // 예시
                        }
                    }));
                }, Math.random() * 3000 + 1000); // 1-4초 랜덤 지연
            });

        } catch (error) {
            console.error('일괄 보강 실패:', error);
            alert('일괄 보강에 실패했습니다: ' + error.message);
        } finally {
            setIsEnriching(false);
        }
    };

    // 자동 보강 시작
    const handleAutoEnrichment = async () => {
        const limit = prompt('최대 보강할 기관 수를 입력하세요 (기본값: 100)', '100');
        if (!limit) return;

        const numLimit = parseInt(limit);
        if (isNaN(numLimit) || numLimit <= 0) {
            alert('올바른 숫자를 입력해주세요.');
            return;
        }

        if (!confirm(`최대 ${numLimit}개 기관의 자동 보강을 시작하시겠습니까?`)) {
            return;
        }

        try {
            setIsEnriching(true);
            const result = await API.startAutoEnrichment(numLimit);
            alert(result.message);
            
            // 진행 상황 모니터링 시작
            // 실제 구현에서는 WebSocket이나 주기적 polling 사용
            
        } catch (error) {
            console.error('자동 보강 시작 실패:', error);
            alert('자동 보강 시작에 실패했습니다: ' + error.message);
        } finally {
            setIsEnriching(false);
        }
    };

    if (loading) {
        return (
            <div className="h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">보강 후보 로딩 중...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* 헤더 */}
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">연락처 보강</h2>
                <p className="text-gray-600 mt-1">
                    누락된 연락처 정보를 자동으로 크롤링하여 보강합니다.
                </p>
            </div>

            {/* 통계 카드 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-blue-100">
                            <i className="fas fa-list text-blue-600 text-xl"></i>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-2xl font-bold text-gray-900">{candidates.length}</h3>
                            <p className="text-gray-600">보강 후보</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-green-100">
                            <i className="fas fa-check text-green-600 text-xl"></i>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-2xl font-bold text-gray-900">{stats.completed}</h3>
                            <p className="text-gray-600">완료</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-yellow-100">
                            <i className="fas fa-spinner text-yellow-600 text-xl"></i>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-2xl font-bold text-gray-900">{stats.inProgress}</h3>
                            <p className="text-gray-600">진행 중</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-red-100">
                            <i className="fas fa-times text-red-600 text-xl"></i>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-2xl font-bold text-gray-900">{stats.failed}</h3>
                            <p className="text-gray-600">실패</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* 액션 버튼 */}
            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <div className="flex flex-wrap gap-4">
                    <button 
                        onClick={handleAutoEnrichment}
                        disabled={isEnriching}
                        className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center"
                    >
                        <i className="fas fa-magic mr-2"></i>
                        자동 보강 시작
                    </button>
                    
                    {selectedCandidates.size > 0 && (
                        <button 
                            onClick={handleBatchEnrichment}
                            disabled={isEnriching}
                            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center"
                        >
                            <i className="fas fa-play mr-2"></i>
                            선택된 기관 보강 ({selectedCandidates.size})
                        </button>
                    )}
                    
                    <button 
                        onClick={loadCandidates}
                        className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center"
                    >
                        <i className="fas fa-refresh mr-2"></i>
                        새로고침
                    </button>
                </div>
            </div>

            {/* 보강 후보 테이블 */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {candidates.length === 0 ? (
                    <div className="p-8 text-center">
                        <i className="fas fa-magic text-4xl text-gray-400 mb-4"></i>
                        <p className="text-gray-600 mb-4">보강이 필요한 기관이 없습니다.</p>
                        <p className="text-sm text-gray-500">모든 기관의 연락처 정보가 완성되었습니다!</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left">
                                        <input
                                            type="checkbox"
                                            checked={selectedCandidates.size === candidates.length && candidates.length > 0}
                                            onChange={(e) => handleSelectAll(e.target.checked)}
                                            className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                                        />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        기관명
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        카테고리
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        누락 항목
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        우선순위
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        상태
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        액션
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {candidates.map((candidate) => (
                                    <EnrichmentCandidateRow
                                        key={candidate.id}
                                        candidate={candidate}
                                        selected={selectedCandidates.has(candidate.id)}
                                        onSelect={handleCandidateSelect}
                                        onEnrich={handleSingleEnrichment}
                                        result={enrichmentResults[candidate.id]}
                                        disabled={isEnriching}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

// 보강 후보 행 컴포넌트
function EnrichmentCandidateRow({ candidate, selected, onSelect, onEnrich, result, disabled }) {
    const getMissingFieldsBadge = (fields) => {
        const missing = [];
        if (!candidate.phone) missing.push('전화번호');
        if (!candidate.fax) missing.push('팩스');
        if (!candidate.email) missing.push('이메일');
        if (!candidate.homepage) missing.push('홈페이지');
        if (!candidate.address) missing.push('주소');
        return missing;
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <i className="fas fa-check-circle text-green-500" title="보강 완료"></i>;
            case 'failed':
                return <i className="fas fa-times-circle text-red-500" title="보강 실패"></i>;
            case 'in_progress':
                return <i className="fas fa-spinner fa-spin text-blue-500" title="보강 중"></i>;
            default:
                return <i className="fas fa-clock text-gray-400" title="대기 중"></i>;
        }
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

    const missingFields = getMissingFieldsBadge();

    return (
        <tr className="hover:bg-gray-50 transition-colors">
            <td className="px-6 py-4">
                <input
                    type="checkbox"
                    checked={selected}
                    onChange={(e) => onSelect(candidate.id, e.target.checked)}
                    disabled={disabled}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
            </td>
            <td className="px-6 py-4">
                <div className="text-sm font-medium text-gray-900">{candidate.name}</div>
                <div className="text-sm text-gray-500">{candidate.address || '주소 없음'}</div>
            </td>
            <td className="px-6 py-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {candidate.category || '미분류'}
                </span>
            </td>
            <td className="px-6 py-4">
                <div className="flex flex-wrap gap-1">
                    {missingFields.map((field, index) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                            {field}
                        </span>
                    ))}
                </div>
            </td>
            <td className="px-6 py-4">
                {getPriorityBadge(missingFields.length)}
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center space-x-2">
                    {getStatusIcon(result?.status)}
                    {result?.message && (
                        <span className="text-xs text-gray-600">{result.message}</span>
                    )}
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex space-x-2">
                    <button
                        onClick={() => onEnrich(candidate.id)}
                        disabled={disabled || result?.status === 'in_progress'}
                        className="text-purple-600 hover:text-purple-900 disabled:text-gray-400 p-1 rounded transition-colors"
                        title="단일 보강"
                    >
                        <i className="fas fa-magic"></i>
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
            </td>
        </tr>
    );
}

// React 앱 렌더링
ReactDOM.render(<EnrichmentApp />, document.getElementById('enrichment-root')); 
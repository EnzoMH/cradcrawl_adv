// 기관 관리 React 애플리케이션
const { useState, useEffect, useCallback } = React;

// API는 api.js에서 전역으로 로드됨

// 기관 목록 컴포넌트
function OrganizationsList() {
    const [organizations, setOrganizations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [pagination, setPagination] = useState({});
    const [filters, setFilters] = useState({
        page: 1,
        per_page: 50, // 기본값 50개 유지
        search: '',
        category: '',
        status: '',
        priority: ''
    });
    const [selectedOrgs, setSelectedOrgs] = useState(new Set());
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingOrg, setEditingOrg] = useState(null);
    const [enrichmentStatus, setEnrichmentStatus] = useState({});

    // 기관 목록 로드
    const loadOrganizations = useCallback(async () => {
        try {
            setLoading(true);
            console.log('🔍 기관 목록 로드 시작, 필터:', filters);
            
            const result = await API.getOrganizations(filters);
            console.log('📊 API 응답 받음:', result);
            console.log('📋 응답 구조:', {
                status: result.status,
                organizations_count: result.organizations ? result.organizations.length : 0,
                pagination: result.pagination,
                total_count: result.total_count
            });
            
            const organizations = result.organizations || [];
            const pagination = result.pagination || {};
            
            console.log('✅ 상태 업데이트:', {
                organizations_length: organizations.length,
                pagination: pagination
            });
            
            setOrganizations(organizations);
            setPagination(pagination);
            
            if (organizations.length === 0) {
                console.warn('⚠️ 조회된 기관이 없습니다');
            }
            
        } catch (error) {
            console.error('❌ 기관 목록 로드 실패:', error);
            console.error('❌ 오류 상세:', error.message, error.stack);
            alert('기관 목록을 불러올 수 없습니다: ' + error.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        loadOrganizations();
    }, [loadOrganizations]);

    // 필터 변경 핸들러
    const handleFilterChange = (key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            page: 1 // 필터 변경 시 첫 페이지로
        }));
    };

    // 페이지 변경
    const handlePageChange = (page) => {
        setFilters(prev => ({ ...prev, page }));
    };

    // 기관 선택
    const handleOrgSelect = (orgId, checked) => {
        const newSelected = new Set(selectedOrgs);
        if (checked) {
            newSelected.add(orgId);
        } else {
            newSelected.delete(orgId);
        }
        setSelectedOrgs(newSelected);
    };

    // 전체 선택
    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedOrgs(new Set(organizations.map(org => org.id)));
        } else {
            setSelectedOrgs(new Set());
        }
    };

    // 선택된 기관들 일괄 보강
    const handleBatchEnrichment = async () => {
        if (selectedOrgs.size === 0) {
            alert('보강할 기관을 선택해주세요.');
            return;
        }

        if (!confirm(`선택된 ${selectedOrgs.size}개 기관의 연락처를 보강하시겠습니까?`)) {
            return;
        }

        try {
            const orgIds = Array.from(selectedOrgs);
            
            // 보강 상태 초기화
            const newStatus = {};
            orgIds.forEach(id => {
                newStatus[id] = { status: 'in_progress', message: '보강 중...' };
            });
            setEnrichmentStatus(newStatus);

            const result = await API.enrichBatch(orgIds);
            alert(result.message);

            // 보강 완료 후 목록 새로고침
            setTimeout(() => {
                loadOrganizations();
                setSelectedOrgs(new Set());
                setEnrichmentStatus({});
            }, 2000);

        } catch (error) {
            console.error('일괄 보강 실패:', error);
            alert('일괄 보강에 실패했습니다: ' + error.message);
            setEnrichmentStatus({});
        }
    };

    // 기관 삭제
    const handleDelete = async (orgId) => {
        if (!confirm('정말로 이 기관을 삭제하시겠습니까?')) return;
        
        try {
            await API.deleteOrganization(orgId);
            alert('기관이 삭제되었습니다.');
            loadOrganizations();
        } catch (error) {
            console.error('삭제 실패:', error);
            alert('기관 삭제에 실패했습니다.');
        }
    };

    // 기관 수정 모달 열기
    const handleEdit = async (orgId) => {
        try {
            const result = await API.getOrganization(orgId);
            setEditingOrg(result.organization);
            setShowEditModal(true);
        } catch (error) {
            console.error('기관 정보 로드 실패:', error);
            alert('기관 정보를 불러올 수 없습니다.');
        }
    };

    // 검색 디바운스
    const [searchTimeout, setSearchTimeout] = useState(null);
    const handleSearchChange = (value) => {
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        setSearchTimeout(setTimeout(() => {
            handleFilterChange('search', value);
        }, 500));
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* 헤더 및 액션 버튼 */}
            <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">기관 관리</h2>
                    <p className="text-gray-600 mt-1">
                        총 {pagination.total_count || 0}개 기관
                        {selectedOrgs.size > 0 && (
                            <span className="ml-2 text-blue-600 font-medium">
                                ({selectedOrgs.size}개 선택됨)
                            </span>
                        )}
                    </p>
                </div>
                <div className="flex flex-wrap gap-3">
                    {selectedOrgs.size > 0 && (
                        <button 
                            onClick={handleBatchEnrichment}
                            className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
                        >
                            <i className="fas fa-magic mr-2"></i>
                            선택된 기관 보강 ({selectedOrgs.size})
                        </button>
                    )}
                    <button 
                        onClick={() => setShowCreateModal(true)}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
                    >
                        <i className="fas fa-plus mr-2"></i>
                        새 기관 추가
                    </button>
                    <button 
                        onClick={loadOrganizations}
                        className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
                    >
                        <i className="fas fa-refresh mr-2"></i>
                        새로고침
                    </button>
                </div>
            </div>

            {/* 검색 및 필터 */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            검색
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                defaultValue={filters.search}
                                onChange={(e) => handleSearchChange(e.target.value)}
                                placeholder="기관명, 주소, 전화번호 등..."
                                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            카테고리
                        </label>
                        <select
                            value={filters.category}
                            onChange={(e) => handleFilterChange('category', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">전체</option>
                            <option value="교회">교회</option>
                            <option value="학원">학원</option>
                            <option value="공공기관">공공기관</option>
                            <option value="학교">학교</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            상태
                        </label>
                        <select
                            value={filters.status}
                            onChange={(e) => handleFilterChange('status', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">전체</option>
                            <option value="NEW">신규</option>
                            <option value="CONTACTED">접촉함</option>
                            <option value="QUALIFIED">검증됨</option>
                            <option value="LOST">실패</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            우선순위
                        </label>
                        <select
                            value={filters.priority}
                            onChange={(e) => handleFilterChange('priority', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">전체</option>
                            <option value="HIGH">높음</option>
                            <option value="MEDIUM">보통</option>
                            <option value="LOW">낮음</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            페이지당 항목 수
                        </label>
                        <select
                            value={filters.per_page}
                            onChange={(e) => handleFilterChange('per_page', parseInt(e.target.value))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value={20}>20개</option>
                            <option value={50}>50개</option>
                            <option value={100}>100개 (최대)</option>
                        </select>
                    </div>
                </div>
                
                {/* 필터 초기화 및 통계 */}
                <div className="mt-4 flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                        총 {pagination.total_count || 0}개 기관 중 {organizations.length}개 표시
                        {pagination.total_pages > 1 && (
                            <span className="ml-2">
                                (페이지 {pagination.page || 1}/{pagination.total_pages})
                            </span>
                        )}
                    </div>
                    {(filters.search || filters.category || filters.status || filters.priority) && (
                        <button
                            onClick={() => {
                                setFilters({
                                    page: 1,
                                    per_page: filters.per_page, // 현재 per_page 값 유지
                                    search: '',
                                    category: '',
                                    status: '',
                                    priority: ''
                                });
                                // 검색 입력 필드도 초기화
                                document.querySelector('input[placeholder*="기관명"]').value = '';
                            }}
                            className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                        >
                            <i className="fas fa-times mr-1"></i>
                            필터 초기화
                        </button>
                    )}
                </div>
            </div>

            {/* 기관 목록 테이블 */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p className="text-gray-600">로딩 중...</p>
                    </div>
                ) : organizations.length === 0 ? (
                    <div className="p-8 text-center">
                        <i className="fas fa-inbox text-4xl text-gray-400 mb-4"></i>
                        <p className="text-gray-600 mb-4">
                            {filters.search || filters.category || filters.status || filters.priority 
                                ? '검색 조건에 맞는 기관이 없습니다.' 
                                : '등록된 기관이 없습니다.'
                            }
                        </p>
                        <button 
                            onClick={() => setShowCreateModal(true)}
                            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
                        >
                            첫 번째 기관 추가하기
                        </button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left">
                                        <input
                                            type="checkbox"
                                            checked={selectedOrgs.size === organizations.length && organizations.length > 0}
                                            onChange={(e) => handleSelectAll(e.target.checked)}
                                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                        />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        기관명
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        유형
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        연락처
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        상태
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        완성도
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        액션
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {organizations.map((org) => (
                                    <OrganizationRow
                                        key={org.id}
                                        organization={org}
                                        selected={selectedOrgs.has(org.id)}
                                        onSelect={handleOrgSelect}
                                        onEdit={handleEdit}
                                        onDelete={handleDelete}
                                        enrichmentStatus={enrichmentStatus[org.id]}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* 페이지네이션 */}
            {pagination.total_pages > 1 && (
                <Pagination
                    currentPage={pagination.page}
                    totalPages={pagination.total_pages}
                    onPageChange={handlePageChange}
                />
            )}

            {/* 모달들 */}
            {showCreateModal && (
                <CreateOrganizationModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={() => {
                        setShowCreateModal(false);
                        loadOrganizations();
                    }}
                />
            )}

            {showEditModal && editingOrg && (
                <EditOrganizationModal
                    organization={editingOrg}
                    onClose={() => {
                        setShowEditModal(false);
                        setEditingOrg(null);
                    }}
                    onSuccess={() => {
                        setShowEditModal(false);
                        setEditingOrg(null);
                        loadOrganizations();
                    }}
                />
            )}
        </div>
    );
}

// 기관 행 컴포넌트
function OrganizationRow({ organization, selected, onSelect, onEdit, onDelete, enrichmentStatus }) {
    const getStatusBadge = (status) => {
        const colors = {
            'NEW': 'bg-blue-100 text-blue-800',
            'CONTACTED': 'bg-yellow-100 text-yellow-800',
            'QUALIFIED': 'bg-green-100 text-green-800',
            'LOST': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const getPriorityBadge = (priority) => {
        const colors = {
            'HIGH': 'bg-red-100 text-red-800',
            'MEDIUM': 'bg-yellow-100 text-yellow-800',
            'LOW': 'bg-green-100 text-green-800'
        };
        return colors[priority] || 'bg-gray-100 text-gray-800';
    };

    const getCompletionRate = (org) => {
        const fields = ['phone', 'fax', 'email', 'homepage', 'address'];
        const filled = fields.filter(field => org[field] && org[field].trim() !== '').length;
        return Math.round((filled / fields.length) * 100);
    };

    const completionRate = getCompletionRate(organization);

    return (
        <tr className="hover:bg-gray-50 transition-colors">
            <td className="px-6 py-4">
                <input
                    type="checkbox"
                    checked={selected}
                    onChange={(e) => onSelect(organization.id, e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
            </td>
            <td className="px-6 py-4">
                <div className="flex items-start space-x-3">
                    <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">
                            {organization.name}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                            {organization.address || '주소 없음'}
                        </div>
                        {organization.priority && organization.priority !== 'MEDIUM' && (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-1 ${getPriorityBadge(organization.priority)}`}>
                                {organization.priority === 'HIGH' ? '높음' : '낮음'}
                            </span>
                        )}
                    </div>
                    {enrichmentStatus && (
                        <div className="flex-shrink-0">
                            {enrichmentStatus.status === 'in_progress' && (
                                <i className="fas fa-spinner fa-spin text-blue-500" title="보강 중..."></i>
                            )}
                        </div>
                    )}
                </div>
            </td>
            <td className="px-6 py-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {organization.type || organization.category}
                </span>
            </td>
            <td className="px-6 py-4 text-sm text-gray-900">
                <div className="space-y-1">
                    <div className="flex items-center">
                        <i className="fas fa-phone text-gray-400 w-4 mr-2"></i>
                        <span>{organization.phone || '전화번호 없음'}</span>
                    </div>
                    <div className="flex items-center">
                        <i className="fas fa-envelope text-gray-400 w-4 mr-2"></i>
                        <span className="text-gray-500">{organization.email || '이메일 없음'}</span>
                    </div>
                    {organization.homepage && (
                        <div className="flex items-center">
                            <i className="fas fa-globe text-gray-400 w-4 mr-2"></i>
                            <a 
                                href={organization.homepage} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-500 hover:text-blue-700 text-xs truncate max-w-32"
                            >
                                {organization.homepage}
                            </a>
                        </div>
                    )}
                </div>
            </td>
            <td className="px-6 py-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(organization.contact_status)}`}>
                    {organization.contact_status === 'NEW' ? '신규' :
                     organization.contact_status === 'CONTACTED' ? '접촉함' :
                     organization.contact_status === 'QUALIFIED' ? '검증됨' :
                     organization.contact_status === 'LOST' ? '실패' : organization.contact_status || 'NEW'}
                </span>
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center space-x-2">
                    <div className="flex-1">
                        <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div 
                                    className={`h-2 rounded-full transition-all duration-300 ${
                                        completionRate >= 80 ? 'bg-green-500' : 
                                        completionRate >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                    }`}
                                    style={{ width: `${completionRate}%` }}
                                ></div>
                            </div>
                            <span className="text-sm text-gray-600 font-medium">{completionRate}%</span>
                        </div>
                    </div>
                </div>
            </td>
            <td className="px-6 py-4 text-sm font-medium">
                <div className="flex space-x-2">
                    <button
                        onClick={() => onEdit(organization.id)}
                        className="text-blue-600 hover:text-blue-900 p-1 rounded transition-colors"
                        title="수정"
                    >
                        <i className="fas fa-edit"></i>
                    </button>
                    <button
                        onClick={() => onDelete(organization.id)}
                        className="text-red-600 hover:text-red-900 p-1 rounded transition-colors"
                        title="삭제"
                    >
                        <i className="fas fa-trash"></i>
                    </button>
                    <button
                        onClick={() => window.open(`/organizations/${organization.id}`, '_blank')}
                        className="text-gray-600 hover:text-gray-900 p-1 rounded transition-colors"
                        title="상세보기"
                    >
                        <i className="fas fa-external-link-alt"></i>
                    </button>
                </div>
            </td>
        </tr>
    );
}

// 향상된 페이지네이션 컴포넌트
function Pagination({ currentPage, totalPages, onPageChange }) {
    const [jumpPage, setJumpPage] = useState('');
    const maxVisible = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
    }

    const handleJumpToPage = (e) => {
        e.preventDefault();
        const pageNum = parseInt(jumpPage);
        if (pageNum >= 1 && pageNum <= totalPages) {
            onPageChange(pageNum);
            setJumpPage('');
        }
    };

    const getQuickJumpPages = () => {
        const jumps = [];
        const step = Math.ceil(totalPages / 10);
        for (let i = step; i < totalPages; i += step) {
            if (Math.abs(i - currentPage) > 2) {
                jumps.push(i);
            }
        }
        return jumps.slice(0, 3);
    };

    return (
        <div className="bg-white px-4 py-4 border-t border-gray-200 mt-6 rounded-b-lg">
            {/* 모바일 버전 */}
            <div className="flex flex-col sm:hidden space-y-3">
                <div className="flex justify-between">
                    <button
                        onClick={() => onPageChange(currentPage - 1)}
                        disabled={currentPage <= 1}
                        className="flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <i className="fas fa-chevron-left mr-2"></i>
                        이전
                    </button>
                    <span className="flex items-center text-sm text-gray-700">
                        {currentPage} / {totalPages}
                    </span>
                    <button
                        onClick={() => onPageChange(currentPage + 1)}
                        disabled={currentPage >= totalPages}
                        className="flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        다음
                        <i className="fas fa-chevron-right ml-2"></i>
                    </button>
                </div>
                
                {/* 모바일 빠른 이동 */}
                <form onSubmit={handleJumpToPage} className="flex justify-center">
                    <div className="flex items-center space-x-2">
                        <input
                            type="number"
                            min="1"
                            max={totalPages}
                            value={jumpPage}
                            onChange={(e) => setJumpPage(e.target.value)}
                            placeholder="페이지"
                            className="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-center"
                        />
                        <button
                            type="submit"
                            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                        >
                            이동
                        </button>
                    </div>
                </form>
            </div>
            
            {/* 데스크톱 버전 */}
            <div className="hidden sm:flex sm:items-center sm:justify-between">
                <div className="flex items-center space-x-4">
                    <p className="text-sm text-gray-700">
                        총 <span className="font-medium">{totalPages.toLocaleString()}</span> 페이지 중{' '}
                        <span className="font-medium">{currentPage.toLocaleString()}</span> 페이지
                    </p>
                    
                    {/* 빠른 이동 버튼들 */}
                    {getQuickJumpPages().length > 0 && (
                        <div className="flex items-center space-x-1">
                            <span className="text-xs text-gray-500">빠른 이동:</span>
                            {getQuickJumpPages().map(page => (
                                <button
                                    key={page}
                                    onClick={() => onPageChange(page)}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                                >
                                    {page}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
                
                <div className="flex items-center space-x-4">
                    {/* 페이지 입력 */}
                    <form onSubmit={handleJumpToPage} className="flex items-center space-x-2">
                        <input
                            type="number"
                            min="1"
                            max={totalPages}
                            value={jumpPage}
                            onChange={(e) => setJumpPage(e.target.value)}
                            placeholder="페이지 번호"
                            className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                        <button
                            type="submit"
                            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
                        >
                            이동
                        </button>
                    </form>
                    
                    {/* 페이지 네비게이션 */}
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        {/* 첫 페이지 */}
                        <button
                            onClick={() => onPageChange(1)}
                            disabled={currentPage <= 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="첫 페이지"
                        >
                            <i className="fas fa-angle-double-left"></i>
                        </button>
                        
                        {/* 이전 페이지 */}
                        <button
                            onClick={() => onPageChange(currentPage - 1)}
                            disabled={currentPage <= 1}
                            className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="이전 페이지"
                        >
                            <i className="fas fa-chevron-left"></i>
                        </button>
                        
                        {/* 페이지 번호들 */}
                        {startPage > 1 && (
                            <>
                                <button
                                    onClick={() => onPageChange(1)}
                                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                                >
                                    1
                                </button>
                                {startPage > 2 && (
                                    <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                        ...
                                    </span>
                                )}
                            </>
                        )}
                        
                        {pages.map(page => (
                            <button
                                key={page}
                                onClick={() => onPageChange(page)}
                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium transition-colors ${
                                    page === currentPage
                                        ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                }`}
                            >
                                {page}
                            </button>
                        ))}
                        
                        {endPage < totalPages && (
                            <>
                                {endPage < totalPages - 1 && (
                                    <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                        ...
                                    </span>
                                )}
                                <button
                                    onClick={() => onPageChange(totalPages)}
                                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                                >
                                    {totalPages}
                                </button>
                            </>
                        )}
                        
                        {/* 다음 페이지 */}
                        <button
                            onClick={() => onPageChange(currentPage + 1)}
                            disabled={currentPage >= totalPages}
                            className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="다음 페이지"
                        >
                            <i className="fas fa-chevron-right"></i>
                        </button>
                        
                        {/* 마지막 페이지 */}
                        <button
                            onClick={() => onPageChange(totalPages)}
                            disabled={currentPage >= totalPages}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="마지막 페이지"
                        >
                            <i className="fas fa-angle-double-right"></i>
                        </button>
                    </nav>
                </div>
            </div>
        </div>
    );
}

// 기관 생성 모달
function CreateOrganizationModal({ onClose, onSuccess }) {
    const [formData, setFormData] = useState({
        name: '',
        type: '교회',
        category: '',
        phone: '',
        fax: '',
        email: '',
        homepage: '',
        address: '',
        contact_status: 'NEW',
        priority: 'MEDIUM'
    });
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.name.trim()) {
            newErrors.name = '기관명은 필수입니다.';
        }
        
        if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = '올바른 이메일 형식이 아닙니다.';
        }
        
        if (formData.homepage && !/^https?:\/\/.+/.test(formData.homepage)) {
            newErrors.homepage = 'http:// 또는 https://로 시작해야 합니다.';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        try {
            setLoading(true);
            await API.createOrganization(formData);
            alert('기관이 성공적으로 생성되었습니다.');
            onSuccess();
        } catch (error) {
            console.error('기관 생성 실패:', error);
            alert('기관 생성에 실패했습니다: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (key, value) => {
        setFormData(prev => ({ ...prev, [key]: value }));
        // 에러 메시지 클리어
        if (errors[key]) {
            setErrors(prev => ({ ...prev, [key]: '' }));
        }
    };

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-2xl bg-white rounded-lg shadow-xl">
                <div className="flex justify-between items-center p-6 border-b">
                    <h3 className="text-lg font-medium text-gray-900">새 기관 추가</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <i className="fas fa-times text-xl"></i>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6">
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    기관명 *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.name ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="기관명을 입력하세요"
                                />
                                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    유형
                                </label>
                                <select
                                    value={formData.type}
                                    onChange={(e) => handleInputChange('type', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="교회">교회</option>
                                    <option value="학원">학원</option>
                                    <option value="공공기관">공공기관</option>
                                    <option value="학교">학교</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    전화번호
                                </label>
                                <input
                                    type="text"
                                    value={formData.phone}
                                    onChange={(e) => handleInputChange('phone', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="02-1234-5678"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    팩스
                                </label>
                                <input
                                    type="text"
                                    value={formData.fax}
                                    onChange={(e) => handleInputChange('fax', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="02-1234-5679"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    이메일
                                </label>
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange('email', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.email ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="contact@example.com"
                                />
                                {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    홈페이지
                                </label>
                                <input
                                    type="url"
                                    value={formData.homepage}
                                    onChange={(e) => handleInputChange('homepage', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.homepage ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="https://example.com"
                                />
                                {errors.homepage && <p className="mt-1 text-sm text-red-600">{errors.homepage}</p>}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                주소
                            </label>
                            <input
                                type="text"
                                value={formData.address}
                                onChange={(e) => handleInputChange('address', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="서울특별시 강남구..."
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    상태
                                </label>
                                <select
                                    value={formData.contact_status}
                                    onChange={(e) => handleInputChange('contact_status', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="NEW">신규</option>
                                    <option value="CONTACTED">접촉함</option>
                                    <option value="QUALIFIED">검증됨</option>
                                    <option value="LOST">실패</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    우선순위
                                </label>
                                <select
                                    value={formData.priority}
                                    onChange={(e) => handleInputChange('priority', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="HIGH">높음</option>
                                    <option value="MEDIUM">보통</option>
                                    <option value="LOW">낮음</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end space-x-3 mt-6 pt-6 border-t">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                        >
                            {loading && <i className="fas fa-spinner fa-spin mr-2"></i>}
                            {loading ? '생성 중...' : '생성'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// 기관 수정 모달
function EditOrganizationModal({ organization, onClose, onSuccess }) {
    const [formData, setFormData] = useState({
        name: organization.name || '',
        type: organization.type || '교회',
        category: organization.category || '',
        phone: organization.phone || '',
        fax: organization.fax || '',
        email: organization.email || '',
        homepage: organization.homepage || '',
        address: organization.address || '',
        contact_status: organization.contact_status || 'NEW',
        priority: organization.priority || 'MEDIUM'
    });
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.name.trim()) {
            newErrors.name = '기관명은 필수입니다.';
        }
        
        if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = '올바른 이메일 형식이 아닙니다.';
        }
        
        if (formData.homepage && !/^https?:\/\/.+/.test(formData.homepage)) {
            newErrors.homepage = 'http:// 또는 https://로 시작해야 합니다.';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        try {
            setLoading(true);
            await API.updateOrganization(organization.id, formData);
            alert('기관 정보가 성공적으로 수정되었습니다.');
            onSuccess();
        } catch (error) {
            console.error('기관 수정 실패:', error);
            alert('기관 수정에 실패했습니다: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (key, value) => {
        setFormData(prev => ({ ...prev, [key]: value }));
        // 에러 메시지 클리어
        if (errors[key]) {
            setErrors(prev => ({ ...prev, [key]: '' }));
        }
    };

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-2xl bg-white rounded-lg shadow-xl">
                <div className="flex justify-between items-center p-6 border-b">
                    <h3 className="text-lg font-medium text-gray-900">기관 정보 수정</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <i className="fas fa-times text-xl"></i>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6">
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    기관명 *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.name ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="기관명을 입력하세요"
                                />
                                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    유형
                                </label>
                                <select
                                    value={formData.type}
                                    onChange={(e) => handleInputChange('type', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="교회">교회</option>
                                    <option value="학원">학원</option>
                                    <option value="공공기관">공공기관</option>
                                    <option value="학교">학교</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    전화번호
                                </label>
                                <input
                                    type="text"
                                    value={formData.phone}
                                    onChange={(e) => handleInputChange('phone', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="02-1234-5678"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    팩스
                                </label>
                                <input
                                    type="text"
                                    value={formData.fax}
                                    onChange={(e) => handleInputChange('fax', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="02-1234-5679"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    이메일
                                </label>
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange('email', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.email ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="contact@example.com"
                                />
                                {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    홈페이지
                                </label>
                                <input
                                    type="url"
                                    value={formData.homepage}
                                    onChange={(e) => handleInputChange('homepage', e.target.value)}
                                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                        errors.homepage ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="https://example.com"
                                />
                                {errors.homepage && <p className="mt-1 text-sm text-red-600">{errors.homepage}</p>}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                주소
                            </label>
                            <input
                                type="text"
                                value={formData.address}
                                onChange={(e) => handleInputChange('address', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="서울특별시 강남구..."
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    상태
                                </label>
                                <select
                                    value={formData.contact_status}
                                    onChange={(e) => handleInputChange('contact_status', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="NEW">신규</option>
                                    <option value="CONTACTED">접촉함</option>
                                    <option value="QUALIFIED">검증됨</option>
                                    <option value="LOST">실패</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    우선순위
                                </label>
                                <select
                                    value={formData.priority}
                                    onChange={(e) => handleInputChange('priority', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="HIGH">높음</option>
                                    <option value="MEDIUM">보통</option>
                                    <option value="LOW">낮음</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end space-x-3 mt-6 pt-6 border-t">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                        >
                            {loading && <i className="fas fa-spinner fa-spin mr-2"></i>}
                            {loading ? '수정 중...' : '수정'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// React 앱 렌더링
ReactDOM.render(<OrganizationsList />, document.getElementById('organizations-root'));
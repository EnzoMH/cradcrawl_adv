let statusInterval;
let resultsInterval;
let lastResultCount = 0;

// 🆕 추가: 실시간 모니터링 관련 변수
let progressInterval = null;
let resultsContainer = null;
let isRealTimeMonitoringActive = false;

// 상태 업데이트
function updateStatus(message) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = 'status-message';
    }
    console.log('상태 업데이트:', message);
}

// 실시간 결과 업데이트
function updateResults() {
    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            if (data.count > lastResultCount) {
                displayRealtimeResults(data.results);
                lastResultCount = data.count;
            }
        })
        .catch(error => console.error('결과 업데이트 실패:', error));
}

// 한국 전화번호 검증 함수
function isValidKoreanPhoneNumber(phoneNumber) {
    if (!phoneNumber) return false;
    
    const number = phoneNumber.replace(/[^\d]/g, '');
    
    const validPrefixes = {
        '02': { minLength: 9, maxLength: 10, area: '서울' },
        '031': { minLength: 10, maxLength: 11, area: '경기' },
        '032': { minLength: 10, maxLength: 11, area: '인천' },
        '033': { minLength: 10, maxLength: 11, area: '강원' },
        '041': { minLength: 10, maxLength: 11, area: '충남' },
        '042': { minLength: 10, maxLength: 11, area: '대전' },
        '043': { minLength: 10, maxLength: 11, area: '충북' },
        '051': { minLength: 10, maxLength: 11, area: '부산' },
        '052': { minLength: 10, maxLength: 11, area: '울산' },
        '053': { minLength: 10, maxLength: 11, area: '대구' },
        '054': { minLength: 10, maxLength: 11, area: '경북' },
        '055': { minLength: 10, maxLength: 11, area: '경남' },
        '061': { minLength: 10, maxLength: 11, area: '전남' },
        '062': { minLength: 10, maxLength: 11, area: '광주' },
        '063': { minLength: 10, maxLength: 11, area: '전북' },
        '064': { minLength: 10, maxLength: 11, area: '제주' },
        '070': { minLength: 11, maxLength: 11, area: '인터넷전화' },
        '010': { minLength: 11, maxLength: 11, area: '핸드폰' },
        '017': { minLength: 11, maxLength: 11, area: '핸드폰' }
    };
    
    for (const [prefix, rules] of Object.entries(validPrefixes)) {
        if (number.startsWith(prefix)) {
            return number.length >= rules.minLength && number.length <= rules.maxLength;
        }
    }
    
    return false;
}

// 지역 정보 추출 함수
function getAreaInfo(phoneNumber) {
    if (!phoneNumber) return null;
    
    const number = phoneNumber.replace(/[^\d]/g, '');
    const areaMap = {
        '02': '서울', '031': '경기', '032': '인천', '033': '강원',
        '041': '충남', '042': '대전', '043': '충북',
        '051': '부산', '052': '울산', '053': '대구', '054': '경북', '055': '경남',
        '061': '전남', '062': '광주', '063': '전북', '064': '제주',
        '070': '인터넷전화', '010': '핸드폰', '017': '핸드폰'
    };
    
    for (const [prefix, area] of Object.entries(areaMap)) {
        if (number.startsWith(prefix)) {
            return { code: prefix, area: area };
        }
    }
    
    return null;
}

// 실시간 결과 표시 (엑셀 형식)
function displayRealtimeResults(results) {
    const resultsDiv = document.getElementById('realtimeResults');
    
    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<div class="loading">크롤링 결과가 없습니다.</div>';
        return;
    }

    let html = `
        <table class="excel-table" id="dataTable">
            <thead>
                <tr>
                    <th>번호</th>
                    <th class="name-col">기관명</th>
                    <th class="category-col">카테고리</th>
                    <th class="phone-col">전화번호 (구글)</th>
                    <th class="fax-col">팩스번호 (구글)</th>
                    <th class="status-col">상태</th>
                    <th class="area-col">지역정보</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    results.forEach((item, index) => {
        const phoneGoogle = item.phone_google || '';
        const faxGoogle = item.fax_google || '';
        let status = '';
        let areaInfo = '';
        
        // 전화번호 유효성 검증
        const isPhoneValid = isValidKoreanPhoneNumber(phoneGoogle);
        const isFaxValid = isValidKoreanPhoneNumber(faxGoogle);
        
        if (phoneGoogle && faxGoogle) {
            if (faxGoogle === '전화번호와 일치') {
                status = '📞📠 완전일치';
                const phoneArea = getAreaInfo(phoneGoogle);
                areaInfo = phoneArea ? `${phoneArea.area}(${phoneArea.code})` : '';
            } else {
                // 유사 패턴 감지 (앞자리 같고 뒷자리 다름)
                const phoneDigits = phoneGoogle.replace(/[^\d]/g, '');
                const faxDigits = faxGoogle.replace(/[^\d]/g, '');
                
                if (phoneDigits.length === faxDigits.length && phoneDigits.length >= 10) {
                    const prefixLength = phoneDigits.length === 10 ? 6 : 7;
                    if (phoneDigits.substring(0, prefixLength) === faxDigits.substring(0, prefixLength)) {
                        status = '📞📠 유사패턴';
                    } else {
                        status = '📞📠 별도';
                    }
                } else {
                    status = '📞📠 별도';
                }
                
                const phoneArea = getAreaInfo(phoneGoogle);
                const faxArea = getAreaInfo(faxGoogle);
                if (phoneArea && faxArea) {
                    areaInfo = phoneArea.area === faxArea.area ? 
                        `${phoneArea.area}(${phoneArea.code})` : 
                        `📞${phoneArea.area} 📠${faxArea.area}`;
                } else if (phoneArea) {
                    areaInfo = `📞${phoneArea.area}(${phoneArea.code})`;
                } else if (faxArea) {
                    areaInfo = `📠${faxArea.area}(${faxArea.code})`;
                }
            }
        } else if (phoneGoogle) {
            status = isPhoneValid ? '📞 전화만' : '📞 전화만(무효)';
            const phoneArea = getAreaInfo(phoneGoogle);
            areaInfo = phoneArea ? `${phoneArea.area}(${phoneArea.code})` : '알 수 없음';
        } else if (faxGoogle) {
            status = isFaxValid ? '📠 팩스만' : '📠 팩스만(무효)';
            const faxArea = getAreaInfo(faxGoogle);
            areaInfo = faxArea ? `${faxArea.area}(${faxArea.code})` : '알 수 없음';
        } else {
            status = '❌ 없음';
            areaInfo = '';
        }
        
        // 유효하지 않은 번호는 스타일 변경
        const rowClass = (!isPhoneValid && phoneGoogle) || (!isFaxValid && faxGoogle) ? 
            'result-row invalid-number' : 'result-row';
        
        html += `
            <tr onclick="toggleRowSelection(this)" data-index="${index}" class="${rowClass}">
                <td>${index + 1}</td>
                <td class="name-col">${item.name || ''}</td>
                <td class="category-col">${item.category || ''}</td>
                <td class="phone-col">${phoneGoogle}</td>
                <td class="fax-col">${faxGoogle}</td>
                <td class="status-col">${status}</td>
                <td class="area-col">${areaInfo}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    resultsDiv.innerHTML = html;
    
    // 테이블을 맨 아래로 스크롤 (최신 결과 보이도록)
    resultsDiv.scrollTop = resultsDiv.scrollHeight;
}

// 🆕 추가: 크롤링 시작 시 실시간 모니터링 시작
function startCrawling() {
    const testMode = document.getElementById('testMode')?.checked || false;
    const testCount = parseInt(document.getElementById('testCount')?.value || '10');
    const useAi = document.getElementById('useAi')?.checked || true;
    
    const config = {
        mode: 'enhanced',
        test_mode: testMode,
        test_count: testCount,
        use_ai: useAi
    };

    fetch('/api/start-crawling', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        console.log('크롤링 시작:', data);
        updateStatus('크롤링이 시작되었습니다...');
        
        // 🆕 추가: 실시간 모니터링 시작
        startRealTimeMonitoring();
    })
    .catch(error => {
        console.error('크롤링 시작 실패:', error);
        updateStatus('크롤링 시작에 실패했습니다.');
    });
}

// 🆕 추가: 실시간 모니터링 함수
function startRealTimeMonitoring() {
    if (isRealTimeMonitoringActive) {
        return; // 이미 실행 중이면 중복 실행 방지
    }
    
    isRealTimeMonitoringActive = true;
    
    // 결과 컨테이너 생성
    createResultsContainer();
    
    // 진행 상황 폴링 시작 (3초마다)
    progressInterval = setInterval(updateProgress, 3000);
    
    console.log('실시간 모니터링 시작');
}

// 🆕 추가: 실시간 결과 컨테이너 생성
function createResultsContainer() {
    const existingContainer = document.getElementById('real-time-results');
    if (existingContainer) {
        existingContainer.remove();
    }
    
    const container = document.createElement('div');
    container.id = 'real-time-results';
    container.innerHTML = `
        <h3>📊 실시간 크롤링 결과</h3>
        <div id="progress-section">
            <div id="progress-bar-container">
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill"></div>
                    <span id="progress-text">0%</span>
                </div>
            </div>
            <div id="current-organization">현재 처리 중: -</div>
            <div id="current-step">단계: 대기 중</div>
            <div id="stats-summary">
                <span id="completed-count">완료: 0</span> | 
                <span id="failed-count">실패: 0</span> | 
                <span id="total-count">전체: 0</span>
            </div>
        </div>
        <div id="results-table-container">
            <h4>최근 처리 결과 (최신 20개)</h4>
            <table id="results-table">
                <thead>
                    <tr>
                        <th>기관명</th>
                        <th>분류</th>
                        <th>전화번호</th>
                        <th>팩스</th>
                        <th>이메일</th>
                        <th>우편번호</th>
                        <th>주소</th>
                        <th>홈페이지</th>
                        <th>상태</th>
                        <th>단계</th>
                        <th>처리시간</th>
                    </tr>
                </thead>
                <tbody id="results-tbody">
                </tbody>
            </table>
        </div>
    `;
    
    // 메인 컨텐츠 영역에 추가
    const mainContent = document.querySelector('main') || document.body;
    mainContent.appendChild(container);
    
    resultsContainer = container;
}

// 🆕 추가: 진행 상황 업데이트
async function updateProgress() {
    try {
        const response = await fetch('/api/all-real-time-results');
        const data = await response.json();
        
        // 진행률 업데이트
        const progress = data.progress;
        updateProgressBar(progress);
        
        // 통계 업데이트
        updateStatsSummary(data);
        
        // 최신 결과들을 테이블에 추가
        if (data.results && data.results.length > 0) {
            updateResultsTable(data.results);
        }
        
        // 크롤링 완료 시 폴링 중지
        if (progress.status === 'completed' || progress.status === 'stopped' || progress.status === 'error') {
            stopRealTimeMonitoring();
            updateStatus(`크롤링 ${getStatusText(progress.status)}`);
        }
        
    } catch (error) {
        console.error('진행 상황 업데이트 실패:', error);
    }
}

// 🆕 추가: 진행률 바 업데이트
function updateProgressBar(progress) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const currentOrg = document.getElementById('current-organization');
    const currentStep = document.getElementById('current-step');
    
    if (progressFill && progressText) {
        const percentage = Math.round(progress.percentage || 0);
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}% (${progress.current_index}/${progress.total_count})`;
    }
    
    if (currentOrg) {
        currentOrg.textContent = `현재 처리 중: ${progress.current_organization || '-'}`;
    }
    
    if (currentStep && progress.latest_result) {
        currentStep.textContent = `단계: ${progress.latest_result.current_step || '처리 중'}`;
    }
}

// 🆕 추가: 통계 요약 업데이트
function updateStatsSummary(data) {
    const completedCount = document.getElementById('completed-count');
    const failedCount = document.getElementById('failed-count');
    const totalCount = document.getElementById('total-count');
    
    if (completedCount) {
        completedCount.textContent = `완료: ${data.completed_count || 0}`;
    }
    
    if (failedCount) {
        failedCount.textContent = `실패: ${data.failed_count || 0}`;
    }
    
    if (totalCount) {
        totalCount.textContent = `전체: ${data.total_count || 0}`;
    }
}

// 🆕 추가: 결과 테이블 업데이트
function updateResultsTable(results) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;
    
    // 최신 20개만 표시
    const latestResults = results.slice(-20).reverse();
    
    // 테이블 내용 완전히 새로 고침 (중복 방지)
    tbody.innerHTML = '';
    
    latestResults.forEach(result => {
        addResultToTable(result, tbody);
    });
}

// 🆕 추가: 결과를 테이블에 추가
function addResultToTable(result, tbody) {
    const row = document.createElement('tr');
    row.className = `result-row status-${result.status}`;
    
    // 홈페이지 URL 링크 처리
    const homepageLink = result.homepage_url ? 
        `<a href="${result.homepage_url}" target="_blank" title="${result.homepage_url}">링크</a>` : 
        '-';
    
    // 주소 길이 제한 (30자)
    const shortAddress = result.address && result.address.length > 30 ? 
        result.address.substring(0, 30) + '...' : 
        result.address || '-';
    
    row.innerHTML = `
        <td><strong>${result.name}</strong></td>
        <td>${result.category}</td>
        <td>${result.phone || '-'}</td>
        <td>${result.fax || '-'}</td>
        <td>${result.email || '-'}</td>
        <td>${result.postal_code || '-'}</td>
        <td title="${result.address || ''}">${shortAddress}</td>
        <td>${homepageLink}</td>
        <td><span class="status-badge status-${result.status}">${getStatusText(result.status)}</span></td>
        <td class="step-cell">${result.current_step || '-'}</td>
        <td>${result.processing_time || '-'}</td>
    `;
    
    tbody.appendChild(row);
}

// 🆕 추가: 상태 텍스트 변환
function getStatusText(status) {
    switch (status) {
        case 'completed': return '완료';
        case 'failed': return '실패';
        case 'processing': return '처리중';
        case 'stopped': return '중지됨';
        case 'error': return '오류';
        case 'idle': return '대기';
        case 'running': return '실행중';
        default: return status || '알 수 없음';
    }
}

// 🆕 추가: 실시간 모니터링 중지
function stopRealTimeMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    isRealTimeMonitoringActive = false;
    console.log('실시간 모니터링 중지');
}

// 🔧 수정: 크롤링 중지 함수 개선
function stopCrawling() {
    fetch('/api/stop-crawling', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('크롤링 중지:', data);
        updateStatus('크롤링이 중지되었습니다.');
        stopRealTimeMonitoring();
    })
    .catch(error => {
        console.error('크롤링 중지 실패:', error);
        updateStatus('크롤링 중지에 실패했습니다.');
    });
}

// 행 선택 기능
function toggleRowSelection(row) {
    row.classList.toggle('selected');
    if (row.classList.contains('selected')) {
        row.style.backgroundColor = '#007bff';
        row.style.color = 'white';
    } else {
        row.style.backgroundColor = '';
        row.style.color = '';
    }
}

// 전체 행 선택
function selectAllRows() {
    const rows = document.querySelectorAll('#dataTable tbody tr');
    rows.forEach(row => {
        if (!row.classList.contains('selected')) {
            toggleRowSelection(row);
        }
    });
}

// 테이블 데이터 복사 (전체)
function copyTableData() {
    const table = document.getElementById('dataTable');
    if (!table) {
        showAlert('복사할 데이터가 없습니다.', 'warning');
        return;
    }

    let copyText = '';
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = [];
        // 번호 컬럼 제외하고 복사
        for (let i = 1; i < cells.length; i++) {
            rowData.push(cells[i].textContent.trim());
        }
        copyText += rowData.join('\t') + '\n';
    });

    copyToClipboard(copyText);
    showAlert('전체 데이터가 클립보드에 복사되었습니다.', 'success');
}

// 선택된 행 복사
function copySelectedRows() {
    const selectedRows = document.querySelectorAll('#dataTable tbody tr.selected');
    if (selectedRows.length === 0) {
        showAlert('선택된 행이 없습니다.', 'warning');
        return;
    }

    let copyText = '';
    selectedRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = [];
        // 번호 컬럼 제외하고 복사
        for (let i = 1; i < cells.length; i++) {
            rowData.push(cells[i].textContent.trim());
        }
        copyText += rowData.join('\t') + '\n';
    });

    copyToClipboard(copyText);
    showAlert(`${selectedRows.length}개 행이 클립보드에 복사되었습니다.`, 'success');
}

// 클립보드에 복사
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text);
    } else {
        // 폴백 방법
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    }
}

// 🆕 추가: 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('크롤링 제어 시스템 로드 완료');
    
    // 기존 크롤링이 진행 중인지 확인
    fetch('/api/progress')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'running') {
                console.log('진행 중인 크롤링 발견, 실시간 모니터링 시작');
                startRealTimeMonitoring();
            }
        })
        .catch(error => {
            console.log('진행 상황 확인 실패:', error);
        });
});

// 🆕 추가: 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    stopRealTimeMonitoring();
}); 
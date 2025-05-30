let statusInterval;
let resultsInterval;
let lastResultCount = 0;

// 상태 업데이트
function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('processedCount').textContent = data.processed_count;
            document.getElementById('totalCount').textContent = data.total_count;
            document.getElementById('currentOrganization').textContent = data.current_organization || '대기 중...';
            
            // 진행률 계산
            const progress = data.total_count > 0 ? (data.processed_count / data.total_count) * 100 : 0;
            document.getElementById('progressFill').style.width = progress + '%';
            
            // 크롤링 완료 확인
            if (!data.is_running && data.processed_count > 0) {
                showAlert('크롤링이 완료되었습니다!', 'success');
                stopStatusUpdates();
            }
        })
        .catch(error => console.error('상태 업데이트 실패:', error));
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

// 크롤링 시작
function startCrawling() {
    const config = {};  // 배치 크기 제거

    fetch('/api/start-crawling', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        showAlert(data.message, 'success');
        startRealtimeUpdates();
    })
    .catch(error => {
        showAlert('크롤링 시작 실패: ' + error.message, 'danger');
    });
}

// 크롤링 중지
function stopCrawling() {
    fetch('/api/stop-crawling', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        showAlert(data.message, 'warning');
        stopRealtimeUpdates();
    })
    .catch(error => {
        showAlert('크롤링 중지 실패: ' + error.message, 'danger');
    });
}

// 결과 다운로드
function downloadResults() {
    fetch('/api/download-results')
        .then(response => response.json())
        .then(data => {
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = data.filename;
            link.click();
            showAlert('파일 다운로드가 시작되었습니다.', 'success');
        })
        .catch(error => {
            showAlert('다운로드 실패: ' + error.message, 'danger');
        });
}

// 알림 표시
function showAlert(message, type) {
    const alertArea = document.getElementById('alertArea');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    alertArea.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 실시간 업데이트 시작
function startRealtimeUpdates() {
    if (statusInterval) clearInterval(statusInterval);
    if (resultsInterval) clearInterval(resultsInterval);
    
    statusInterval = setInterval(updateStatus, 2000);
    resultsInterval = setInterval(updateResults, 3000);
    
    // 초기 결과 로드
    updateResults();
}

// 실시간 업데이트 중지
function stopRealtimeUpdates() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    if (resultsInterval) {
        clearInterval(resultsInterval);
        resultsInterval = null;
    }
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

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    updateStatus();
    startStatusUpdates();
    loadStatistics(); // 통계 로드 추가
});

// 통계 관련 함수들
function loadStatistics() {
    console.log('통계 데이터 로딩 시작...');
    
    // 기본 통계 로드
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayBasicStatistics(data.data);
            } else {
                console.error('통계 로드 실패:', data.message);
                showStatisticsError('기본 통계를 불러올 수 없습니다.');
            }
        })
        .catch(error => {
            console.error('통계 API 오류:', error);
            showStatisticsError('통계 서버 연결에 실패했습니다.');
        });
}

function displayBasicStatistics(data) {
    console.log('기본 통계 표시:', data);
    
    // 기본 통계 카드 업데이트
    const basicStats = data.basic_stats || {};
    const contactCoverage = data.contact_coverage || {};
    const qualityMetrics = data.quality_metrics || {};
    
    // 기관 수 및 연락처 수 표시
    document.getElementById('totalOrganizations').textContent = basicStats.total_organizations?.toLocaleString() || '0';
    document.getElementById('phoneCount').textContent = `${contactCoverage.phone?.count || 0} (${contactCoverage.phone?.rate || 0}%)`;
    document.getElementById('faxCount').textContent = `${contactCoverage.fax?.count || 0} (${contactCoverage.fax?.rate || 0}%)`;
    document.getElementById('emailCount').textContent = `${contactCoverage.email?.count || 0} (${contactCoverage.email?.rate || 0}%)`;
    
    // 품질 지표 프로그레스 바 업데이트
    updateQualityBar('phoneValidityBar', 'phoneValidityText', qualityMetrics.phone_validity || 0);
    updateQualityBar('faxValidityBar', 'faxValidityText', qualityMetrics.fax_validity || 0);
    updateQualityBar('completenessBar', 'completenessText', qualityMetrics.completeness_score || 0);
    
    console.log('기본 통계 표시 완료');
}

function updateQualityBar(barId, textId, value) {
    const bar = document.getElementById(barId);
    const text = document.getElementById(textId);
    
    if (bar && text) {
        const percentage = Math.round(value);
        bar.style.width = percentage + '%';
        text.textContent = percentage + '%';
        
        // 색상 변경 (품질에 따라)
        if (percentage >= 80) {
            bar.style.backgroundColor = '#28a745'; // 녹색
        } else if (percentage >= 60) {
            bar.style.backgroundColor = '#ffc107'; // 노란색
        } else {
            bar.style.backgroundColor = '#dc3545'; // 빨간색
        }
    }
}

function toggleStatisticsDetails() {
    const detailsDiv = document.getElementById('statisticsDetails');
    const button = event.target;
    
    if (detailsDiv.style.display === 'none') {
        detailsDiv.style.display = 'block';
        button.textContent = '📋 상세 숨기기';
        loadDetailedStatistics();
    } else {
        detailsDiv.style.display = 'none';
        button.textContent = '📋 상세 보기';
    }
}

function loadDetailedStatistics() {
    console.log('상세 통계 로딩 시작...');
    
    // 지역별 통계 로드
    loadRegionalStatistics();
    
    // 카테고리별 통계 로드
    loadCategoryStatistics();
}

function loadRegionalStatistics() {
    fetch('/api/statistics/regions')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayRegionalChart(data.data.regions);
            } else {
                console.error('지역 통계 로드 실패:', data.message);
            }
        })
        .catch(error => {
            console.error('지역 통계 API 오류:', error);
        });
}

function displayRegionalChart(regions) {
    const chartContainer = document.getElementById('regionalChart');
    
    if (!regions || regions.length === 0) {
        chartContainer.innerHTML = '<div class="no-data">지역별 데이터가 없습니다.</div>';
        return;
    }
    
    // 상위 10개 지역만 표시
    const topRegions = regions.slice(0, 10);
    
    let chartHTML = '<div class="bar-chart">';
    const maxContacts = Math.max(...topRegions.map(r => r.total_contacts));
    
    topRegions.forEach(region => {
        const percentage = (region.total_contacts / maxContacts) * 100;
        chartHTML += `
            <div class="bar-item">
                <div class="bar-label">${region.area_name}(${region.area_code})</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="bar-value">${region.total_contacts}개</div>
            </div>
        `;
    });
    
    chartHTML += '</div>';
    chartContainer.innerHTML = chartHTML;
}

function loadCategoryStatistics() {
    fetch('/api/statistics/categories')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayCategoryChart(data.data.categories);
            } else {
                console.error('카테고리 통계 로드 실패:', data.message);
            }
        })
        .catch(error => {
            console.error('카테고리 통계 API 오류:', error);
        });
}

function displayCategoryChart(categories) {
    const chartContainer = document.getElementById('categoryChart');
    
    if (!categories || categories.length === 0) {
        chartContainer.innerHTML = '<div class="no-data">카테고리 데이터가 없습니다.</div>';
        return;
    }
    
    let chartHTML = '<div class="category-table"><table>';
    chartHTML += `
        <thead>
            <tr>
                <th>카테고리</th>
                <th>총 기관</th>
                <th>전화번호</th>
                <th>팩스번호</th>
                <th>이메일</th>
                <th>완성도</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    categories.forEach(category => {
        chartHTML += `
            <tr>
                <td><strong>${category.name}</strong></td>
                <td>${category.total_count}</td>
                <td>${category.phone_count} (${category.phone_coverage}%)</td>
                <td>${category.fax_count} (${category.fax_coverage}%)</td>
                <td>${category.email_count} (${category.email_coverage}%)</td>
                <td>
                    <div class="mini-progress">
                        <div class="mini-progress-fill" style="width: ${category.completeness}%"></div>
                    </div>
                    ${category.completeness}%
                </td>
            </tr>
        `;
    });
    
    chartHTML += '</tbody></table></div>';
    chartContainer.innerHTML = chartHTML;
}

function showStatisticsError(message) {
    const overviewDiv = document.getElementById('statisticsOverview');
    if (overviewDiv) {
        overviewDiv.innerHTML = `
            <div class="error-message">
                <h3>⚠️ 통계 로드 실패</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="loadStatistics()">🔄 다시 시도</button>
            </div>
        `;
    }
}

// 크롤링 완료 시 통계 자동 갱신
function stopStatusUpdates() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    if (resultsInterval) {
        clearInterval(resultsInterval);
        resultsInterval = null;
    }
    
    // 크롤링 완료 후 통계 자동 갱신
    setTimeout(() => {
        console.log('크롤링 완료 - 통계 자동 갱신');
        loadStatistics();
    }, 2000);
} 
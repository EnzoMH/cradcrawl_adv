
# 🏢 Advanced Organization Crawler

한국 기관/단체의 연락처 정보를 자동으로 수집하고 분석하는 지능형 크롤링 시스템

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [설치 방법](#설치-방법)
- [사용법](#사용법)
- [프로젝트 구조](#프로젝트-구조)
- [API 설정](#api-설정)
- [예제](#예제)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

## 🎯 개요

**Advanced Organization Crawler**는 한국의 교회, 태권도장, 교육기관 등 다양한 기관의 연락처 정보를 자동으로 수집하는 시스템입니다. 

### ✨ 핵심 특징

- 🔍 **기관명만으로 홈페이지 자동 검색** (네이버 검색 엔진 활용)
- 🤖 **AI 기반 지능형 웹 분석** (Google Gemini API)
- 📞 **정확한 연락처 추출** (전화번호, 팩스, 이메일, 주소)
- 🧹 **중복 제거 및 데이터 검증**
- 📊 **다양한 출력 형식** (JSON, Excel)
- ⚡ **비동기 처리**로 빠른 성능

## 🚀 주요 기능

### 1. 홈페이지 URL 자동 검색
```python
# 기관명만 입력하면 공식 홈페이지를 자동으로 찾아줍니다
search_result = extractor.search_homepage_url_with_ai_analysis("흥광장로교회")
# 결과: "https://www.hkchurch.or.kr"
```

### 2. AI 기반 연락처 추출
- **전화번호**: 한국 지역번호 형식 검증
- **팩스번호**: 전화번호와 중복 검사
- **이메일**: 유효한 이메일 형식만 추출
- **주소**: 완전한 주소 정보 수집
- **우편번호**: 5자리 우편번호 추출

### 3. 지능형 데이터 처리
- JSON 데이터 활용 우선
- 부족한 정보만 웹 크롤링
- AI가 웹페이지 내용을 이해하고 판단
- 하드코딩된 선택자 없이 유연한 분석

### 4. 대용량 데이터 처리
- 비동기 처리로 빠른 성능
- TPM(Tokens Per Minute) 제한 자동 관리
- 메모리 효율적인 청크 처리

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/advanced-organization-crawler.git
cd advanced-organization-crawler
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🔧 API 설정

### Google Gemini API 키 발급
1. [Google AI Studio](https://makersuite.google.com/app/apikey)에 접속
2. API 키 생성
3. `.env` 파일에 키 추가

### ChromeDriver 설정
Selenium 사용을 위해 ChromeDriver가 필요합니다:
```bash
# Chrome 브라우저가 설치되어 있어야 합니다
# ChromeDriver는 자동으로 관리됩니다
```

## 💻 사용법

### 기본 사용법

```python
from enhanced_detail_extractor import extract_enhanced_details

# 완전 자동화 처리
results, json_file, excel_file, stats = extract_enhanced_details(
    json_file_path="raw_data.json",
    use_selenium=True,      # URL 검색 활성화
    headless=False,         # 브라우저 창 표시
    test_mode=True,         # 테스트 모드
    test_count=10           # 10개 기관만 처리
)

print(f"처리 완료: {len(results)}개 기관")
print(f"JSON 파일: {json_file}")
print(f"Excel 파일: {excel_file}")
```

### CSV를 JSON으로 변환

```python
from legacy.csvtojson import CSVtoJSONConverter

converter = CSVtoJSONConverter()
converter.convert_csv_to_json(
    csv_file="raw_data.csv",
    output_file="converted_data.json"
)
```

### URL만 추출하기

```python
from legacy.url_extractor import URLExtractor

extractor = URLExtractor(headless=False)
organizations = [...] # 기관 데이터 리스트
processed = extractor.process_organizations(organizations)
```

## 📁 프로젝트 구조

```
advanced_crawling/
├── enhanced_detail_extractor.py   # 🎯 핵심 추출 엔진
├── constants.py                   # 📋 전역 상수 정의
├── ai_helpers.py                  # 🤖 AI 유틸리티
├── utils/                         # 🛠️ 유틸리티 모듈
│   ├── phone_utils.py            # 📞 전화번호 처리
│   ├── file_utils.py             # 📁 파일 입출력
│   ├── crawler_utils.py          # 🌐 크롤링 유틸
│   └── logger_utils.py           # 📝 로깅 관리
├── legacy/                        # 📚 레거시 도구들
│   ├── csvtojson.py              # CSV → JSON 변환
│   ├── url_extractor.py          # URL 추출 (Selenium)
│   └── ...
├── validator.py                   # ✅ 데이터 검증
├── parser.py                      # 🔍 웹페이지 파싱
├── app.py                         # 🚀 메인 애플리케이션
└── requirements.txt               # 📦 의존성 목록
```

### 핵심 모듈 설명

| 모듈 | 설명 | 주요 기능 |
|------|------|-----------|
| `enhanced_detail_extractor.py` | 메인 추출 엔진 | AI 기반 연락처 추출, URL 검색 |
| `utils/phone_utils.py` | 전화번호 처리 | 한국 전화번호 검증, 포맷팅, 중복 검사 |
| `utils/crawler_utils.py` | 크롤링 유틸 | 세션 관리, 요청 처리 |
| `ai_helpers.py` | AI 관련 기능 | Gemini API 관리, 프롬프트 처리 |
| `legacy/url_extractor.py` | URL 검색 도구 | Selenium 기반 네이버 검색 |

## 📊 입력/출력 형식

### 입력 JSON 형식
```json
[
  {
    "name": "흥광장로교회",
    "category": "교회",
    "address": "인천광역시 남동구",
    "phone": "",
    "homepage": ""
  }
]
```

### 출력 JSON 형식
```json
[
  {
    "기관명": "흥광장로교회",
    "홈페이지": "https://www.hkchurch.or.kr",
    "주소": "인천광역시 남동구 구월동 123-45",
    "우편번호": "21565",
    "전화번호": "032-123-4567",
    "팩스번호": "032-123-4568",
    "이메일": "info@hkchurch.or.kr",
    "추출방법": "JSON+크롤링",
    "추출상태": "성공"
  }
]
```

## ⚙️ 설정 옵션

### AI 모델 설정 (`constants.py`)
```python
AI_MODEL_CONFIG = {
    'temperature': 0.1,      # 창의성 낮음 (정확성 우선)
    'top_p': 0.8,
    'top_k': 10,
    'max_output_tokens': 1000,
}

TPM_LIMITS = {
    'requests_per_minute': 6,  # 분당 6회 (무료 제한)
    'max_wait_time': 30       # 최대 대기 시간
}
```

### 크롤링 설정
```python
CRAWLING_CONFIG = {
    "timeout": 10,           # 요청 타임아웃
    "max_text_length": 10000, # 최대 텍스트 길이
    "async_timeout": 120     # 비동기 타임아웃
}
```

## 🔍 예제

### 완전 자동화 예제

```python
import asyncio
from enhanced_detail_extractor import extract_enhanced_details

async def main():
    # 테스트 모드로 5개 기관 처리
    results, json_file, excel_file, stats = await extract_enhanced_details(
        json_file_path="sample_data.json",
        api_key="your_gemini_api_key",  # 선택사항 (.env 사용 가능)
        use_selenium=True,              # URL 검색 활성화
        headless=False,                 # 브라우저 창 보이기
        test_mode=True,                 # 테스트 모드
        test_count=5                    # 5개만 처리
    )
    
    print(f"✅ 처리 완료!")
    print(f"📊 처리된 기관: {stats['total_processed']}개")
    print(f"🔍 URL 발견: {stats['url_found']}개")
    print(f"📞 전화번호 발견: {stats['phone_found']}개")
    print(f"🤖 AI 호출: {stats['api_calls_made']}회")

# 실행
asyncio.run(main())
```

### 단계별 처리 예제

```python
from enhanced_detail_extractor import EnhancedDetailExtractor

# 1. 추출기 초기화
extractor = EnhancedDetailExtractor(
    use_selenium=True,
    headless=False
)

# 2. 단일 기관 처리
org_data = {
    "name": "삼성교회",
    "address": "서울시 강남구"
}

result = await extractor.process_single_organization_enhanced(org_data)
print(result)

# 3. 드라이버 정리
extractor.close_selenium_driver()
```

## 📈 성능 최적화

### 1. TPM 제한 관리
- Gemini 1.5-flash 무료 버전: 분당 6회 제한
- 자동 대기 및 재시도 로직

### 2. 토큰 사용 최적화  
- 입력 텍스트를 30K 토큰 이하로 제한
- 중요 부분 우선 추출 (Footer, Contact 섹션)

### 3. 메모리 효율성
- 청크 단위 처리
- 불필요한 HTML 태그 제거

## 🐛 문제 해결

### 자주 발생하는 오류

#### 1. ChromeDriver 오류
```bash
# Chrome 브라우저 업데이트
# ChromeDriver는 자동으로 관리됩니다
```

#### 2. Gemini API 오류
```python
# API 키 확인
print(os.getenv('GEMINI_API_KEY'))

# 요청 제한 확인
# 무료 버전: 분당 6회, 일일 1000회
```

#### 3. 메모리 부족
```python
# 테스트 모드로 소량 처리
test_mode=True, test_count=10
```

## 📋 요구사항

### Python 버전
- Python 3.8 이상

### 주요 의존성
```
selenium>=4.0.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
google-generativeai>=0.3.0
requests>=2.28.0
openpyxl>=3.0.0
python-dotenv>=0.19.0
```

## 🤝 기여하기

1. 이 저장소를 Fork합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

### 개발 가이드라인
- 코드 스타일: PEP 8 준수
- 문서화: 함수별 docstring 작성
- 테스트: 새 기능 추가시 테스트 코드 포함

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **Google Gemini API**: AI 기반 웹 분석 기능
- **Selenium**: 브라우저 자동화
- **BeautifulSoup**: HTML 파싱
- **네이버**: 검색 엔진 API

## 📞 문의

- 이슈: [GitHub Issues](https://github.com/your-username/advanced-organization-crawler/issues)
- 이메일: isfs003@gmail.com

---

⭐ **이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

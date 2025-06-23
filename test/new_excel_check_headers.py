#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 통합 CRM 데이터베이스 구축을 위한 헤더 분석 및 AI 기반 합병 방안 제시
Version 2: 교회 데이터 3행 헤더 처리 + 새로운 SimpleAI 클라이언트
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
import asyncio
from typing import Dict, List, Any, Optional

# 상대경로 import를 위한 path 설정
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Gemini AI 모듈 import
try:
    import google.generativeai as genai
    from settings import GEMINI_API_KEY, GEMINI_MODEL_TEXT
    GEMINI_AVAILABLE = True and bool(GEMINI_API_KEY)
    print(f"✅ Gemini AI 사용 가능: {GEMINI_AVAILABLE}")
except ImportError as e:
    print(f"⚠️ Gemini AI 모듈을 가져올 수 없습니다: {e}")
    GEMINI_AVAILABLE = False
    genai = None
    GEMINI_API_KEY = None
    GEMINI_MODEL_TEXT = "gemini-1.5-flash"

# 기존 ai_helpers도 시도 (fallback용)
try:
    from ai_helpers import AIModelManager, extract_with_gemini_text
    AI_HELPERS_AVAILABLE = True
except ImportError:
    print("⚠️ AI helpers 모듈을 가져올 수 없습니다.")
    AI_HELPERS_AVAILABLE = False

class SimpleAIClient:
    """간단한 Gemini AI 클라이언트 (ai_helpers와 별도)"""
    
    def __init__(self):
        self.model = None
        self.available = GEMINI_AVAILABLE
        
        if self.available and genai and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL_TEXT)
                print(f"✅ SimpleAI 클라이언트 초기화 완료 (모델: {GEMINI_MODEL_TEXT})")
            except Exception as e:
                print(f"❌ SimpleAI 클라이언트 초기화 실패: {e}")
                self.available = False
                self.model = None
        else:
            print("⚠️ SimpleAI 클라이언트 비활성화 (API 키 또는 모듈 없음)")
    
    def generate_response(self, prompt: str) -> str:
        """AI 응답 생성 (동기 방식)"""
        if not self.available or not self.model:
            return "AI 기능을 사용할 수 없습니다. 수동 분석 결과를 사용합니다."
        
        try:
            print("🤖 Gemini AI 응답 생성 중...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            print(f"✅ AI 응답 생성 완료 (길이: {len(response_text)} chars)")
            return response_text
            
        except Exception as e:
            print(f"❌ AI 응답 생성 오류: {str(e)}")
            return f"AI 오류로 인한 더미 응답: {str(e)}"


class DataHeaderAnalyzer:
    """데이터 파일 헤더 분석 및 AI 기반 합병 방안 제시 클래스"""
    
    def __init__(self):
        # 다중 AI 방식 설정 (우선순위: SimpleAI → ai_helpers → 수동분석)
        self.simple_ai = SimpleAIClient()
        
        if AI_HELPERS_AVAILABLE:
            self.ai_manager = AIModelManager()
        else:
            self.ai_manager = None
        
        self.data_files = {
            'academy': '../학원교습소정보_2024년10월31일기준20250617수정.xlsx',
            'church': '../data/excel/교회_원본_수정01.xlsx',
            'filtered_json': '../data/json/filtered_data_updated_20250613_013541.json'
        }
        self.headers = {}
        self.sample_data = {}
        
    def analyze_church_excel_with_header_row_3(self, file_path: str) -> Dict[str, Any]:
        """교회 엑셀 파일 분석 (3행이 헤더)"""
        try:
            abs_path = Path(current_dir) / file_path
            print(f"📊 교회 파일 분석 중 (3행 헤더): {abs_path}")
            
            # 3행을 헤더로 지정 (pandas에서는 0부터 시작하므로 2)
            df = pd.read_excel(abs_path, header=2, nrows=10)
            headers = df.columns.tolist()
            sample_data = df.head(3).to_dict('records')
            
            # NaN 값이 많은 헤더들 정리
            cleaned_headers = []
            for i, h in enumerate(headers):
                if pd.isna(h) or str(h).startswith('Unnamed'):
                    # 실제 데이터에서 첫 번째 값을 헤더로 사용
                    try:
                        first_val = df[h].dropna().iloc[0] if not df[h].dropna().empty else f"Column_{i}"
                        cleaned_headers.append(str(first_val))
                    except:
                        cleaned_headers.append(f"Column_{i}")
                else:
                    cleaned_headers.append(str(h))
            
            analysis = {
                'file_path': str(abs_path),
                'file_type': 'church',
                'headers': cleaned_headers,
                'original_headers': headers,
                'header_count': len(cleaned_headers),
                'sample_data': sample_data,
                'data_shape': df.shape,
                'note': '3행을 헤더로 사용하여 분석됨'
            }
            
            print(f"✅ 교회 데이터 헤더 개수: {len(cleaned_headers)}")
            print(f"📝 정리된 헤더 목록: {cleaned_headers[:10]}{'...' if len(cleaned_headers) > 10 else ''}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ 교회 파일 분석 오류: {str(e)}")
            return None
        
    def analyze_excel_headers(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """엑셀 파일의 헤더 분석 (다양한 방식으로 시도)"""
        try:
            abs_path = Path(current_dir) / file_path
            print(f"📊 {file_type} 파일 분석 중: {abs_path}")
            
            # 먼저 기본 방식으로 시도
            try:
                df = pd.read_excel(abs_path, nrows=10)
                headers = df.columns.tolist()
                sample_data = df.head(3).to_dict('records')
                
                # 헤더가 'Unnamed'인 경우 다른 방식으로 시도
                if any('Unnamed' in str(h) for h in headers):
                    print(f"⚠️ {file_type} 파일에서 Unnamed 헤더 발견. 다른 방식으로 시도...")
                    
                    # 헤더가 2번째 또는 3번째 행에 있을 수 있음
                    for header_row in [1, 2, 3]:
                        try:
                            df_alt = pd.read_excel(abs_path, header=header_row, nrows=10)
                            headers_alt = df_alt.columns.tolist()
                            if not any('Unnamed' in str(h) for h in headers_alt):
                                headers = headers_alt
                                sample_data = df_alt.head(3).to_dict('records')
                                print(f"✅ {file_type} 헤더를 {header_row+1}번째 행에서 찾았습니다.")
                                break
                        except:
                            continue
                            
            except Exception as e:
                print(f"❌ {file_type} 파일 기본 읽기 실패: {str(e)}")
                return None
            
            analysis = {
                'file_path': str(abs_path),
                'file_type': file_type,
                'headers': headers,
                'header_count': len(headers),
                'sample_data': sample_data,
                'data_shape': df.shape if 'df' in locals() else (0, 0)
            }
            
            print(f"✅ {file_type} 헤더 개수: {len(headers)}")
            print(f"📝 헤더 목록: {headers[:10]}{'...' if len(headers) > 10 else ''}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ {file_type} 파일 분석 오류: {str(e)}")
            return None
    
    def analyze_json_headers(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """JSON 파일의 헤더 분석"""
        try:
            abs_path = Path(current_dir) / file_path
            print(f"📊 {file_type} 파일 분석 중: {abs_path}")
            
            with open(abs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return None
            
            # 첫 번째 항목에서 키 추출
            sample_item = data[0] if isinstance(data, list) else data
            headers = list(sample_item.keys())
            
            # 샘플 데이터 가져오기 (처음 3개)
            sample_data = data[:3] if isinstance(data, list) else [data]
            
            analysis = {
                'file_path': str(abs_path),
                'file_type': file_type,
                'headers': headers,
                'header_count': len(headers),
                'sample_data': sample_data,
                'data_count': len(data) if isinstance(data, list) else 1
            }
            
            print(f"✅ {file_type} 헤더 개수: {len(headers)}")
            print(f"📝 헤더 목록: {headers}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ {file_type} 파일 분석 오류: {str(e)}")
            return None
    
    def analyze_all_files(self):
        """모든 파일의 헤더 분석"""
        print("🔍 데이터 파일 헤더 분석 시작...")
        
        # 학원 데이터 분석
        academy_analysis = self.analyze_excel_headers(
            self.data_files['academy'], 'academy'
        )
        if academy_analysis:
            self.headers['academy'] = academy_analysis
        
        # 교회 데이터 분석 (3행 헤더 사용)
        print("📋 교회 데이터는 3행이 실제 헤더로 처리됩니다.")
        church_analysis = self.analyze_church_excel_with_header_row_3(
            self.data_files['church']
        )
        if church_analysis:
            self.headers['church'] = church_analysis
        
        # JSON 데이터 분석
        json_analysis = self.analyze_json_headers(
            self.data_files['filtered_json'], 'filtered_json'
        )
        if json_analysis:
            self.headers['filtered_json'] = json_analysis
        
        print(f"\n📊 총 {len(self.headers)}개 파일 분석 완료")
        return self.headers
    
    def identify_common_fields(self) -> Dict[str, List[str]]:
        """공통 필드 식별"""
        common_mapping = {
            '상호명': [],
            '주소': [],
            '전화번호': [],
            '모바일번호': [],
            '카테고리': []
        }
        
        # 각 데이터 소스에서 공통 필드 매핑
        for source_name, analysis in self.headers.items():
            headers = analysis['headers']
            
            # 상호명 매핑
            name_fields = [h for h in headers if any(keyword in str(h).lower() for keyword in ['name', '명', '상호', '학원명', '교회'])]
            if name_fields:
                common_mapping['상호명'].append(f"{source_name}: {name_fields}")
            
            # 주소 매핑
            address_fields = [h for h in headers if any(keyword in str(h).lower() for keyword in ['address', '주소', '소재지', '위치'])]
            if address_fields:
                common_mapping['주소'].append(f"{source_name}: {address_fields}")
            
            # 전화번호 매핑
            phone_fields = [h for h in headers if any(keyword in str(h).lower() for keyword in ['phone', '전화', '연락처', 'tel'])]
            if phone_fields:
                common_mapping['전화번호'].append(f"{source_name}: {phone_fields}")
            
            # 모바일번호 매핑
            mobile_fields = [h for h in headers if any(keyword in str(h).lower() for keyword in ['mobile', '휴대폰', '핸드폰', '모바일'])]
            if mobile_fields:
                common_mapping['모바일번호'].append(f"{source_name}: {mobile_fields}")
            
            # 카테고리 매핑
            category_fields = [h for h in headers if any(keyword in str(h).lower() for keyword in ['category', '카테고리', '분류', '유형', '종류'])]
            if category_fields:
                common_mapping['카테고리'].append(f"{source_name}: {category_fields}")
        
        return common_mapping
    
    def create_manual_merge_strategy(self) -> Dict[str, Any]:
        """수동으로 합병 전략 생성"""
        common_fields = self.identify_common_fields()
        
        strategy = {
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "data_sources": {
                source: {
                    "file_path": analysis['file_path'],
                    "header_count": analysis['header_count'],
                    "headers": analysis['headers']
                }
                for source, analysis in self.headers.items()
            },
            "common_fields_mapping": common_fields,
            "recommended_unified_schema": {
                "table_name": "unified_crm_database",
                "primary_columns": [
                    {"name": "id", "type": "INTEGER PRIMARY KEY AUTOINCREMENT", "description": "고유 식별자"},
                    {"name": "business_name", "type": "TEXT NOT NULL", "description": "상호명/기관명"},
                    {"name": "full_address", "type": "TEXT", "description": "전체 주소"},
                    {"name": "phone_number", "type": "TEXT", "description": "대표 전화번호"},
                    {"name": "mobile_number", "type": "TEXT", "description": "모바일 번호"},
                    {"name": "category", "type": "TEXT NOT NULL", "description": "카테고리 (종교/교습소/학원/공공기관)"},
                    {"name": "data_source", "type": "TEXT NOT NULL", "description": "데이터 출처"},
                    {"name": "additional_info", "type": "JSON", "description": "추가 정보 (JSON 형태)"},
                    {"name": "created_at", "type": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "description": "생성일시"},
                    {"name": "updated_at", "type": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "description": "수정일시"}
                ]
            },
            "merge_implementation_steps": [
                "1. 각 데이터 소스별로 표준화된 형태로 데이터 추출",
                "2. 공통 필드 매핑 규칙에 따라 데이터 변환",
                "3. 중복 데이터 식별 및 제거 (상호명 + 주소 기준)",
                "4. 카테고리 표준화 (종교시설, 교육기관, 공공기관 등)",
                "5. 통합 데이터베이스 테이블 생성",
                "6. 변환된 데이터 삽입",
                "7. 데이터 품질 검증 및 보완"
            ],
            "data_quality_considerations": [
                "전화번호 형식 표준화 (하이픈 추가/제거)",
                "주소 표준화 (도로명 주소 우선)",
                "중복 업체 식별 로직 (이름 유사도 + 주소 유사도)",
                "빈 값 처리 방안",
                "특수문자 및 인코딩 문제 해결"
            ]
        }
        
        return strategy
    
    def get_ai_merge_strategy_simple(self) -> Optional[Dict[str, Any]]:
        """SimpleAI 클라이언트를 사용하여 합병 전략 생성 (동기 방식)"""
        try:
            print("\n🤖 SimpleAI를 사용하여 데이터 합병 전략 생성 중...")
            
            # 고급 프롬프트 사용
            prompt = self.create_advanced_ai_prompt()
            
            # AI 응답 받기
            ai_response = self.simple_ai.generate_response(prompt)
            
            if "AI 기능을 사용할 수 없습니다" in ai_response or "오류" in ai_response:
                print("⚠️ SimpleAI 사용 불가. 다른 방식으로 시도합니다.")
                return None
            
            print("✅ SimpleAI 합병 전략 생성 완료")
            
            # 텍스트 응답을 구조화된 데이터로 변환
            strategy = self.create_manual_merge_strategy()
            strategy["ai_analysis"] = ai_response
            strategy["ai_method"] = "SimpleAI (Gemini)"
            
            return strategy
                
        except Exception as e:
            print(f"❌ SimpleAI 합병 전략 생성 오류: {str(e)}")
            return None
    
    async def get_ai_merge_strategy_helpers(self) -> Optional[Dict[str, Any]]:
        """AI helpers를 사용하여 합병 전략 생성 (비동기 방식)"""
        if not AI_HELPERS_AVAILABLE or not self.ai_manager:
            print("⚠️ AI helpers를 사용할 수 없습니다.")
            return None
        
        try:
            print("\n🤖 AI helpers를 사용하여 데이터 합병 전략 생성 중...")
            
            # AI 모델 초기화
            await self.ai_manager.setup_models()
            
            prompt = self.create_ai_prompt_for_merge_strategy()
            
            # AI 응답 받기
            ai_response = await extract_with_gemini_text(prompt, "")
            
            print("✅ AI helpers 합병 전략 생성 완료")
            
            # JSON 파싱 시도
            try:
                strategy = json.loads(ai_response)
                strategy["ai_method"] = "AI helpers"
                return strategy
            except json.JSONDecodeError:
                print("⚠️ AI 응답을 JSON으로 파싱할 수 없습니다.")
                # 텍스트 응답을 구조화된 데이터로 변환
                strategy = self.create_manual_merge_strategy()
                strategy["ai_analysis"] = ai_response
                strategy["ai_method"] = "AI helpers (text)"
                return strategy
                
        except Exception as e:
            print(f"❌ AI helpers 합병 전략 생성 오류: {str(e)}")
            return None
    
    async def get_ai_merge_strategy(self) -> Optional[Dict[str, Any]]:
        """다중 AI 방식으로 합병 전략 생성 (우선순위: SimpleAI → ai_helpers → 수동분석)"""
        print("\n🔄 다중 AI 방식으로 데이터 합병 전략 생성 시도...")
        
        # 방법 1: SimpleAI 시도
        strategy = self.get_ai_merge_strategy_simple()
        if strategy:
            return strategy
        
        # 방법 2: AI helpers 시도
        strategy = await self.get_ai_merge_strategy_helpers()
        if strategy:
            return strategy
        
        # 방법 3: 수동 분석 (최종 fallback)
        print("📝 모든 AI 방식 실패. 수동 분석 결과를 사용합니다.")
        strategy = self.create_manual_merge_strategy()
        strategy["ai_method"] = "Manual analysis (fallback)"
        return strategy
    
    def create_advanced_ai_prompt(self) -> str:
        """고급 AI 프롬프트 생성 (urlextractor_2.py 스타일 참고)"""
        prompt = f"""
# 통합 CRM 데이터베이스 구축을 위한 전문가 분석 요청

안녕하세요. 데이터베이스 통합 전문가로서 다음 3개의 서로 다른 데이터 소스를 하나의 통합 CRM 시스템으로 합병하는 전략을 수립해주세요.

## 📊 데이터 소스 상세 분석
"""
        
        for source_name, analysis in self.headers.items():
            prompt += f"""
### 【{source_name.upper()} 데이터】
- **파일 경로**: {analysis['file_path']}
- **총 컬럼 수**: {analysis['header_count']}개
- **데이터 크기**: {analysis.get('data_shape', 'N/A')}
- **특별 사항**: {analysis.get('note', '일반 처리')}
- **전체 컬럼 목록**: {', '.join(analysis['headers'])}

**샘플 데이터 (첫 번째 레코드)**:
```json
{json.dumps(analysis['sample_data'][0] if analysis['sample_data'] else {}, ensure_ascii=False, indent=2)}
```
"""
        
        # 공통 필드 매핑 정보 추가
        common_fields = self.identify_common_fields()
        prompt += """

## 🔗 현재 식별된 공통 필드 매핑
"""
        for field_name, mappings in common_fields.items():
            prompt += f"\n**{field_name}**:\n"
            if mappings:
                for mapping in mappings:
                    prompt += f"  - {mapping}\n"
            else:
                prompt += "  - 매핑된 필드 없음\n"
        
        prompt += """

## 🎯 분석 요청사항

다음 사항들을 종합적으로 분석하여 전문적인 데이터베이스 통합 전략을 제시해주세요:

1. **공통 필드 매핑 전략**
   - 상호명/기관명 통합 방안
   - 주소 정보 표준화 방안
   - 전화번호/모바일번호 통합 정책
   - 카테고리 분류 체계 설계

2. **통합 데이터베이스 스키마 설계**
   - 기본 테이블 구조
   - 인덱스 전략
   - 확장 가능한 구조 설계
   - 메타데이터 관리 방안

3. **데이터 품질 및 중복 관리**
   - 중복 데이터 식별 알고리즘
   - 데이터 정합성 검증 방법
   - 오류 데이터 처리 전략
   - 데이터 표준화 규칙

4. **구현 계획**
   - 단계별 마이그레이션 계획
   - 성능 최적화 방안
   - 모니터링 및 검증 방법
   - 롤백 전략

## 📋 응답 형식

다음과 같은 구조화된 형식으로 답변해주세요:

**FIELD_MAPPING**: 각 공통 필드별 매핑 전략
**UNIFIED_SCHEMA**: 통합 데이터베이스 스키마
**QUALITY_STRATEGY**: 데이터 품질 관리 전략
**IMPLEMENTATION**: 구현 계획 및 순서
**ADDITIONAL_CONSIDERATIONS**: 추가 고려사항

답변은 한국어로 작성하고, 실무에서 바로 활용할 수 있도록 구체적이고 실용적인 내용으로 구성해주세요.
"""
        return prompt
    
    def create_ai_prompt_for_merge_strategy(self) -> str:
        """AI 모델에 전달할 프롬프트 생성 (기존 버전 유지)"""
        prompt = """
다음은 3개의 서로 다른 데이터 소스의 헤더 정보와 샘플 데이터입니다.
이 데이터들을 하나의 통합 CRM 데이터베이스로 합병하는 전략을 제시해주세요.

=== 데이터 소스 분석 ===
"""
        
        for source_name, analysis in self.headers.items():
            prompt += f"\n【{source_name.upper()}】\n"
            prompt += f"- 파일 경로: {analysis['file_path']}\n"
            prompt += f"- 헤더 개수: {analysis['header_count']}\n"
            prompt += f"- 헤더 목록: {analysis['headers']}\n"
            prompt += f"- 샘플 데이터 (첫 번째 항목): {analysis['sample_data'][0] if analysis['sample_data'] else 'N/A'}\n"
        
        prompt += """

=== 요구사항 ===
1. 공통 필드 식별: 상호명, 주소, 전화번호, 모바일번호, 카테고리(종교/교습소/학원/공공기관)
2. 각 데이터 소스의 고유 필드들도 보존
3. 데이터 품질 및 중복 제거 전략
4. 새로운 통합 스키마 설계

=== 답변 형식 ===
다음 JSON 형식으로 답변해주세요:

{
    "common_fields_mapping": {
        "상호명": ["academy_field", "church_field", "json_field"],
        "주소": ["academy_field", "church_field", "json_field"],
        "전화번호": ["academy_field", "church_field", "json_field"],
        "모바일번호": ["academy_field", "church_field", "json_field"],
        "카테고리": ["academy_field", "church_field", "json_field"]
    },
    "unified_schema": {
        "table_name": "unified_crm",
        "columns": [
            {"name": "id", "type": "INTEGER PRIMARY KEY AUTOINCREMENT"},
            {"name": "business_name", "type": "TEXT"},
            {"name": "address", "type": "TEXT"},
            {"name": "phone", "type": "TEXT"},
            {"name": "mobile", "type": "TEXT"},
            {"name": "category", "type": "TEXT"},
            {"name": "additional_fields", "type": "JSON"}
        ]
    },
    "merge_strategy": {
        "deduplication_rules": ["rule1", "rule2"],
        "data_transformation": ["transformation1", "transformation2"],
        "quality_checks": ["check1", "check2"]
    },
    "implementation_plan": [
        "step1: 데이터 추출 및 정규화",
        "step2: 공통 필드 매핑",
        "step3: 중복 제거",
        "step4: 통합 데이터베이스 생성"
    ]
}
"""
        return prompt
    
    def save_analysis_results(self, merge_strategy: Dict[str, Any]):
        """분석 결과를 파일로 저장"""
        try:
            results = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'header_analysis': self.headers,
                'merge_strategy': merge_strategy
            }
            
            output_file = Path(current_dir) / 'database_merge_analysis.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"📁 분석 결과 저장 완료: {output_file}")
            
        except Exception as e:
            print(f"❌ 결과 저장 오류: {str(e)}")
    
    def print_detailed_summary(self):
        """상세한 분석 결과 요약 출력"""
        print("\n" + "="*80)
        print("📊 데이터 파일 상세 헤더 분석 결과")
        print("="*80)
        
        for source_name, analysis in self.headers.items():
            print(f"\n【{source_name.upper()}】")
            print(f"  📂 파일: {os.path.basename(analysis['file_path'])}")
            print(f"  📈 헤더 개수: {analysis['header_count']}")
            print(f"  📏 데이터 크기: {analysis.get('data_shape', 'N/A')}")
            print(f"  📝 전체 헤더 목록:")
            for i, header in enumerate(analysis['headers'], 1):
                print(f"    {i:2d}. {header}")
            
            # 샘플 데이터 출력
            if analysis['sample_data']:
                print(f"  🔍 샘플 데이터 (첫 번째 항목):")
                sample = analysis['sample_data'][0]
                for key, value in sample.items():
                    if len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"    - {key}: {value}")
        
        # 공통 필드 매핑 결과
        print(f"\n" + "="*80)
        print("🔗 공통 필드 매핑 분석")
        print("="*80)
        
        common_fields = self.identify_common_fields()
        for field_name, mappings in common_fields.items():
            print(f"\n📌 {field_name}:")
            if mappings:
                for mapping in mappings:
                    print(f"  - {mapping}")
            else:
                print("  - 매핑된 필드 없음")
    
    async def run_full_analysis(self):
        """전체 분석 프로세스 실행"""
        print("🚀 통합 CRM 데이터베이스 구축을 위한 상세 분석 시작")
        print("="*80)
        
        # 1. 헤더 분석
        self.analyze_all_files()
        
        # 2. 상세 요약 출력
        self.print_detailed_summary()
        
        # 3. AI 합병 전략 생성 (또는 수동 분석)
        merge_strategy = await self.get_ai_merge_strategy()
        
        # 4. 결과 저장
        if merge_strategy:
            self.save_analysis_results(merge_strategy)
            
            # 전략 출력
            print("\n" + "="*80)
            print("📋 데이터베이스 합병 전략")
            print("="*80)
            
            # AI 방식 정보 출력
            ai_method = merge_strategy.get('ai_method', 'Unknown')
            print(f"🤖 사용된 AI 방식: {ai_method}")
            
            # AI 분석 결과가 있으면 출력
            if 'ai_analysis' in merge_strategy:
                print(f"\n📝 AI 분석 결과:")
                print("-" * 50)
                print(merge_strategy['ai_analysis'][:2000] + ("..." if len(merge_strategy['ai_analysis']) > 2000 else ""))
                print("-" * 50)
            
            # 구조화된 전략 출력
            if 'raw_response' in merge_strategy:
                print(merge_strategy['raw_response'])
            else:
                # AI 분석 제외하고 출력 (너무 길어서)
                display_strategy = {k: v for k, v in merge_strategy.items() if k != 'ai_analysis'}
                print(json.dumps(display_strategy, ensure_ascii=False, indent=2))
        
        print("\n✅ 전체 분석 완료!")
        print("🎯 다음 단계: 분석 결과를 바탕으로 실제 데이터 통합 스크립트를 작성하세요.")


async def main():
    """메인 실행 함수"""
    analyzer = DataHeaderAnalyzer()
    await analyzer.run_full_analysis()


if __name__ == "__main__":
    asyncio.run(main())

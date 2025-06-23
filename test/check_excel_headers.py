#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
엑셀 파일 헤더 및 샘플 데이터 확인 + AI 정리 + DB 저장
복잡한 헤더 구조 대응 + 학원 데이터 특화
"""

import pandas as pd
import sys
import os
from datetime import datetime
import json
from typing import Dict, List, Optional, Any
import re
import sqlite3

# 상위 디렉토리에서 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ Google Generative AI 라이브러리가 없습니다. AI 기능은 비활성화됩니다.")

from database.database import ChurchCRMDatabase
from database.models import OrganizationType

def load_env_file(env_path: str = None) -> Dict[str, str]:
    """환경 변수 파일(.env) 로드"""
    if env_path is None:
        # 상위 디렉토리의 .env 파일 경로
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    env_vars = {}
    
    try:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")  # 따옴표 제거
                        env_vars[key] = value
            print(f"✅ .env 파일 로드 완료: {env_path}")
        else:
            print(f"⚠️ .env 파일을 찾을 수 없습니다: {env_path}")
    except Exception as e:
        print(f"⚠️ .env 파일 로드 실패: {e}")
    
    return env_vars

def _initialize_database(self):
    """데이터베이스 초기화 (강력한 오류 처리 포함)"""
    try:
        print(f"🔍 데이터베이스 파일 확인 중: {self.db_path}")
        
        # 기존 DB 파일이 있으면 완전히 검증
        if os.path.exists(self.db_path):
            is_valid_db = False
            
            try:
                # 파일 크기 확인 (0바이트면 손상)
                file_size = os.path.getsize(self.db_path)
                if file_size == 0:
                    print(f"⚠️ 빈 파일입니다: {self.db_path} (크기: 0)")
                    is_valid_db = False
                else:
                    # SQLite 파일 헤더 확인
                    with open(self.db_path, 'rb') as f:
                        header = f.read(16)
                        if not header.startswith(b'SQLite format 3'):
                            print(f"⚠️ SQLite 파일이 아닙니다: {self.db_path}")
                            is_valid_db = False
                        else:
                            # 실제 연결 테스트
                            conn = sqlite3.connect(self.db_path)
                            conn.execute("SELECT 1")
                            conn.close()
                            is_valid_db = True
                            print(f"✅ 유효한 데이터베이스 파일: {self.db_path}")
                            
            except Exception as e:
                print(f"⚠️ 데이터베이스 파일 검증 실패: {e}")
                is_valid_db = False
            
            # 손상된 파일 처리
            if not is_valid_db:
                print(f"🔧 손상된 데이터베이스 파일 처리 중...")
                
                # 백업 시도
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{self.db_path}.corrupted_{timestamp}"
                
                try:
                    # 강제로 파일 삭제 시도
                    if os.path.exists(self.db_path):
                        # 읽기 전용 속성 제거
                        os.chmod(self.db_path, 0o777)
                        
                        # 백업 시도
                        try:
                            os.rename(self.db_path, backup_path)
                            print(f"📁 손상된 파일 백업 완료: {backup_path}")
                        except:
                            # 백업 실패 시 직접 삭제
                            os.remove(self.db_path)
                            print(f"🗑️ 손상된 파일 삭제 완료")
                            
                except Exception as delete_error:
                    print(f"❌ 파일 삭제 실패: {delete_error}")
                    
                    # 최후의 수단: 다른 파일명 사용
                    original_path = self.db_path
                    self.db_path = f"{original_path}.new_{timestamp}.db"
                    print(f"🔄 새 파일명 사용: {self.db_path}")
        
        # 새 데이터베이스 생성
        print(f"🔄 새 데이터베이스 생성 중: {self.db_path}")
        
        # 디렉토리가 없으면 생성
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # 새 데이터베이스 생성
        return ChurchCRMDatabase(self.db_path)
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 최종 실패: {e}")
        
        # 마지막 시도: 임시 파일명으로 생성
        temp_db_path = f"temp_academy_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        print(f"🚨 임시 데이터베이스로 시도: {temp_db_path}")
        
        try:
            self.db_path = temp_db_path
            return ChurchCRMDatabase(self.db_path)
        except Exception as final_error:
            print(f"❌ 임시 데이터베이스 생성도 실패: {final_error}")
            raise

class ExcelAnalyzerWithAI:
    """Excel 파일 분석 + AI 정리 + DB 변환 통합 클래스"""
    
    def __init__(self, ai_api_key: str = None):
        self.excel_file_path = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\학원교습소정보_2024년10월31일기준20250617수정.xlsx"
        self.db_path = r"C:\Users\kimyh\makedb\Python\cradcrawl_adv\churches_crm_company.db"
        
        # AI 설정
        self.use_ai = AI_AVAILABLE and ai_api_key is not None
        self.ai_model = None
        
        if self.use_ai:
            try:
                genai.configure(api_key=ai_api_key)
                self.ai_model = genai.GenerativeModel('gemini-pro')
                print("🤖 AI 기능 활성화됨 (Gemini)")
            except Exception as e:
                print(f"⚠️ AI 초기화 실패: {e}")
                self.use_ai = False
        
        # 데이터베이스 연결 (오류 처리 포함)
        self.db = self._initialize_database()
        
        # 통계
        self.stats = {
            "total_processed": 0,
            "successfully_created": 0,
            "ai_enhanced": 0,
            "duplicates_skipped": 0,
            "failed": 0,
            "errors": []
        }
    
    def _initialize_database(self):
        """데이터베이스 초기화 (강력한 오류 처리 포함)"""
        try:
            print(f"🔍 데이터베이스 파일 확인 중: {self.db_path}")
            
            # 기존 DB 파일이 있으면 완전히 검증
            if os.path.exists(self.db_path):
                is_valid_db = False
                
                try:
                    # 파일 크기 확인 (0바이트면 손상)
                    file_size = os.path.getsize(self.db_path)
                    if file_size == 0:
                        print(f"⚠️ 빈 파일입니다: {self.db_path} (크기: 0)")
                        is_valid_db = False
                    else:
                        # SQLite 파일 헤더 확인
                        with open(self.db_path, 'rb') as f:
                            header = f.read(16)
                            if not header.startswith(b'SQLite format 3'):
                                print(f"⚠️ SQLite 파일이 아닙니다: {self.db_path}")
                                is_valid_db = False
                            else:
                                # 실제 연결 테스트
                                conn = sqlite3.connect(self.db_path)
                                conn.execute("SELECT 1")
                                conn.close()
                                is_valid_db = True
                                print(f"✅ 유효한 데이터베이스 파일: {self.db_path}")
                                
                except Exception as e:
                    print(f"⚠️ 데이터베이스 파일 검증 실패: {e}")
                    is_valid_db = False
                
                # 손상된 파일 처리
                if not is_valid_db:
                    print(f"🔧 손상된 데이터베이스 파일 처리 중...")
                    
                    # 백업 시도
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_path = f"{self.db_path}.corrupted_{timestamp}"
                    
                    try:
                        # 강제로 파일 삭제 시도
                        if os.path.exists(self.db_path):
                            # 읽기 전용 속성 제거
                            os.chmod(self.db_path, 0o777)
                            
                            # 백업 시도
                            try:
                                os.rename(self.db_path, backup_path)
                                print(f"📁 손상된 파일 백업 완료: {backup_path}")
                            except:
                                # 백업 실패 시 직접 삭제
                                os.remove(self.db_path)
                                print(f"🗑️ 손상된 파일 삭제 완료")
                                
                    except Exception as delete_error:
                        print(f"❌ 파일 삭제 실패: {delete_error}")
                        
                        # 최후의 수단: 다른 파일명 사용
                        original_path = self.db_path
                        self.db_path = f"{original_path}.new_{timestamp}.db"
                        print(f"🔄 새 파일명 사용: {self.db_path}")
            
            # 새 데이터베이스 생성
            print(f"🔄 새 데이터베이스 생성 중: {self.db_path}")
            
            # 디렉토리가 없으면 생성
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # 새 데이터베이스 생성
            return ChurchCRMDatabase(self.db_path)
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 최종 실패: {e}")
            
            # 마지막 시도: 임시 파일명으로 생성
            temp_db_path = f"temp_academy_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            print(f"🚨 임시 데이터베이스로 시도: {temp_db_path}")
            
            try:
                self.db_path = temp_db_path
                return ChurchCRMDatabase(self.db_path)
            except Exception as final_error:
                print(f"❌ 임시 데이터베이스 생성도 실패: {final_error}")
                raise
    
    def analyze_excel_structure(self):
        """엑셀 파일 구조 분석"""
        print("=" * 60)
        print("🔍 엑셀 파일 구조 분석 (복잡한 헤더)")
        print("=" * 60)
        
        try:
            # Excel 파일 존재 확인
            if not os.path.exists(self.excel_file_path):
                print(f"❌ Excel 파일을 찾을 수 없습니다: {self.excel_file_path}")
                return None, []
            
            # 원본 구조 확인
            print("📋 원본 파일 구조 (처음 5행):")
            df_raw = pd.read_excel(self.excel_file_path, header=None, nrows=5)
            
            for i in range(len(df_raw)):
                print(f"\n[행 {i+1}]")
                non_empty_cols = []
                for j, value in enumerate(df_raw.iloc[i]):
                    if pd.notna(value) and str(value).strip():
                        non_empty_cols.append(f"컬럼{j}: {value}")
                if non_empty_cols:
                    print("  " + " | ".join(non_empty_cols[:10]))
                else:
                    print("  (모든 컬럼이 비어있음)")
            
            # 3행을 헤더로 사용
            print("\n" + "="*60)
            print("📊 3행을 헤더로 사용하여 데이터 읽기")
            print("="*60)
            
            df = pd.read_excel(self.excel_file_path, header=2)
            print(f"📊 총 행수: {len(df)}")
            print(f"📊 총 열수: {len(df.columns)}")
            
            # 헤더 분석
            print(f"\n📋 의미있는 헤더들:")
            meaningful_headers = []
            for i, col in enumerate(df.columns):
                if pd.notna(col) and str(col).strip() and not str(col).startswith('Unnamed'):
                    meaningful_headers.append((i, col))
                    print(f"  [{i}] '{col}'")
            
            # 샘플 데이터
            self._show_sample_data(df)
            
            # 학원 특화 컬럼 분석
            self._analyze_academy_columns(df)
            
            return df, meaningful_headers
            
        except Exception as e:
            print(f"❌ 구조 분석 오류: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    def _show_sample_data(self, df):
        """샘플 데이터 표시"""
        print(f"\n🔍 데이터 샘플 (처음 3행):")
        for i in range(min(3, len(df))):
            print(f"\n[데이터 행 {i+1}]")
            data_found = False
            for col in df.columns:
                value = df.iloc[i][col]
                if pd.notna(value) and str(value).strip():
                    print(f"  {col}: {value}")
                    data_found = True
            if not data_found:
                print("  (모든 컬럼이 비어있음)")
    
    def _analyze_academy_columns(self, df):
        """학원 데이터 특화 컬럼 분석"""
        # 학원명 관련
        academy_cols = self._find_columns_by_keywords(df, ['학원', '교습소', '명칭', '기관명', '상호'])
        # 주소 관련  
        address_cols = self._find_columns_by_keywords(df, ['주소', '소재지', '위치', '도로명'])
        # 전화번호 관련
        phone_cols = self._find_columns_by_keywords(df, ['전화', '번호', 'tel', 'phone'])
        # 교습 과목
        subject_cols = self._find_columns_by_keywords(df, ['과목', '교습', '분야', '종류'])
        # 설립/등록 관련
        register_cols = self._find_columns_by_keywords(df, ['등록', '설립', '인가', '승인'])
        
        self._print_column_analysis("🏫 학원명 관련 컬럼", academy_cols, df)
        self._print_column_analysis("🏢 주소 관련 컬럼", address_cols, df)
        self._print_column_analysis("📞 전화번호 관련 컬럼", phone_cols, df)
        self._print_column_analysis("📚 교습과목 관련 컬럼", subject_cols, df)
        self._print_column_analysis("📋 등록/설립 관련 컬럼", register_cols, df)
    
    def _find_columns_by_keywords(self, df, keywords):
        """키워드로 컬럼 찾기"""
        found_cols = []
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in keywords):
                found_cols.append(col)
        return found_cols
    
    def _print_column_analysis(self, title, columns, df):
        """컬럼 분석 결과 출력"""
        if columns:
            print(f"\n{title}:")
            for col in columns:
                non_empty = df[col].notna() & (df[col] != "")
                non_empty_count = non_empty.sum()
                print(f"  {col}: {non_empty_count}개 데이터 존재")
                if non_empty_count > 0:
                    samples = df[df[col].notna() & (df[col] != "")][col].head(3)
                    print(f"    샘플: {list(samples)}")
    
    def convert_to_database_with_ai(self, batch_size: int = 20):
        """AI로 정리하여 데이터베이스로 변환"""
        print("\n" + "="*60)
        print("🤖 AI 정리 + 데이터베이스 변환 시작")
        print("="*60)
        
        try:
            # Excel 데이터 로드
            df = pd.read_excel(self.excel_file_path, header=2)
            print(f"📊 처리할 데이터: {len(df)}행")
            
            # 배치 처리
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(df) + batch_size - 1) // batch_size
                
                print(f"\n📦 배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개)...")
                
                for _, row in batch.iterrows():
                    try:
                        self.stats["total_processed"] += 1
                        
                        # 기본 데이터 변환
                        org_data = self._transform_academy_row_to_org(row)
                        
                        # 필수 데이터 검증
                        if not org_data.get('name', '').strip():
                            self.stats["failed"] += 1
                            self.stats["errors"].append("학원명이 없는 데이터")
                            continue
                        
                        # AI로 데이터 정리 및 보완
                        if self.use_ai:
                            enhanced_data = self._enhance_academy_data_with_ai(org_data, row)
                            if enhanced_data:
                                org_data.update(enhanced_data)
                                self.stats["ai_enhanced"] += 1
                                print(f"🤖 AI 정리 완료: {org_data.get('name', 'Unknown')}")
                        
                        # 중복 체크
                        if self._check_duplicate_in_db(org_data):
                            self.stats["duplicates_skipped"] += 1
                            continue
                        
                        # 데이터베이스에 저장
                        org_id = self.db.create_organization(org_data)
                        if org_id:
                            self.stats["successfully_created"] += 1
                            if self.stats["successfully_created"] % 10 == 0:
                                print(f"✅ {self.stats['successfully_created']}개 저장 완료...")
                        else:
                            self.stats["failed"] += 1
                            self.stats["errors"].append(f"저장 실패: {org_data.get('name', 'Unknown')}")
                            
                    except Exception as e:
                        self.stats["failed"] += 1
                        error_msg = f"행 처리 실패: {str(e)}"
                        self.stats["errors"].append(error_msg)
                        print(f"⚠️ {error_msg}")
                
                # 진행률 표시
                progress = (self.stats["total_processed"] / len(df)) * 100
                print(f"📈 진행률: {progress:.1f}% ({self.stats['total_processed']}/{len(df)})")
            
            # 결과 출력
            self._print_conversion_summary()
            
        except Exception as e:
            print(f"❌ 변환 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def _transform_academy_row_to_org(self, row: pd.Series) -> Dict[str, Any]:
        """학원 Excel 행을 organization 데이터로 변환"""
        
        # 학원 특화 매핑
        org_data = {
            'name': self._get_value_from_row(row, [
                '학원명', '교습소명', '기관명', '상호', '명칭', '업체명', 
                '학교명', 'name', '시설명'
            ]),
            'type': OrganizationType.ACADEMY.value,
            'category': self._get_value_from_row(row, [
                '교습과목', '분야', '과목', '종류', '업종', '교습계열', 
                '교습형태', 'category', '전공분야'
            ]),
            'address': self._get_value_from_row(row, [
                '소재지', '주소', '도로명주소', '지번주소', '위치', 
                '본점소재지', 'address', '전체주소'
            ]),
            'phone': self._get_value_from_row(row, [
                '전화번호', '연락처', '대표전화', 'tel', 'phone', '번호'
            ]),
            'email': self._get_value_from_row(row, [
                '이메일', 'email', 'e-mail', '전자우편'
            ]),
            'homepage': self._get_value_from_row(row, [
                '홈페이지', '웹사이트', 'website', 'url', 'homepage'
            ]),
            
            # 학원 특화 정보
            'organization_size': self._get_value_from_row(row, [
                '규모', '정원', '학생수', '수용인원', '시설규모'
            ]),
            'founding_year': self._get_numeric_value_from_row(row, [
                '등록년도', '설립년도', '인가년도', '개원년도', '승인년도'
            ]),
            'denomination': self._get_value_from_row(row, [
                '교습계열', '교육과정', '전공분야', '특성화분야'
            ]),
            
            # CRM 기본값
            'contact_status': 'NEW',
            'priority': 'MEDIUM',
            'lead_source': 'ACADEMY_EXCEL',
            'estimated_value': 0,
            'sales_notes': f"학원교습소 정보에서 가져온 데이터",
            'internal_notes': f"가져온 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'created_by': 'ACADEMY_IMPORT'
        }
        
        return org_data
    
    def _get_value_from_row(self, row: pd.Series, column_names: List[str]) -> str:
        """행에서 값 추출 (여러 가능한 컬럼명 시도)"""
        for col_name in column_names:
            if col_name in row.index and pd.notna(row[col_name]):
                value = str(row[col_name]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    return value
        return ""
    
    def _get_numeric_value_from_row(self, row: pd.Series, column_names: List[str]) -> Optional[int]:
        """행에서 숫자 값 추출"""
        value_str = self._get_value_from_row(row, column_names)
        if value_str:
            try:
                numbers = re.findall(r'\d+', value_str)
                if numbers:
                    return int(numbers[0])
            except:
                pass
        return None
    
    def _enhance_academy_data_with_ai(self, org_data: Dict[str, Any], 
                                     original_row: pd.Series) -> Optional[Dict[str, Any]]:
        """AI로 학원 데이터 정리 및 보완"""
        if not self.use_ai or not self.ai_model:
            return None
        
        try:
            academy_name = org_data.get('name', '알 수 없음')
            
            # 원본 데이터 정보 수집
            raw_data_info = []
            for col, value in original_row.items():
                if pd.notna(value) and str(value).strip():
                    raw_data_info.append(f"- {col}: {str(value).strip()}")
            
            raw_data_text = "\n".join(raw_data_info) if raw_data_info else "정보 없음"
            
            # AI 프롬프트 구성 (학원 특화)
            prompt = f"""
'{academy_name}' 학원/교습소의 Excel 데이터를 분석하고 정리해주세요.

**원본 Excel 데이터:**
{raw_data_text}

**현재 매핑된 정보:**
- 학원명: {org_data.get('name', '')}
- 교습과목/분야: {org_data.get('category', '')}
- 주소: {org_data.get('address', '')}
- 전화번호: {org_data.get('phone', '')}

**분석 요청 (학원/교습소 특화):**
1. 학원 유형 분류 (학원/교습소/과외/온라인교육/기타)
2. 주요 교습분야 정리 (수학/영어/국어/과학/예체능/입시/자격증 등)
3. 대상 학년/연령층 (초등/중등/고등/성인/전연령)
4. 학원 규모 추정 (대형/중형/소형)
5. 지역 특성 파악 (강남/서초/목동 등 교육특구 여부)
6. 영업 우선순위 제안 (HIGH/MEDIUM/LOW)
7. 학원 특징 및 장점 (2-3문장)
8. 영업 접근 방법 제안

**응답 형식:**
TYPE: [학원유형]
SUBJECT: [주요교습분야]
TARGET: [대상학년/연령]
SIZE: [학원규모]
LOCATION_TYPE: [지역특성]
PRIORITY: [영업우선순위]
DESCRIPTION: [학원특징및장점]
SALES_APPROACH: [영업접근방법]
NOTES: [기타특이사항]
"""
            
            # AI 호출
            response = self.ai_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # 응답 파싱
            enhanced_data = self._parse_ai_academy_response(response_text, academy_name)
            
            return enhanced_data
            
        except Exception as e:
            print(f"⚠️ AI 정리 실패: {academy_name} - {e}")
            return None
    
    def _parse_ai_academy_response(self, response_text: str, academy_name: str) -> Dict[str, Any]:
        """AI 응답을 파싱하여 학원 데이터로 변환"""
        enhanced_data = {}
        
        try:
            # 패턴 매칭으로 정보 추출
            patterns = {
                'type': r'TYPE:\s*(.+)',
                'subject': r'SUBJECT:\s*(.+)',
                'target': r'TARGET:\s*(.+)',
                'size': r'SIZE:\s*(.+)',
                'location_type': r'LOCATION_TYPE:\s*(.+)',
                'priority': r'PRIORITY:\s*(.+)',
                'description': r'DESCRIPTION:\s*(.+)',
                'sales_approach': r'SALES_APPROACH:\s*(.+)',
                'notes': r'NOTES:\s*(.+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, response_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    
                    if key == 'subject':
                        enhanced_data['category'] = value
                    elif key == 'size':
                        enhanced_data['organization_size'] = value
                    elif key == 'priority':
                        enhanced_data['priority'] = value.upper() if value.upper() in ['HIGH', 'MEDIUM', 'LOW'] else 'MEDIUM'
                    elif key == 'description':
                        enhanced_data['sales_notes'] = value
                    elif key == 'sales_approach':
                        enhanced_data['internal_notes'] = f"영업접근: {value}"
                    elif key == 'notes':
                        existing_notes = enhanced_data.get('internal_notes', '')
                        enhanced_data['internal_notes'] = f"{existing_notes}\n기타: {value}"
            
            # AI 정리 메타데이터 추가
            enhanced_data['crawling_data'] = {
                'ai_processed': True,
                'ai_response': response_text,
                'ai_processed_at': datetime.now().isoformat(),
                'data_source': 'academy_excel'
            }
            
        except Exception as e:
            print(f"⚠️ AI 응답 파싱 실패: {academy_name} - {e}")
            enhanced_data = {
                'crawling_data': {
                    'ai_processed': True,
                    'ai_response': response_text,
                    'ai_processed_at': datetime.now().isoformat(),
                    'parsing_error': str(e)
                }
            }
        
        return enhanced_data
    
    def _check_duplicate_in_db(self, org_data: Dict[str, Any]) -> bool:
        """데이터베이스에서 중복 체크"""
        try:
            with self.db.get_connection() as conn:
                existing = conn.execute('''
                SELECT COUNT(*) FROM organizations 
                WHERE name = ? AND is_active = 1
                ''', (org_data['name'],)).fetchone()[0]
                
                return existing > 0
                
        except Exception as e:
            print(f"⚠️ 중복 체크 실패: {e}")
            return False
    
    def _print_conversion_summary(self):
        """변환 결과 요약 출력"""
        print("\n" + "="*60)
        print("🎉 학원 데이터 AI 정리 + DB 변환 완료")
        print("="*60)
        print(f"총 처리된 행: {self.stats['total_processed']:,}개")
        print(f"성공적으로 생성: {self.stats['successfully_created']:,}개")
        print(f"🤖 AI로 정리됨: {self.stats['ai_enhanced']:,}개")
        print(f"중복으로 건너뜀: {self.stats['duplicates_skipped']:,}개")
        print(f"실패: {self.stats['failed']:,}개")
        
        if self.stats['errors']:
            print(f"\n❌ 오류 목록 (최근 10개):")
            for error in self.stats['errors'][-10:]:
                print(f"  - {error}")
        
        success_rate = (self.stats['successfully_created'] / max(1, self.stats['total_processed'])) * 100
        ai_rate = (self.stats['ai_enhanced'] / max(1, self.stats['successfully_created'])) * 100
        
        print(f"\n✅ 성공률: {success_rate:.1f}%")
        print(f"🤖 AI 정리율: {ai_rate:.1f}%")
        print("="*60)

def main():
    """메인 실행 함수"""
    print("🏫 학원 데이터 분석 + AI 정리 + DB 변환 도구")
    print("="*60)
    
    # .env 파일에서 API 키 로드
    env_vars = load_env_file()
    api_key = env_vars.get('GEMINI_API_KEY')
    
    if api_key:
        print(f"🔑 .env 파일에서 API 키 발견: {api_key[:10]}...{api_key[-5:]}")
        use_env_key = input("🤖 .env 파일의 API 키를 사용하시겠습니까? (Y/n): ").strip().lower()
        
        if use_env_key in ['', 'y', 'yes']:
            print("✅ .env 파일의 API 키를 사용합니다.")
        else:
            api_key = input("🔑 새로운 Gemini API 키를 입력하세요: ").strip()
    else:
        print("⚠️ .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
        api_key = input("🔑 Gemini API 키를 입력하세요 (없으면 엔터): ").strip()
    
    if not api_key:
        print("⚠️ API 키가 없어도 기본 분석은 가능합니다.")
    
    try:
        print("\n🔧 시스템 초기화 중...")
        
        # 분석기 생성 (데이터베이스 문제 해결)
        analyzer = ExcelAnalyzerWithAI(ai_api_key=api_key)
        print(f"✅ 데이터베이스 준비 완료: {analyzer.db_path}")
        
        # 1. Excel 구조 분석
        print("\n📊 Excel 파일 분석 시작...")
        df, headers = analyzer.analyze_excel_structure()
        
        if df is None:
            print("❌ Excel 파일 분석 실패")
            return
        
        # 2. 변환 여부 확인
        print(f"\n📊 총 {len(df)}개의 학원 데이터를 발견했습니다.")
        
        if api_key:
            convert_choice = input("🤖 AI로 정리하여 데이터베이스에 저장하시겠습니까? (y/N): ").strip().lower()
        else:
            convert_choice = input("🗄️ 기본 매핑으로 데이터베이스에 저장하시겠습니까? (y/N): ").strip().lower()
        
        if convert_choice in ['y', 'yes']:
            # 3. 데이터베이스 변환
            print(f"\n🚀 변환 시작 - 저장 위치: {analyzer.db_path}")
            analyzer.convert_to_database_with_ai(batch_size=20)
        else:
            print("✅ 분석만 완료했습니다.")
            
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        
        # 수동으로 파일 삭제 안내
        print("\n" + "="*60)
        print("🔧 수동 해결 방법:")
        print("="*60)
        print("1. 다음 파일을 수동으로 삭제해보세요:")
        print(f"   {os.path.abspath('churches_crm_company.db')}")
        print("2. 또는 Windows 탐색기에서 해당 파일을 휴지통으로 이동")
        print("3. 그 다음 다시 실행해보세요")
        print("="*60)
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
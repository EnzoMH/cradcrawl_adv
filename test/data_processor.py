#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 데이터 처리 모듈
기존 jsontoexcel.py + exceltojson.py + combined.py 통합
config.py 설정 활용
"""

import json
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# 프로젝트 설정 import
from utils.settings import *
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils

class DataProcessor:
    """통합 데이터 처리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.logger = LoggerUtils.setup_logger("data_processor")
        self.conversion_config = CONVERSION_CONFIG
        self.logger.info("📊 데이터 처리기 초기화 완료")
    
    # ===== JSON ↔ Excel 변환 =====
    
    def json_to_excel(self, json_file: Union[str, Path], excel_file: Optional[str] = None, 
                     exclude_fields: Optional[List[str]] = None) -> str:
        """JSON 파일을 Excel로 변환"""
        try:
            self.logger.info(f"📄 JSON → Excel 변환 시작: {json_file}")
            
            # 파일 로드
            data = FileUtils.load_json(json_file)
            if not data:
                raise ValueError(f"JSON 파일을 로드할 수 없습니다: {json_file}")
            
            # 출력 파일명 생성
            if not excel_file:
                excel_file = generate_output_filename("excel_filtered", EXCEL_DIR)
            
            # 제외 필드 설정
            exclude_fields = exclude_fields or self.conversion_config["exclude_fields"]
            
            # 데이터 필터링
            filtered_data = self._filter_excluded_fields(data, exclude_fields)
            
            # DataFrame 생성
            df = pd.DataFrame(filtered_data)
            
            # 컬럼 순서 조정
            df = self._reorder_columns(df)
            
            # Excel 파일로 저장
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 메인 데이터 시트
                df.to_excel(writer, sheet_name='데이터', index=False)
                
                # 통계 시트 생성
                stats_df = self._create_statistics_sheet(df)
                stats_df.to_excel(writer, sheet_name='통계', index=False)
            
            self.logger.info(f"✅ Excel 변환 완료: {excel_file}")
            self.logger.info(f"📊 데이터: {len(df)}행, {len(df.columns)}열")
            
            return str(excel_file)
            
        except Exception as e:
            self.logger.error(f"❌ JSON → Excel 변환 실패: {e}")
            raise
    
    def excel_to_json(self, excel_file: Union[str, Path], json_file: Optional[str] = None,
                     sheet_name: str = None) -> str:
        """Excel 파일을 JSON으로 변환"""
        try:
            self.logger.info(f"📊 Excel → JSON 변환 시작: {excel_file}")
            
            # Excel 파일 읽기
            if sheet_name:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_file)
            
            # 출력 파일명 생성
            if not json_file:
                json_file = generate_output_filename("converted_json", JSON_DIR)
            
            # 데이터 변환
            json_data = []
            for _, row in df.iterrows():
                item = {
                    "name": self._get_value_from_row(row, ['name', '이름', '업체명', '회사명', '기관명']),
                    "category": self._get_value_from_row(row, ['category', '카테고리', '업종', '분류']),
                    "homepage": self._get_value_from_row(row, ['homepage', '홈페이지', '웹사이트', 'website']),
                    "phone": self._get_value_from_row(row, ['phone', '전화번호', '전화', 'tel']),
                    "fax": self._get_value_from_row(row, ['fax', '팩스', 'facsimile']),
                    "email": self._get_value_from_row(row, ['email', '이메일', 'mail']),
                    "mobile": self._get_value_from_row(row, ['mobile', '휴대폰', '핸드폰', '모바일']),
                    "postal_code": self._get_value_from_row(row, ['postal_code', '우편번호', 'zipcode']),
                    "address": self._get_value_from_row(row, ['address', '주소', 'addr', '소재지'])
                }
                json_data.append(item)
            
            # JSON 파일로 저장
            FileUtils.save_json(json_data, json_file)
            
            self.logger.info(f"✅ JSON 변환 완료: {json_file}")
            self.logger.info(f"📊 데이터: {len(json_data)}개 항목")
            
            return str(json_file)
            
        except Exception as e:
            self.logger.error(f"❌ Excel → JSON 변환 실패: {e}")
            raise
    
    # ===== 데이터 결합 및 병합 =====
    
    def combine_datasets(self, file_paths: List[Union[str, Path]], 
                        output_file: Optional[str] = None) -> str:
        """여러 데이터셋을 결합"""
        try:
            self.logger.info(f"🔗 데이터셋 결합 시작: {len(file_paths)}개 파일")
            
            combined_data = []
            
            for file_path in file_paths:
                self.logger.info(f"  📂 로딩: {file_path}")
                
                if str(file_path).endswith('.json'):
                    data = FileUtils.load_json(file_path)
                elif str(file_path).endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                    data = df.to_dict('records')
                else:
                    self.logger.warning(f"  ⚠️ 지원하지 않는 파일 형식: {file_path}")
                    continue
                
                if isinstance(data, list):
                    combined_data.extend(data)
                elif isinstance(data, dict):
                    # 딕셔너리 구조인 경우 값들을 추출
                    for key, value in data.items():
                        if isinstance(value, list):
                            combined_data.extend(value)
                
                self.logger.info(f"  ✅ 로딩 완료: {len(data) if isinstance(data, list) else '?'}개 항목")
            
            # 중복 제거
            unique_data = self._remove_duplicates(combined_data)
            
            # 출력 파일명 생성
            if not output_file:
                output_file = generate_output_filename("combined", JSON_DIR)
            
            # 결합된 데이터 저장
            FileUtils.save_json(unique_data, output_file)
            
            self.logger.info(f"✅ 데이터셋 결합 완료: {output_file}")
            self.logger.info(f"📊 총 {len(unique_data)}개 항목 (중복 제거 후)")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"❌ 데이터셋 결합 실패: {e}")
            raise
    
    def merge_with_validation(self, primary_file: Union[str, Path], 
                            secondary_file: Union[str, Path],
                            output_file: Optional[str] = None) -> str:
        """검증을 통한 데이터 병합"""
        try:
            self.logger.info(f"🔍 검증 병합 시작")
            self.logger.info(f"  📂 주 파일: {primary_file}")
            self.logger.info(f"  📂 보조 파일: {secondary_file}")
            
            # 데이터 로드
            primary_data = FileUtils.load_json(primary_file)
            secondary_data = FileUtils.load_json(secondary_file)
            
            if not primary_data or not secondary_data:
                raise ValueError("파일을 로드할 수 없습니다.")
            
            # 병합 로직
            merged_data = []
            
            for primary_item in primary_data:
                # 이름으로 매칭
                primary_name = primary_item.get('name', '').strip().lower()
                
                # 보조 데이터에서 매칭되는 항목 찾기
                matched_item = None
                for secondary_item in secondary_data:
                    secondary_name = secondary_item.get('name', '').strip().lower()
                    if primary_name == secondary_name:
                        matched_item = secondary_item
                        break
                
                # 병합
                if matched_item:
                    merged_item = self._merge_items(primary_item, matched_item)
                    merged_item['merge_status'] = 'matched'
                else:
                    merged_item = primary_item.copy()
                    merged_item['merge_status'] = 'primary_only'
                
                merged_data.append(merged_item)
            
            # 출력 파일명 생성
            if not output_file:
                output_file = generate_output_filename("merged", JSON_DIR)
            
            # 병합된 데이터 저장
            FileUtils.save_json(merged_data, output_file)
            
            # 통계 출력
            matched_count = len([item for item in merged_data if item.get('merge_status') == 'matched'])
            self.logger.info(f"✅ 검증 병합 완료: {output_file}")
            self.logger.info(f"📊 총 {len(merged_data)}개 항목, {matched_count}개 매칭")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"❌ 검증 병합 실패: {e}")
            raise
    
    # ===== 데이터 분석 및 통계 =====
    
    def analyze_data(self, data_file: Union[str, Path]) -> Dict[str, Any]:
        """데이터 분석"""
        try:
            self.logger.info(f"📈 데이터 분석 시작: {data_file}")
            
            # 데이터 로드
            data = FileUtils.load_json(data_file)
            if not data:
                raise ValueError(f"데이터를 로드할 수 없습니다: {data_file}")
            
            analysis = {
                "basic_stats": self._get_basic_stats(data),
                "field_analysis": self._analyze_fields(data),
                "quality_metrics": self._calculate_quality_metrics(data),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ 데이터 분석 완료")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 분석 실패: {e}")
            raise
    
    def generate_report(self, data_file: Union[str, Path], 
                       output_file: Optional[str] = None) -> str:
        """데이터 리포트 생성"""
        try:
            # 분석 실행
            analysis = self.analyze_data(data_file)
            
            # 출력 파일명 생성
            if not output_file:
                output_file = generate_output_filename("report", OUTPUT_DIR)
                output_file = str(output_file).replace('.json', '_report.json')
            
            # 리포트 저장
            FileUtils.save_json(analysis, output_file)
            
            self.logger.info(f"📋 리포트 생성 완료: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"❌ 리포트 생성 실패: {e}")
            raise
    
    # ===== 내부 헬퍼 메서드들 =====
    
    def _filter_excluded_fields(self, data: List[Dict], exclude_fields: List[str]) -> List[Dict]:
        """제외 필드 필터링"""
        if not exclude_fields:
            return data
        
        filtered_data = []
        for item in data:
            filtered_item = {k: v for k, v in item.items() if k not in exclude_fields}
            filtered_data.append(filtered_item)
        
        return filtered_data
    
    def _reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼 순서 재정렬"""
        priority_columns = self.conversion_config["priority_columns"]
        
        # 존재하는 우선순위 컬럼들만 필터링
        existing_priority = [col for col in priority_columns if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in existing_priority]
        
        # 컬럼 순서 재정렬
        new_column_order = existing_priority + remaining_columns
        return df[new_column_order]
    
    def _create_statistics_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """통계 시트 생성"""
        stats_data = []
        
        for column in df.columns:
            non_null_count = df[column].notna().sum()
            non_empty_count = df[column].astype(str).str.strip().ne('').sum()
            
            stats_data.append({
                '필드명': column,
                '전체_레코드수': len(df),
                '비어있지않은_레코드수': non_empty_count,
                '채움률_퍼센트': round((non_empty_count / len(df)) * 100, 1),
                '샘플_데이터': str(df[column].dropna().iloc[0] if not df[column].dropna().empty else '')[:50]
            })
        
        return pd.DataFrame(stats_data)
    
    def _get_value_from_row(self, row, column_names: List[str]) -> str:
        """행에서 값 추출"""
        for col_name in column_names:
            if col_name in row.index and pd.notna(row[col_name]):
                value = str(row[col_name]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    return value
        return ""
    
    def _remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """중복 제거"""
        seen_names = set()
        unique_data = []
        
        for item in data:
            name = item.get('name', '').strip().lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_data.append(item)
        
        return unique_data
    
    def _merge_items(self, primary: Dict, secondary: Dict) -> Dict:
        """두 항목 병합"""
        merged = primary.copy()
        
        # 빈 필드를 보조 데이터로 채우기
        for key, value in secondary.items():
            if key not in merged or not str(merged.get(key, '')).strip():
                merged[key] = value
        
        return merged
    
    def _get_basic_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """기본 통계"""
        return {
            "total_records": len(data),
            "unique_names": len(set(item.get('name', '') for item in data if item.get('name'))),
            "categories": list(set(item.get('category', '') for item in data if item.get('category'))),
            "has_homepage": len([item for item in data if item.get('homepage')]),
            "has_phone": len([item for item in data if item.get('phone')]),
            "has_email": len([item for item in data if item.get('email')])
        }
    
    def _analyze_fields(self, data: List[Dict]) -> Dict[str, Any]:
        """필드 분석"""
        if not data:
            return {}
        
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        
        field_analysis = {}
        for field in all_fields:
            non_empty_count = len([item for item in data if item.get(field) and str(item.get(field)).strip()])
            field_analysis[field] = {
                "fill_rate": (non_empty_count / len(data)) * 100,
                "non_empty_count": non_empty_count,
                "total_count": len(data)
            }
        
        return field_analysis
    
    def _calculate_quality_metrics(self, data: List[Dict]) -> Dict[str, Any]:
        """품질 지표 계산"""
        if not data:
            return {}
        
        # 필수 필드 채움률
        required_fields = ["name", "category"]
        optional_fields = ["phone", "fax", "email", "address"]
        
        required_score = 0
        for field in required_fields:
            filled = len([item for item in data if item.get(field) and str(item.get(field)).strip()])
            required_score += (filled / len(data)) * 100
        
        optional_score = 0
        for field in optional_fields:
            filled = len([item for item in data if item.get(field) and str(item.get(field)).strip()])
            optional_score += (filled / len(data)) * 100
        
        return {
            "required_fields_score": required_score / len(required_fields),
            "optional_fields_score": optional_score / len(optional_fields),
            "overall_score": (required_score / len(required_fields) * 0.7 + 
                            optional_score / len(optional_fields) * 0.3)
        }

# 편의 함수들
def quick_json_to_excel(json_file: str, excel_file: str = None) -> str:
    """빠른 JSON → Excel 변환"""
    processor = DataProcessor()
    return processor.json_to_excel(json_file, excel_file)

def quick_excel_to_json(excel_file: str, json_file: str = None) -> str:
    """빠른 Excel → JSON 변환"""
    processor = DataProcessor()
    return processor.excel_to_json(excel_file, json_file)

def quick_combine(file_paths: List[str], output_file: str = None) -> str:
    """빠른 데이터 결합"""
    processor = DataProcessor()
    return processor.combine_datasets(file_paths, output_file)

# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("📊 통합 데이터 처리 시스템")
    print("="*60)
    
    try:
        # 프로젝트 초기화
        initialize_project()
        
        # 데이터 처리기 생성
        processor = DataProcessor()
        
        # 최신 JSON 파일 찾기
        latest_json = get_latest_input_file()
        if latest_json:
            print(f"📂 최신 JSON 파일: {latest_json}")
            
            # Excel로 변환
            excel_file = processor.json_to_excel(latest_json)
            print(f"✅ Excel 변환 완료: {excel_file}")
            
            # 데이터 분석
            analysis = processor.analyze_data(latest_json)
            print(f"📈 데이터 분석 완료")
            print(f"  - 총 레코드: {analysis['basic_stats']['total_records']}개")
            print(f"  - 품질 점수: {analysis['quality_metrics']['overall_score']:.1f}점")
        else:
            print("❌ 처리할 JSON 파일을 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main() 
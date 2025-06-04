#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV to JSON 변환기 (9개 필드 버전)
"""

import pandas as pd
import json
import os
import sys
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class SimplePhoneValidator:
    """간단한 전화번호 검증 클래스"""
    
    @staticmethod
    def is_valid_korean_phone(phone: str) -> bool:
        """한국 전화번호 유효성 검증"""
        if not phone:
            return False
        
        # 숫자만 추출
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # 길이 체크 (10자리 또는 11자리)
        if len(clean_phone) not in [10, 11]:
            return False
        
        # 지역번호 체크
        valid_codes = ["02", "031", "032", "033", "041", "042", "043", "044", 
                      "051", "052", "053", "054", "055", "061", "062", "063", "064"]
        
        for code in valid_codes:
            if clean_phone.startswith(code):
                return True
        
        return False
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """전화번호 표준 형식으로 포맷팅"""
        if not phone:
            return ""
        
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        if len(clean_phone) == 10:
            if clean_phone.startswith('02'):
                return f"{clean_phone[:2]}-{clean_phone[2:6]}-{clean_phone[6:]}"
            else:
                return f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
        elif len(clean_phone) == 11:
            return f"{clean_phone[:3]}-{clean_phone[3:7]}-{clean_phone[7:]}"
        
        return phone

class SimpleLogger:
    """간단한 로거 클래스"""
    
    def __init__(self, name):
        self.name = name
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")

class CSVtoJSONConverter:
    """CSV to JSON 변환기 클래스 (9개 필드)"""
    
    def __init__(self):
        self.logger = SimpleLogger("csvtojson")
        self.phone_utils = SimplePhoneValidator
        
        # 실제 CSV 컬럼명에 맞춘 매핑
        self.column_mapping = {
            # 기본 정보
            'Name': 'name',
            '기관명': 'name',
            'name': 'name',
            
            # 카테고리
            'Category': 'category', 
            '분류': 'category',
            'category': 'category',
            
            # 홈페이지
            'homepage': 'homepage',
            '홈페이지': 'homepage',
            'url': 'homepage',
            
            # 연락처
            '전화번호': 'phone',
            'phone': 'phone',
            '전화': 'phone',
            
            '팩스1': 'fax',
            '팩스번호': 'fax',
            'fax': 'fax',
            '팩스': 'fax',
            
            '이메일': 'email',
            'email': 'email',
            
            '핸드폰1': 'mobile',
            '핸드폰': 'mobile',
            'mobile': 'mobile',
            
            # 주소 정보
            '우편번호': 'postal_code',
            'postal_code': 'postal_code',
            
            '주소2': 'address',
            '주소': 'address',
            'address': 'address'
        }

    def clean_data(self, value: Any) -> str:
        """데이터 정제"""
        if pd.isna(value) or value is None:
            return ""
        
        # 문자열 변환 및 정제
        cleaned = str(value).strip()
        
        # 빈 문자열 또는 의미없는 값 제거
        if cleaned in ['nan', 'NaN', 'null', 'NULL', '-', 'N/A', '없음', 'X']:
            return ""
        
        return cleaned
    
    def validate_and_format_phone(self, phone: str) -> str:
        """전화번호 검증 및 포맷팅"""
        if not phone or phone == "":
            return ""
        
        if self.phone_utils.is_valid_korean_phone(phone):
            return self.phone_utils.format_phone_number(phone)
        else:
            # 검증 실패해도 원본 반환 (로그만 남김)
            self.logger.warning(f"검증 실패한 전화번호: {phone}")
            return phone
    
    def validate_email(self, email: str) -> str:
        """이메일 간단 검증"""
        if not email or email == "":
            return ""
        
        if '@' in email and '.' in email:
            return email
        else:
            self.logger.warning(f"검증 실패한 이메일: {email}")
            return ""
    
    def format_url(self, url: str) -> str:
        """URL 포맷팅"""
        if not url or url == "":
            return ""
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'http://' + url
            elif '.' in url:
                url = 'http://' + url
        
        return url

    def convert_csv_to_json(self, csv_file_path: str, output_file_path: str = None) -> str:
        """CSV 파일을 JSON으로 변환 (9개 필드)"""
        try:
            self.logger.info(f"CSV 파일 변환 시작: {csv_file_path}")
            
            # CSV 파일 로드
            if not os.path.exists(csv_file_path):
                raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
            
            # 다양한 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file_path, encoding=encoding)
                    self.logger.info(f"CSV 로드 성공 (인코딩: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("CSV 파일을 읽을 수 없습니다. 인코딩을 확인해주세요.")
            
            self.logger.info(f"로드된 데이터: {len(df)}행, {len(df.columns)}열")
            self.logger.info(f"컬럼명: {list(df.columns)}")
            
            # 데이터 변환
            organizations = []
            processed_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 9개 필드 기본 구조
                    org_data = {
                        "name": "",
                        "category": "",
                        "homepage": "",
                        "phone": "",
                        "fax": "",
                        "email": "",
                        "mobile": "",
                        "postal_code": "",
                        "address": ""
                    }
                    
                    # CSV 컬럼을 JSON 필드로 매핑
                    for csv_col in df.columns:
                        csv_col_clean = csv_col.strip()
                        
                        if csv_col_clean in self.column_mapping:
                            json_field = self.column_mapping[csv_col_clean]
                            cleaned_value = self.clean_data(row[csv_col])
                            
                            # 각 필드별 특별 처리
                            if json_field == 'phone':
                                org_data[json_field] = self.validate_and_format_phone(cleaned_value)
                            elif json_field == 'fax':
                                org_data[json_field] = self.validate_and_format_phone(cleaned_value)
                            elif json_field == 'mobile':
                                org_data[json_field] = self.validate_and_format_phone(cleaned_value)
                            elif json_field == 'email':
                                org_data[json_field] = self.validate_email(cleaned_value)
                            elif json_field == 'homepage':
                                org_data[json_field] = self.format_url(cleaned_value)
                            else:
                                org_data[json_field] = cleaned_value
                    
                    # 기관명이 없으면 스킵
                    if not org_data['name']:
                        self.logger.warning(f"행 {index+1}: 기관명이 없어서 스킵")
                        error_count += 1
                        continue
                    
                    organizations.append(org_data)
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        self.logger.info(f"진행 상황: {processed_count}개 처리 완료")
                
                except Exception as e:
                    self.logger.error(f"행 {index+1} 처리 중 오류: {e}")
                    error_count += 1
                    continue
            
            # 결과 통계
            self.logger.info(f"변환 완료:")
            self.logger.info(f"  📊 총 처리: {processed_count}개")
            self.logger.info(f"  ❌ 오류: {error_count}개")
            
            # 출력 파일명 생성
            if not output_file_path:
                base_name = os.path.basename(csv_file_path)
                if 'rawdata_' in base_name:
                    date_part = base_name.split('rawdata_')[1].split('.')[0]
                    output_file_path = f"raw_data_{date_part}.json"
                else:
                    date_str = datetime.now().strftime("%m%d")
                    output_file_path = f"raw_data_{date_str}.json"
            
            # 절대 경로로 저장
            if not os.path.isabs(output_file_path):
                output_file_path = os.path.join(r"C:\Users\kimyh\makedb\Python\advanced_crawling", output_file_path)
            
            # JSON 파일 저장 (단순한 리스트 형태)
            success = self.save_json(organizations, output_file_path)
            
            if success:
                self.logger.info(f"✅ JSON 변환 완료: {output_file_path}")
                return output_file_path
            else:
                raise Exception("JSON 파일 저장 실패")
                
        except Exception as e:
            self.logger.error(f"❌ CSV 변환 실패: {e}")
            raise
    
    def save_json(self, data: List, output_path: str) -> bool:
        """JSON 파일 저장"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"JSON 저장 실패: {e}")
            return False

def get_file_info(file_path: str) -> dict:
    """파일 정보 조회"""
    try:
        stat = os.stat(file_path)
        size_mb = stat.st_size / (1024 * 1024)
        created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        return {
            'size_mb': round(size_mb, 2),
            'created_time': created_time
        }
    except Exception:
        return {'size_mb': 0, 'created_time': 'Unknown'}

def count_data_in_json(file_path: str) -> int:
    """JSON 파일의 데이터 수 조회"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return len(data)
        else:
            return 0
    except Exception:
        return 0

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📄 CSV to JSON 변환기 (9개 필드)")
    print("=" * 60)
    
    converter = CSVtoJSONConverter()
    
    # 기본 파일 경로
    default_csv_path = r"C:\Users\kimyh\makedb\Python\advanced_crawling\rawdata_0530.csv"
    
    # 사용자 입력 또는 기본값 사용
    csv_path = input(f"CSV 파일 경로 (엔터 시 기본값 사용):\n기본값: {default_csv_path}\n입력: ").strip()
    
    if not csv_path:
        csv_path = default_csv_path
    
    try:
        # 변환 실행
        output_file = converter.convert_csv_to_json(csv_path)
        
        print("\n🎉 변환 완료!")
        print(f"📁 출력 파일: {output_file}")
        
        # 파일 정보 출력
        if os.path.exists(output_file):
            file_info = get_file_info(output_file)
            print(f"📊 파일 크기: {file_info['size_mb']} MB")
            print(f"🕐 생성 시간: {file_info['created_time']}")
        
        # 데이터 수 출력
        data_count = count_data_in_json(output_file)
        print(f"📈 총 데이터 수: {data_count}개")
        
        # 샘플 데이터 출력 (처음 2개만)
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            if sample_data and len(sample_data) > 0:
                print(f"\n📋 샘플 데이터 (처음 2개):")
                for i, item in enumerate(sample_data[:2]):
                    print(f"  {i+1}. name: {item['name']}")
                    print(f"     category: {item['category']}")
                    print(f"     homepage: {item['homepage']}")
                    print(f"     phone: {item['phone']}")
                    print(f"     fax: {item['fax']}")
                    print(f"     email: {item['email']}")
                    print(f"     mobile: {item['mobile']}")
                    print(f"     postal_code: {item['postal_code']}")
                    print(f"     address: {item['address']}")
                    print()
        except:
            pass
        
    except Exception as e:
        print(f"\n❌ 변환 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
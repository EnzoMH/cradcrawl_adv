#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel to JSON 변환기 (수정버전)
Excel 파일을 raw_data_0530.json 형태의 JSON으로 변환합니다.

작성자: AI Assistant
수정일: 2025년 6월 18일
목적: 교회_원본_수정01.xlsx 파일을 JSON 형태로 변환
"""

import pandas as pd
import json
import os
import re
from datetime import datetime

def analyze_phone_type(phone_str):
    """
    전화번호 유형 분석
    Returns: 'mobile', 'landline', 'invalid'
    """
    if not phone_str or pd.isna(phone_str):
        return 'invalid'
    
    # 숫자만 추출
    clean_phone = re.sub(r'[^\d]', '', str(phone_str))
    
    if not clean_phone or len(clean_phone) < 10:
        return 'invalid'
    
    # 이동전화 번호 패턴 (010, 011, 016, 017, 018, 019로 시작)
    mobile_prefixes = ['010', '011', '016', '017', '018', '019']
    
    for prefix in mobile_prefixes:
        if clean_phone.startswith(prefix) and len(clean_phone) == 11:
            return 'mobile'
    
    # 지역번호로 시작하는 일반 전화번호
    landline_prefixes = ['02', '031', '032', '033', '041', '042', '043', '044', 
                        '051', '052', '053', '054', '055', '061', '062', '063', '064', '070']
    
    for prefix in landline_prefixes:
        if clean_phone.startswith(prefix) and len(clean_phone) in [10, 11]:
            return 'landline'
    
    return 'invalid'

def format_phone_number(phone_str):
    """전화번호 포맷팅"""
    if not phone_str or pd.isna(phone_str):
        return ""
    
    # 숫자만 추출
    clean_phone = re.sub(r'[^\d]', '', str(phone_str))
    
    if not clean_phone:
        return ""
    
    # 한국 전화번호 형식으로 포맷팅
    if len(clean_phone) == 10:
        if clean_phone.startswith('02'):
            return f"{clean_phone[:2]}-{clean_phone[2:6]}-{clean_phone[6:]}"
        else:
            return f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
    elif len(clean_phone) == 11:
        return f"{clean_phone[:3]}-{clean_phone[3:7]}-{clean_phone[7:]}"
    else:
        return clean_phone

def parse_multiple_phones_enhanced(phone_str):
    """
    전화번호2의 다양한 번호 형태를 파싱
    Returns: {'mobile': [], 'fax': [], 'additional': []}
    """
    result = {'mobile': [], 'fax': [], 'additional': []}
    
    if not phone_str or pd.isna(phone_str):
        return result
    
    # 공백, 쉼표, 슬래시로 구분된 번호들 분리
    phone_parts = re.split(r'[\s,/]+', str(phone_str))
    
    for part in phone_parts:
        part = part.strip()
        if not part:
            continue
        
        # 팩스 키워드 체크 (대소문자 무관)
        fax_keywords = ['팩스', 'fax', '팩', 'FAX']
        is_fax = any(keyword in part for keyword in fax_keywords)
        
        # 번호 부분만 추출 (괄호 안 텍스트 제거)
        phone_number = re.sub(r'\([^)]*\)', '', part)  # (팩스) 같은 부분 제거
        phone_number = re.sub(r'[^\d-]', '', phone_number)  # 숫자와 하이픈만 남김
        
        if not phone_number:
            continue
        
        # 번호 형태 분석
        phone_type = analyze_phone_type(phone_number)
        formatted_phone = format_phone_number(phone_number)
        
        if not formatted_phone:
            continue
        
        # 분류 로직
        if is_fax:
            # 팩스 키워드가 있으면 무조건 팩스
            result['fax'].append(formatted_phone)
        elif phone_type == 'mobile':
            # 010/011로 시작하는 모바일
            result['mobile'].append(formatted_phone)
        elif phone_type == 'landline':
            # 일반 전화번호는 추가 번호로 분류
            result['additional'].append(formatted_phone)
        else:
            # 기타 형식
            result['additional'].append(formatted_phone)
    
    return result

def format_url(url_str):
    """URL 포맷팅"""
    if not url_str or pd.isna(url_str):
        return ""
    
    url = str(url_str).strip()
    if not url:
        return ""
    
    if not url.startswith(('http://', 'https://')):
        if url.startswith('www.'):
            url = 'http://' + url
        elif '.' in url:
            url = 'http://' + url
    
    return url

def excel_to_json(excel_file_path, output_file_path):
    """
    Excel 파일을 JSON 형태로 변환하는 함수 (개선버전)
    """
    try:
        # Excel 파일 읽기
        print(f"📖 Excel 파일을 읽는 중: {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        
        # 컬럼명 출력 (디버깅용)
        print(f"📋 Excel 파일의 컬럼: {list(df.columns)}")
        print(f"📊 총 {len(df)}개의 행이 있습니다.")
        
        # 데이터를 JSON 형태로 변환
        json_data = []
        processed_count = 0
        error_count = 0
        
        # 통계 카운터
        phone_stats = {
            'phone1_used': 0,           # 전화번호1 사용된 개수
            'phone1_empty': 0,          # 전화번호1 비어있는 개수
            'phone2_mobile': 0,         # 전화번호2에서 모바일로 분류된 개수
            'phone2_fax': 0,            # 전화번호2에서 팩스로 분류된 개수
            'phone2_additional': 0,     # 전화번호2에서 추가번호로 분류된 개수
            'phone2_empty': 0,          # 전화번호2 비어있는 개수
            'phone2_multiple': 0        # 전화번호2에 여러 번호가 있는 경우
        }
        
        print("\n🔄 데이터 변환 중...")
        
        for index, row in df.iterrows():
            try:
                # JSON 구조 생성 (additional_phone_numbers 필드 추가)
                item = {
                    "name": "",
                    "category": "종교시설",
                    "homepage": "",
                    "phone": "",
                    "fax": "",
                    "email": "",
                    "mobile": "",
                    "postal_code": "",
                    "address": "",
                    "additional_phone_numbers": []  # 새 필드 추가
                }
                
                # 상호명
                if '상호명' in df.columns and pd.notna(row['상호명']):
                    item['name'] = str(row['상호명']).strip()
                
                # 업종명 (카테고리)
                if '업종명' in df.columns and pd.notna(row['업종명']):
                    item['category'] = str(row['업종명']).strip()
                
                # 주소 (도로명 주소 우선)
                if '도로명 주소' in df.columns and pd.notna(row['도로명 주소']):
                    item['address'] = str(row['도로명 주소']).strip()
                elif '지번주소 ' in df.columns and pd.notna(row['지번주소 ']):
                    item['address'] = str(row['지번주소 ']).strip()
                
                # 우편번호 (숫자를 문자열로 변환)
                if '우편번호 ' in df.columns and pd.notna(row['우편번호 ']):
                    postal_code = str(int(float(row['우편번호 ']))).zfill(5)
                    item['postal_code'] = postal_code
                
                # 홈페이지
                if '홈페이지' in df.columns and pd.notna(row['홈페이지']):
                    item['homepage'] = format_url(str(row['홈페이지']).strip())
                
                # 전화번호 1 처리 (무조건 phone 필드로)
                if '전화번호 1' in df.columns and pd.notna(row['전화번호 1']):
                    phone1 = str(row['전화번호 1']).strip()
                    item['phone'] = format_phone_number(phone1)
                    phone_stats['phone1_used'] += 1
                else:
                    phone_stats['phone1_empty'] += 1
                
                # 전화번호 2 처리 (개선된 파싱)
                if '전화번호 2' in df.columns and pd.notna(row['전화번호 2']):
                    phone2_str = str(row['전화번호 2']).strip()
                    parsed_phones = parse_multiple_phones_enhanced(phone2_str)
                    
                    # 여러 번호가 있는 경우
                    total_numbers = (len(parsed_phones['mobile']) + 
                                   len(parsed_phones['fax']) + 
                                   len(parsed_phones['additional']))
                    if total_numbers > 1:
                        phone_stats['phone2_multiple'] += 1
                    
                    # 모바일 번호 처리
                    if parsed_phones['mobile'] and not item['mobile']:
                        item['mobile'] = parsed_phones['mobile'][0]
                        phone_stats['phone2_mobile'] += len(parsed_phones['mobile'])
                    
                    # 팩스 번호 처리
                    if parsed_phones['fax'] and not item['fax']:
                        item['fax'] = parsed_phones['fax'][0]
                        phone_stats['phone2_fax'] += len(parsed_phones['fax'])
                    
                    # 추가 번호들 처리
                    if parsed_phones['additional']:
                        item['additional_phone_numbers'] = parsed_phones['additional']
                        phone_stats['phone2_additional'] += len(parsed_phones['additional'])
                        
                else:
                    phone_stats['phone2_empty'] += 1
                
                # 기관명이 없으면 스킵
                if not item['name']:
                    print(f"⚠️  행 {index+1}: 기관명이 없어서 스킵")
                    error_count += 1
                    continue
                
                json_data.append(item)
                processed_count += 1
                
                # 진행률 표시
                if processed_count % 5000 == 0:
                    print(f"📈 진행률: {processed_count:,}개 처리 완료...")
                
            except Exception as e:
                print(f"❌ 행 {index+1} 처리 중 오류: {e}")
                error_count += 1
                continue
        
        # JSON 파일로 저장
        print(f"💾 JSON 파일로 저장 중: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 변환 완료!")
        print(f"📈 총 {len(json_data)}개의 항목이 변환되었습니다.")
        print(f"⚠️  오류: {error_count}개")
        print(f"📁 저장 경로: {output_file_path}")
        print(f"💾 파일 크기: {os.path.getsize(output_file_path) / (1024*1024):.2f} MB")
        
        # 전화번호 통계 출력
        print(f"\n📞 전화번호 분류 통계:")
        print(f"📞 전화번호1:")
        print(f"   📞 phone 필드로: {phone_stats['phone1_used']:,}개")  
        print(f"   ⭕ 빈 값: {phone_stats['phone1_empty']:,}개")
        
        print(f"📞 전화번호2:")
        print(f"   📱 이동전화 → mobile: {phone_stats['phone2_mobile']:,}개")
        print(f"   📠 팩스번호 → fax: {phone_stats['phone2_fax']:,}개")
        print(f"   📋 추가번호 → additional: {phone_stats['phone2_additional']:,}개")
        print(f"   🔢 다중번호: {phone_stats['phone2_multiple']:,}개")
        print(f"   ⭕ 빈 값: {phone_stats['phone2_empty']:,}개")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ 오류: Excel 파일을 찾을 수 없습니다. - {excel_file_path}")
        return False
    except Exception as e:
        print(f"❌ 변환 중 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
def get_value_from_row(row, column_names):
    """
    여러 컬럼명 중에서 값을 찾아 반환하는 함수
    
    Args:
        row: 데이터프레임의 행
        column_names: 찾을 컬럼명 리스트
    
    Returns:
        str: 찾은 값 (문자열로 변환) 또는 빈 문자열
    """
    for col_name in column_names:
        if col_name in row.index and pd.notna(row[col_name]):
            value = str(row[col_name]).strip()
            if value and value.lower() not in ['nan', 'none', 'null', '']:
                return value
    return ""

def preview_excel_structure(excel_file_path):
    """
    Excel 파일의 구조를 미리 확인하는 함수
    
    Args:
        excel_file_path (str): Excel 파일 경로
    """
    try:
        df = pd.read_excel(excel_file_path)
        print("=" * 60)
        print("📊 Excel 파일 구조 미리보기")
        print("=" * 60)
        print(f"📏 총 행 수: {len(df)}")
        print(f"📋 총 열 수: {len(df.columns)}")
        print("\n컬럼 목록:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print("\n🔍 첫 3행 데이터 미리보기:")
        print(df.head(3).to_string())
        
        # 전화번호 2 샘플 분석 (수정된 부분)
        phone2_samples = df['전화번호 2'].dropna().head(10)
        if len(phone2_samples) > 0:
            print(f"\n📞 전화번호 2 샘플 ({len(phone2_samples)}개):")
            for i, sample in enumerate(phone2_samples):
                parsed = parse_multiple_phones_enhanced(sample)  # ✅ 올바른 함수 호출
                print(f"  [{i+1}] '{sample}'")
                print(f"      → 모바일: {parsed['mobile']}")
                print(f"      → 팩스: {parsed['fax']}")           # ✅ 수정됨
                print(f"      → 추가번호: {parsed['additional']}")  # ✅ 수정됨
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Excel 파일 미리보기 중 오류: {str(e)}")

def validate_json_structure(json_file_path):
    """
    생성된 JSON 파일의 구조를 검증하는 함수 (개선버전)
    
    Args:
        json_file_path (str): 검증할 JSON 파일 경로
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n🔍 생성된 JSON 파일 검증:")
        print(f"📊 총 항목 수: {len(data)}")
        
        if len(data) > 0:
            # 연락처 정보가 있는 샘플 찾기
            samples_with_contact = [item for item in data 
                                  if item['phone'] or item['mobile'] or item['fax'] 
                                  or item.get('additional_phone_numbers', [])]  # ✅ 추가
            
            print(f"\n📞 연락처 정보가 있는 항목: {len(samples_with_contact)}개")
            
            if len(samples_with_contact) > 0:
                print("\n📋 연락처 있는 샘플 3개:")
                for i, item in enumerate(samples_with_contact[:3]):
                    print(f"\n[{i+1}] {item['name']}")
                    print(f"    📞 전화: {item['phone']}")
                    print(f"    📠 팩스: {item['fax']}")
                    print(f"    📱 모바일: {item['mobile']}")
                    print(f"    📋 추가번호: {item.get('additional_phone_numbers', [])}")  # ✅ 추가
                    print(f"    🌐 홈페이지: {item['homepage']}")
                    print(f"    📍 주소: {item['address'][:50]}{'...' if len(item['address']) > 50 else ''}")
        
        # 필수 필드 체크 (수정된 부분)
        required_fields = ['name', 'category', 'homepage', 'phone', 'fax', 'email', 
                          'mobile', 'postal_code', 'address', 'additional_phone_numbers']  # ✅ 추가
        missing_fields = [field for field in required_fields if field not in data[0].keys()]
        
        if missing_fields:
            print(f"⚠️  누락된 필드: {missing_fields}")
        else:
            print("✅ 모든 필수 필드가 포함되었습니다.")
            
    except Exception as e:
        print(f"❌ JSON 검증 중 오류: {str(e)}")

def main():
    """
    메인 실행 함수
    """
    # 파일 경로 설정
    excel_file_path = r"C:\Users\MyoengHo Shin\pjt\advanced_crawling\data\excel\교회_원본_수정01.xlsx"
    output_dir = r"C:\Users\MyoengHo Shin\pjt\advanced_crawling\data\json"
    
    # 출력 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"church_data_converted_{timestamp}.json"
    output_file_path = os.path.join(output_dir, output_file_name)
    
    print("=" * 60)
    print("🔄 Excel to JSON 변환기 (수정버전)")
    print("=" * 60)
    print(f"📥 입력 파일: {excel_file_path}")
    print(f"📤 출력 파일: {output_file_path}")
    print("-" * 60)
    
    # 파일 존재 확인
    if not os.path.exists(excel_file_path):
        print(f"❌ 오류: Excel 파일이 존재하지 않습니다.")
        print(f"   경로: {excel_file_path}")
        return
    
    # 출력 디렉토리 확인 및 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 출력 디렉토리를 생성했습니다: {output_dir}")
    
    # Excel 구조 미리보기
    preview_excel_structure(excel_file_path)
    
    print("\n🚀 변환을 시작합니다...")
    
    # 변환 실행
    success = excel_to_json(excel_file_path, output_file_path)
    
    if success:
        print("\n🎉 변환이 성공적으로 완료되었습니다!")
        print(f"📁 저장된 파일: {output_file_path}")
        
        # JSON 구조 검증
        validate_json_structure(output_file_path)
        
        print("\n📝 다음 단계:")
        print("  1. 생성된 JSON 파일을 확인하세요")
        print("  2. raw_data_0530.json과 동일한 구조로 변환되었습니다")
        print("  3. 전화번호가 적절히 분류되었는지 확인하세요")
        
    else:
        print("\n❌변환 중 오류가 발생했습니다.")
        print("  Excel 파일의 구조를 확인하고 다시 시도해주세요.")

if __name__ == "__main__":
    main()
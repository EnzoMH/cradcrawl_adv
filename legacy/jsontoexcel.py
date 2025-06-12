import json
import pandas as pd
from datetime import datetime
import os

def load_and_analyze_json(json_file_path):
    """JSON 파일 로드 및 기본 분석"""
    try:
        print(f"📂 JSON 파일 로딩 중: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON 파일 로드 완료")
        print(f"📊 데이터 타입: {type(data)}")
        
        if isinstance(data, list):
            print(f"📋 총 레코드 수: {len(data)}")
            if len(data) > 0:
                print(f"🔍 첫 번째 레코드 키들: {list(data[0].keys())}")
                print(f"📝 첫 번째 레코드 예시:")
                for key, value in list(data[0].items())[:5]:  # 처음 5개 필드만 출력
                    print(f"  - {key}: {value}")
        elif isinstance(data, dict):
            print(f"📋 최상위 키들: {list(data.keys())}")
            
        return data
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 파일 로딩 중 오류: {e}")
        return None

def filter_excluded_fields(data, exclude_fields):
    """지정된 필드들을 제외한 데이터 반환"""
    if isinstance(data, list):
        filtered_data = []
        for record in data:
            if isinstance(record, dict):
                filtered_record = {k: v for k, v in record.items() if k not in exclude_fields}
                filtered_data.append(filtered_record)
            else:
                filtered_data.append(record)
        return filtered_data
    elif isinstance(data, dict):
        return {k: v for k, v in data.items() if k not in exclude_fields}
    return data

def analyze_data_structure(data, exclude_fields=None):
    """데이터 구조 상세 분석 (제외 필드 고려)"""
    print("\n🔍 데이터 구조 분석 중...")
    
    if exclude_fields:
        print(f"🚫 제외할 필드들: {', '.join(exclude_fields)}")
    
    if isinstance(data, list) and len(data) > 0:
        # 모든 키들 수집
        all_keys = set()
        sample_records = data[:min(10, len(data))]  # 처음 10개 레코드 분석
        
        for record in sample_records:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        # 제외 필드 제거
        if exclude_fields:
            all_keys = all_keys - set(exclude_fields)
        
        print(f"📋 포함될 필드들 ({len(all_keys)}개):")
        for key in sorted(all_keys):
            print(f"  - {key}")
        
        # 필드별 데이터 현황 분석
        print(f"\n📊 필드별 데이터 현황 (상위 {len(sample_records)}개 레코드 기준):")
        field_stats = {}
        
        for key in sorted(all_keys):
            non_empty_count = 0
            for record in sample_records:
                if record.get(key) and str(record.get(key)).strip():
                    non_empty_count += 1
            
            field_stats[key] = {
                'non_empty': non_empty_count,
                'empty': len(sample_records) - non_empty_count,
                'fill_rate': (non_empty_count / len(sample_records)) * 100
            }
            
            print(f"  📌 {key}: {non_empty_count}/{len(sample_records)} 채워짐 ({field_stats[key]['fill_rate']:.1f}%)")
        
        return all_keys, field_stats
    
    return None, None

def convert_to_excel(data, excel_file_path, exclude_fields=None, all_keys=None):
    """JSON 데이터를 엑셀로 변환 (특정 필드 제외)"""
    try:
        print(f"\n💾 엑셀 파일 생성 중: {excel_file_path}")
        
        # 제외 필드 적용
        if exclude_fields:
            print(f"🚫 제외되는 필드들: {', '.join(exclude_fields)}")
            data = filter_excluded_fields(data, exclude_fields)
        
        if isinstance(data, list):
            # 리스트 형태의 데이터를 DataFrame으로 변환
            df = pd.DataFrame(data)
            
            # 컬럼 순서 조정 (중요한 필드들을 앞으로) - 제외 필드는 제거
            priority_columns = ['name', 'category', 'phone', 'fax', 'email', 'address', 'postal_code', 'mobile']
            
            # 제외 필드가 있으면 우선순위에서도 제거
            if exclude_fields:
                priority_columns = [col for col in priority_columns if col not in exclude_fields]
            
            # 존재하는 우선순위 컬럼들만 필터링
            existing_priority = [col for col in priority_columns if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in existing_priority]
            
            # 컬럼 순서 재정렬
            new_column_order = existing_priority + remaining_columns
            df = df[new_column_order]
            
            print(f"📋 DataFrame 생성 완료: {len(df)} 행, {len(df.columns)} 열")
            print(f"📊 포함된 컬럼 목록: {list(df.columns)}")
            
        elif isinstance(data, dict):
            # 딕셔너리 형태의 데이터를 처리
            if 'churches' in data:
                churches_data = data['churches']
                if exclude_fields:
                    churches_data = filter_excluded_fields(churches_data, exclude_fields)
                df = pd.DataFrame(churches_data)
            else:
                # 딕셔너리를 하나의 행으로 변환
                df = pd.DataFrame([data])
        else:
            print("❌ 지원하지 않는 데이터 형태입니다.")
            return False
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            # 메인 데이터 시트
            df.to_excel(writer, sheet_name='교회_데이터', index=False)
            
            # 통계 시트 생성
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
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='필드_통계', index=False)
        
        print(f"✅ 엑셀 파일 생성 완료: {excel_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 엑셀 변환 중 오류: {e}")
        return False

def preview_excel_file(excel_file_path, num_rows=5):
    """엑셀 파일 미리보기"""
    try:
        print(f"\n👀 엑셀 파일 미리보기: {excel_file_path}")
        
        # 교회 데이터 시트 읽기
        df = pd.read_excel(excel_file_path, sheet_name='교회_데이터')
        
        print(f"📊 전체 데이터 크기: {len(df)} 행, {len(df.columns)} 열")
        print(f"📋 상위 {num_rows}개 레코드:")
        print(df.head(num_rows).to_string())
        
        # 필드 통계 시트 읽기
        try:
            stats_df = pd.read_excel(excel_file_path, sheet_name='필드_통계')
            print(f"\n📈 필드별 통계 (상위 10개):")
            print(stats_df.head(10).to_string(index=False))
        except:
            print("📈 통계 시트를 읽을 수 없습니다.")
        
    except Exception as e:
        print(f"❌ 엑셀 미리보기 중 오류: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📊 JSON to Excel 변환기 (필드 제외 기능)")
    print("=" * 60)
    
    # 파일 경로 설정
    json_file = "churches_enhanced_final_20250611_182318.json"
    
    # 제외할 필드들 설정
    exclude_fields = ["homepage", "extraction_summary"]
    
    # 타임스탬프 포함한 엑셀 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"church_data_filtered_{timestamp}.xlsx"
    
    print(f"📂 입력 파일: {json_file}")
    print(f"💾 출력 파일: {excel_file}")
    print(f"🚫 제외할 필드: {', '.join(exclude_fields)}")
    
    # 파일 존재 확인
    if not os.path.exists(json_file):
        print(f"❌ 입력 파일을 찾을 수 없습니다: {json_file}")
        return
    
    # 1단계: JSON 파일 로드 및 기본 분석
    data = load_and_analyze_json(json_file)
    if data is None:
        return
    
    # 2단계: 데이터 구조 상세 분석 (제외 필드 고려)
    all_keys, field_stats = analyze_data_structure(data, exclude_fields)
    
    # 3단계: 엑셀로 변환 (제외 필드 적용)
    success = convert_to_excel(data, excel_file, exclude_fields, all_keys)
    
    if success:
        # 4단계: 결과 미리보기
        preview_excel_file(excel_file, num_rows=3)
        
        print(f"\n🎉 변환 완료!")
        print(f"📁 생성된 파일: {excel_file}")
        print(f"📊 데이터 시트: '교회_데이터'")
        print(f"📈 통계 시트: '필드_통계'")
        print(f"🚫 제외된 필드: {', '.join(exclude_fields)}")
    else:
        print("❌ 변환 실패")

if __name__ == "__main__":
    main()
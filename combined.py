import json
import os
from datetime import datetime
from validator import ContactValidator

def load_json_file(filepath):
    """JSON 파일 로드"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {filepath} 로드 완료 ({len(data) if isinstance(data, list) else len(data.get('churches', []))} 개)")
        return data
    except Exception as e:
        print(f"❌ {filepath} 로드 실패: {e}")
        return None

def normalize_ref_data(data, source_file):
    """참조 데이터를 일관된 형태로 정규화"""
    churches = []
    
    if isinstance(data, list):
        # raw_data_0530.json 형태
        for item in data:
            churches.append({
                'name': item.get('name', ''),
                'phone': item.get('phone', ''),
                'fax': item.get('fax', ''),
                'email': item.get('email', ''),
                'homepage': item.get('homepage', ''),
                'address': item.get('address', ''),
                'source': source_file
            })
    elif isinstance(data, dict) and 'churches' in data:
        # raw_data_with_homepages_20250527_142101.json 형태
        for item in data['churches']:
            # 홈페이지 컨텐츠에서 연락처 정보 추출
            extracted_phone = ''
            extracted_fax = ''
            extracted_email = ''
            
            if 'homepage_content' in item and item['homepage_content']:
                content = item['homepage_content']
                if 'parsed_contact' in content:
                    parsed = content['parsed_contact']
                    if parsed.get('phones'):
                        extracted_phone = parsed['phones'][0]
                    if parsed.get('faxes'):
                        extracted_fax = parsed['faxes'][0]
                    if parsed.get('emails'):
                        extracted_email = parsed['emails'][0]
            
            churches.append({
                'name': item.get('name', ''),
                'phone': item.get('phone', '') or extracted_phone,
                'fax': item.get('fax', '') or extracted_fax,
                'email': item.get('email', '') or extracted_email,
                'homepage': item.get('homepage', ''),
                'address': '',  # 필요시 parsed_contact.addresses에서 추출 가능
                'source': source_file
            })
    
    return churches

def update_base_data(base_data, ref_data_list, validator):
    """기준 데이터를 참조 데이터로 업데이트"""
    print("\n🔍 교차검증 및 데이터 업데이트 시작")
    
    # 참조 데이터를 소스별로 분리
    ref_0530_dict = {}
    ref_20250527_dict = {}
    
    for ref_data, source_name in ref_data_list:
        if 'raw_data_0530.json' in source_name:
            ref_0530_dict = {item.get('name', ''): item for item in ref_data if item.get('name')}
        elif 'raw_data_with_homepages_20250527_142101.json' in source_name:
            ref_20250527_dict = {item.get('name', ''): item for item in ref_data if item.get('name')}
    
    validation_stats = {
        'total': len(base_data),
        'phone_updated': 0,
        'fax_updated': 0,
        'email_updated': 0,
        'homepage_updated': 0,
        'homepage_overwritten': 0,  # 20250527 파일로 덮어쓴 경우
        'address_updated': 0,
        'phone_validated': 0,
        'fax_validated': 0,
        'validation_failed': 0
    }
    
    # 기준 데이터 업데이트
    for i, church in enumerate(base_data):
        name = church.get('name', '')
        if not name:
            continue
            
        if i % 100 == 0:  # 100개마다 진행상황 출력
            print(f"📍 처리 중: {i+1}/{len(base_data)} - {name}")
        
        # 참조 데이터에서 정보 찾기
        ref_0530_info = ref_0530_dict.get(name, {})
        ref_20250527_info = ref_20250527_dict.get(name, {})
        
        updated_fields = []
        
        # 1. 일반 필드들 (phone, fax, email, address) - 빈 값만 채우기
        for field in ['phone', 'fax', 'email', 'address']:
            current_value = church.get(field, '')
            
            # 현재 값이 비어있는 경우에만 업데이트
            if not current_value:
                # 먼저 raw_data_0530.json에서 찾기
                if ref_0530_info.get(field):
                    church[field] = ref_0530_info[field]
                    validation_stats[f'{field}_updated'] += 1
                    updated_fields.append(f"{field}: {ref_0530_info[field]} (from raw_data_0530.json)")
                # 없으면 20250527 파일에서 찾기
                elif ref_20250527_info.get(field):
                    church[field] = ref_20250527_info[field]
                    validation_stats[f'{field}_updated'] += 1
                    updated_fields.append(f"{field}: {ref_20250527_info[field]} (from raw_data_with_homepages_20250527_142101.json)")
        
        # 2. homepage 필드 - 20250527 파일을 우선적으로 사용 (덮어쓰기 포함)
        if ref_20250527_info.get('homepage'):
            original_homepage = church.get('homepage', '')
            church['homepage'] = ref_20250527_info['homepage']
            
            if original_homepage:
                validation_stats['homepage_overwritten'] += 1
                updated_fields.append(f"homepage: {ref_20250527_info['homepage']} (덮어쓰기 from raw_data_with_homepages_20250527_142101.json)")
            else:
                validation_stats['homepage_updated'] += 1
                updated_fields.append(f"homepage: {ref_20250527_info['homepage']} (신규 from raw_data_with_homepages_20250527_142101.json)")
        # 20250527에 없고 현재 값이 비어있으면 0530에서 찾기
        elif not church.get('homepage') and ref_0530_info.get('homepage'):
            church['homepage'] = ref_0530_info['homepage']
            validation_stats['homepage_updated'] += 1
            updated_fields.append(f"homepage: {ref_0530_info['homepage']} (from raw_data_0530.json)")
        
        # 업데이트된 내용이 있으면 출력
        if updated_fields:
            print(f"  ✨ {name} 업데이트:")
            for update in updated_fields:
                print(f"    - {update}")
        
        # 전화번호/팩스번호 검증 및 정제
        phone_to_validate = church.get('phone', '')
        fax_to_validate = church.get('fax', '')
        
        if phone_to_validate or fax_to_validate:
            validation_result = validator.clean_contact_data(phone_to_validate, fax_to_validate)
            
            # 검증 결과로 업데이트
            original_phone = church.get('phone', '')
            original_fax = church.get('fax', '')
            
            church['phone'] = validation_result['phone']
            church['fax'] = validation_result['fax']
            
            # 검증으로 인한 변경사항 체크
            if original_phone != church['phone'] and validation_result['phone']:
                print(f"    🔧 전화번호 정제: {original_phone} → {church['phone']}")
            if original_fax != church['fax'] and validation_result['fax']:
                print(f"    🔧 팩스번호 정제: {original_fax} → {church['fax']}")
            
            if validation_result['phone_valid']:
                validation_stats['phone_validated'] += 1
            if validation_result['fax_valid']:
                validation_stats['fax_validated'] += 1
            if not validation_result['phone_valid'] and not validation_result['fax_valid'] and (phone_to_validate or fax_to_validate):
                validation_stats['validation_failed'] += 1
    
    print(f"\n📊 업데이트 통계:")
    print(f"  📋 총 교회 수: {validation_stats['total']}")
    print(f"  📞 전화번호 업데이트: {validation_stats['phone_updated']}")
    print(f"  📠 팩스번호 업데이트: {validation_stats['fax_updated']}")
    print(f"  📧 이메일 업데이트: {validation_stats['email_updated']}")
    print(f"  🌐 홈페이지 신규 추가: {validation_stats['homepage_updated']}")
    print(f"  🔄 홈페이지 덮어쓰기: {validation_stats['homepage_overwritten']}")
    print(f"  📍 주소 업데이트: {validation_stats['address_updated']}")
    print(f"  ✅ 전화번호 검증 성공: {validation_stats['phone_validated']}")
    print(f"  ✅ 팩스번호 검증 성공: {validation_stats['fax_validated']}")
    print(f"  ❌ 검증 실패: {validation_stats['validation_failed']}")
    
    return base_data, validation_stats

def save_combined_data(data, filepath):
    """업데이트된 데이터를 새 파일에 저장"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {filepath} 저장 완료 ({len(data)} 개 교회)")
        return True
    except Exception as e:
        print(f"❌ {filepath} 저장 실패: {e}")
        return False

def main():
    print("🚀 교회 데이터 교차검증 및 병합 시작")
    print("=" * 50)
    
    # 파일 경로 설정
    base_file = 'raw_data_with_homepages_20250604_142232.json'  # 기준 파일
    ref_files = [
        'raw_data_0530.json',                           # 참조 파일 1
        'raw_data_with_homepages_20250527_142101.json'  # 참조 파일 2 (홈페이지 우선)
    ]
    
    # 파일 존재 확인
    all_files = [base_file] + ref_files
    for filepath in all_files:
        if not os.path.exists(filepath):
            print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
            return
    
    # JSON 파일들 로드
    print("\n📂 파일 로딩 중...")
    base_data = load_json_file(base_file)
    
    if not base_data:
        print("❌ 기준 파일 로딩 실패")
        return
    
    # 참조 파일들 로드 및 정규화
    ref_data_list = []
    for ref_file in ref_files:
        ref_raw = load_json_file(ref_file)
        if ref_raw:
            ref_normalized = normalize_ref_data(ref_raw, ref_file)
            ref_data_list.append((ref_normalized, ref_file))
            print(f"  📊 {ref_file}: {len(ref_normalized)} 개")
    
    if not ref_data_list:
        print("❌ 참조 파일 로딩 실패")
        return
    
    print(f"  📊 기준 데이터: {len(base_data)} 개")
    print(f"  🎯 홈페이지 우선: raw_data_with_homepages_20250527_142101.json")
    
    # ContactValidator 초기화
    print("\n🛠️ 연락처 검증기 초기화 중...")
    validator = ContactValidator()
    
    # 교차검증 및 업데이트 (원본 파일은 건드리지 않음)
    combined_data, stats = update_base_data(base_data.copy(), ref_data_list, validator)
    
    # 결과 저장 (새 파일 생성)
    print(f"\n💾 combined.json 생성 중...")
    if save_combined_data(combined_data, "combined.json"):
        # 타임스탬프 포함된 백업 파일도 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"combined_{timestamp}.json"
        save_combined_data(combined_data, backup_filename)
        print(f"📁 메인 파일: combined.json")
        print(f"📁 백업 파일: {backup_filename}")
    
    print("\n🎉 교차검증 및 병합 완료!")
    print("📝 원본 파일들은 변경되지 않았습니다.")
    print("=" * 50)

if __name__ == "__main__":
    main()
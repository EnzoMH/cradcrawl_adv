import json
import os
from datetime import datetime

# 기본 필드 정의
DEFAULT_FIELDS = {
    "name": "",
    "category": "종교시설",
    "homepage": "",
    "phone": "",
    "fax": "",
    "email": "",
    "mobile": "",
    "postal_code": "",
    "address": ""
}

def load_json_file(file_path):
    """JSON 파일을 로드합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON 구조 확인
        if isinstance(data, dict) and 'churches' in data:
            churches = data['churches']
            print(f"✅ {os.path.basename(file_path)} 로드 완료 - 교회 수: {len(churches)} (객체 형태)")
        elif isinstance(data, list):
            churches = data
            print(f"✅ {os.path.basename(file_path)} 로드 완료 - 교회 수: {len(churches)} (배열 형태)")
        else:
            print(f"⚠️ {os.path.basename(file_path)} - 알 수 없는 구조: {type(data)}")
            churches = []
        
        return data
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return None

def extract_churches(data):
    """데이터에서 교회 목록을 추출합니다."""
    if isinstance(data, dict) and 'churches' in data:
        return data['churches']
    elif isinstance(data, list):
        return data
    else:
        print(f"⚠️ 지원하지 않는 데이터 형태: {type(data)}")
        return []

def normalize_church_data(church):
    """교회 데이터를 표준화합니다 (기본 필드 보장)."""
    normalized = DEFAULT_FIELDS.copy()
    
    # 기존 데이터 업데이트
    normalized.update(church)
    
    return normalized

def merge_church_data(file1_path, file2_path, output_path=None):
    """두 교회 데이터 JSON 파일을 합칩니다."""
    
    # 파일 로드
    print("📂 JSON 파일들을 로드합니다...")
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)
    
    if not data1 or not data2:
        print("❌ 파일 로드 실패!")
        return False
    
    # 교회 데이터 추출
    churches1 = extract_churches(data1)
    churches2 = extract_churches(data2)
    
    print(f"📊 파일1: {len(churches1)}개 교회")
    print(f"📊 파일2: {len(churches2)}개 교회")
    
    # 첫 번째 파일의 몇 개 샘플 출력
    if churches1:
        print(f"📋 파일1 샘플 필드: {list(churches1[0].keys())}")
    if churches2:
        print(f"📋 파일2 샘플 필드: {list(churches2[0].keys())}")
    
    # 중복 제거를 위한 교회 이름 기준 병합
    merged_churches = []
    church_names = set()
    
    # 첫 번째 파일의 교회들 추가 (표준화)
    for church in churches1:
        normalized_church = normalize_church_data(church)
        name = normalized_church.get('name', '').strip()
        if name and name not in church_names:
            merged_churches.append(normalized_church)
            church_names.add(name)
    
    # 두 번째 파일의 교회들 추가 (중복 제외, 표준화)
    duplicates = 0
    added_from_file2 = 0
    for church in churches2:
        normalized_church = normalize_church_data(church)
        name = normalized_church.get('name', '').strip()
        if name and name not in church_names:
            merged_churches.append(normalized_church)
            church_names.add(name)
            added_from_file2 += 1
        elif name:
            duplicates += 1
    
    print(f"🔄 병합 완료:")
    print(f"   - 파일1에서 추가: {len(churches1) - len([c for c in churches1 if not c.get('name', '').strip()])}개")
    print(f"   - 파일2에서 추가: {added_from_file2}개")
    print(f"   - 총 교회 수: {len(merged_churches)}")
    print(f"   - 중복 제거: {duplicates}개")
    
    # 출력 파일 경로 설정
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"../data/json/merged_church_data_{timestamp}.json"
    
    # 병합된 데이터 구조 생성
    merged_data = {
        "churches": merged_churches,
        "metadata": {
            "merged_at": datetime.now().isoformat(),
            "source_files": [
                os.path.basename(file1_path),
                os.path.basename(file2_path)
            ],
            "total_churches": len(merged_churches),
            "duplicates_removed": duplicates,
            "file1_churches": len(churches1),
            "file2_churches": len(churches2),
            "file2_added": added_from_file2,
            "default_fields": list(DEFAULT_FIELDS.keys())
        }
    }
    
    # 파일 저장
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 병합 완료! 저장 위치: {output_path}")
        print(f"📋 모든 교회 데이터가 기본 필드를 포함하도록 표준화되었습니다.")
        print(f"🔧 기본 필드: {', '.join(DEFAULT_FIELDS.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🔧 JSON 교회 데이터 병합도구 (필드 표준화 포함)")
    print("=" * 60)
    
    # 파일 경로 설정 (test 디렉토리에서 실행 기준)
    file1 = "../data/json/parsed_homepages_20250617_192102.json"
    file2 = "../data/json/church_data_converted_20250617_202219.json"
    
    print(f"📁 파일1: {file1}")
    print(f"📁 파일2: {file2}")
    print(f"🔧 기본 필드: {', '.join(DEFAULT_FIELDS.keys())}")
    print()
    
    # 병합 실행
    success = merge_church_data(file1, file2)
    
    if success:
        print("\n🎉 병합 작업이 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 병합 작업 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()
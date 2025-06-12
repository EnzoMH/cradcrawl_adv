import pandas as pd
import json
from datetime import datetime
from pathlib import Path

def excel_to_json():
    # 프로젝트 루트 경로 설정
    base_dir = Path(__file__).parent.parent
    excel_dir = base_dir / "data" / "excel"
    json_dir = base_dir / "data" / "json"
    
    # 디렉토리가 없으면 생성
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # 엑셀 파일 경로
    excel_path = excel_dir / "filtered_data_0612.xlsx"
    
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_path)
    
    # JSON 데이터 리스트
    json_data = []
    
    # 각 행을 JSON 객체로 변환
    for _, row in df.iterrows():
        json_obj = {
            "name": str(row.get('name', '')).strip() if pd.notna(row.get('name', '')) else '',
            "category": str(row.get('category', '')).strip() if pd.notna(row.get('category', '')) else '',
            "homepage": str(row.get('homepage', '')).strip() if pd.notna(row.get('homepage', '')) else '',
            "phone": str(row.get('phone', '')).strip() if pd.notna(row.get('phone', '')) else '',
            "fax": str(row.get('fax', '')).strip() if pd.notna(row.get('fax', '')) else '',
            "email": str(row.get('email', '')).strip() if pd.notna(row.get('email', '')) else '',
            "mobile": str(row.get('mobile', '')).strip() if pd.notna(row.get('mobile', '')) else '',
            "postal_code": str(row.get('postal_code', '')).strip() if pd.notna(row.get('postal_code', '')) else '',
            "address": str(row.get('address', '')).strip() if pd.notna(row.get('address', '')) else ''
        }
        json_data.append(json_obj)
    
    # 타임스탬프가 포함된 출력 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_data_converted_{timestamp}.json"
    output_path = json_dir / output_filename
    
    # JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"변환 완료! 파일 저장됨: {output_path}")
    print(f"총 {len(json_data)}개의 데이터가 변환되었습니다.")

if __name__ == "__main__":
    excel_to_json()
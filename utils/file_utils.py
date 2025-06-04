#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 I/O 관련 유틸리티 통합
기존 3개 크롤러 파일의 중복된 파일 처리 기능을 통합
"""

import json
import os
import glob
from typing import Dict, List, Optional, Any
from datetime import datetime

class FileUtils:
    """파일 처리 관련 유틸리티 클래스 - 중복 제거"""
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict]:
        """
        JSON 파일 로드 (통합)
        fax_crawler.py + naver_map_crawler.py + url_extractor.py 통합
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ 파일이 존재하지 않습니다: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON 파일 로드 성공: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {file_path}, 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 파일 로드 실패: {file_path}, 오류: {e}")
            return None
    
    @staticmethod
    def save_json(data: Dict, file_path: str, backup: bool = True) -> bool:
        """
        JSON 파일 저장 (통합)
        3개 크롤러의 저장 로직 통합
        """
        try:
            # 백업 파일 생성 (선택사항)
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(file_path, backup_path)
                print(f"📄 백업 파일 생성: {backup_path}")
            
            # JSON 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON 파일 저장 성공: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 파일 저장 실패: {file_path}, 오류: {e}")
            return False
    
    @staticmethod
    def find_latest_file(pattern: str, directory: str = ".") -> Optional[str]:
        """
        최신 파일 찾기 (통합)
        jsontocsv.py + jsontoexcel.py 통합
        """
        try:
            search_pattern = os.path.join(directory, pattern)
            files = glob.glob(search_pattern)
            
            if not files:
                print(f"⚠️ 패턴에 맞는 파일이 없습니다: {pattern}")
                return None
            
            # 파일 수정 시간 기준으로 최신 파일 찾기
            latest_file = max(files, key=os.path.getmtime)
            print(f"📄 최신 파일 발견: {latest_file}")
            
            return latest_file
            
        except Exception as e:
            print(f"❌ 파일 검색 실패: {pattern}, 오류: {e}")
            return None
    
    @staticmethod
    def find_latest_json_file(directory: str = ".") -> Optional[str]:
        """최신 JSON 파일 찾기 (jsontocsv.py, jsontoexcel.py에서 사용)"""
        return FileUtils.find_latest_file("raw_data_with_contacts_*.json", directory)
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """파일 정보 조회"""
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "created_time": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    @staticmethod
    def create_timestamped_filename(base_name: str, extension: str = "json") -> str:
        """타임스탬프가 포함된 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"
    
    @staticmethod
    def ensure_directory_exists(directory: str) -> bool:
        """디렉토리가 없으면 생성"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"❌ 디렉토리 생성 실패: {directory}, 오류: {e}")
            return False
    
    @staticmethod
    def count_data_in_json(file_path: str) -> Dict[str, int]:
        """JSON 파일 내 데이터 개수 집계 (jsontocsv.py에서 사용)"""
        data = FileUtils.load_json(file_path)
        if not data:
            return {}
        
        counts = {}
        if isinstance(data, dict):
            for category, items in data.items():
                if isinstance(items, list):
                    counts[category] = len(items)
                else:
                    counts[category] = 1
        elif isinstance(data, list):
            counts["total"] = len(data)
        
        return counts
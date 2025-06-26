#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 로그 파일 정리 스크립트
"""

import os
import glob
from datetime import datetime

def cleanup_log_files():
    """기존 로그 파일들을 정리합니다."""
    
    # 현재 디렉토리의 .log 파일들 찾기
    log_files = glob.glob("*.log")
    
    if not log_files:
        print("✅ 정리할 로그 파일이 없습니다.")
        return
    
    print(f"🗑️  {len(log_files)}개의 로그 파일을 발견했습니다:")
    for log_file in log_files:
        print(f"   - {log_file}")
    
    # 사용자 확인
    response = input("\n이 파일들을 모두 삭제하시겠습니까? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        deleted_count = 0
        for log_file in log_files:
            try:
                os.remove(log_file)
                print(f"✅ 삭제됨: {log_file}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 삭제 실패: {log_file} - {e}")
        
        print(f"\n🎉 총 {deleted_count}개의 로그 파일이 삭제되었습니다.")
    else:
        print("❌ 삭제가 취소되었습니다.")

if __name__ == "__main__":
    cleanup_log_files() 
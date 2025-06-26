#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로거 설정 관련 유틸리티 통합
기존 5개 파일의 중복된 로거 설정 기능을 통합
"""

import logging
import os
from datetime import datetime
from typing import Optional
from utils.settings import LOGGER_NAMES, LOG_FORMAT, ENABLE_FILE_LOGGING, LOG_LEVEL

class LoggerUtils:
    """로거 설정 관련 유틸리티 클래스 - 중복 제거"""
    
    @staticmethod
    def setup_logger(name: str, log_file: Optional[str] = None, level: int = None,
                console: bool = True, file_logging: bool = None) -> logging.Logger:
        """
        통합 로거 설정 - 파일 로깅 기본 비활성화
        """
        # 환경 변수에서 기본값 설정
        if level is None:
            level = getattr(logging, LOG_LEVEL, logging.INFO)
        if file_logging is None:
            file_logging = ENABLE_FILE_LOGGING
        
        # 로거 이름 매핑 (constants.py 활용)
        logger_name = LOGGER_NAMES.get(name, name)
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 포맷터 설정
        formatter = logging.Formatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        
        # 콘솔 핸들러 추가
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 파일 핸들러 추가 (명시적으로 요청한 경우에만)
        if file_logging and log_file:
            # 로그 디렉토리 생성
            log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"로그 파일 설정: {log_file}")
        
        logger.info(f"로거 '{logger_name}' 설정 완료 (파일 로깅: {'ON' if file_logging else 'OFF'})")
        return logger
    
    @staticmethod
    def setup_crawler_logger(crawler_name: str, enable_file_logging: bool = False) -> logging.Logger:
        """
        크롤러 전용 로거 (파일 로깅 선택적)
        """
        if enable_file_logging:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/{crawler_name}_{timestamp}.log"
        else:
            log_file = None
        
        return LoggerUtils.setup_logger(
            name=crawler_name,
            log_file=log_file,
            level=logging.INFO,
            console=True,
            file_logging=enable_file_logging
        )
    
    @staticmethod
    def setup_ai_logger(enable_file_logging: bool = False) -> logging.Logger:
        """
        AI 응답 전용 로거 (파일 로깅 선택적)
        """
        if enable_file_logging:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/gemini_responses_{timestamp}.log"
        else:
            log_file = None
        
        logger = LoggerUtils.setup_logger(
            name="ai_helpers", 
            log_file=log_file,
            level=logging.INFO,
            console=True,
            file_logging=enable_file_logging
        )
        
        if enable_file_logging:
            logger.info("AI 응답 로깅 시작")
        return logger
    
    @staticmethod
    def setup_validator_logger() -> logging.Logger:
        """
        검증기 전용 로거 (콘솔만)
        """
        return LoggerUtils.setup_logger(
            name="validator",
            level=logging.INFO,
            console=True,
            file_logging=False
        )
    
    @staticmethod
    def setup_app_logger() -> logging.Logger:
        """
        웹앱 전용 로거 (콘솔만)
        """
        return LoggerUtils.setup_logger(
            name="app",
            level=logging.INFO,
            console=True,
            file_logging=False
        )
    
    @staticmethod
    def create_timestamped_log_file(base_name: str, directory: str = "logs") -> str:
        """타임스탬프가 포함된 로그 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(directory, exist_ok=True)
        return f"{directory}/{base_name}_{timestamp}.log"
    
    @staticmethod
    def set_log_level(logger: logging.Logger, level_name: str):
        """로그 레벨 동적 변경"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        level = level_map.get(level_name.upper(), logging.INFO)
        logger.setLevel(level)
        
        # 핸들러들도 레벨 변경
        for handler in logger.handlers:
            handler.setLevel(level)
        
        logger.info(f"로그 레벨 변경: {level_name}")
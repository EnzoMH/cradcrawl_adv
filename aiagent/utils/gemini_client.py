#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 클라이언트
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    """Gemini API 클라이언트"""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-pro"):
        """
        Gemini 클라이언트 초기화
        
        Args:
            api_key: Gemini API 키 (None이면 환경변수에서 가져옴)
            model_name: 사용할 모델 이름
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. 환경변수 또는 매개변수로 제공해주세요.")
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # 요청 제한 설정
        self.max_requests_per_minute = 60
        self.request_count = 0
        self.last_reset_time = time.time()
        
        logger.info(f"Gemini 클라이언트 초기화 완료 (모델: {self.model_name})")
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        컨텐츠 생성
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트
        """
        try:
            # 요청 제한 확인
            self._check_rate_limit()
            
            # 기본 생성 설정
            generation_config = {
                'temperature': kwargs.get('temperature', 0.7),
                'top_p': kwargs.get('top_p', 0.8),
                'top_k': kwargs.get('top_k', 40),
                'max_output_tokens': kwargs.get('max_output_tokens', 2048),
            }
            
            # 컨텐츠 생성
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # 요청 카운트 증가
            self.request_count += 1
            
            # 응답 텍스트 반환
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Gemini API 응답이 비어있습니다.")
                return ""
                
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {str(e)}")
            raise
    
    def generate_structured_content(self, prompt: str, expected_format: str = "json", **kwargs) -> Dict[str, Any]:
        """
        구조화된 컨텐츠 생성
        
        Args:
            prompt: 입력 프롬프트
            expected_format: 예상 출력 형식 (json, yaml 등)
            **kwargs: 추가 생성 옵션
            
        Returns:
            구조화된 데이터
        """
        try:
            # 구조화된 출력을 위한 프롬프트 보강
            structured_prompt = f"""
{prompt}

응답은 반드시 다음 형식으로 제공해주세요:
- 형식: {expected_format}
- 올바른 구문을 사용해주세요
- 추가 설명 없이 데이터만 반환해주세요

응답:
"""
            
            response_text = self.generate_content(structured_prompt, **kwargs)
            
            # JSON 파싱 시도
            if expected_format.lower() == "json":
                import json
                try:
                    # JSON 블록 추출
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    elif "{" in response_text and "}" in response_text:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_text = response_text[json_start:json_end]
                    else:
                        json_text = response_text
                    
                    return json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 파싱 실패: {e}")
                    return {"raw_response": response_text, "parse_error": str(e)}
            
            # 기본적으로 텍스트 반환
            return {"content": response_text}
            
        except Exception as e:
            logger.error(f"구조화된 컨텐츠 생성 실패: {str(e)}")
            return {"error": str(e)}
    
    def analyze_text(self, text: str, analysis_type: str = "general", **kwargs) -> Dict[str, Any]:
        """
        텍스트 분석
        
        Args:
            text: 분석할 텍스트
            analysis_type: 분석 유형 (general, sentiment, extraction 등)
            **kwargs: 추가 분석 옵션
            
        Returns:
            분석 결과
        """
        analysis_prompts = {
            "general": f"""
다음 텍스트를 분석하고 주요 정보를 추출해주세요:

텍스트: {text}

분석 결과를 JSON 형식으로 제공해주세요:
{{
    "summary": "텍스트 요약",
    "key_points": ["주요 포인트 1", "주요 포인트 2"],
    "entities": ["개체명 1", "개체명 2"],
    "sentiment": "긍정/부정/중립",
    "confidence": 0.8
}}
""",
            "contact": f"""
다음 텍스트에서 연락처 정보를 추출해주세요:

텍스트: {text}

연락처 정보를 JSON 형식으로 제공해주세요:
{{
    "phone_numbers": ["전화번호1", "전화번호2"],
    "fax_numbers": ["팩스번호1", "팩스번호2"],
    "email_addresses": ["이메일1", "이메일2"],
    "websites": ["웹사이트1", "웹사이트2"],
    "addresses": ["주소1", "주소2"],
    "confidence": 0.8
}}
""",
            "validation": f"""
다음 데이터의 유효성을 검증해주세요:

데이터: {text}

검증 결과를 JSON 형식으로 제공해주세요:
{{
    "is_valid": true/false,
    "validation_errors": ["오류1", "오류2"],
    "suggestions": ["개선사항1", "개선사항2"],
    "confidence": 0.8
}}
"""
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        return self.generate_structured_content(prompt, "json", **kwargs)
    
    def _check_rate_limit(self):
        """요청 제한 확인"""
        current_time = time.time()
        
        # 1분마다 카운트 리셋
        if current_time - self.last_reset_time >= 60:
            self.request_count = 0
            self.last_reset_time = current_time
        
        # 요청 제한 확인
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.last_reset_time)
            logger.warning(f"요청 제한 도달. {wait_time:.1f}초 대기 중...")
            time.sleep(wait_time)
            self.request_count = 0
            self.last_reset_time = time.time()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """사용량 통계 반환"""
        return {
            "model_name": self.model_name,
            "request_count": self.request_count,
            "max_requests_per_minute": self.max_requests_per_minute,
            "last_reset_time": self.last_reset_time
        }
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            test_response = self.generate_content("안녕하세요. 연결 테스트입니다.")
            return bool(test_response)
        except Exception as e:
            logger.error(f"연결 테스트 실패: {str(e)}")
            return False 
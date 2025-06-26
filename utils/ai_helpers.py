"""
AI 유틸리티 모듈

나라장터 크롤링 과정에서 사용되는 AI 관련 함수들을 제공합니다.
"""

import os
import json
import re
import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, Union, List
import google.generativeai as genai
from utils.settings import AI_MODEL_CONFIG  # AI_MODEL_CONFIG만 import
from utils.logger_utils import LoggerUtils

import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 로거 설정
logger = logging.getLogger(__name__)

# Gemini API 관련 상수 (환경변수에서 직접 가져오기)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. AI 기능을 사용할 수 없습니다.")
else:
    logger.info(f"AI 유틸리티에서 GEMINI_API_KEY를 로드했습니다.")

GEMINI_MODEL_TEXT = "gemini-1.5-flash"
GEMINI_MODEL_VISION = "gemini-1.5-flash"

# 전역 변수
gemini_model = None

class AIModelManager:
    """AI 모델 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.gemini_model = None
        self.gemini_config = None
        self.setup_models()
    
    def setup_models(self):
        """AI 모델 초기화"""
        try:
            # Gemini 설정
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_config = AI_MODEL_CONFIG
            self.gemini_model = genai.GenerativeModel(
                GEMINI_MODEL_TEXT,
                generation_config=self.gemini_config
            )
            
            # 전역 변수에도 설정 (기존 함수 호환성 유지)
            global gemini_model
            gemini_model = self.gemini_model
            
            logger.info("AI 모델 초기화 성공")
        except Exception as e:
            logger.error(f"AI 모델 초기화 실패: {e}")
            # 초기화 실패시 오류를 발생시키지 않고 로그만 남김
            logger.debug(traceback.format_exc())
    
    
    async def extract_with_gemini(self, text_content: str, prompt_template: str) -> str:
        """
        텍스트 콘텐츠를 Gemini API에 전달하여 정보 추출
        
        Args:
            text_content: 분석할 텍스트 콘텐츠
            prompt_template: 프롬프트 템플릿 문자열 ('{content}' 플레이스홀더 포함)
            
        Returns:
            추출된 정보 문자열
        """
        try:
            # 보안 및 처리를 위한 텍스트 길이 제한
            max_length = 32000  # Gemini 모델의 최대 컨텍스트 길이보다 적게 설정
            if len(text_content) > max_length:
                # 앞부분 2/3, 뒷부분 1/3 유지
                front_portion = int(max_length * 0.67)
                back_portion = max_length - front_portion
                text_content = text_content[:front_portion] + "\n... (중략) ...\n" + text_content[-back_portion:]
                logger.warning(f"텍스트가 너무 길어 일부를 생략했습니다: {len(text_content)} -> {max_length}")
            
            # 프롬프트 구성
            prompt = prompt_template.format(text_content=text_content)  # 이 줄을 수정
            
            # 응답 생성
            response = self.gemini_model.generate_content(prompt)
            
            # 응답 추출 및 정리
            result_text = response.text
            
            # 결과 로깅 (첫 200자만)
            logger.info(f"Gemini API 응답 (일부): {result_text[:200]}...")
            
            return result_text
            
        except Exception as e:
            logger.error(f"Gemini API 호출 중 오류: {str(e)}")
            logger.debug(traceback.format_exc())
            return f"오류: {str(e)}"
    
    async def check_relevance(self, title: str, keyword: str) -> bool:
        """
        Gemini AI를 사용하여 검색어와 공고명 사이의 연관성을 판단
        
        Args:
            title: 공고명
            keyword: 검색어
            
        Returns:
            bool: 연관성이 있으면 True, 없으면 False
        """
        try:
            logger.info(f"검색어 '{keyword}'와 공고명 '{title}' 사이의 연관성 판단 중...")
            
            # 프롬프트 구성
            prompt = f"""
            당신은 입찰공고명과 검색어 사이의 실제 연관성을 판단하는 AI 어시스턴트입니다.
            
            입찰공고명: {title}
            검색어: {keyword}
            
            위 입찰공고가 검색어와 실제로 연관이 있는지 판단해주세요.
            
            다음 규칙을 따라주세요:
            1. 단순히 텍스트가 포함되어 있는 것이 아니라 의미적 연관성을 판단해야 합니다.
            2. 같은 의미를 가진 유사어도 연관성이 있다고 판단합니다 (예: '인공지능'과 'AI', '머신러닝'과 'ML' 등).
            3. 제품명이나 회사명에 우연히 검색어의 일부가 포함된 경우는 연관이 없습니다 (예: 'AI'가 'MAIN', 'TRAIN'의 일부로 포함된 경우).
            4. 검색어가 약어인 경우 전체 단어도 확인합니다 (예: 'AI'는 'Artificial Intelligence'와 연관).
            
            
            결과는 아래 형식으로 출력해주세요:
            {{
                "is_relevant": true/false,
                "reason": "판단 이유를 1-2문장으로 설명"
            }}
            """
            
            # 모델 호출
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.gemini_model.generate_content(prompt)
            )
            
            # 응답 텍스트
            result_text = response.text
            
            # JSON 부분 추출 시도
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
            if json_match:
                result_text = json_match.group(1)
            
            # 중괄호로 둘러싸인 부분을 찾아 추출
            json_match = re.search(r'(\{[\s\S]*\})', result_text)
            if json_match:
                result_text = json_match.group(1)
            
            try:
                # JSON 파싱 시도
                result_data = json.loads(result_text)
                is_relevant = result_data.get("is_relevant", False)
                reason = result_data.get("reason", "이유 없음")
                
                if is_relevant:
                    logger.info(f"판단 결과: 연관성 있음 - {reason}")
                else:
                    logger.info(f"판단 결과: 연관성 없음 - {reason}")
                    
                return is_relevant
                
            except json.JSONDecodeError:
                logger.warning("JSON 파싱 실패, 텍스트에서 결과 추출 시도")
                
                # 텍스트 기반 판단을 위한 보다 정교한 분석
                result_text_lower = result_text.lower()
                
                # 긍정 표현 패턴
                positive_patterns = [
                    "is_relevant.*true", "연관성.*있", "관련.*있", "관계.*있", 
                    "연관.*있", "관련.*높", "관계.*높", "연관.*높",
                    "연관성.*O", "관련성.*O", "연관도.*높", "관련도.*높"
                ]
                
                # 부정 표현 패턴
                negative_patterns = [
                    "is_relevant.*false", "연관성.*없", "관련.*없", "관계.*없", 
                    "연관.*없", "관련.*낮", "관계.*낮", "연관.*낮",
                    "연관성.*X", "관련성.*X", "연관도.*낮", "관련도.*낮"
                ]
                
                # 각 패턴을 검사하여 점수 계산
                positive_score = sum(1 for pattern in positive_patterns if re.search(pattern, result_text_lower))
                negative_score = sum(1 for pattern in negative_patterns if re.search(pattern, result_text_lower))
                
                # 판단 결과 도출
                is_relevant = positive_score > negative_score
                
                # 단일 패턴 확인 (점수가 동일한 경우 백업 판단 기준)
                if positive_score == negative_score:
                    # 기본 확인: "is_relevant.*true" 패턴 확인
                    if re.search(r"is_relevant.*true", result_text_lower):
                        is_relevant = True
                        logger.info("기본 패턴 검사를 통해 연관성 있음으로 판단")
                    else:
                        # 모호한 경우 긍정 판단 (false negative 방지)
                        logger.info("판단 모호하여 연관성 있음으로 기본 설정")
                        is_relevant = True
                
                logger.info(f"텍스트 분석 기반 판단 결과: {'연관성 있음' if is_relevant else '연관성 없음'} (긍정점수: {positive_score}, 부정점수: {negative_score})")
                
                return is_relevant
        
        except Exception as e:
            logger.error(f"연관성 판단 중 오류: {str(e)}")
            logger.debug(traceback.format_exc())
            # 오류 발생 시 기본적으로 연관성 있다고 가정 (false negative 방지)
            return True

# AI 모델 관리자 인스턴스 생성
ai_model_manager = AIModelManager()

async def _init_gemini_model():
    """Gemini 모델 초기화"""
    global gemini_model
    
    # 이미 초기화되었으면 건너뜀
    if gemini_model is not None:
        return
    
    try:
        # Gemini API 키 설정
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Gemini 모델 초기화 (centralized config 사용)
        gemini_model = genai.GenerativeModel(
            GEMINI_MODEL_TEXT,
            generation_config=AI_MODEL_CONFIG
        )
        
        logger.info("독립 Gemini 모델 초기화 성공")
    except Exception as e:
        logger.error(f"독립 Gemini 모델 초기화 실패: {e}")
        logger.debug(traceback.format_exc())

async def extract_with_gemini_text(text_content: str, prompt_template: str) -> str:
    """
    Gemini API를 사용하여 텍스트에서 정보 추출
    
    Args:
        text_content: 처리할 텍스트 내용
        prompt_template: 프롬프트 템플릿 ('{text_content}'를 포함해야 함)
        
    Returns:
        추출된 정보 (텍스트) 또는 None (실패 시)
    """
    try:
        # AI 모델 관리자 사용 시도
        if ai_model_manager and ai_model_manager.gemini_model:
            # 기존 호환성 유지를 위해 content 키를 text_content로 변경
            modified_template = prompt_template.replace("{content}", "{text_content}")
            result = await ai_model_manager.extract_with_gemini(text_content, modified_template)
            return result
            
        # 기존 방식 - 독립적인 모델 초기화 방식 (백업)
        model = await _init_gemini_model()
        if model is None:
            logger.error("Gemini 모델 초기화 실패로 정보 추출을 건너뜁니다.")
            return None
        
        # 너무 긴 텍스트 처리
        if len(text_content) > 30000:
            logger.warning(f"텍스트가 너무 깁니다. 처음 30000자로 자릅니다: {len(text_content)}자")
            text_content = text_content[:30000]
        
        # 프롬프트 준비
        prompt = prompt_template.format(text_content=text_content)
        
        # API 호출
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        
        # 응답 처리
        if response and hasattr(response, 'text'):
            logger.info("Gemini API 호출 성공")
            return response.text
        else:
            logger.warning("Gemini API 응답 형식 오류")
            return None
            
    except Exception as e:
        logger.error(f"Gemini API 호출 오류: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

async def check_relevance_with_ai(title: str, keyword: str) -> bool:
    """
    타이틀과 키워드 간의 관련성을 AI로 확인
    
    Args:
        title: 입찰 공고 제목
        keyword: 검색 키워드
        
    Returns:
        관련성 있음 (True) 또는 없음 (False)
    """
    try:
        # AI 모델 관리자 사용 시도
        if ai_model_manager and ai_model_manager.gemini_model:
            return await ai_model_manager.check_relevance(title, keyword)
        
        # 기존 방식 유지 (백업)
        # 모델 초기화
        model = await _init_gemini_model()
        if model is None:
            logger.warning("Gemini 모델 초기화 실패로 관련성 검사를 건너뜁니다.")
            return True  # 기본적으로 관련 있다고 간주
            
        # 프롬프트 준비
        prompt = f"""
        제목: "{title}"
        키워드: "{keyword}"
        
        위 제목과 키워드 간의 관련성을 판단해주세요.
        첫 줄에는 반드시 다음 중 하나만 작성해주세요:
        - 관련있음
        - 관련없음
        
        두 번째 줄부터는 간략한 이유를 작성해주세요.
        
        제목이 키워드와 조금이라도 관련이 있으면 '관련있음'으로 판단해주세요.
        """
        
        # API 호출
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        
        # 응답 처리
        if response and hasattr(response, 'text'):
            response_text = response.text.strip().lower()
            
            # 첫 줄 추출
            first_line = response_text.split('\n')[0].strip()
            
            # 한국어 또는 영어로 '관련 있음' 여부 판단
            positive_match = (
                "관련있음" in first_line or 
                "관련 있음" in first_line or
                "relevant" in first_line or 
                "related" in first_line or
                "yes" in first_line
            )
            
            negative_match = (
                "관련없음" in first_line or 
                "관련 없음" in first_line or
                "not relevant" in first_line or
                "not related" in first_line or
                "no" == first_line.strip()
            )
            
            # 부정적 표현이 명확히 있으면 부정, 아니면 긍정적 표현 여부 확인
            is_relevant = not negative_match and positive_match
            
            # 둘 다 매치되지 않으면, 전체 텍스트에서 판단
            if not positive_match and not negative_match:
                is_relevant = (
                    "관련" in response_text or 
                    "연관" in response_text or
                    "관계가 있" in response_text or
                    "relevant" in response_text or 
                    "related" in response_text
                ) and not (
                    "관련이 없" in response_text or 
                    "관련 없" in response_text or
                    "not relevant" in response_text or
                    "not related" in response_text or
                    "irrelevant" in response_text
                )
            
            # 이유 추출 (있을 경우)
            reason_lines = response_text.split('\n')[1:]
            reason = ' '.join(reason_lines).strip() if reason_lines else '이유 없음'
            
            logger.info(f"관련성 검사 결과: {is_relevant} - {reason}")
            return is_relevant
        else:
            logger.warning("Gemini API 응답 형식 오류")
            return True  # 기본적으로 관련 있다고 간주
            
    except Exception as e:
        logger.error(f"관련성 검사 중 오류: {str(e)}")
        logger.debug(traceback.format_exc())
        return True  # 오류 시 기본적으로 관련 있다고 간주 

async def loop_run_in_executor(func):
    """
    함수를 비동기적으로 실행합니다.
    
    Args:
        func: 실행할 함수
        
    Returns:
        함수 실행 결과
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func)

def parse_gemini_text_to_json(text):
    """
    Gemini API의 텍스트 응답을 구조화된 JSON으로 변환
    
    Args:
        text: Gemini API의 응답 텍스트
        
    Returns:
        구조화된 JSON 객체
    """
    try:
        result = {}
        
        # 줄 단위로 분리
        lines = text.strip().split('\n')
        current_key = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 숫자로 시작하는 줄은 새로운 항목으로 간주
            if line[0].isdigit() and '. ' in line:
                # 이전 항목 저장
                if current_key and current_value:
                    result[current_key] = '\n'.join(current_value).strip()
                    current_value = []
                
                # 새 항목 파싱
                parts = line.split('. ', 1)
                if len(parts) == 2:
                    key_value = parts[1].split(':', 1)
                    if len(key_value) == 2:
                        current_key = key_value[0].strip()
                        value_part = key_value[1].strip()
                        current_value.append(value_part)
                    else:
                        current_key = parts[1].strip()
            else:
                # 값 계속 누적
                if current_key:
                    current_value.append(line)
        
        # 마지막 항목 저장
        if current_key and current_value:
            result[current_key] = '\n'.join(current_value).strip()
        
        return result
    except Exception as e:
        logger.warning(f"Gemini 텍스트 파싱 실패: {str(e)}")
        return {"raw_text": text}

def process_gemini_response(gemini_response, detail_data):
    """
    Gemini API 응답을 처리하고 세부 데이터에 통합
    
    Args:
        gemini_response: Gemini API 응답 텍스트
        detail_data: 기존 세부 데이터 딕셔너리
        
    Returns:
        통합된 세부 데이터 딕셔너리
    """
    try:
        # Gemini 응답을 문자열로 변환하여 저장
        if isinstance(gemini_response, dict):
            # 딕셔너리인 경우 문자열로 변환
            detail_data["prompt_result"] = json.dumps(gemini_response, ensure_ascii=False)
        else:
            # 이미 문자열인 경우 그대로 저장
            detail_data["prompt_result"] = str(gemini_response)
        
        # 텍스트 응답을 구조화된 데이터로 변환하여 저장
        parsed_result = parse_gemini_text_to_json(detail_data["prompt_result"])
        detail_data["prompt_result_parsed"] = parsed_result
        
        # 중요 필드들을 메인 데이터로 가져오기
        for key, value in parsed_result.items():
            if "계약방법" in key.lower() and not detail_data.get("contract_method"):
                detail_data["contract_method"] = value
            elif "입찰방식" in key.lower() and not detail_data.get("bid_type"):
                detail_data["bid_type"] = value
            elif "추정가격" in key.lower() or "사업금액" in key.lower() or "기초금액" in key.lower():
                detail_data["estimated_price"] = value
            elif "계약기간" in key.lower() or "납품기한" in key.lower():
                detail_data["contract_period"] = value
            elif "납품장소" in key.lower() or "이행장소" in key.lower():
                detail_data["delivery_location"] = value
            elif "참가자격" in key.lower() or "자격요건" in key.lower():
                detail_data["qualification"] = value
        
        logger.info("Gemini API 응답 처리 완료")
        return detail_data
        
    except Exception as e:
        logger.error(f"Gemini 응답 처리 중 오류: {str(e)}")
        logger.debug(traceback.format_exc())
        return detail_data 
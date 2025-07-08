#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연락처 추출 전문 에이전트
텍스트에서 정확한 연락처 정보를 추출하는 AI 에이전트
"""

import re
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from ..core.agent_base import BaseAgent, AgentTask, AgentResult
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ContactAgent(BaseAgent):
    """연락처 추출 전문 에이전트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("contact_agent", config)
        
        # 정규식 패턴들
        self.phone_patterns = [
            r'(?:전화|TEL|Phone|T\.?)\s*:?\s*([0-9]{2,3}-[0-9]{3,4}-[0-9]{4})',
            r'(?:전화|TEL|Phone|T\.?)\s*:?\s*([0-9]{2,3}\.[0-9]{3,4}\.[0-9]{4})',
            r'(?:전화|TEL|Phone|T\.?)\s*:?\s*([0-9]{2,3}\s[0-9]{3,4}\s[0-9]{4})',
            r'([0-9]{2,3}-[0-9]{3,4}-[0-9]{4})',
            r'([0-9]{2,3}\.[0-9]{3,4}\.[0-9]{4})',
        ]
        
        self.fax_patterns = [
            r'(?:팩스|FAX|Fax|F\.?)\s*:?\s*([0-9]{2,3}-[0-9]{3,4}-[0-9]{4})',
            r'(?:팩스|FAX|Fax|F\.?)\s*:?\s*([0-9]{2,3}\.[0-9]{3,4}\.[0-9]{4})',
            r'(?:팩스|FAX|Fax|F\.?)\s*:?\s*([0-9]{2,3}\s[0-9]{3,4}\s[0-9]{4})',
        ]
        
        self.email_patterns = [
            r'(?:이메일|Email|E-mail|메일)\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        
        self.website_patterns = [
            r'(?:홈페이지|웹사이트|Website|Homepage|URL)\s*:?\s*(https?://[^\s]+)',
            r'(?:홈페이지|웹사이트|Website|Homepage|URL)\s*:?\s*(www\.[^\s]+)',
            r'(https?://[^\s]+)',
            r'(www\.[^\s]+)',
        ]
    
    def get_system_prompt(self) -> str:
        """연락처 추출 전문 시스템 프롬프트"""
        return """
당신은 연락처 정보 추출 전문가입니다. 텍스트에서 정확한 연락처 정보를 추출하고 검증해주세요.

**전문 영역:**
1. 전화번호 추출 및 형식 정규화
2. 팩스번호 추출 및 검증
3. 이메일 주소 추출 및 유효성 검사
4. 웹사이트 URL 추출 및 정규화
5. 주소 정보 추출

**추출 기준:**
- 한국 전화번호 형식 (02-1234-5678, 031-123-4567 등)
- 팩스번호 형식 (전화번호와 동일)
- 이메일 형식 (name@domain.com)
- 웹사이트 URL (http://, https://, www. 포함)
- 주소 정보 (시/도, 시/군/구, 상세주소)

**검증 기준:**
- 형식 정확성
- 실제 존재 가능성
- 중복 제거
- 신뢰도 평가

**응답 형식:**
반드시 JSON 형식으로 응답해주세요.
"""
    
    def process_task(self, task: AgentTask) -> AgentResult:
        """연락처 추출 작업 처리"""
        try:
            data = task.data
            text = data.get('text', '')
            extraction_type = data.get('extraction_type', 'all')  # all, phone, fax, email, website
            
            if not text:
                return AgentResult(
                    task_id=task.task_id,
                    success=False,
                    data={},
                    error_message="추출할 텍스트가 제공되지 않았습니다."
                )
            
            # 1. 기본 정규식 추출
            regex_results = self._extract_with_regex(text, extraction_type)
            
            # 2. AI 기반 추출
            ai_results = self._extract_with_ai(text, extraction_type)
            
            # 3. 결과 통합 및 검증
            combined_results = self._combine_and_validate_results(regex_results, ai_results)
            
            # 4. 최종 정리 및 형식화
            final_results = self._finalize_results(combined_results)
            
            return AgentResult(
                task_id=task.task_id,
                success=True,
                data=final_results,
                confidence_score=final_results.get('confidence', 0.0)
            )
            
        except Exception as e:
            logger.error(f"연락처 추출 중 오류: {str(e)}")
            return AgentResult(
                task_id=task.task_id,
                success=False,
                data={},
                error_message=str(e)
            )
    
    def _extract_with_regex(self, text: str, extraction_type: str) -> Dict[str, List[str]]:
        """정규식을 사용한 연락처 추출"""
        results = {
            'phone_numbers': [],
            'fax_numbers': [],
            'email_addresses': [],
            'websites': [],
            'addresses': []
        }
        
        try:
            if extraction_type in ['all', 'phone']:
                for pattern in self.phone_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    results['phone_numbers'].extend(matches)
            
            if extraction_type in ['all', 'fax']:
                for pattern in self.fax_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    results['fax_numbers'].extend(matches)
            
            if extraction_type in ['all', 'email']:
                for pattern in self.email_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    results['email_addresses'].extend(matches)
            
            if extraction_type in ['all', 'website']:
                for pattern in self.website_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    results['websites'].extend(matches)
            
            # 중복 제거
            for key in results:
                results[key] = list(set(results[key]))
                
        except Exception as e:
            logger.error(f"정규식 추출 중 오류: {str(e)}")
        
        return results
    
    def _extract_with_ai(self, text: str, extraction_type: str) -> Dict[str, Any]:
        """AI를 사용한 연락처 추출"""
        try:
            prompt = f"""
다음 텍스트에서 연락처 정보를 추출해주세요:

텍스트: {text}

추출 유형: {extraction_type}

연락처 정보를 JSON 형식으로 제공해주세요:
{{
    "phone_numbers": ["전화번호1", "전화번호2"],
    "fax_numbers": ["팩스번호1", "팩스번호2"],
    "email_addresses": ["이메일1", "이메일2"],
    "websites": ["웹사이트1", "웹사이트2"],
    "addresses": ["주소1", "주소2"],
    "confidence": 0.8,
    "extraction_notes": "추출 과정에서의 특이사항"
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                import json
                try:
                    return json.loads(response['content'])
                except json.JSONDecodeError:
                    return {'confidence': 0.0}
            else:
                return {'confidence': 0.0}
                
        except Exception as e:
            logger.error(f"AI 추출 중 오류: {str(e)}")
            return {'confidence': 0.0}
    
    def _combine_and_validate_results(self, regex_results: Dict[str, List[str]], 
                                    ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """결과 통합 및 검증"""
        combined = {
            'phone_numbers': [],
            'fax_numbers': [],
            'email_addresses': [],
            'websites': [],
            'addresses': []
        }
        
        # 정규식 결과와 AI 결과 통합
        for key in combined.keys():
            regex_items = regex_results.get(key, [])
            ai_items = ai_results.get(key, [])
            
            # 모든 결과 합치기
            all_items = list(set(regex_items + ai_items))
            
            # 각 항목 검증
            validated_items = []
            for item in all_items:
                if self._validate_contact_item(item, key):
                    validated_items.append(item)
            
            combined[key] = validated_items
        
        # 신뢰도 계산
        combined['confidence'] = self._calculate_extraction_confidence(combined, ai_results)
        
        return combined
    
    def _validate_contact_item(self, item: str, item_type: str) -> bool:
        """개별 연락처 항목 검증"""
        if not item or not item.strip():
            return False
        
        try:
            if item_type == 'phone_numbers':
                return self._validate_phone_number(item)
            elif item_type == 'fax_numbers':
                return self._validate_fax_number(item)
            elif item_type == 'email_addresses':
                return self._validate_email(item)
            elif item_type == 'websites':
                return self._validate_website(item)
            elif item_type == 'addresses':
                return self._validate_address(item)
            else:
                return True
        except Exception:
            return False
    
    def _validate_phone_number(self, phone: str) -> bool:
        """전화번호 유효성 검사"""
        # 한국 전화번호 패턴 검증
        patterns = [
            r'^0[2-9]{1,2}-[0-9]{3,4}-[0-9]{4}$',  # 지역번호
            r'^01[0-9]-[0-9]{3,4}-[0-9]{4}$',      # 휴대폰
            r'^070-[0-9]{3,4}-[0-9]{4}$',          # 인터넷전화
        ]
        
        # 하이픈 정규화
        normalized = re.sub(r'[.\s]', '-', phone)
        
        for pattern in patterns:
            if re.match(pattern, normalized):
                return True
        return False
    
    def _validate_fax_number(self, fax: str) -> bool:
        """팩스번호 유효성 검사 (전화번호와 동일)"""
        return self._validate_phone_number(fax)
    
    def _validate_email(self, email: str) -> bool:
        """이메일 유효성 검사"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_website(self, website: str) -> bool:
        """웹사이트 URL 유효성 검사"""
        try:
            # URL 정규화
            if not website.startswith(('http://', 'https://')):
                if website.startswith('www.'):
                    website = 'http://' + website
                else:
                    website = 'http://www.' + website
            
            parsed = urlparse(website)
            return bool(parsed.netloc and parsed.scheme)
        except Exception:
            return False
    
    def _validate_address(self, address: str) -> bool:
        """주소 유효성 검사"""
        # 한국 주소 패턴 검증
        korean_regions = [
            '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
            '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'
        ]
        
        for region in korean_regions:
            if region in address:
                return True
        
        # 도로명주소 패턴
        if re.search(r'(로|길)\s*\d+', address):
            return True
        
        # 지번주소 패턴
        if re.search(r'\d+-\d+', address):
            return True
        
        return len(address) > 10  # 최소 길이 조건
    
    def _calculate_extraction_confidence(self, combined: Dict[str, Any], 
                                       ai_results: Dict[str, Any]) -> float:
        """추출 신뢰도 계산"""
        total_items = sum(len(combined[key]) for key in combined.keys() if key != 'confidence')
        
        if total_items == 0:
            return 0.0
        
        # 기본 신뢰도
        base_confidence = 0.6
        
        # AI 신뢰도 반영
        ai_confidence = ai_results.get('confidence', 0.5)
        
        # 추출된 항목 수에 따른 보정
        item_bonus = min(0.3, total_items * 0.05)
        
        # 최종 신뢰도
        final_confidence = (base_confidence + ai_confidence + item_bonus) / 2
        
        return min(1.0, final_confidence)
    
    def _finalize_results(self, combined: Dict[str, Any]) -> Dict[str, Any]:
        """최종 결과 정리"""
        final_results = {
            'phone_numbers': self._format_phone_numbers(combined.get('phone_numbers', [])),
            'fax_numbers': self._format_phone_numbers(combined.get('fax_numbers', [])),
            'email_addresses': combined.get('email_addresses', []),
            'websites': self._format_websites(combined.get('websites', [])),
            'addresses': combined.get('addresses', []),
            'confidence': combined.get('confidence', 0.0),
            'extraction_summary': {
                'total_phone': len(combined.get('phone_numbers', [])),
                'total_fax': len(combined.get('fax_numbers', [])),
                'total_email': len(combined.get('email_addresses', [])),
                'total_website': len(combined.get('websites', [])),
                'total_address': len(combined.get('addresses', []))
            }
        }
        
        return final_results
    
    def _format_phone_numbers(self, phone_numbers: List[str]) -> List[str]:
        """전화번호 형식 정규화"""
        formatted = []
        for phone in phone_numbers:
            # 하이픈으로 통일
            normalized = re.sub(r'[.\s]', '-', phone)
            formatted.append(normalized)
        return formatted
    
    def _format_websites(self, websites: List[str]) -> List[str]:
        """웹사이트 URL 형식 정규화"""
        formatted = []
        for website in websites:
            if not website.startswith(('http://', 'https://')):
                if website.startswith('www.'):
                    website = 'http://' + website
                else:
                    website = 'http://www.' + website
            formatted.append(website)
        return formatted
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """추출 통계 반환"""
        stats = self.get_performance_stats()
        return {
            'total_extractions': stats.get('total_tasks', 0),
            'successful_extractions': stats.get('successful_tasks', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'average_confidence': stats.get('average_confidence', 0.0),
            'average_extraction_time': stats.get('average_duration', 0.0)
        } 
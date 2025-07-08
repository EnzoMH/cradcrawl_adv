#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 검증 전문 에이전트
추출된 데이터의 품질을 검증하고 개선사항을 제안하는 AI 에이전트
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..core.agent_base import BaseAgent, AgentTask, AgentResult
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """데이터 검증 전문 에이전트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("validation_agent", config)
        
        # 검증 규칙들
        self.validation_rules = {
            'phone_number': {
                'patterns': [r'^0[2-9]{1,2}-[0-9]{3,4}-[0-9]{4}$', r'^01[0-9]-[0-9]{3,4}-[0-9]{4}$'],
                'required_length': (12, 13),
                'allowed_chars': '0123456789-'
            },
            'fax_number': {
                'patterns': [r'^0[2-9]{1,2}-[0-9]{3,4}-[0-9]{4}$'],
                'required_length': (12, 13),
                'allowed_chars': '0123456789-'
            },
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'max_length': 254,
                'required_parts': ['@', '.']
            },
            'website': {
                'patterns': [r'^https?://', r'^www\.'],
                'required_parts': ['.'],
                'max_length': 2048
            }
        }
    
    def get_system_prompt(self) -> str:
        """데이터 검증 전문 시스템 프롬프트"""
        return """
당신은 데이터 품질 검증 전문가입니다. 추출된 데이터의 정확성, 완전성, 일관성을 검증하고 개선사항을 제안해주세요.

**전문 영역:**
1. 데이터 형식 검증 (전화번호, 이메일, URL 등)
2. 데이터 일관성 검사
3. 중복 데이터 식별
4. 누락 데이터 감지
5. 데이터 품질 점수 산정

**검증 기준:**
- 형식 정확성 (포맷, 길이, 패턴)
- 논리적 일관성 (조직명-주소-연락처 일치)
- 완전성 (필수 필드 존재 여부)
- 신뢰성 (실제 존재 가능성)
- 최신성 (정보의 현재성)

**품질 등급:**
- A급 (90-100%): 매우 우수
- B급 (80-89%): 우수
- C급 (70-79%): 보통
- D급 (60-69%): 미흡
- F급 (60% 미만): 불량

**응답 형식:**
반드시 JSON 형식으로 응답해주세요.
"""
    
    def process_task(self, task: AgentTask) -> AgentResult:
        """데이터 검증 작업 처리"""
        try:
            data = task.data
            validation_type = data.get('validation_type', 'comprehensive')  # comprehensive, format, consistency, completeness
            target_data = data.get('target_data', {})
            
            if not target_data:
                return AgentResult(
                    task_id=task.task_id,
                    success=False,
                    data={},
                    error_message="검증할 데이터가 제공되지 않았습니다."
                )
            
            # 1. 기본 형식 검증
            format_validation = self._validate_format(target_data)
            
            # 2. 일관성 검증
            consistency_validation = self._validate_consistency(target_data)
            
            # 3. 완전성 검증
            completeness_validation = self._validate_completeness(target_data)
            
            # 4. AI 기반 종합 검증
            ai_validation = self._validate_with_ai(target_data, validation_type)
            
            # 5. 최종 검증 결과 통합
            final_validation = self._integrate_validation_results(
                format_validation, consistency_validation, 
                completeness_validation, ai_validation
            )
            
            return AgentResult(
                task_id=task.task_id,
                success=True,
                data=final_validation,
                confidence_score=final_validation.get('overall_confidence', 0.0)
            )
            
        except Exception as e:
            logger.error(f"데이터 검증 중 오류: {str(e)}")
            return AgentResult(
                task_id=task.task_id,
                success=False,
                data={},
                error_message=str(e)
            )
    
    def _validate_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """형식 검증"""
        format_results = {
            'phone_validation': {},
            'fax_validation': {},
            'email_validation': {},
            'website_validation': {},
            'overall_format_score': 0.0
        }
        
        total_validations = 0
        passed_validations = 0
        
        try:
            # 전화번호 검증
            if 'phone_numbers' in data:
                phone_result = self._validate_phone_format(data['phone_numbers'])
                format_results['phone_validation'] = phone_result
                total_validations += 1
                if phone_result.get('is_valid', False):
                    passed_validations += 1
            
            # 팩스번호 검증
            if 'fax_numbers' in data:
                fax_result = self._validate_fax_format(data['fax_numbers'])
                format_results['fax_validation'] = fax_result
                total_validations += 1
                if fax_result.get('is_valid', False):
                    passed_validations += 1
            
            # 이메일 검증
            if 'email_addresses' in data:
                email_result = self._validate_email_format(data['email_addresses'])
                format_results['email_validation'] = email_result
                total_validations += 1
                if email_result.get('is_valid', False):
                    passed_validations += 1
            
            # 웹사이트 검증
            if 'websites' in data:
                website_result = self._validate_website_format(data['websites'])
                format_results['website_validation'] = website_result
                total_validations += 1
                if website_result.get('is_valid', False):
                    passed_validations += 1
            
            # 전체 형식 점수 계산
            if total_validations > 0:
                format_results['overall_format_score'] = passed_validations / total_validations
            
        except Exception as e:
            logger.error(f"형식 검증 중 오류: {str(e)}")
        
        return format_results
    
    def _validate_phone_format(self, phone_numbers: List[str]) -> Dict[str, Any]:
        """전화번호 형식 검증"""
        if not phone_numbers:
            return {'is_valid': False, 'errors': ['전화번호가 없습니다.']}
        
        valid_phones = []
        invalid_phones = []
        errors = []
        
        for phone in phone_numbers:
            if self._check_phone_pattern(phone):
                valid_phones.append(phone)
            else:
                invalid_phones.append(phone)
                errors.append(f"잘못된 전화번호 형식: {phone}")
        
        return {
            'is_valid': len(valid_phones) > 0,
            'valid_count': len(valid_phones),
            'invalid_count': len(invalid_phones),
            'valid_phones': valid_phones,
            'invalid_phones': invalid_phones,
            'errors': errors,
            'success_rate': len(valid_phones) / len(phone_numbers) if phone_numbers else 0
        }
    
    def _validate_fax_format(self, fax_numbers: List[str]) -> Dict[str, Any]:
        """팩스번호 형식 검증"""
        return self._validate_phone_format(fax_numbers)  # 전화번호와 동일한 형식
    
    def _validate_email_format(self, email_addresses: List[str]) -> Dict[str, Any]:
        """이메일 형식 검증"""
        if not email_addresses:
            return {'is_valid': False, 'errors': ['이메일이 없습니다.']}
        
        valid_emails = []
        invalid_emails = []
        errors = []
        
        for email in email_addresses:
            if self._check_email_pattern(email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
                errors.append(f"잘못된 이메일 형식: {email}")
        
        return {
            'is_valid': len(valid_emails) > 0,
            'valid_count': len(valid_emails),
            'invalid_count': len(invalid_emails),
            'valid_emails': valid_emails,
            'invalid_emails': invalid_emails,
            'errors': errors,
            'success_rate': len(valid_emails) / len(email_addresses) if email_addresses else 0
        }
    
    def _validate_website_format(self, websites: List[str]) -> Dict[str, Any]:
        """웹사이트 형식 검증"""
        if not websites:
            return {'is_valid': False, 'errors': ['웹사이트가 없습니다.']}
        
        valid_websites = []
        invalid_websites = []
        errors = []
        
        for website in websites:
            if self._check_website_pattern(website):
                valid_websites.append(website)
            else:
                invalid_websites.append(website)
                errors.append(f"잘못된 웹사이트 형식: {website}")
        
        return {
            'is_valid': len(valid_websites) > 0,
            'valid_count': len(valid_websites),
            'invalid_count': len(invalid_websites),
            'valid_websites': valid_websites,
            'invalid_websites': invalid_websites,
            'errors': errors,
            'success_rate': len(valid_websites) / len(websites) if websites else 0
        }
    
    def _check_phone_pattern(self, phone: str) -> bool:
        """전화번호 패턴 검사"""
        for pattern in self.validation_rules['phone_number']['patterns']:
            if re.match(pattern, phone):
                return True
        return False
    
    def _check_email_pattern(self, email: str) -> bool:
        """이메일 패턴 검사"""
        pattern = self.validation_rules['email']['pattern']
        return re.match(pattern, email) is not None
    
    def _check_website_pattern(self, website: str) -> bool:
        """웹사이트 패턴 검사"""
        if not website:
            return False
        
        # 기본 URL 형식 검사
        if not any(website.startswith(prefix) for prefix in ['http://', 'https://', 'www.']):
            return False
        
        # 도메인 형식 검사
        if '.' not in website:
            return False
        
        return True
    
    def _validate_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """일관성 검증"""
        consistency_results = {
            'organization_consistency': {},
            'contact_consistency': {},
            'overall_consistency_score': 0.0
        }
        
        try:
            # 조직 정보 일관성 검사
            org_consistency = self._check_organization_consistency(data)
            consistency_results['organization_consistency'] = org_consistency
            
            # 연락처 정보 일관성 검사
            contact_consistency = self._check_contact_consistency(data)
            consistency_results['contact_consistency'] = contact_consistency
            
            # 전체 일관성 점수
            consistency_scores = [
                org_consistency.get('score', 0.0),
                contact_consistency.get('score', 0.0)
            ]
            consistency_results['overall_consistency_score'] = sum(consistency_scores) / len(consistency_scores)
            
        except Exception as e:
            logger.error(f"일관성 검증 중 오류: {str(e)}")
        
        return consistency_results
    
    def _check_organization_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """조직 정보 일관성 검사"""
        org_name = data.get('organization_name', '')
        address = data.get('address', '')
        
        consistency_issues = []
        score = 1.0
        
        # 조직명과 주소의 지역 일치성 검사
        if org_name and address:
            # 간단한 지역 일치성 검사 (실제로는 더 복잡한 로직 필요)
            if '서울' in org_name and '서울' not in address:
                consistency_issues.append("조직명에 서울이 포함되어 있지만 주소에는 없습니다.")
                score -= 0.2
        
        return {
            'score': max(0.0, score),
            'issues': consistency_issues,
            'is_consistent': len(consistency_issues) == 0
        }
    
    def _check_contact_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """연락처 정보 일관성 검사"""
        phone_numbers = data.get('phone_numbers', [])
        fax_numbers = data.get('fax_numbers', [])
        
        consistency_issues = []
        score = 1.0
        
        # 전화번호와 팩스번호의 지역번호 일치성 검사
        if phone_numbers and fax_numbers:
            phone_area_codes = [phone.split('-')[0] for phone in phone_numbers if '-' in phone]
            fax_area_codes = [fax.split('-')[0] for fax in fax_numbers if '-' in fax]
            
            if phone_area_codes and fax_area_codes:
                if not any(phone_code in fax_area_codes for phone_code in phone_area_codes):
                    consistency_issues.append("전화번호와 팩스번호의 지역번호가 일치하지 않습니다.")
                    score -= 0.3
        
        return {
            'score': max(0.0, score),
            'issues': consistency_issues,
            'is_consistent': len(consistency_issues) == 0
        }
    
    def _validate_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """완전성 검증"""
        required_fields = ['organization_name', 'phone_numbers', 'address']
        optional_fields = ['fax_numbers', 'email_addresses', 'websites']
        
        completeness_results = {
            'required_fields_status': {},
            'optional_fields_status': {},
            'completeness_score': 0.0,
            'missing_fields': [],
            'recommendations': []
        }
        
        try:
            # 필수 필드 검사
            required_score = 0
            for field in required_fields:
                if field in data and data[field]:
                    completeness_results['required_fields_status'][field] = 'present'
                    required_score += 1
                else:
                    completeness_results['required_fields_status'][field] = 'missing'
                    completeness_results['missing_fields'].append(field)
                    completeness_results['recommendations'].append(f"{field} 정보가 필요합니다.")
            
            # 선택 필드 검사
            optional_score = 0
            for field in optional_fields:
                if field in data and data[field]:
                    completeness_results['optional_fields_status'][field] = 'present'
                    optional_score += 1
                else:
                    completeness_results['optional_fields_status'][field] = 'missing'
            
            # 완전성 점수 계산 (필수 필드 80%, 선택 필드 20%)
            required_percentage = required_score / len(required_fields)
            optional_percentage = optional_score / len(optional_fields)
            completeness_results['completeness_score'] = (required_percentage * 0.8) + (optional_percentage * 0.2)
            
        except Exception as e:
            logger.error(f"완전성 검증 중 오류: {str(e)}")
        
        return completeness_results
    
    def _validate_with_ai(self, data: Dict[str, Any], validation_type: str) -> Dict[str, Any]:
        """AI 기반 종합 검증"""
        try:
            prompt = f"""
다음 데이터의 품질을 종합적으로 검증해주세요:

데이터: {json.dumps(data, ensure_ascii=False, indent=2)}
검증 유형: {validation_type}

다음 관점에서 분석해주세요:
1. 데이터의 신뢰성
2. 실제 존재 가능성
3. 정보의 일관성
4. 데이터 품질 등급

검증 결과를 JSON 형식으로 제공해주세요:
{{
    "reliability_score": 0.85,
    "existence_probability": 0.9,
    "consistency_score": 0.8,
    "quality_grade": "A",
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1", "약점2"],
    "improvement_suggestions": ["개선사항1", "개선사항2"],
    "risk_factors": ["위험요소1", "위험요소2"],
    "confidence": 0.8
}}
"""
            
            response = self.query_gemini(prompt)
            if response['success']:
                try:
                    return json.loads(response['content'])
                except json.JSONDecodeError:
                    return {'confidence': 0.0, 'quality_grade': 'F'}
            else:
                return {'confidence': 0.0, 'quality_grade': 'F'}
                
        except Exception as e:
            logger.error(f"AI 검증 중 오류: {str(e)}")
            return {'confidence': 0.0, 'quality_grade': 'F'}
    
    def _integrate_validation_results(self, format_validation: Dict[str, Any], 
                                    consistency_validation: Dict[str, Any],
                                    completeness_validation: Dict[str, Any],
                                    ai_validation: Dict[str, Any]) -> Dict[str, Any]:
        """검증 결과 통합"""
        
        # 각 검증 점수 수집
        format_score = format_validation.get('overall_format_score', 0.0)
        consistency_score = consistency_validation.get('overall_consistency_score', 0.0)
        completeness_score = completeness_validation.get('completeness_score', 0.0)
        ai_reliability = ai_validation.get('reliability_score', 0.0)
        ai_confidence = ai_validation.get('confidence', 0.0)
        
        # 가중 평균으로 전체 점수 계산
        weights = {
            'format': 0.25,
            'consistency': 0.2,
            'completeness': 0.25,
            'ai_reliability': 0.2,
            'ai_confidence': 0.1
        }
        
        overall_score = (
            format_score * weights['format'] +
            consistency_score * weights['consistency'] +
            completeness_score * weights['completeness'] +
            ai_reliability * weights['ai_reliability'] +
            ai_confidence * weights['ai_confidence']
        )
        
        # 품질 등급 결정
        quality_grade = self._determine_quality_grade(overall_score)
        
        # 통합 결과
        integrated_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'quality_grade': quality_grade,
            'detailed_scores': {
                'format_score': format_score,
                'consistency_score': consistency_score,
                'completeness_score': completeness_score,
                'ai_reliability_score': ai_reliability,
                'ai_confidence_score': ai_confidence
            },
            'format_validation': format_validation,
            'consistency_validation': consistency_validation,
            'completeness_validation': completeness_validation,
            'ai_validation': ai_validation,
            'overall_confidence': overall_score,
            'summary': self._generate_validation_summary(overall_score, quality_grade),
            'recommendations': self._generate_recommendations(
                format_validation, consistency_validation, 
                completeness_validation, ai_validation
            )
        }
        
        return integrated_results
    
    def _determine_quality_grade(self, score: float) -> str:
        """품질 등급 결정"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _generate_validation_summary(self, score: float, grade: str) -> str:
        """검증 요약 생성"""
        if grade == 'A':
            return f"매우 우수한 데이터 품질입니다. (점수: {score:.2f})"
        elif grade == 'B':
            return f"우수한 데이터 품질입니다. (점수: {score:.2f})"
        elif grade == 'C':
            return f"보통 수준의 데이터 품질입니다. (점수: {score:.2f})"
        elif grade == 'D':
            return f"미흡한 데이터 품질입니다. 개선이 필요합니다. (점수: {score:.2f})"
        else:
            return f"불량한 데이터 품질입니다. 대폭적인 개선이 필요합니다. (점수: {score:.2f})"
    
    def _generate_recommendations(self, format_val: Dict, consistency_val: Dict, 
                                completeness_val: Dict, ai_val: Dict) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 형식 검증 기반 권장사항
        if format_val.get('overall_format_score', 0) < 0.8:
            recommendations.append("연락처 정보의 형식을 표준화해주세요.")
        
        # 완전성 검증 기반 권장사항
        missing_fields = completeness_val.get('missing_fields', [])
        if missing_fields:
            recommendations.append(f"누락된 필드를 보완해주세요: {', '.join(missing_fields)}")
        
        # AI 검증 기반 권장사항
        ai_suggestions = ai_val.get('improvement_suggestions', [])
        recommendations.extend(ai_suggestions)
        
        return recommendations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """검증 통계 반환"""
        stats = self.get_performance_stats()
        return {
            'total_validations': stats.get('total_tasks', 0),
            'successful_validations': stats.get('successful_tasks', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'average_confidence': stats.get('average_confidence', 0.0),
            'average_validation_time': stats.get('average_duration', 0.0)
        } 
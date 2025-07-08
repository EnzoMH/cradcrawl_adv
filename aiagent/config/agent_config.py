#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 설정 및 구성
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import os

class AgentType(Enum):
    """에이전트 타입"""
    HOMEPAGE_SEARCH = "homepage_search"
    CONTACT_EXTRACTION = "contact_extraction"
    DATA_VALIDATION = "data_validation"
    OPTIMIZER = "optimizer"

@dataclass
class AgentConfig:
    """개별 에이전트 설정"""
    name: str
    agent_type: AgentType
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: float = 60.0
    confidence_threshold: float = 0.5
    resource_limit: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

class ConfigPresets:
    """설정 프리셋"""
    
    @staticmethod
    def get_development_config() -> Dict[str, AgentConfig]:
        """개발 환경 설정"""
        return {
            'homepage_agent': AgentConfig(
                name='homepage_agent',
                agent_type=AgentType.HOMEPAGE_SEARCH,
                max_retries=2,
                timeout_seconds=30.0,
                confidence_threshold=0.4
            ),
            'contact_agent': AgentConfig(
                name='contact_agent',
                agent_type=AgentType.CONTACT_EXTRACTION,
                max_retries=3,
                timeout_seconds=45.0,
                confidence_threshold=0.5
            ),
            'validation_agent': AgentConfig(
                name='validation_agent',
                agent_type=AgentType.DATA_VALIDATION,
                max_retries=2,
                timeout_seconds=60.0,
                confidence_threshold=0.6
            ),
            'optimizer_agent': AgentConfig(
                name='optimizer_agent',
                agent_type=AgentType.OPTIMIZER,
                max_retries=1,
                timeout_seconds=120.0,
                confidence_threshold=0.7
            )
        }
    
    @staticmethod
    def get_production_config() -> Dict[str, AgentConfig]:
        """운영 환경 설정"""
        return {
            'homepage_agent': AgentConfig(
                name='homepage_agent',
                agent_type=AgentType.HOMEPAGE_SEARCH,
                max_retries=3,
                timeout_seconds=60.0,
                confidence_threshold=0.6
            ),
            'contact_agent': AgentConfig(
                name='contact_agent',
                agent_type=AgentType.CONTACT_EXTRACTION,
                max_retries=3,
                timeout_seconds=60.0,
                confidence_threshold=0.7
            ),
            'validation_agent': AgentConfig(
                name='validation_agent',
                agent_type=AgentType.DATA_VALIDATION,
                max_retries=3,
                timeout_seconds=90.0,
                confidence_threshold=0.8
            ),
            'optimizer_agent': AgentConfig(
                name='optimizer_agent',
                agent_type=AgentType.OPTIMIZER,
                max_retries=2,
                timeout_seconds=180.0,
                confidence_threshold=0.8
            )
        }
    
    @staticmethod
    def get_high_performance_config() -> Dict[str, AgentConfig]:
        """고성능 설정"""
        return {
            'homepage_agent': AgentConfig(
                name='homepage_agent',
                agent_type=AgentType.HOMEPAGE_SEARCH,
                max_retries=5,
                timeout_seconds=120.0,
                confidence_threshold=0.8,
                resource_limit={'max_workers': 8}
            ),
            'contact_agent': AgentConfig(
                name='contact_agent',
                agent_type=AgentType.CONTACT_EXTRACTION,
                max_retries=5,
                timeout_seconds=90.0,
                confidence_threshold=0.8,
                resource_limit={'max_workers': 6}
            ),
            'validation_agent': AgentConfig(
                name='validation_agent',
                agent_type=AgentType.DATA_VALIDATION,
                max_retries=3,
                timeout_seconds=120.0,
                confidence_threshold=0.9
            ),
            'optimizer_agent': AgentConfig(
                name='optimizer_agent',
                agent_type=AgentType.OPTIMIZER,
                max_retries=3,
                timeout_seconds=300.0,
                confidence_threshold=0.9
            )
        } 
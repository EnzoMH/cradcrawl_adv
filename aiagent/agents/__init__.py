#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 패키지
각 전문 영역별 에이전트들을 제공합니다.
"""

from .homepage_agent import HomepageAgent
from .contact_agent import ContactAgent
from .validation_agent import ValidationAgent
from .optimizer_agent import OptimizerAgent

__all__ = [
    'HomepageAgent',
    'ContactAgent', 
    'ValidationAgent',
    'OptimizerAgent'
]

# 에이전트 레지스트리
AGENT_REGISTRY = {
    'homepage_agent': HomepageAgent,
    'contact_agent': ContactAgent,
    'validation_agent': ValidationAgent,
    'optimizer_agent': OptimizerAgent
}

def get_agent_class(agent_name: str):
    """에이전트 이름으로 클래스 반환"""
    return AGENT_REGISTRY.get(agent_name)

def get_available_agents():
    """사용 가능한 에이전트 목록 반환"""
    return list(AGENT_REGISTRY.keys())

def create_agent(agent_name: str, config=None):
    """에이전트 인스턴스 생성"""
    agent_class = get_agent_class(agent_name)
    if agent_class:
        return agent_class(config)
    else:
        raise ValueError(f"Unknown agent: {agent_name}") 
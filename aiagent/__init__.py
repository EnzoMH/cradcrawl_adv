#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 에이전트 시스템 - Gemini 기반 멀티 에이전트 크롤링 시스템
각 Task마다 AI가 결정을 내리는 고도화된 자동화 시스템

Author: Advanced Crawling Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Advanced Crawling Team"
__description__ = "AI 에이전트 시스템 - Gemini 기반 멀티 에이전트 크롤링 시스템"

# 메인 시스템 import
from .core.agent_system import AIAgentSystem
from .core.coordinator import AgentCoordinator
from .config.agent_config import AgentConfig, ConfigPresets

# 개별 에이전트들
from .agents.homepage_agent import HomepageAgent
from .agents.contact_agent import ContactAgent
from .agents.validation_agent import ValidationAgent
from .agents.optimizer_agent import OptimizerAgent

# 유틸리티
from .utils.gemini_client import GeminiClient
from .metrics.performance import PerformanceTracker

__all__ = [
    'AIAgentSystem',
    'AgentCoordinator',
    'AgentConfig',
    'ConfigPresets',
    'HomepageAgent',
    'ContactAgent',
    'ValidationAgent',
    'OptimizerAgent',
    'GeminiClient',
    'PerformanceTracker'
] 
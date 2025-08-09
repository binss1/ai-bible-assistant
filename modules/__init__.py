# -*- coding: utf-8 -*-
"""
AI Bible Assistant 모듈 패키지
"""

__version__ = "1.0.0"
__author__ = "AI Bible Assistant Team"
__description__ = "성경 말씀 기반 AI 상담 챗봇"

from .bible_manager import bible_manager
from .claude_api import claude_api
from .conversation_manager import conversation_manager
from .kakao_formatter import response_builder, request_parser

__all__ = [
    'bible_manager',
    'claude_api', 
    'conversation_manager',
    'response_builder',
    'request_parser'
]

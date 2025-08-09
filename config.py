# -*- coding: utf-8 -*-
"""
AI Bible Assistant 설정 관리
환경변수와 설정값들을 중앙에서 관리합니다.
"""

import os
from pathlib import Path

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent

class Config:
    """애플리케이션 설정 클래스"""
    
    # 기본 설정
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 8080))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Claude API 설정
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')  # 가장 저렴한 모델
    CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', 800))
    CLAUDE_TEMPERATURE = float(os.getenv('CLAUDE_TEMPERATURE', 0.7))
    
    # MongoDB 설정
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'bible_assistant')
    CONVERSATIONS_COLLECTION = 'conversations'
    ANALYTICS_COLLECTION = 'analytics'
    
    # 성경 임베딩 파일 설정
    BIBLE_EMBEDDINGS_URL = os.getenv('BIBLE_EMBEDDINGS_URL')
    BIBLE_EMBEDDINGS_PATH = os.path.join(BASE_DIR, 'bible_embeddings.json')
    BIBLE_EMBEDDINGS_LOCAL = os.path.join(BASE_DIR, 'bible_embeddings_local.json.gz')  # 로컬 압축 파일
    
    # 카카오 챗봇 설정
    KAKAO_WEBHOOK_URL = '/webhook'
    KAKAO_TIMEOUT = 4.5  # 카카오 타임아웃보다 약간 짧게
    
    # 성경 검색 설정
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.3))
    MAX_BIBLE_RESULTS = int(os.getenv('MAX_BIBLE_RESULTS', 5))
    
    # 대화 관리 설정
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', 5))
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', 24))
    
    # 메모리 관리 설정 (Railway 512MB 제한)
    MAX_MEMORY_MB = int(os.getenv('MAX_MEMORY_MB', 410))  # 410MB로 여유분 증가
    CACHE_SIZE_LIMIT = int(os.getenv('CACHE_SIZE_LIMIT', 100))
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(BASE_DIR, 'app.log')
    
    # 모니터링 설정
    HEALTH_CHECK_URL = '/health'
    STATUS_CHECK_URL = '/status'
    METRICS_URL = '/metrics'
    
    # 고민 카테고리 설정
    CATEGORIES = [
        '관계',     # 가족, 친구, 연인, 직장 관계
        '진로',     # 진로, 직업, 학업
        '신앙',     # 신앙, 기도, 교회
        '감정',     # 우울, 불안, 분노, 기쁨
        '윤리',     # 도덕적 고민, 선택
        '건강',     # 신체적, 정신적 건강
        '경제'      # 돈, 재정 관리
    ]
    
    # 응답 템플릿 설정
    WELCOME_MESSAGE = """🙏 안녕하세요! AI Bible Assistant입니다.

성경 말씀을 통한 상담을 도와드리겠습니다.
어떤 고민이나 질문이 있으시면 편안하게 말씀해 주세요."""

    FALLBACK_MESSAGE = """죄송합니다. 잘 이해하지 못했습니다.

성경 말씀을 통한 상담을 위해 구체적인 고민이나 질문을 말씀해 주시면 더 나은 답변을 드릴 수 있습니다.

예: "가족과의 갈등으로 힘들어요", "진로 선택에 고민이 있어요" 등"""

    ERROR_MESSAGE = """🙏 죄송합니다. 현재 일시적인 문제가 발생했습니다.

잠시 후 다시 시도해 주시거나, 간단한 질문으로 다시 말씀해 주세요."""

    @classmethod
    def validate_config(cls):
        """필수 환경변수 검증"""
        required_vars = [
            'CLAUDE_API_KEY',
            'MONGODB_URI'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        return True

    @classmethod
    def get_bible_embeddings_source(cls):
        """성경 임베딩 파일 소스 결정 (로컬 파일 최우선)"""
        # 1순위: 로컬 압축 파일 (가장 신뢰성 높음)
        if os.path.exists(cls.BIBLE_EMBEDDINGS_LOCAL):
            return cls.BIBLE_EMBEDDINGS_LOCAL
        
        # 2순위: 로컬 비압축 파일
        if os.path.exists(cls.BIBLE_EMBEDDINGS_PATH):
            return cls.BIBLE_EMBEDDINGS_PATH
        
        # 3순위: 원격 URL
        if cls.BIBLE_EMBEDDINGS_URL:
            return cls.BIBLE_EMBEDDINGS_URL
        
        raise ValueError("성경 임베딩 파일을 찾을 수 없습니다. 로컬 파일이나 URL을 설정해주세요.")

# 전역 설정 인스턴스
config = Config()

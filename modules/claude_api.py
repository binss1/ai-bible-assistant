# -*- coding: utf-8 -*-
"""
Claude API 연동 모듈
Claude AI와의 상호작용을 담당합니다.
"""

import logging
from typing import Optional, List, Dict, Any
import anthropic
from anthropic import Anthropic
import json
import time

from config import config
from utils import ResponseTimer, global_cache, log_function_call
from utils import TextProcessor

logger = logging.getLogger(__name__)

class PromptBuilder:
    """AI 상담용 프롬프트 생성기"""
    
    @staticmethod
    def build_counseling_prompt(user_message: str, bible_verses: List[Dict], 
                              conversation_history: List[Dict] = None,
                              user_categories: List[str] = None) -> str:
        """
        성경 기반 상담용 프롬프트를 생성합니다.
        
        Args:
            user_message: 사용자 메시지
            bible_verses: 관련 성경 구절들
            conversation_history: 이전 대화 기록
            user_categories: 사용자 고민 카테고리
            
        Returns:
            str: 완성된 프롬프트
        """
        
        # 기본 역할 설정
        base_prompt = """당신은 성경 말씀을 기반으로 상담을 제공하는 AI Bible Assistant입니다.

역할과 원칙:
1. 성경 말씀을 근거로 하여 따뜻하고 위로가 되는 상담을 제공합니다
2. 판단하기보다는 격려하고 희망을 주는 방향으로 응답합니다
3. 구체적인 성경 구절을 인용하여 답변의 근거를 제시합니다
4. 한국어로 자연스럽고 친근하게 대화합니다
5. 상담자의 상황에 맞는 실용적인 조언도 함께 제공합니다

응답 형식:
- 공감과 위로의 말로 시작
- 관련 성경 구절 1-2개 인용 (구절과 출처 명시)
- 성경 말씀에 기반한 해석과 적용
- 구체적인 실천 방안이나 기도 제안
- 따뜻한 격려의 말로 마무리

주의사항:
- 의학적, 법적 조언은 피하고 전문가 상담을 권유
- 복잡한 신학적 논쟁은 피하고 실용적 위로에 집중
- 절대적 판단보다는 하나님의 사랑과 은혜 강조"""

        prompt_parts = [base_prompt]
        
        # 사용자 카테고리 정보 추가
        if user_categories:
            category_text = "사용자의 고민 영역: " + ", ".join(user_categories)
            prompt_parts.append(category_text)
        
        # 관련 성경 구절 정보 추가
        if bible_verses:
            prompt_parts.append("\n관련 성경 구절들:")
            for i, verse in enumerate(bible_verses[:3], 1):  # 최대 3개만 사용
                reference = verse.get('reference', f"{verse.get('book', '')} {verse.get('chapter', '')}:{verse.get('verse', '')}")
                text = verse.get('text', '')
                similarity = verse.get('similarity_score', 0)
                prompt_parts.append(f"{i}. {reference} - \"{text}\" (관련도: {similarity:.2f})")
        
        # 대화 기록 추가 (최근 2개만)
        if conversation_history:
            prompt_parts.append("\n최근 대화 맥락:")
            for msg in conversation_history[-2:]:
                if msg.get('role') == 'user':
                    prompt_parts.append(f"사용자: {msg.get('content', '')}")
                elif msg.get('role') == 'assistant':
                    prompt_parts.append(f"상담사: {msg.get('content', '')}")
        
        # 현재 사용자 메시지
        prompt_parts.append(f"\n현재 사용자 메시지: {user_message}")
        
        # 응답 요청
        prompt_parts.append("""
위의 내용을 바탕으로 성경 말씀에 근거한 따뜻한 상담을 제공해 주세요. 
응답은 한국어로 작성하며, 반드시 구체적인 성경 구절(책명, 장, 절)을 포함해야 합니다.
500자 내외로 간결하지만 의미 있게 답변해 주세요.""")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_welcome_prompt() -> str:
        """웰컴 메시지용 간단한 프롬프트"""
        return """사용자가 처음 인사했습니다. AI Bible Assistant로서 따뜻하게 환영하고, 
성경 말씀을 통한 상담 서비스를 간단히 소개해 주세요. 
100자 내외로 간결하게 응답해 주세요."""
    
    @staticmethod
    def build_fallback_prompt(user_message: str) -> str:
        """이해하지 못한 경우의 프롬프트"""
        return f"""사용자가 다음과 같이 말했습니다: "{user_message}"

이 메시지를 잘 이해하지 못했습니다. AI Bible Assistant로서 정중하게 다시 
구체적인 고민이나 질문을 부탁드리는 응답을 해주세요. 
예시를 들어주시면 더 좋습니다. 150자 내외로 응답해 주세요."""

class ClaudeAPI:
    """Claude API 클라이언트 클래스"""
    
    def __init__(self):
        self.client: Optional[Anthropic] = None
        self.api_key = config.CLAUDE_API_KEY
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS
        self.temperature = config.CLAUDE_TEMPERATURE
        
        # API 호출 통계
        self.api_calls_count = 0
        self.total_tokens_used = 0
        self.total_response_time = 0.0
        
        logger.info(f"ClaudeAPI 초기화 - 모델: {self.model}")
    
    def _initialize_client(self) -> bool:
        """Claude 클라이언트 초기화"""
        if self.client is not None:
            return True
        
        try:
            if not self.api_key:
                logger.error("Claude API 키가 설정되지 않았습니다")
                return False
            
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Claude 클라이언트 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"Claude 클라이언트 초기화 실패: {str(e)}")
            return False
    
    @ResponseTimer.timeout_handler(config.KAKAO_TIMEOUT * 0.8)  # 카카오 타임아웃보다 짧게
    def generate_response(self, prompt: str, use_cache: bool = True) -> Optional[str]:
        """
        Claude API를 호출하여 응답을 생성합니다.
        
        Args:
            prompt: 입력 프롬프트
            use_cache: 캐시 사용 여부
            
        Returns:
            Optional[str]: 생성된 응답 (실패시 None)
        """
        log_function_call("generate_response", prompt_length=len(prompt), use_cache=use_cache)
        
        if not self._initialize_client():
            return None
        
        # 캐시 확인
        cache_key = f"claude_response_{hash(prompt)}"
        if use_cache:
            cached_response = global_cache.get(cache_key)
            if cached_response:
                logger.info("캐시에서 응답 반환")
                return cached_response
        
        start_time = time.time()
        
        try:
            # 프롬프트 길이 체크 및 조정
            if len(prompt) > 8000:  # 대략적인 토큰 제한
                prompt = TextProcessor.truncate_text(prompt, 8000)
                logger.warning("프롬프트가 길어서 잘랐습니다")
            
            # Claude API 호출
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 응답 추출
            if response.content and len(response.content) > 0:
                generated_text = response.content[0].text.strip()
                
                # 통계 업데이트
                self.api_calls_count += 1
                if hasattr(response, 'usage'):
                    self.total_tokens_used += getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)
                
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                logger.info(f"Claude API 호출 성공 ({response_time:.2f}초)")
                
                # 캐시에 저장 (메모리가 충분한 경우에만)
                from utils import MemoryManager
                if use_cache and not MemoryManager.is_memory_critical():
                    global_cache.set(cache_key, generated_text)
                
                return generated_text
            else:
                logger.error("Claude API에서 빈 응답을 받았습니다")
                return None
                
        except anthropic.APITimeoutError:
            logger.error("Claude API 타임아웃")
            return None
            
        except anthropic.RateLimitError:
            logger.error("Claude API 요청 한도 초과")
            return None
            
        except anthropic.APIConnectionError:
            logger.error("Claude API 연결 오류")
            return None
            
        except Exception as e:
            logger.error(f"Claude API 호출 오류: {str(e)}")
            return None
    
    def generate_counseling_response(self, user_message: str, bible_verses: List[Dict] = None,
                                   conversation_history: List[Dict] = None,
                                   user_categories: List[str] = None) -> Optional[str]:
        """
        성경 기반 상담 응답을 생성합니다.
        
        Args:
            user_message: 사용자 메시지
            bible_verses: 관련 성경 구절들
            conversation_history: 대화 기록
            user_categories: 고민 카테고리
            
        Returns:
            Optional[str]: 상담 응답
        """
        prompt = PromptBuilder.build_counseling_prompt(
            user_message=user_message,
            bible_verses=bible_verses or [],
            conversation_history=conversation_history or [],
            user_categories=user_categories or []
        )
        
        return self.generate_response(prompt, use_cache=True)
    
    def generate_welcome_response(self) -> Optional[str]:
        """웰컴 메시지 생성"""
        prompt = PromptBuilder.build_welcome_prompt()
        return self.generate_response(prompt, use_cache=True)
    
    def generate_fallback_response(self, user_message: str) -> Optional[str]:
        """폴백 메시지 생성"""
        prompt = PromptBuilder.build_fallback_prompt(user_message)
        return self.generate_response(prompt, use_cache=False)  # 폴백은 캐시 안함
    
    def get_stats(self) -> Dict[str, Any]:
        """API 사용 통계 반환"""
        avg_response_time = (
            self.total_response_time / self.api_calls_count 
            if self.api_calls_count > 0 else 0
        )
        
        return {
            'api_calls_count': self.api_calls_count,
            'total_tokens_used': self.total_tokens_used,
            'avg_response_time_sec': round(avg_response_time, 2),
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'is_initialized': self.client is not None
        }
    
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            test_response = self.generate_response("테스트 메시지입니다. 간단히 '연결 확인'이라고만 답해주세요.", use_cache=False)
            return test_response is not None
        except Exception as e:
            logger.error(f"API 연결 테스트 실패: {str(e)}")
            return False

# 전역 Claude API 인스턴스
claude_api = ClaudeAPI()

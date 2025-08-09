# -*- coding: utf-8 -*-
"""
카카오톡 응답 포맷터 모듈
카카오톡 챗봇 API 규격에 맞는 응답을 생성합니다.
"""

import logging
from typing import Dict, List, Any, Optional
import json
import re

from config import config
from utils import TextProcessor, DateTimeHelper

logger = logging.getLogger(__name__)

class KakaoResponseBuilder:
    """카카오톡 응답 생성기"""
    
    @staticmethod
    def create_simple_text(text: str) -> Dict[str, Any]:
        """
        간단한 텍스트 응답 생성
        
        Args:
            text: 응답 텍스트
            
        Returns:
            Dict: 카카오톡 응답 형식
        """
        # 텍스트 길이 제한 (카카오톡 제한: 400자)
        if len(text) > 380:
            text = TextProcessor.truncate_text(text, 380)
        
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": text
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def create_counseling_response(ai_response: str, bible_verses: List[Dict] = None,
                                 show_references: bool = True) -> Dict[str, Any]:
        """
        성경 기반 상담 응답 생성
        
        Args:
            ai_response: AI 생성 응답
            bible_verses: 관련 성경 구절들
            show_references: 성경 구절 참조 표시 여부
            
        Returns:
            Dict: 포맷된 카카오톡 응답
        """
        # 메인 응답 텍스트 정리
        main_text = KakaoResponseBuilder._format_main_response(ai_response)
        
        outputs = []
        
        # 메인 응답 추가
        outputs.append({
            "simpleText": {
                "text": main_text
            }
        })
        
        # 성경 구절 참조 추가 (선택적)
        if show_references and bible_verses:
            reference_text = KakaoResponseBuilder._format_bible_references(bible_verses)
            if reference_text:
                outputs.append({
                    "simpleText": {
                        "text": reference_text
                    }
                })
        
        return {
            "version": "2.0",
            "template": {
                "outputs": outputs
            }
        }
    
    @staticmethod
    def create_card_response(title: str, description: str, 
                           buttons: List[Dict] = None) -> Dict[str, Any]:
        """
        카드 형태 응답 생성
        
        Args:
            title: 카드 제목
            description: 카드 설명
            buttons: 버튼 리스트
            
        Returns:
            Dict: 카드 응답 형식
        """
        card_content = {
            "title": title,
            "description": description
        }
        
        if buttons:
            card_content["buttons"] = buttons
        
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "basicCard": card_content
                    }
                ]
            }
        }
    
    @staticmethod
    def create_quick_replies_response(text: str, quick_replies: List[str]) -> Dict[str, Any]:
        """
        빠른 답장 버튼이 포함된 응답 생성
        
        Args:
            text: 메인 텍스트
            quick_replies: 빠른 답장 옵션 리스트
            
        Returns:
            Dict: 빠른 답장 포함 응답
        """
        quick_reply_items = []
        for reply in quick_replies[:10]:  # 최대 10개
            quick_reply_items.append({
                "label": reply,
                "action": "message",
                "messageText": reply
            })
        
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": text
                        }
                    }
                ],
                "quickReplies": quick_reply_items
            }
        }
    
    @staticmethod
    def create_error_response(error_message: str = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        if not error_message:
            error_message = config.ERROR_MESSAGE
        
        return KakaoResponseBuilder.create_simple_text(error_message)
    
    @staticmethod
    def create_welcome_response() -> Dict[str, Any]:
        """웰컴 메시지 응답 생성"""
        quick_replies = [
            "가족 문제로 고민이에요",
            "진로에 대해 고민 중입니다",
            "기도 부탁드려요",
            "오늘의 말씀"
        ]
        
        return KakaoResponseBuilder.create_quick_replies_response(
            config.WELCOME_MESSAGE,
            quick_replies
        )
    
    @staticmethod
    def create_fallback_response(user_message: str = "") -> Dict[str, Any]:
        """폴백 응답 생성"""
        base_message = config.FALLBACK_MESSAGE
        
        # 사용자 메시지에 따른 맞춤형 가이드
        suggestions = KakaoResponseBuilder._get_contextual_suggestions(user_message)
        
        if suggestions:
            return KakaoResponseBuilder.create_quick_replies_response(base_message, suggestions)
        else:
            return KakaoResponseBuilder.create_simple_text(base_message)
    
    @staticmethod
    def _format_main_response(ai_response: str) -> str:
        """AI 응답을 카카오톡에 맞게 포맷팅"""
        # 기본 정리
        text = TextProcessor.clean_text(ai_response)
        
        # 성경 구절 인용 형식 통일
        # 예: "요한복음 3:16" -> "📖 요한복음 3:16"
        text = re.sub(r'([가-힣]+)\s*(\d+):(\d+)', r'📖 \1 \2:\3', text)
        
        # 단락 구분을 위한 줄바꿈 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 카카오톡 텍스트 길이 제한
        if len(text) > 380:
            text = TextProcessor.truncate_text(text, 380)
        
        return text
    
    @staticmethod
    def _format_bible_references(bible_verses: List[Dict]) -> str:
        """성경 구절 참조 포맷팅"""
        if not bible_verses:
            return ""
        
        reference_parts = ["📚 참고 구절:"]
        
        for i, verse in enumerate(bible_verses[:3], 1):  # 최대 3개
            reference = verse.get('reference', '')
            text = verse.get('text', '')
            
            if reference and text:
                # 구절 텍스트가 너무 길면 줄임
                if len(text) > 100:
                    text = TextProcessor.truncate_text(text, 100)
                
                reference_parts.append(f"{i}. {reference}")
                reference_parts.append(f"   \"{text}\"")
        
        result = "\n".join(reference_parts)
        
        # 전체 길이 제한
        if len(result) > 300:
            result = TextProcessor.truncate_text(result, 300)
        
        return result
    
    @staticmethod
    def _get_contextual_suggestions(user_message: str) -> List[str]:
        """사용자 메시지 맥락에 따른 제안 생성"""
        message_lower = user_message.lower()
        suggestions = []
        
        # 키워드 기반 제안
        suggestion_map = {
            '가족': ["가족과의 갈등으로 힘들어요", "부모님과의 관계 개선"],
            '친구': ["친구 관계에 고민이 있어요", "친구와의 갈등 해결"],
            '직장': ["직장에서의 스트레스", "상사와의 관계"],
            '결혼': ["결혼에 대한 고민", "배우자와의 관계"],
            '진로': ["진로 선택의 어려움", "취업 스트레스"],
            '돈': ["경제적 어려움", "재정 관리 고민"],
            '건강': ["건강 문제로 걱정", "몸과 마음이 지쳐요"],
            '신앙': ["믿음에 대한 의문", "기도 응답이 없어요"],
            '우울': ["마음이 우울해요", "희망을 잃었어요"],
            '불안': ["불안하고 걱정돼요", "미래가 두려워요"]
        }
        
        for keyword, related_suggestions in suggestion_map.items():
            if keyword in message_lower:
                suggestions.extend(related_suggestions)
                break
        
        # 기본 제안들 추가
        if not suggestions:
            suggestions = [
                "가족 문제로 고민이에요",
                "진로에 대해 고민 중입니다",
                "인간관계가 힘들어요",
                "기도 부탁드려요"
            ]
        
        return suggestions[:4]  # 최대 4개

class KakaoRequestParser:
    """카카오톡 요청 파싱"""
    
    @staticmethod
    def parse_user_request(request_data: Dict) -> Dict[str, Any]:
        """
        카카오톡 요청을 파싱하여 필요한 정보 추출
        
        Args:
            request_data: 카카오톡 요청 데이터
            
        Returns:
            Dict: 파싱된 사용자 정보
        """
        try:
            # 사용자 발화 추출
            user_utterance = request_data.get('userRequest', {}).get('utterance', '')
            
            # 사용자 정보 추출
            user = request_data.get('userRequest', {}).get('user', {})
            user_id = user.get('id', '')
            
            # 블록 정보 추출
            bot = request_data.get('bot', {})
            
            # 액션 정보 추출
            action = request_data.get('action', {})
            action_id = action.get('id', '')
            action_name = action.get('name', '')
            
            # 파라미터 추출
            params = action.get('params', {})
            
            return {
                'user_message': user_utterance,
                'user_id': user_id,
                'action_id': action_id,
                'action_name': action_name,
                'parameters': params,
                'bot_id': bot.get('id', ''),
                'timestamp': DateTimeHelper.get_kst_now()
            }
            
        except Exception as e:
            logger.error(f"카카오톡 요청 파싱 오류: {str(e)}")
            return {
                'user_message': '',
                'user_id': 'unknown',
                'action_id': '',
                'action_name': '',
                'parameters': {},
                'bot_id': '',
                'timestamp': DateTimeHelper.get_kst_now(),
                'parse_error': str(e)
            }
    
    @staticmethod
    def is_valid_request(request_data: Dict) -> bool:
        """요청 데이터 유효성 검사"""
        try:
            # 필수 필드 확인
            required_fields = ['userRequest', 'bot', 'action']
            for field in required_fields:
                if field not in request_data:
                    return False
            
            # 사용자 메시지 확인
            user_utterance = request_data.get('userRequest', {}).get('utterance', '')
            if not user_utterance.strip():
                return False
            
            return True
            
        except:
            return False

# 전역 포맷터 인스턴스들
response_builder = KakaoResponseBuilder()
request_parser = KakaoRequestParser()

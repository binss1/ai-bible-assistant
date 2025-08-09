# -*- coding: utf-8 -*-
"""
AI Bible Assistant 메인 서버
Flask 웹서버를 통해 카카오톡 챗봇 서비스를 제공합니다.
"""

import logging
import os
import sys
from flask import Flask, request, jsonify
import traceback
from typing import Dict, Any, Optional

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from utils import (
    MemoryManager, ResponseTimer, DateTimeHelper, 
    global_cache, log_function_call, safe_execute
)

# 모듈 임포트
from modules.bible_manager import bible_manager
from modules.claude_api import claude_api
from modules.conversation_manager import conversation_manager
from modules.kakao_formatter import response_builder, request_parser

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 출력을 위해

# 전역 상태 추적
app_status = {
    'startup_time': DateTimeHelper.get_kst_now(),
    'total_requests': 0,
    'successful_responses': 0,
    'error_responses': 0,
    'is_healthy': False
}

def initialize_services():
    """서비스 초기화"""
    logger.info("=== AI Bible Assistant 서비스 초기화 시작 ===")
    
    try:
        # 1. 설정 유효성 검사
        logger.info("1. 설정 유효성 검사")
        config.validate_config()
        logger.info("✓ 설정 유효성 검사 완료")
        
        # 2. 성경 임베딩 로드
        logger.info("2. 성경 임베딩 데이터 확인")
        if bible_manager.is_loaded:
            logger.info("✓ 성경 임베딩 이미 로드됨 (중복 로드 방지)")
        elif bible_manager.load_embeddings():
            logger.info("✓ 성경 임베딩 로드 완료")
        else:
            logger.error("✗ 성경 임베딩 로드 실패")
            return False
        
        # 3. Claude API 연결 테스트
        logger.info("3. Claude API 연결 테스트")
        if claude_api.test_connection():
            logger.info("✓ Claude API 연결 성공")
        else:
            logger.warning("⚠ Claude API 연결 실패 (서비스는 계속 실행)")
        
        # 4. MongoDB 연결 테스트
        logger.info("4. MongoDB 연결 테스트")
        if conversation_manager.test_connection():
            logger.info("✓ MongoDB 연결 성공")
        else:
            logger.warning("⚠ MongoDB 연결 실패 (오프라인 모드로 실행)")
        
        # 5. 메모리 상태 확인
        memory_usage = MemoryManager.get_memory_usage()
        logger.info(f"5. 현재 메모리 사용량: {memory_usage:.1f}MB")
        
        app_status['is_healthy'] = True
        logger.info("=== 서비스 초기화 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Flask 오래된 데코레이터 (중복 방지를 위해 비활성화)
#@app.before_first_request
#def startup():
#    """애플리케이션 시작 시 초기화"""
#    initialize_services()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트 - 실시간 상태 확인"""
    try:
        memory_usage = MemoryManager.get_memory_usage()
        
        # 실시간으로 성경 데이터 상태 확인
        bible_loaded = hasattr(bible_manager, 'verses') and len(bible_manager.verses) > 0
        
        # 전체 서비스 상태 결정
        is_healthy = bible_loaded and (memory_usage < config.MAX_MEMORY_MB)
        
        health_data = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': DateTimeHelper.get_kst_now().isoformat(),
            'memory_usage_mb': round(memory_usage, 1),
            'memory_limit_mb': config.MAX_MEMORY_MB,
            'uptime_seconds': int((DateTimeHelper.get_kst_now() - app_status['startup_time']).total_seconds()),
            'bible_loaded': bible_loaded,
            'total_requests': app_status['total_requests'],
            'app_initialized': app_status.get('is_healthy', False)
        }
        
        # 디버깅 정보 추가
        if bible_loaded:
            health_data['bible_verses_count'] = len(bible_manager.verses)
            health_data['bible_memory_mb'] = round(bible_manager.embeddings_matrix.nbytes / 1024 / 1024, 1) if hasattr(bible_manager, 'embeddings_matrix') and bible_manager.embeddings_matrix is not None else 0
        else:
            # 성경 데이터가 없으면 지금 당장 로드 시도
            logger.warning("헬스체크: 성경 데이터가 로드되지 않음 - 재로드 시도")
            try:
                if bible_manager.load_embeddings():
                    health_data['bible_loaded'] = True
                    health_data['bible_verses_count'] = len(bible_manager.verses)
                    health_data['emergency_reload'] = True
                    is_healthy = True
                    health_data['status'] = 'healthy'
            except Exception as e:
                health_data['reload_error'] = str(e)
        
        status_code = 200 if is_healthy else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': DateTimeHelper.get_kst_now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def status_check():
    """상세 상태 정보"""
    try:
        status_data = {
            'app_status': app_status,
            'bible_stats': bible_manager.get_stats(),
            'claude_stats': claude_api.get_stats(),
            'conversation_stats': conversation_manager.get_global_statistics(),
            'cache_stats': global_cache.get_stats(),
            'config': {
                'model': config.CLAUDE_MODEL,
                'max_tokens': config.CLAUDE_MAX_TOKENS,
                'similarity_threshold': config.SIMILARITY_THRESHOLD,
                'categories': config.CATEGORIES
            }
        }
        
        return jsonify(status_data), 200
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
@ResponseTimer.timeout_handler(config.KAKAO_TIMEOUT)
def webhook():
    """카카오톡 챗봇 웹훅 엔드포인트"""
    app_status['total_requests'] += 1
    
    try:
        # 요청 데이터 파싱
        request_data = request.get_json()
        
        if not request_data:
            logger.error("빈 요청 데이터")
            app_status['error_responses'] += 1
            return jsonify(response_builder.create_error_response()), 400
        
        # 요청 유효성 검사
        if not request_parser.is_valid_request(request_data):
            logger.error("유효하지 않은 요청")
            app_status['error_responses'] += 1
            return jsonify(response_builder.create_error_response()), 400
        
        # 사용자 정보 추출
        parsed_request = request_parser.parse_user_request(request_data)
        user_id = parsed_request['user_id']
        user_message = parsed_request['user_message']
        
        logger.info(f"사용자 요청: {user_id[:8]}*** -> {user_message[:50]}...")
        
        # 메모리 상태 체크
        if MemoryManager.is_memory_critical():
            logger.warning("메모리 부족 - 가비지 컬렉션 실행")
            MemoryManager.force_gc()
        
        # 챗봇 응답 처리
        response = process_chatbot_request(user_id, user_message, parsed_request)
        
        app_status['successful_responses'] += 1
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"웹훅 처리 오류: {str(e)}")
        logger.error(traceback.format_exc())
        
        app_status['error_responses'] += 1
        
        # 에러 응답 반환
        error_response = response_builder.create_error_response()
        return jsonify(error_response), 500

def process_chatbot_request(user_id: str, user_message: str, request_info: Dict) -> Dict[str, Any]:
    """
    챗봇 요청 처리 메인 로직
    
    Args:
        user_id: 사용자 ID
        user_message: 사용자 메시지
        request_info: 요청 정보
        
    Returns:
        Dict: 카카오톡 응답 데이터
    """
    log_function_call("process_chatbot_request", 
                     user_id=user_id[:8] + "***", 
                     message_length=len(user_message))
    
    try:
        # 1. 사용자 세션 로드
        user_session = conversation_manager.get_user_session(user_id)
        
        # 2. 특별한 명령어 처리
        special_response = handle_special_commands(user_message, user_session)
        if special_response:
            return special_response
        
        # 3. 메시지 타입 판단
        message_type = classify_message_type(user_message, user_session)
        
        if message_type == 'greeting':
            response = handle_greeting(user_message)
        elif message_type == 'counseling':
            response = handle_counseling_request(user_message, user_session)
        else:
            response = handle_fallback(user_message)
        
        # 4. 대화 기록 저장
        user_session.add_message('user', user_message)
        
        # AI 응답이 있으면 저장
        if response and 'template' in response and 'outputs' in response['template']:
            ai_response = extract_ai_response(response)
            if ai_response:
                user_session.add_message('assistant', ai_response)
        
        # 세션 저장
        conversation_manager.save_user_session(user_session)
        
        # 상호작용 로그
        conversation_manager.log_interaction(
            user_id, 
            'message',
            {
                'message_type': message_type,
                'message_length': len(user_message),
                'categories': user_session.user_categories
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"챗봇 요청 처리 오류: {str(e)}")
        return response_builder.create_error_response()

def classify_message_type(user_message: str, user_session) -> str:
    """메시지 타입 분류"""
    message_lower = user_message.lower().strip()
    
    # 인사말 패턴
    greetings = ['안녕', '하이', '안녕하세요', '처음', '시작', 'hi', 'hello']
    if any(greeting in message_lower for greeting in greetings) and len(user_session.conversation_history) <= 1:
        return 'greeting'
    
    # 상담 요청 패턴 (기본값)
    return 'counseling'

def handle_special_commands(user_message: str, user_session) -> Optional[Dict]:
    """특별한 명령어 처리"""
    message_lower = user_message.lower().strip()
    
    # 도움말 요청
    if message_lower in ['도움말', 'help', '도움', '사용법']:
        help_text = """🙏 AI Bible Assistant 사용법

✨ 주요 기능:
• 성경 말씀 기반 상담
• 개인적인 고민 상담
• 신앙적 조언 제공
• 기도 요청

💬 사용 예시:
"가족과의 갈등으로 힘들어요"
"진로 선택에 고민이 있어요"
"기도 부탁드려요"

📖 언제든 편안하게 말씀해 주세요!"""
        
        return response_builder.create_simple_text(help_text)
    
    # 기도 요청
    if '기도' in message_lower and any(word in message_lower for word in ['부탁', '해주', '드려', '요청']):
        prayer_response = handle_prayer_request(user_message)
        return prayer_response
    
    return None

def handle_greeting(user_message: str) -> Dict:
    """인사 메시지 처리"""
    return response_builder.create_welcome_response()

def handle_counseling_request(user_message: str, user_session) -> Dict:
    """상담 요청 처리"""
    try:
        # 1. 고민 카테고리 분류
        categories = bible_manager.classify_concern(user_message)
        category_names = [cat[0] for cat in categories[:3] if cat[1] > 1.0]  # 높은 점수만
        
        # 사용자 카테고리 업데이트
        if category_names:
            user_session.update_categories(category_names)
        
        # 2. 관련 성경 구절 검색
        bible_verses = bible_manager.search_verses(user_message, top_k=config.MAX_BIBLE_RESULTS)
        
        if not bible_verses:
            # 인기 구절로 대체
            bible_verses = bible_manager.get_popular_verses(
                category=category_names[0] if category_names else None,
                count=3
            )
        
        # 3. AI 상담 응답 생성
        verse_dicts = [verse.to_dict() for verse in bible_verses]
        conversation_history = user_session.get_recent_messages(4)
        
        ai_response = claude_api.generate_counseling_response(
            user_message=user_message,
            bible_verses=verse_dicts,
            conversation_history=conversation_history,
            user_categories=category_names
        )
        
        if not ai_response:
            # AI 응답 실패시 기본 응답
            ai_response = f"""🙏 {user_message}로 고민하고 계시는군요. 

이런 상황에서 하나님의 말씀을 통해 위로를 받으시기 바랍니다. 모든 어려움 속에서도 하나님께서 함께하시며, 가장 좋은 길로 인도해 주실 것입니다.

기도와 함께 지혜를 구하시며, 필요하다면 믿을 만한 분들과 상의해 보시기 바랍니다."""
        
        # 4. 포맷된 응답 생성
        response = response_builder.create_counseling_response(
            ai_response=ai_response,
            bible_verses=verse_dicts,
            show_references=len(bible_verses) > 0
        )
        
        return response
        
    except Exception as e:
        logger.error(f"상담 요청 처리 오류: {str(e)}")
        return response_builder.create_error_response()

def handle_prayer_request(user_message: str) -> Dict:
    """기도 요청 처리"""
    prayer_text = """🙏 기도 요청을 받았습니다.

하나님께서 당신의 마음을 아시고, 가장 필요한 것을 채워주시기를 기도합니다. 

"너희 중에 두세 사람이 내 이름으로 모인 곳에는 나도 그들 중에 있느니라" (마태복음 18:20)

하나님의 평안과 은혜가 함께하시기를 축복합니다. 🕊️"""
    
    return response_builder.create_simple_text(prayer_text)

def handle_fallback(user_message: str) -> Dict:
    """폴백 응답 처리"""
    # AI 폴백 시도
    ai_response = claude_api.generate_fallback_response(user_message)
    
    if ai_response:
        return response_builder.create_simple_text(ai_response)
    else:
        return response_builder.create_fallback_response(user_message)

def extract_ai_response(kakao_response: Dict) -> str:
    """카카오톡 응답에서 AI 응답 텍스트 추출"""
    try:
        outputs = kakao_response.get('template', {}).get('outputs', [])
        if outputs and 'simpleText' in outputs[0]:
            return outputs[0]['simpleText']['text']
    except:
        pass
    return ""

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal Server Error'}), 500

# 메인 실행 (개발 환경용)
if __name__ == '__main__':
    logger.info(f"AI Bible Assistant 서버 시작 - 포트: {config.PORT}")
    
    # 개발 환경에서는 바로 초기화
    if not initialize_services():
        logger.error("서비스 초기화 실패 - 서버 종료")
        sys.exit(1)
    
    # Flask 서버 시작
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )
else:
    # Gunicorn 환경 (Railway 등)에서는 여기서 초기화
    logger.info("Gunicorn 환경에서 AI Bible Assistant 시작")
    initialize_services()

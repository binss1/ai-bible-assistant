# -*- coding: utf-8 -*-
"""
AI Bible Assistant 메인 서버 (개선안 적용)
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

# --- 서비스 초기화 및 헬스체크 함수 (기존 코드와 동일) ---

def ensure_bible_loaded():
    """성경 데이터가 로드되어 있는지 확인하고, 없으면 강제 로드"""
    try:
        if not hasattr(bible_manager, 'verses') or len(bible_manager.verses) == 0:
            logger.info("성경 데이터가 없음 - 강제 로드 시작")
            bible_manager.load_embeddings()
            return len(bible_manager.verses) > 0
        return True
    except Exception as e:
        logger.error(f"성경 데이터 강제 로드 실패: {e}")
        return False

def initialize_services():
    """서비스 초기화"""
    logger.info("=== AI Bible Assistant 서비스 초기화 시작 ===")
    try:
        logger.info("1. 설정 유효성 검사")
        config.validate_config()
        logger.info("✓ 설정 유효성 검사 완료")

        logger.info("2. 성경 임베딩 데이터 확인")
        if bible_manager.is_loaded:
            logger.info("✓ 성경 임베딩 이미 로드됨 (중복 로드 방지)")
        elif bible_manager.load_embeddings():
            logger.info("✓ 성경 임베딩 로드 완료")
        else:
            logger.error("✗ 성경 임베딩 로드 실패")
            return False

        logger.info("3. Claude API 연결 테스트")
        if claude_api.test_connection():
            logger.info("✓ Claude API 연결 성공")
        else:
            logger.warning("⚠ Claude API 연결 실패 (서비스는 계속 실행)")

        logger.info("4. MongoDB 연결 테스트")
        if conversation_manager.test_connection():
            logger.info("✓ MongoDB 연결 성공")
        else:
            logger.warning("⚠ MongoDB 연결 실패 (오프라인 모드로 실행)")

        memory_usage = MemoryManager.get_memory_usage()
        logger.info(f"5. 현재 메모리 사용량: {memory_usage:.1f}MB")

        app_status['is_healthy'] = True
        logger.info("=== 서비스 초기화 완료 ===")
        return True
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트 - 강제 초기화 포함"""
    try:
        memory_usage = MemoryManager.get_memory_usage()
        bible_loaded = ensure_bible_loaded()
        is_healthy = bible_loaded and (memory_usage < config.MAX_MEMORY_MB)

        if is_healthy:
            app_status['is_healthy'] = True

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
        if not bible_loaded:
            health_data['error'] = '성경 데이터 로드 실패'
            
        status_code = 200 if is_healthy else 503
        return jsonify(health_data), status_code
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status_check():
    """상세 상태 정보"""
    # ... (기존 코드와 동일, 생략)
    pass


@app.route('/webhook', methods=['POST'])
@ResponseTimer.timeout_handler(config.KAKAO_TIMEOUT)
def webhook():
    """카카오톡 챗봇 웹훅 엔드포인트"""
    app_status['total_requests'] += 1
    try:
        if not ensure_bible_loaded():
            logger.error("웹훅: 성경 데이터 로드 실패")
            app_status['error_responses'] += 1
            return jsonify(response_builder.create_error_response()), 500

        request_data = request.get_json()
        if not request_data or not request_parser.is_valid_request(request_data):
            logger.error("유효하지 않은 요청 데이터")
            app_status['error_responses'] += 1
            return jsonify(response_builder.create_error_response()), 400

        parsed_request = request_parser.parse_user_request(request_data)
        user_id = parsed_request['user_id']
        user_message = parsed_request['user_message']
        logger.info(f"사용자 요청: {user_id[:8]}*** -> {user_message[:50]}...")

        if MemoryManager.is_memory_critical():
            logger.warning("메모리 부족 - 가비지 컬렉션 실행")
            MemoryManager.force_gc()

        response = process_chatbot_request(user_id, user_message, parsed_request)

        app_status['successful_responses'] += 1
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"웹훅 처리 오류: {str(e)}\n{traceback.format_exc()}")
        app_status['error_responses'] += 1
        return jsonify(response_builder.create_error_response()), 500

# --- 챗봇 로직 (개선안 적용) ---

def process_chatbot_request(user_id: str, user_message: str, request_info: Dict) -> Dict[str, Any]:
    """
    챗봇 요청 처리 메인 로직 (개선)
    """
    log_function_call("process_chatbot_request", user_id=user_id[:8] + "***", message_length=len(user_message))
    try:
        user_session = conversation_manager.get_user_session(user_id)

        # 1. 특별 명령어 우선 처리
        special_response = handle_special_commands(user_message, user_session)
        if special_response:
            response = special_response
        else:
            # 2. 메시지 의도 분류
            intent = classify_intent(user_message, user_session)

            if intent == 'greeting':
                response = handle_greeting(user_message, user_session)
            elif intent == 'counseling_start':
                response = handle_counseling_start()
            elif intent == 'counseling_detail':
                response = handle_counseling_request(user_message, user_session)
            else: # fallback
                response = handle_fallback(user_message, user_session)

        # 3. 대화 및 응답 기록
        user_session.add_message('user', user_message)
        ai_response_text = extract_ai_response(response)
        if ai_response_text:
            user_session.add_message('assistant', ai_response_text)

        conversation_manager.save_user_session(user_session)

        conversation_manager.log_interaction(
            user_id,
            'message',
            {
                'intent': intent if 'intent' in locals() else 'special_command',
                'message_length': len(user_message),
                'categories': user_session.user_categories
            }
        )
        return response

    except Exception as e:
        logger.error(f"챗봇 요청 처리 오류: {str(e)}\n{traceback.format_exc()}")
        return response_builder.create_error_response()


def classify_intent(user_message: str, user_session) -> str:
    """메시지 의도 분류 (개선)"""
    message_norm = user_message.lower().strip().replace(" ", "")

    # 인사말 패턴 (대화 초기 또는 단독 인사)
    greetings = ['안녕', '안녕하세요', '하이', '헬로', 'hi', 'hello']
    if any(g == message_norm for g in greetings) and len(user_session.conversation_history) < 2:
        return 'greeting'

    # 간단한 고민 시작 패턴
    counseling_starters = ['고민있어', '고민이있습니다', '상담좀', '이야기좀']
    if any(starter in message_norm for starter in counseling_starters) and len(user_message) < 15:
        return 'counseling_start'

    # 그 외는 모두 구체적인 상담 내용으로 간주
    return 'counseling_detail'


def handle_special_commands(user_message: str, user_session) -> Optional[Dict]:
    """특별한 명령어 처리"""
    message_lower = user_message.lower().strip()
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

    if '기도' in message_lower and any(word in message_lower for word in ['부탁', '해주', '드려', '요청']):
        return handle_prayer_request(user_message)

    return None


def handle_greeting(user_message: str, user_session) -> Dict:
    """인사 메시지 처리"""
    if len(user_session.conversation_history) == 0:
        return response_builder.create_welcome_response()
    else:
        return response_builder.create_simple_text("네, 안녕하세요! 오늘은 어떤 이야기를 나누고 싶으신가요?")


def handle_counseling_start() -> Dict:
    """간단한 고민 시작 메시지 처리"""
    text = "네, 어떤 고민이 있으신가요? 편안하게 말씀해주세요. 제가 듣고 함께 기도하며 돕겠습니다."
    return response_builder.create_simple_text(text)


def handle_counseling_request(user_message: str, user_session) -> Dict:
    """상담 요청 처리 (개선)"""
    try:
        # 1. 관련 성경 구절 검색
        bible_verses = bible_manager.search_verses(user_message, top_k=5)

        if not bible_verses:
            logger.warning(f"'{user_message}'에 대한 관련 구절을 찾지 못했습니다. 인기 구절로 대체합니다.")
            categories = bible_manager.classify_concern(user_message)
            top_category = categories[0][0] if categories else None
            bible_verses = bible_manager.get_popular_verses(category=top_category, count=3)

        # 2. AI 상담 응답 생성
        verse_dicts = [verse.to_dict() for verse in bible_verses]
        conversation_history = user_session.get_recent_messages(6)
        user_categories = [cat[0] for cat in bible_manager.classify_concern(user_message)]

        ai_response = claude_api.generate_counseling_response(
            user_message=user_message,
            bible_verses=verse_dicts,
            conversation_history=conversation_history,
            user_categories=user_categories
        )

        # AI 응답 생성 실패 시, 더 안전한 폴백 응답
        if not ai_response or len(ai_response.strip()) < 10:
            logger.error("Claude API 응답 생성 실패 또는 부적절한 응답")
            ai_response = """마음이 많이 힘드시군요. 그 마음에 하나님의 위로가 함께하기를 기도합니다.

어떤 상황에 처해있든지, 주님께서는 당신과 함께하시며 모든 것을 합력하여 선을 이루실 것입니다.

잠시 호흡을 가다듬고, 주님께 그 마음을 솔직하게 아뢰어보세요. 가장 좋은 길로 인도해주실 것입니다."""
            return response_builder.create_simple_text(ai_response)

        # 3. 포맷된 응답 생성
        return response_builder.create_counseling_response(
            ai_response=ai_response,
            bible_verses=verse_dicts,
            show_references=len(verse_dicts) > 0
        )

    except Exception as e:
        logger.error(f"상담 요청 처리 오류: {str(e)}\n{traceback.format_exc()}")
        return response_builder.create_error_response()


def handle_prayer_request(user_message: str) -> Dict:
    """기도 요청 처리"""
    prayer_text = """🙏 기도 요청을 받았습니다.

하나님께서 당신의 마음을 아시고, 가장 필요한 것을 채워주시기를 기도합니다.

"너희 중에 두세 사람이 내 이름으로 모인 곳에는 나도 그들 중에 있느니라" (마태복음 18:20)

하나님의 평안과 은혜가 함께하시기를 축복합니다. 🕊️"""
    return response_builder.create_simple_text(prayer_text)


def handle_fallback(user_message: str, user_session) -> Dict:
    """폴백 응답 처리 (개선)"""
    history = user_session.get_recent_messages(4)
    ai_response = claude_api.generate_fallback_response(user_message, history)

    if ai_response:
        return response_builder.create_simple_text(ai_response)
    else:
        # 최종 폴백
        return response_builder.create_fallback_response()


def extract_ai_response(kakao_response: Dict) -> str:
    """카카오톡 응답에서 AI 응답 텍스트 추출"""
    try:
        outputs = kakao_response.get('template', {}).get('outputs', [])
        for output in outputs:
            if 'simpleText' in output:
                return output['simpleText']['text']
            if 'basicCard' in output:
                return output['basicCard'].get('description', '')
    except Exception:
        pass
    return ""

# --- 에러 핸들러 및 서버 실행 (기존 코드와 동일) ---

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    logger.info(f"AI Bible Assistant 서버 시작 - 포트: {config.PORT}")
    if not initialize_services():
        logger.error("서비스 초기화 실패 - 서버 종료")
        sys.exit(1)
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )
else:
    logger.info("Gunicorn 환경에서 AI Bible Assistant 시작")
    initialize_services()
    ensure_bible_loaded()
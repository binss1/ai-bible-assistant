# -*- coding: utf-8 -*-
"""
AI Bible Assistant 메인 서버 (안정성 강화 최종안)
Flask 웹서버를 통해 카카오톡 챗봇 서비스를 제공합니다.
"""

import logging
import os
import sys
import traceback
import time
from flask import Flask, request, jsonify
from typing import Dict, Any, Optional

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- 모듈 임포트 ---
# 다른 파이썬 파일에서 정의한 클래스나 함수를 가져옵니다.
# config.py, utils.py 등이 같은 폴더에 있어야 합니다.
from config import config
from utils import (
    MemoryManager, ResponseTimer, DateTimeHelper,
    global_cache, log_function_call, safe_execute
)
from modules.bible_manager import bible_manager
from modules.claude_api import claude_api
from modules.conversation_manager import conversation_manager
from modules.kakao_formatter import response_builder, request_parser

# --- 로깅 설정 ---
# 챗봇의 동작 상태를 파일과 콘솔에 기록합니다.
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Flask 앱 초기화 ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글이 깨지지 않도록 설정

# --- 전역 상태 변수 ---
# 앱의 전반적인 상태를 추적합니다.
app_status = {
    'startup_time': DateTimeHelper.get_kst_now(),
    'total_requests': 0,
    'successful_responses': 0,
    'error_responses': 0,
    'is_healthy': False
}


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
    """서비스 시작 시 필요한 모든 것을 초기화합니다."""
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
    """서버가 정상적으로 동작하는지 확인하는 엔드포인트"""
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
        }
        status_code = 200 if is_healthy else 503
        return jsonify(health_data), status_code
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/webhook', methods=['POST'])
@ResponseTimer.timeout_handler(config.KAKAO_TIMEOUT)
def webhook():
    """카카오톡 챗봇의 모든 메시지를 받는 메인 엔드포인트"""
    app_status['total_requests'] += 1
    request_time = time.time()

    try:
        if not ensure_bible_loaded():
            raise RuntimeError("성경 데이터 로드에 실패하여 요청을 처리할 수 없습니다.")

        request_data = request.get_json()
        if not request_data or not request_parser.is_valid_request(request_data):
            raise ValueError("유효하지 않은 요청 데이터 형식입니다.")

        parsed_request = request_parser.parse_user_request(request_data)
        user_id = parsed_request['user_id']
        user_message = parsed_request['user_message']
        logger.info(f"사용자 요청 수신: {user_id[:8]}*** -> '{user_message[:50]}...'")

    except Exception as e:
        logger.error(f"웹훅 요청 전처리 오류: {str(e)}\n{traceback.format_exc()}")
        app_status['error_responses'] += 1
        return jsonify(response_builder.create_error_response("요청을 처리하는 중 문제가 발생했습니다.")), 200

    try:
        if MemoryManager.is_memory_critical():
            logger.warning("메모리 부족 - 가비지 컬렉션 실행")
            MemoryManager.force_gc()

        response = process_chatbot_request(user_id, user_message, parsed_request)
        app_status['successful_responses'] += 1

    except Exception as e:
        logger.error(f"!!! CRITICAL: process_chatbot_request 처리 중 예측하지 못한 오류 발생 !!!")
        logger.error(f"사용자: {user_id[:8]}***, 메시지: '{user_message}'")
        logger.error(f"{str(e)}\n{traceback.format_exc()}")
        app_status['error_responses'] += 1
        response = response_builder.create_error_response(
            "죄송합니다, 답변을 준비하는 중 예상치 못한 문제가 발생했어요. 잠시 후 다시 시도해주세요."
        )

    response_time = time.time() - request_time
    logger.info(f"응답 생성 완료. 총 소요시간: {response_time:.2f}초")

    if response_time > 4.5:
         logger.warning(f"응답 시간이 4.5초를 초과했습니다. 타임아웃 위험이 높습니다. (소요시간: {response_time:.2f}초)")

    return jsonify(response), 200


def process_chatbot_request(user_id: str, user_message: str, request_info: Dict) -> Dict[str, Any]:
    """사용자 메시지를 받아 적절한 답변을 생성하는 핵심 로직"""
    user_session = conversation_manager.get_user_session(user_id)

    special_response = handle_special_commands(user_message, user_session)
    if special_response:
        response = special_response
    else:
        intent = classify_intent(user_message, user_session)
        logger.info(f"메시지 의도 분류 결과: {intent}")

        if intent == 'greeting':
            response = handle_greeting(user_message, user_session)
        elif intent == 'counseling_start':
            response = handle_counseling_start()
        elif intent == 'counseling_detail':
            response = handle_counseling_request(user_message, user_session)
        else:
            response = handle_fallback(user_message, user_session)

    user_session.add_message('user', user_message)
    ai_response_text = extract_ai_response(response)
    if ai_response_text:
        user_session.add_message('assistant', ai_response_text)
    conversation_manager.save_user_session(user_session)

    return response


def classify_intent(user_message: str, user_session) -> str:
    """사용자 메시지의 의도를 파악 (인사, 상담 시작, 상담 내용 등)"""
    message_norm = ''.join(filter(str.isalnum, user_message.lower()))

    greetings = ['안녕', '안녕하세요', '하이', '헬로', 'hi', 'hello']
    if message_norm in greetings and len(user_session.conversation_history) < 2:
        return 'greeting'

    counseling_starters = ['고민있어', '고민이있습니다', '상담좀', '이야기좀해', '이야기좀할까']
    if any(starter in message_norm for starter in counseling_starters) and len(message_norm) < 15:
        return 'counseling_start'

    return 'counseling_detail'


def handle_special_commands(user_message: str, user_session) -> Optional[Dict]:
    """'도움말', '기도 요청' 등 특별한 명령어를 처리"""
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
    """인사 메시지에 대한 답변 생성"""
    if len(user_session.conversation_history) == 0:
        return response_builder.create_welcome_response()
    else:
        return response_builder.create_simple_text("네, 안녕하세요! 오늘은 어떤 이야기를 나누고 싶으신가요?")


def handle_counseling_start() -> Dict:
    """'고민있어요' 와 같은 간단한 상담 시작 메시지에 대한 답변 생성"""
    return response_builder.create_simple_text("네, 어떤 고민이 있으신가요? 편안하게 말씀해주세요. 제가 듣고 함께 기도하며 돕겠습니다.")


def handle_counseling_request(user_message: str, user_session) -> Dict:
    """구체적인 상담 내용에 대해 성경 검색과 AI 답변을 생성"""
    try:
        logger.info("상담 요청 처리 시작...")
        logger.info("-> 성경 구절 검색 중...")
        bible_verses = bible_manager.search_verses(user_message, top_k=5)
        if not bible_verses:
            logger.warning(f"관련 구절 없음. 인기 구절로 대체합니다.")
            categories = bible_manager.classify_concern(user_message)
            top_category = categories[0][0] if categories else None
            bible_verses = bible_manager.get_popular_verses(category=top_category, count=3)
        logger.info(f"-> 구절 검색 완료. {len(bible_verses)}개 구절 발견.")

        verse_dicts = [verse.to_dict() for verse in bible_verses]
        conversation_history = user_session.get_recent_messages(6)

        logger.info("-> Claude API 호출 중...")
        ai_response = claude_api.generate_counseling_response(
            user_message=user_message,
            bible_verses=verse_dicts,
            conversation_history=conversation_history,
            user_categories=[]
        )
        logger.info("-> Claude API 응답 수신 완료.")

        if not ai_response or len(ai_response.strip()) < 10:
            raise ValueError("Claude API가 유효한 응답을 생성하지 못했습니다.")

        return response_builder.create_counseling_response(
            ai_response=ai_response,
            bible_verses=verse_dicts,
            show_references=len(verse_dicts) > 0
        )
    except Exception as e:
        logger.error(f"!!! handle_counseling_request 처리 중 오류 발생 !!!")
        logger.error(f"{str(e)}\n{traceback.format_exc()}")
        return response_builder.create_error_response(
            "죄송합니다, 질문을 이해하고 답변을 준비하는 데 시간이 조금 더 필요할 것 같아요. 조금 더 구체적으로 질문해주시거나, 잠시 후 다시 시도해주시겠어요?"
        )


def handle_prayer_request(user_message: str) -> Dict:
    """기도 요청에 대한 답변 생성"""
    prayer_text = """🙏 기도 요청을 받았습니다.

하나님께서 당신의 마음을 아시고, 가장 필요한 것을 채워주시기를 기도합니다.

"너희 중에 두세 사람이 내 이름으로 모인 곳에는 나도 그들 중에 있느니라" (마태복음 18:20)

하나님의 평안과 은혜가 함께하시기를 축복합니다. 🕊️"""
    return response_builder.create_simple_text(prayer_text)


def handle_fallback(user_message: str, user_session) -> Dict:
    """의도를 파악하기 어려운 메시지에 대한 기본 답변 생성"""
    history = user_session.get_recent_messages(4)
    ai_response = claude_api.generate_fallback_response(user_message, history)

    if ai_response:
        return response_builder.create_simple_text(ai_response)
    else:
        return response_builder.create_fallback_response()


def extract_ai_response(kakao_response: Dict) -> str:
    """카카오톡 응답 JSON에서 실제 텍스트 메시지를 추출"""
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


# --- Flask 에러 핸들러 ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal Server Error'}), 500


# --- 서버 실행 ---
if __name__ == '__main__':
    # 개발 환경에서 직접 실행할 때
    logger.info(f"AI Bible Assistant 서버 시작 - 포트: {config.PORT}")
    if not initialize_services():
        logger.error("서비스 초기화 실패 - 서버 종료")
        sys.exit(1)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)
else:
    # Gunicorn과 같은 상용 서버 환경에서 실행될 때
    logger.info("Gunicorn 환경에서 AI Bible Assistant 시작")
    initialize_services()
    ensure_bible_loaded()
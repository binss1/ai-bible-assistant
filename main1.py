import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify

# Flask 앱을 초기화합니다.
app = Flask(__name__)

# --- 서버가 시작될 때 한 번만 실행되는 부분 ---

# API 키를 환경 변수에서 불러옵니다.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
BIBLE_DATA = {} # 성경 데이터를 저장할 변수

# API 키가 제대로 설정되었을 때만 AI 구성을 시도합니다.
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API 키가 성공적으로 설정되었습니다.")
else:
    print("🚨 [에러] GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

# 성경 JSON 파일을 읽어 메모리에 저장합니다.
try:
    with open('bible.json', 'r', encoding='utf-8') as f:
        BIBLE_DATA = json.load(f)
    print("✅ bible.json 파일 로딩 완료!")
except FileNotFoundError:
    print("🚨 [경고] bible.json 파일을 찾을 수 없습니다. 배포 시 파일이 포함되었는지 확인하세요.")
except json.JSONDecodeError:
    print("🚨 [에러] bible.json 파일 형식이 올바르지 않습니다.")


# --- 실제 요청을 처리하는 함수 부분 ---

def search_bible(keywords):
    """성경 데이터에서 관련 구절을 검색하는 함수"""
    search_results = []
    if not BIBLE_DATA:
        return search_results
    
    for verse, content in BIBLE_DATA.items():
        if any(keyword in content for keyword in keywords):
            search_results.append(f"{verse}: {content}")
            if len(search_results) >= 5:
                break
    return search_results

# 카카오톡 요청을 처리할 URL 경로를 설정합니다.
@app.route('/kakao', methods=['POST'])
def kakao_chatbot():
    """카카오톡 서버로부터 요청을 받아 AI 답변을 생성하고 반환하는 함수"""
    # API 키나 성경 데이터가 준비되지 않았다면, 에러 메시지를 반환합니다.
    if not GEMINI_API_KEY or not BIBLE_DATA:
        error_text = "챗봇 서버가 정상적으로 초기화되지 않았습니다. 관리자에게 문의하세요."
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": error_text}}]}
        })
        
    kakao_request = request.get_json()
    user_question = kakao_request.get('userRequest', {}).get('utterance', '')

    if not user_question:
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "안녕하세요! 어떤 고민이 있으신가요?"}}]}})

    model = genai.GenerativeModel('gemini-1.5-flash')
    search_keywords = ["외로", "고독", "괴로우니", "힘들", "낙심", "슬픔", "기도", "감사", "사랑"]
    relevant_verses = search_bible(search_keywords)
    
    prompt = f"""당신은 성경 지식이 매우 풍부한 전문 기독교 상담사입니다. 아래 '참고 자료'로 제시된 성경 구절에만 근거하여, 사용자의 질문에 따뜻하고 지혜롭게 답변해주세요. 참고 자료가 비어있다면, 자료가 없음을 인정하고 일반적인 위로의 말을 건네세요.

    ---
    [참고 자료]
    {relevant_verses}
    ---
    [사용자 질문]
    {user_question}
    ---
    [답변 가이드]
    - 반드시 '참고 자료'의 내용만을 활용하여 답변을 구성하세요.
    - 답변은 매우 정중하고 공감하는 어조로 작성해주세요.
    - 답변의 마지막에는 어떤 성경 구절을 근거로 했는지 반드시 명시해야 합니다. (예: (시편 25:16))
    """
    
    try:
        response = model.generate_content(prompt)
        ai_answer = response.text
    except Exception as e:
        ai_answer = f"AI 모델 응답 중 오류가 발생했습니다: {e}"

    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": ai_answer}}]}
    })

# -*- coding: utf-8 -*-
"""
카카오톡 챗봇 테스트 스크립트
실제 카카오톡 요청 형식으로 로컬에서 테스트합니다.
"""

import requests
import json
import time

# 테스트할 서버 URL
BASE_URL = "https://web-production-4bec8.up.railway.app"
# LOCAL_URL = "http://localhost:8080"  # 로컬 테스트용

def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"상태코드: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 헬스체크 실패: {e}")
        return False

def test_webhook_get():
    """웹훅 GET 테스트"""
    print("\n🔍 웹훅 GET 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/webhook", timeout=10)
        print(f"상태코드: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 웹훅 GET 테스트 실패: {e}")
        return False

def test_kakao_webhook(message="고민이 있습니다"):
    """카카오톡 웹훅 POST 테스트"""
    print(f"\n🔍 카카오톡 웹훅 테스트 - 메시지: '{message}'...")
    
    # 실제 카카오톡 요청 형식
    kakao_request = {
        "userRequest": {
            "utterance": message,
            "user": {
                "id": "test_user_12345"
            }
        },
        "bot": {
            "id": "test_bot"
        },
        "action": {
            "id": "test_action",
            "name": "fallback",
            "params": {}
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook",
            json=kakao_request,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"상태코드: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"응답 형식: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # 응답 내용 추출
            if "template" in response_data and "outputs" in response_data["template"]:
                outputs = response_data["template"]["outputs"]
                for output in outputs:
                    if "simpleText" in output:
                        print(f"\n💬 AI 응답: {output['simpleText']['text']}")
            
            return True
        else:
            print(f"❌ 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 웹훅 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 AI Bible Assistant 테스트 시작")
    print("=" * 50)
    
    # 1. 헬스체크
    health_ok = test_health_check()
    
    # 2. 웹훅 GET 테스트
    webhook_get_ok = test_webhook_get()
    
    # 3. 카카오톡 웹훅 테스트
    webhook_post_ok = test_kakao_webhook("고민이 있습니다")
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약:")
    print(f"✅ 헬스체크: {'통과' if health_ok else '실패'}")
    print(f"✅ 웹훅 GET: {'통과' if webhook_get_ok else '실패'}")
    print(f"✅ 웹훅 POST: {'통과' if webhook_post_ok else '실패'}")
    
    if all([health_ok, webhook_get_ok, webhook_post_ok]):
        print("\n🎉 모든 테스트 통과! 챗봇이 정상 작동합니다.")
    else:
        print("\n⚠️  일부 테스트 실패. 로그를 확인해주세요.")
    
    print("\n💡 추가 테스트할 메시지들:")
    test_messages = [
        "안녕하세요",
        "가족과의 갈등으로 힘들어요",
        "진로 선택에 고민이 있어요",
        "기도 부탁드려요",
        "도움말"
    ]
    
    for msg in test_messages:
        print(f"\n테스트 메시지: '{msg}'")
        if input("테스트하시겠습니까? (y/n): ").lower() == 'y':
            test_kakao_webhook(msg)
            time.sleep(2)  # API 호출 간격

if __name__ == "__main__":
    main()

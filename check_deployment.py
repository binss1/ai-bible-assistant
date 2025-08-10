# 배포 확인 및 테스트 스크립트
import requests
import json
import time

def check_railway_deployment():
    """Railway 배포 상태 확인"""
    base_url = "https://web-production-4bec8.up.railway.app"
    
    print("🔍 Railway 배포 상태 확인 중...")
    print("=" * 50)
    
    # 1. Health Check
    try:
        print("1. Health Check 테스트...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   상태코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 서버 상태: {data.get('status', 'unknown')}")
            print(f"   📊 메모리 사용량: {data.get('memory_usage_mb', 'unknown')}MB")
            print(f"   📖 성경 로드 상태: {data.get('bible_loaded', 'unknown')}")
            if 'error' in data:
                print(f"   ⚠️  오류: {data['error']}")
        else:
            print(f"   ❌ Health Check 실패: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Health Check 오류: {e}")
    
    print()
    
    # 2. Webhook GET 테스트
    try:
        print("2. Webhook GET 테스트...")
        response = requests.get(f"{base_url}/webhook", timeout=10)
        print(f"   상태코드: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Webhook GET 성공")
        else:
            print(f"   ❌ Webhook GET 실패: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Webhook GET 오류: {e}")
    
    print()
    
    # 3. 카카오톡 Webhook POST 테스트
    try:
        print("3. 카카오톡 Webhook POST 테스트...")
        kakao_request = {
            "userRequest": {
                "utterance": "안녕하세요",
                "user": {"id": "test_user_123"}
            },
            "bot": {"id": "test_bot"},
            "action": {"id": "test_action", "name": "fallback", "params": {}}
        }
        
        response = requests.post(
            f"{base_url}/webhook",
            json=kakao_request,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   상태코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 카카오톡 응답 성공")
            
            # 응답 내용 추출
            if "template" in data and "outputs" in data["template"]:
                outputs = data["template"]["outputs"]
                for output in outputs:
                    if "simpleText" in output:
                        print(f"   💬 AI 응답: {output['simpleText']['text'][:100]}...")
        else:
            print(f"   ❌ Webhook POST 실패: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Webhook POST 오류: {e}")
    
    print()
    print("=" * 50)
    print("📋 다음 단계:")
    print("1. ✅ Git 정리 완료")
    print("2. ✅ Railway 배포 완료 (위 결과 확인)")
    print("3. 🔄 성경 임베딩 파일 호스팅 필요")
    print("4. ⚙️  Railway 환경변수 설정 필요")
    print()
    print("🌐 Railway 대시보드: https://railway.app/dashboard")

if __name__ == "__main__":
    check_railway_deployment()

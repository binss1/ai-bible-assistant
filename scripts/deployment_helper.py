# -*- coding: utf-8 -*-
"""
배포 도우미 스크립트
Railway 배포를 위한 사전 검사 및 도우미 기능을 제공합니다.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_environment():
    """환경 설정 검사"""
    print("🔍 환경 설정 검사")
    
    required_env_vars = [
        'CLAUDE_API_KEY',
        'MONGODB_URI'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 누락된 환경변수: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ 모든 필수 환경변수 설정됨")
        return True

def check_files():
    """필수 파일 존재 확인"""
    print("📁 필수 파일 확인")
    
    required_files = [
        'main.py',
        'config.py',
        'utils.py',
        'requirements.txt',
        'Procfile',
        'runtime.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 누락된 파일: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 모든 필수 파일 존재")
        return True

def test_imports():
    """Python 모듈 import 테스트"""
    print("🐍 모듈 import 테스트")
    
    try:
        # 핵심 모듈들 import 테스트
        import config
        from utils import MemoryManager, FileDownloader
        from modules.bible_manager import bible_manager
        from modules.claude_api import claude_api
        from modules.conversation_manager import conversation_manager
        from modules.kakao_formatter import response_builder
        
        print("✅ 모든 모듈 import 성공")
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {str(e)}")
        return False

def test_api_connections():
    """API 연결 테스트"""
    print("🌐 API 연결 테스트")
    
    try:
        from modules.claude_api import claude_api
        from modules.conversation_manager import conversation_manager
        
        # Claude API 테스트
        if claude_api.test_connection():
            print("✅ Claude API 연결 성공")
        else:
            print("⚠️  Claude API 연결 실패")
        
        # MongoDB 연결 테스트
        if conversation_manager.test_connection():
            print("✅ MongoDB 연결 성공")
        else:
            print("⚠️  MongoDB 연결 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ API 테스트 오류: {str(e)}")
        return False

def check_railway_cli():
    """Railway CLI 설치 확인"""
    print("🚂 Railway CLI 확인")
    
    try:
        result = subprocess.run(['railway', '--version'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Railway CLI 설치됨: {result.stdout.strip()}")
            return True
        else:
            print("❌ Railway CLI가 설치되지 않음")
            print("설치 방법: npm install -g @railway/cli")
            return False
    except:
        print("❌ Railway CLI가 설치되지 않음")
        print("설치 방법: npm install -g @railway/cli")
        return False

def generate_railway_json():
    """railway.json 설정 파일 생성"""
    print("⚙️  Railway 설정 파일 생성")
    
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "numReplicas": 1,
            "sleepApplication": False,
            "restartPolicyType": "ON_FAILURE"
        }
    }
    
    with open('railway.json', 'w', encoding='utf-8') as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ railway.json 생성 완료")

def deploy_to_railway():
    """Railway에 배포"""
    print("🚀 Railway 배포 시작")
    
    try:
        # 로그인 확인
        result = subprocess.run(['railway', 'whoami'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Railway 로그인이 필요합니다")
            print("실행: railway login")
            return False
        
        print(f"✅ Railway 로그인됨: {result.stdout.strip()}")
        
        # 배포 실행
        print("배포 중...")
        result = subprocess.run(['railway', 'up'], timeout=300)
        
        if result.returncode == 0:
            print("✅ 배포 성공!")
            
            # 서비스 URL 확인
            try:
                result = subprocess.run(['railway', 'domain'], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    domain = result.stdout.strip()
                    print(f"🌐 서비스 URL: https://{domain}")
                    print(f"🔍 헬스체크: https://{domain}/health")
            except:
                pass
            
            return True
        else:
            print("❌ 배포 실패")
            return False
            
    except Exception as e:
        print(f"❌ 배포 오류: {str(e)}")
        return False

def show_env_template():
    """환경변수 템플릿 표시"""
    print("\n📋 환경변수 설정 가이드")
    print("=" * 50)
    
    template = """
Railway 대시보드에서 다음 환경변수를 설정하세요:

🔑 필수 환경변수:
CLAUDE_API_KEY=sk-ant-api03-your-api-key-here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

📖 성경 데이터:
BIBLE_EMBEDDINGS_URL=https://github.com/your-repo/releases/download/v1.0/bible_embeddings.json.gz

⚙️  선택적 환경변수:
DEBUG=false
LOG_LEVEL=INFO
MAX_MEMORY_MB=400
SIMILARITY_THRESHOLD=0.3

설정 방법:
1. Railway 대시보드 > 프로젝트 선택
2. Variables 탭 클릭
3. 위 환경변수들 추가
4. Deploy 버튼 클릭
"""
    
    print(template)

def main():
    """메인 실행 함수"""
    print("🚀 AI Bible Assistant 배포 도우미")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 1. 파일 확인
    if not check_files():
        all_checks_passed = False
    
    print()
    
    # 2. 환경변수 확인
    if not check_environment():
        all_checks_passed = False
        show_env_template()
    
    print()
    
    # 3. 모듈 import 테스트
    if not test_imports():
        all_checks_passed = False
    
    print()
    
    # 4. API 연결 테스트
    if not test_api_connections():
        print("⚠️  API 연결 문제가 있지만 배포는 가능합니다")
    
    print()
    
    # 5. Railway CLI 확인
    railway_available = check_railway_cli()
    
    print()
    
    # 6. Railway 설정 파일 생성
    generate_railway_json()
    
    print()
    
    # 배포 결정
    if all_checks_passed and railway_available:
        response = input("🚀 지금 Railway에 배포하시겠습니까? (y/N): ")
        if response.lower() in ['y', 'yes']:
            deploy_to_railway()
        else:
            print("배포를 취소했습니다.")
            print("수동 배포: railway up")
    else:
        print("❌ 배포 전에 위의 문제들을 해결해주세요")
        
        if not railway_available:
            print("\n🚂 Railway CLI 설치:")
            print("npm install -g @railway/cli")
        
        if not all_checks_passed:
            print("\n📋 해결해야 할 문제들:")
            print("- 누락된 파일이나 환경변수 확인")
            print("- 모듈 import 오류 해결")

if __name__ == "__main__":
    main()

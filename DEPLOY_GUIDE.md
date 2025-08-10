# AI Bible Assistant 수동 배포 가이드

## 방법 1: Git 명령어로 직접 배포

```bash
# 1. 프로젝트 폴더로 이동
cd C:\Users\user\Desktop\ai-bible-assistant

# 2. 변경사항 추가
git add .

# 3. 커밋
git commit -m "Fix webhook issues and improve logging"

# 4. Railway에 푸시
git push origin main
```

## 방법 2: Railway CLI 사용 (선택사항)

```bash
# Railway CLI 설치 (한 번만)
npm install -g @railway/cli

# Railway 로그인
railway login

# 배포
railway up
```

## 배포 완료 후 테스트

### 1. 헬스체크 테스트
브라우저에서 방문: https://web-production-4bec8.up.railway.app/health

### 2. 웹훅 테스트
브라우저에서 방문: https://web-production-4bec8.up.railway.app/webhook

### 3. Python 테스트 스크립트 실행
```bash
python test_chatbot.py
```

## 카카오톡 설정

웹훅 URL을 카카오 챗봇 빌더에서 업데이트:
```
https://web-production-4bec8.up.railway.app/webhook
```

## 문제 해결

### Railway 배포 상태 확인
https://railway.app/dashboard

### 실시간 로그 확인
Railway 대시보드 → 프로젝트 선택 → Deployments → View Logs

### 환경변수 확인
1. CLAUDE_API_KEY 설정됨
2. MONGODB_URI 설정됨
3. BIBLE_EMBEDDINGS_URL 설정됨 (선택사항)

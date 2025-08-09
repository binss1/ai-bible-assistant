# 🙏 AI Bible Assistant

성경 말씀을 기반으로 한 AI 상담 챗봇입니다. 카카오톡을 통해 24시간 성경적 상담과 격려를 제공합니다.

## ✨ 주요 기능

- 📖 **성경 기반 상담**: 1,000개 이상의 성경 구절을 바탕으로 한 AI 상담
- 🤖 **Claude AI 연동**: Anthropic의 Claude AI를 활용한 자연스러운 대화
- 💬 **카카오톡 지원**: 친숙한 카카오톡 환경에서 이용 가능
- 🔍 **고민 카테고리 분류**: 관계, 진로, 신앙, 감정 등 7개 영역 자동 분류
- 💾 **대화 기록 관리**: MongoDB를 통한 개인화된 상담 기록
- ⚡ **실시간 응답**: 5초 이내 빠른 응답 제공
- 🌐 **24시간 운영**: Railway 클라우드 플랫폼 기반 상시 서비스

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/ai-bible-assistant.git
cd ai-bible-assistant
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 변경
```

필수 환경변수:
- `CLAUDE_API_KEY`: Claude AI API 키
- `MONGODB_URI`: MongoDB 연결 문자열
- `BIBLE_EMBEDDINGS_URL`: 성경 임베딩 파일 URL

### 4. 성경 임베딩 준비
```bash
# 임베딩 파일이 있는 경우 최적화
python scripts/optimize_embeddings.py

# 또는 환경변수에 URL 설정하여 자동 다운로드
```

### 5. 로컬 실행
```bash
python main.py
```

서버가 시작되면 `http://localhost:8080/health`에서 상태를 확인할 수 있습니다.

## 🏗️ 아키텍처

```
📁 ai-bible-assistant/
├── 🎯 main.py                    # 메인 Flask 서버
├── ⚙️ config.py                  # 설정 관리
├── 🛠️ utils.py                   # 유틸리티 함수
├── 📄 requirements.txt           # 패키지 의존성
├── 🚂 Procfile                   # Railway 배포 설정
├── 📁 modules/                   # 핵심 모듈들
│   ├── 📖 bible_manager.py       # 성경 데이터 관리
│   ├── 🤖 claude_api.py          # Claude AI 연동
│   ├── 💬 conversation_manager.py # 대화 관리
│   └── 📱 kakao_formatter.py     # 카카오톡 포맷터
└── 📁 scripts/                   # 유틸리티 스크립트들
```

## 🔧 기술 스택

- **백엔드**: Python 3.11, Flask
- **AI**: Anthropic Claude API
- **데이터베이스**: MongoDB Atlas
- **벡터 검색**: scikit-learn, NumPy
- **배포**: Railway
- **챗봇**: 카카오톡 챗봇 빌더

## 📊 성능 지표

- ⚡ **응답 시간**: 평균 3-5초
- 💾 **메모리 사용량**: 400MB 이하 (Railway 제한)
- 🔍 **검색 정확도**: 85% 이상
- 📈 **가동시간**: 99% 이상 목표

## 🚂 Railway 배포

### 1. Railway 계정 설정
```bash
npm install -g @railway/cli
railway login
```

### 2. 프로젝트 배포
```bash
railway up
```

### 3. 환경변수 설정
Railway 대시보드에서 다음 환경변수 설정:
- `CLAUDE_API_KEY`
- `MONGODB_URI`
- `BIBLE_EMBEDDINGS_URL`

### 4. 도메인 확인
배포 완료 후 제공되는 URL에서 서비스 확인

## 📱 카카오톡 챗봇 연동

### 1. 카카오톡 채널 생성
1. [카카오톡 채널 관리자센터](https://center-pf.kakao.com/) 접속
2. 새 채널 만들기
3. 채널명: "AI Bible Assistant"

### 2. 챗봇 빌더 설정
1. [카카오 챗봇 빌더](https://chatbot.kakao.com/) 접속
2. 새 챗봇 만들기
3. 위에서 만든 채널 연결

### 3. 스킬 서버 등록
1. 설정 → 스킬 서버
2. URL: `https://your-railway-app.railway.app/webhook`
3. 기본 블록에 스킬 연결

## 🔍 모니터링

### 헬스체크
```bash
curl https://your-app.railway.app/health
```

### 상세 상태
```bash
curl https://your-app.railway.app/status
```

### 로그 확인
```bash
railway logs --tail
```

## 💰 비용 최적화

예상 월간 비용 (24시간 운영):
- 🚂 **Railway**: ~$1-2 (500시간 초과분)
- 🍃 **MongoDB Atlas**: $0 (M0 무료 티어)
- 🤖 **Claude API**: ~$3-5 (사용량 기반)
- **총 예상 비용**: **$4-7/월**

### 비용 절약 팁
- Claude Haiku 모델 사용 (가장 저렴)
- 토큰 수 제한 (800개)
- 캐싱으로 중복 호출 방지
- 메모리 사용량 최적화

## 🔧 개발 가이드

### 로컬 개발
```bash
# 개발 모드 실행
DEBUG=true python main.py

# 테스트
python -m pytest tests/

# 코드 정리
black .
flake8 .
```

### 새로운 기능 추가
1. `modules/` 디렉토리에 새 모듈 생성
2. `main.py`에서 모듈 import 및 연동
3. 필요시 `config.py`에 설정 추가

### 환경변수 추가
1. `.env.example`에 새 변수 추가
2. `config.py`의 `Config` 클래스에 변수 정의
3. 문서 업데이트

## 🔒 보안 고려사항

- ✅ API 키 환경변수 관리
- ✅ 사용자 입력 검증
- ✅ 에러 정보 최소화
- ✅ 로그 개인정보 제외
- ✅ HTTPS 강제 사용

## 📈 향후 계획

- [ ] 다국어 지원 (영어, 중국어)
- [ ] 음성 메시지 지원
- [ ] 개인화된 성경 읽기 계획
- [ ] 교회별 맞춤 설정
- [ ] 관리자 대시보드
- [ ] 통계 및 분석 기능

## 🐛 문제 해결

### 자주 발생하는 문제

1. **임베딩 파일 로드 실패**
   ```bash
   # 파일 다운로드 테스트
   python scripts/railway_embeddings_loader.py
   ```

2. **메모리 부족 오류**
   ```bash
   # 메모리 사용량 확인
   curl https://your-app.railway.app/status
   ```

3. **Claude API 오류**
   ```bash
   # API 키 확인
   echo $CLAUDE_API_KEY
   ```

### 로그 분석
```bash
# Railway 로그 실시간 모니터링
railway logs --tail

# 특정 시간대 로그
railway logs --since 1h
```

## 📞 지원

- 📧 **이메일**: support@bible-assistant.com
- 📚 **문서**: [Wiki 페이지](https://github.com/your-username/ai-bible-assistant/wiki)
- 🐛 **버그 리포트**: [Issues](https://github.com/your-username/ai-bible-assistant/issues)
- 💬 **토론**: [Discussions](https://github.com/your-username/ai-bible-assistant/discussions)

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 기여

기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 통계

![GitHub stars](https://img.shields.io/github/stars/your-username/ai-bible-assistant)
![GitHub forks](https://img.shields.io/github/forks/your-username/ai-bible-assistant)
![GitHub issues](https://img.shields.io/github/issues/your-username/ai-bible-assistant)
![GitHub license](https://img.shields.io/github/license/your-username/ai-bible-assistant)

---

> 💝 **"너희 중에 두세 사람이 내 이름으로 모인 곳에는 나도 그들 중에 있느니라"** - 마태복음 18:20

Made with ❤️ for spreading God's love through technology.

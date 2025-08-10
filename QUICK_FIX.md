# 빠른 해결 가이드

## 1단계: Google Drive 업로드 (2분)
1. 파일 위치: C:\Users\user\Desktop\ai-bible-assistant\bible_embeddings_local.json.gz
2. Google Drive에 드래그 앤 드롭으로 업로드
3. 업로드 완료 후 파일 우클릭 → "링크 가져오기"
4. "제한됨" → "링크가 있는 모든 사용자"로 변경
5. 링크 복사

## 2단계: 다운로드 링크 변환 (1분)
복사한 링크를 변환:
- 원본: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
- 변환: https://drive.google.com/uc?export=download&id=FILE_ID

FILE_ID 부분만 추출해서 변환하세요.

## 3단계: Railway 환경변수 설정 (2분)
1. https://railway.app/dashboard 접속
2. ai-bible-assistant 프로젝트 선택
3. Variables 탭 클릭
4. New Variable 클릭
5. 다음 환경변수 추가:

Name: BIBLE_EMBEDDINGS_URL
Value: https://drive.google.com/uc?export=download&id=YOUR_FILE_ID

## 4단계: 배포 재시작
Variables 저장 후 자동으로 재배포됩니다.
5분 후 다시 테스트하세요.

# Google Drive 업로드 가이드

## 1단계: Google Drive 업로드
1. 로컬 파일 위치: C:\Users\user\Desktop\ai-bible-assistant\bible_embeddings_local.json.gz
2. Google Drive에 업로드
3. 파일 우클릭 → "링크 가져오기"
4. "링크가 있는 모든 사용자" 권한으로 설정
5. 링크 복사

## 2단계: 다운로드 링크 변환
Google Drive 공유 링크를 직접 다운로드 링크로 변환:

원본 링크 형식:
https://drive.google.com/file/d/FILE_ID/view?usp=sharing

변환된 다운로드 링크:
https://drive.google.com/uc?export=download&id=FILE_ID

## 3단계: Railway 환경변수 추가
변환된 링크를 환경변수로 설정:
BIBLE_EMBEDDINGS_URL=https://drive.google.com/uc?export=download&id=FILE_ID

## 대안: GitHub Releases
1. 새 저장소 생성: bible-assistant-data
2. Release 생성
3. 파일 업로드
4. 다운로드 URL 사용

@echo off
echo ============================================
echo AI Bible Assistant 수정사항 배포
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo 1. Git 상태 확인...
git status

echo.
echo 2. 변경사항 스테이징...
git add modules/bible_manager.py

echo.
echo 3. 커밋...
git commit -m "Fix: BibleManager 자동 로딩 및 다중 URL 처리 개선

- __init__ 메서드에서 자동으로 load_embeddings() 호출
- 다중 URL 병합 처리 로직 추가
- 메모리 최적화 및 오류 처리 개선"

echo.
echo 4. Railway 배포...
git push origin main

echo.
echo ============================================
echo 배포 완료! 3분 후 헬스체크를 확인하세요.
echo https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

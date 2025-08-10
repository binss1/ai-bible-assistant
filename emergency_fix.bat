@echo off
echo ============================================
echo Emergency Fix Deployment
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Adding missing FileDownloader class...
git add utils.py modules/bible_manager.py

echo Committing emergency fix...
git commit -m "Emergency Fix: Add missing FileDownloader class

- Added FileDownloader.load_json_file method to utils.py
- Fixed import error in bible_manager.py
- Bible embeddings should now load successfully"

echo Deploying to Railway...
git push origin main

echo.
echo ============================================
echo Emergency fix deployed!
echo ============================================
echo.
echo NEXT STEPS:
echo 1. Change Railway environment variable:
echo    BIBLE_EMBEDDINGS_URL = single URL only
echo 2. Wait 3 minutes for deployment
echo 3. Check: https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

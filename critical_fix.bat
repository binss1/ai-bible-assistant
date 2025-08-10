@echo off
echo ============================================
echo Critical Fix - Gunicorn Initialization
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Adding Gunicorn initialization fix...
git add main.py

echo Committing critical fix...
git commit -m "Critical Fix: Initialize services in Gunicorn environment

- Added else block for Gunicorn initialization
- Fixed health check logic to use bible_manager.is_loaded directly
- Added debugging info (bible_verses_count)
- This should fix: bible_loaded false despite successful loading"

echo Deploying critical fix...
git push origin main

echo.
echo ============================================
echo Critical fix deployed!
echo ============================================
echo.
echo Check in 3 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo.
echo Expected SUCCESS result:
echo {"status":"healthy","bible_loaded":true,"bible_verses_count":7772}
echo ============================================

pause

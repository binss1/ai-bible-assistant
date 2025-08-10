@echo off
echo ============================================
echo Fix: App Initialization Status Update
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Fixing app initialization status...
git add main.py

echo Committing app status fix...
git commit -m "Fix: Update app_initialized status in health check

- Health check now updates app_status when healthy
- Fixed bible_books calculation to use all verses
- Should show app_initialized: true when services working"

echo Deploying status fix...
git push origin main

echo.
echo ============================================
echo Status fix deployed!
echo ============================================
echo.
echo Changes:
echo ✅ app_initialized will update to true when healthy
echo ✅ bible_books calculation improved (should show 66)
echo ✅ Health check self-correcting status
echo.
echo Check in 2 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo.
echo Expected result:
echo {"status":"healthy","app_initialized":true,"bible_books":66}
echo ============================================

pause

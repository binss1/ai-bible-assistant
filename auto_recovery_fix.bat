@echo off
echo ============================================
echo CRITICAL: Health Check Auto-Recovery Fix
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Adding auto-recovery health check...
git add main.py Procfile

echo Committing auto-recovery fix...
git commit -m "CRITICAL: Health check auto-recovery + Gunicorn preload

- Health check now does real-time bible data verification
- Auto-reload bible data if not found during health check
- Added --preload to Gunicorn for consistent worker state
- Should fix: bible_loaded false despite successful loading"

echo Deploying auto-recovery fix...
git push origin main

echo.
echo ============================================
echo Auto-recovery deployed!
echo ============================================
echo.
echo New features:
echo ✅ Real-time bible data verification
echo ✅ Emergency reload if data missing
echo ✅ Gunicorn preload for consistency
echo ✅ Enhanced debugging info
echo.
echo Check in 3 minutes (should auto-fix):
echo https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

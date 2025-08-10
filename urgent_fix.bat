@echo off
echo ============================================
echo URGENT: Fix Gunicorn Options Error
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Fixing Procfile gunicorn options...
git add Procfile

echo Committing Procfile fix...
git commit -m "Fix: Remove unsupported --keepalive option from Procfile"

echo Deploying fixed Procfile...
git push origin main

echo.
echo ============================================
echo Procfile fixed and deployed!
echo ============================================
echo.
echo Fixed options:
echo ✅ Removed --keepalive (unsupported)
echo ✅ Kept --preload (for consistency)
echo ✅ Single worker, single thread
echo ✅ 60 second timeout
echo.
echo Check in 2 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

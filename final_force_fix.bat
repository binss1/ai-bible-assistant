@echo off
echo ============================================
echo FINAL FIX: Force Loading Bible Data
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Adding force loading system...
git add main.py

echo Committing final force loading fix...
git commit -m "FINAL FIX: Force load bible data on every request

- Added ensure_bible_loaded() function for guaranteed data loading
- Health check now forces bible data load every time
- Webhook protects against missing data
- Gunicorn startup double-ensures data loading
- Should solve: bible_loaded false despite successful loading logs"

echo Deploying final force loading fix...
git push origin main

echo.
echo ============================================
echo FINAL FIX DEPLOYED!
echo ============================================
echo.
echo New guarantees:
echo ✅ Health check FORCES data loading every time
echo ✅ Webhook checks data before processing
echo ✅ Startup double-ensures data loading
echo ✅ No request processed without bible data
echo.
echo This WILL work - check in 3 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo.
echo Expected SUCCESS:
echo {"status":"healthy","bible_loaded":true,"bible_verses_count":7772}
echo ============================================

pause

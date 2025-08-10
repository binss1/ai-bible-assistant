@echo off
echo ============================================
echo Final Fix - Auto-detect gzip compression
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Adding gzip auto-detection fix...
git add utils.py

echo Committing final fix...
git commit -m "Fix: Auto-detect gzip compression in load_json_file

- Added magic number detection for gzip files
- No longer depends on file extension
- Should fix: 'utf-8' codec can't decode byte 0x8b error"

echo Deploying final fix...
git push origin main

echo.
echo ============================================
echo Final fix deployed! 
echo Wait 3 minutes then check:
echo https://web-production-4bec8.up.railway.app/health
echo ============================================
echo.
echo Expected result:
echo {"bible_loaded": true, "status": "healthy"}
echo ============================================

pause

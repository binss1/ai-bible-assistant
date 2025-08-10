@echo off
echo ============================================
echo CRITICAL Memory Fix - Prevent Duplicate Loading
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Fixing memory issues...
git add main.py requirements.txt

echo Committing memory optimization...
git commit -m "CRITICAL: Fix memory overflow - prevent duplicate loading

- Added duplicate loading prevention in initialize_services()
- Updated anthropic from 0.34.2 to 0.40.0 (fix proxies error)
- Should reduce memory usage from 595MB to ~300MB
- Fixes: Bible data loaded twice causing memory overflow"

echo Deploying memory fix...
git push origin main

echo.
echo ============================================
echo Memory fix deployed!
echo ============================================
echo.
echo Expected memory reduction:
echo From: 595.1MB (OVER LIMIT)
echo To:   ~300MB (SAFE)
echo.
echo Check in 3 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

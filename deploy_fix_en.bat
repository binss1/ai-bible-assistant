@echo off
echo ============================================
echo AI Bible Assistant Fix Deployment
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo 1. Checking Git status...
git status

echo.
echo 2. Adding changes...
git add modules/bible_manager.py

echo.
echo 3. Committing changes...
git commit -m "Fix: Auto-load embeddings and multi-URL support"

echo.
echo 4. Pushing to Railway...
git push origin main

echo.
echo ============================================
echo Deployment complete! Check health in 3 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo ============================================

pause

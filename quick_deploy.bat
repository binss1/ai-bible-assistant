@echo off
echo Deploy AI Bible Assistant to Railway
echo.

echo Checking current directory...
cd /d "%~dp0"
echo Current location: %CD%
echo.

echo Checking git status...
git status --porcelain

echo.
echo Committing and pushing changes...
git add .
git commit -m "Fix webhook issues and improve logging"
git push origin main

echo.
echo Railway deployment started...
echo Check deployment status at: https://railway.app/dashboard
echo.

echo Test URLs after deployment:
echo Health Check: https://web-production-4bec8.up.railway.app/health
echo Webhook Test: https://web-production-4bec8.up.railway.app/webhook
echo.

echo Deployment script completed!
echo Test your KakaoTalk chatbot now.

pause

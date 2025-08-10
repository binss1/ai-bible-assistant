@echo off
echo Force deploy latest code to Railway

echo.
echo Step 1: Add any missed files
git add .

echo.
echo Step 2: Commit latest changes
git commit -m "Update webhook endpoint to support GET method" --allow-empty

echo.
echo Step 3: Push to trigger new deployment
git push origin main

echo.
echo Step 4: Wait for deployment (30 seconds)
timeout /t 30 /nobreak

echo.
echo Step 5: Test updated webhook
python check_deployment.py

echo.
echo Done! Latest code deployed.

pause

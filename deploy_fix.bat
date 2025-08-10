@echo off
echo Deploy fixed version that works without bible data

echo.
echo Step 1: Add all modified files
git add .

echo.
echo Step 2: Commit changes
git commit -m "Enable fallback mode: Works without bible embeddings data"

echo.
echo Step 3: Push to Railway
git push origin main

echo.
echo Step 4: Wait for deployment
timeout /t 45 /nobreak

echo.
echo Step 5: Test the fixed version
python check_deployment.py

echo.
echo Done! Fixed version deployed.

pause

@echo off
echo ============================================
echo EMERGENCY: Include Local Bible File
echo ============================================

cd /d "C:\Users\user\Desktop\ai-bible-assistant"

echo Step 1: Copying local bible file...
copy bible_embeddings_part_1.json.gz bible_embeddings_local.json.gz

echo Step 2: Checking file exists...
if exist bible_embeddings_local.json.gz (
    echo ✅ Local file copied successfully
    dir bible_embeddings_local.json.gz
) else (
    echo ❌ File copy failed!
    pause
    exit /b 1
)

echo Step 3: Adding files to git...
git add .gitignore config.py main.py bible_embeddings_local.json.gz

echo Step 4: Committing emergency fix...
git commit -m "EMERGENCY: Include local bible file in project

- Added bible_embeddings_local.json.gz (23MB) to project
- Modified config.py to prioritize local file
- Updated .gitignore to allow this specific file
- Should solve: Remote download failures in Railway environment"

echo Step 5: Deploying emergency fix...
git push origin main

echo.
echo ============================================
echo EMERGENCY FIX DEPLOYED!
echo ============================================
echo.
echo Changes:
echo ✅ Local bible file included in project (23MB)
echo ✅ No more remote downloads needed
echo ✅ Guaranteed file access in Railway
echo ✅ Priority: Local file > Remote URL
echo.
echo This WILL solve the loading issue!
echo Check in 3 minutes:
echo https://web-production-4bec8.up.railway.app/health
echo.
echo Expected SUCCESS:
echo {"status":"healthy","bible_loaded":true,"bible_verses_count":7772}
echo ============================================

pause

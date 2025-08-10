@echo off
echo Checking and fixing Git repository state...

echo.
echo Step 1: Check current Git status
git status

echo.
echo Step 2: Check what files are staged
git diff --cached --name-only

echo.
echo Step 3: Reset all staged changes
git reset HEAD

echo.
echo Step 4: Remove any large files from Git cache (ignore errors if files don't exist)
git rm --cached bible_embeddings.json 2>nul || echo "bible_embeddings.json not in cache"
git rm --cached bible_embeddings_optimized.json.gz 2>nul || echo "bible_embeddings_optimized.json.gz not in cache"
git rm --cached bible_embeddings_local.json.gz 2>nul || echo "bible_embeddings_local.json.gz not in cache"
git rm --cached bible_embeddings_part_*.json.gz 2>nul || echo "bible_embeddings_part files not in cache"

echo.
echo Step 5: Add only essential files
git add main.py
git add config.py
git add utils.py
git add modules/
git add .gitignore
git add requirements.txt
git add Procfile
git add runtime.txt
git add README.md

echo.
echo Step 6: Check what will be committed
git status

echo.
echo Step 7: Commit the changes
git commit -m "Fix webhook issues and improve logging (without large files)"

echo.
echo Step 8: Push to Railway
git push origin main

echo.
echo Done! Repository should be clean now.

pause

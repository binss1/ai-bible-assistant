@echo off
echo Removing large files from Git repository...

echo.
echo Step 1: Remove large embedding files from Git tracking
git rm --cached bible_embeddings.json
git rm --cached bible_embeddings_optimized.json.gz
git rm --cached bible_embeddings_local.json.gz
git rm --cached bible_embeddings_part_*.json.gz

echo.
echo Step 2: Add changes to git
git add .gitignore

echo.
echo Step 3: Commit changes
git commit -m "Remove large embedding files from Git, add to .gitignore"

echo.
echo Step 4: Push to origin
git push origin main

echo.
echo Done! Large files removed from Git repository.
echo The files still exist locally but won't be pushed to GitHub.

pause

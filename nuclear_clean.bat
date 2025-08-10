@echo off
echo NUCLEAR OPTION: Complete Git history cleanup

echo.
echo This will completely remove large files from Git history
echo Your code will be preserved, but Git history will be cleaned

echo.
set /p confirm="Proceed with complete cleanup? (y/N): "
if not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b
)

echo.
echo Step 1: Create backup of current work
git stash push -m "Backup before nuclear cleanup"

echo.
echo Step 2: Remove large files from entire Git history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch bible_embeddings.json bible_embeddings_optimized.json.gz bible_embeddings_local.json.gz bible_embeddings_part_*.json.gz" --prune-empty --tag-name-filter cat -- --all

echo.
echo Step 3: Clean up Git references
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo Step 4: Restore your work
git stash pop

echo.
echo Step 5: Add only essential files
git add main.py config.py utils.py modules/ .gitignore requirements.txt Procfile runtime.txt README.md

echo.
echo Step 6: Commit clean version
git commit -m "AI Bible Assistant - Clean version without large files"

echo.
echo Step 7: Force push to origin (overwrites remote history)
git push --force origin main

echo.
echo Done! Repository history is now completely clean.

pause

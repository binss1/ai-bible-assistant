@echo off
echo EMERGENCY: Complete Git reset to remove large files

echo.
echo WARNING: This will reset your git repository to the last commit WITHOUT large files
echo All your current code changes will be preserved in a backup branch

echo.
set /p confirm="Are you sure you want to proceed? (y/N): "
if not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit
)

echo.
echo Step 1: Create backup branch
git branch backup-before-clean

echo.
echo Step 2: Soft reset to previous commit (keeps your changes)
git reset --soft HEAD~1

echo.
echo Step 3: Unstage everything
git reset HEAD

echo.
echo Step 4: Add only essential files (no large files)
git add main.py
git add config.py  
git add utils.py
git add modules/
git add .gitignore
git add requirements.txt
git add Procfile
git add runtime.txt
git add README.md
git add test_chatbot.py
git add DEPLOY_GUIDE.md

echo.
echo Step 5: Create new clean commit
git commit -m "AI Bible Assistant - Clean deployment without large files"

echo.
echo Step 6: Force push to origin (WARNING: This overwrites remote history)
git push --force origin main

echo.
echo Done! Repository should be completely clean now.
echo Your backup is in the 'backup-before-clean' branch.

pause

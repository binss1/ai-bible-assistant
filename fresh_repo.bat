@echo off
echo Creating fresh Git repository (safest method)

echo.
echo Step 1: Backup current .git folder
move .git .git_backup

echo.
echo Step 2: Initialize new Git repository
git init

echo.
echo Step 3: Add remote origin
git remote add origin https://github.com/binss1/ai-bible-assistant.git

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
echo Step 5: Create initial commit
git commit -m "AI Bible Assistant - Initial clean commit"

echo.
echo Step 6: Force push to replace remote repository
git push --force origin main

echo.
echo Done! Fresh repository created successfully.
echo Old git history is backed up in .git_backup folder.

pause

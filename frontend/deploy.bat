@echo off
echo ========================================
echo RPA Claude Desktop - Deployment Script
echo ========================================
echo.

REM Change to frontend directory
cd /d "%~dp0"

echo [1/5] Checking if Git is initialized...
if not exist ".git" (
    echo Initializing Git repository...
    git init
    git branch -M main
)

echo.
echo [2/5] Adding files to Git...
git add .

echo.
echo [3/5] Creating commit...
git commit -m "Deploy: RPA Claude Desktop Research Proposal Generator"

echo.
echo [4/5] Setting up remote (if needed)...
REM Replace YOUR_GITHUB_USERNAME and YOUR_REPO_NAME with your actual values
REM git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
echo Please set up your GitHub remote manually:
echo   git remote add origin https://github.com/YOUR_USERNAME/rpa-claude-desktop.git
echo   git push -u origin main

echo.
echo [5/5] Push to GitHub...
echo.
echo After pushing to GitHub, deploy to Vercel:
echo   1. Go to https://vercel.com/new
echo   2. Import your GitHub repository
echo   3. Set environment variables:
echo      - NEXT_PUBLIC_API_URL = your-backend-api-url
echo      - NEXT_PUBLIC_APP_NAME = ResearchAI
echo   4. Click Deploy!
echo.
echo ========================================
echo Deployment preparation complete!
echo ========================================
pause

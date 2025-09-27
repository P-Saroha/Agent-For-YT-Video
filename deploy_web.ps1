#!/usr/bin/env powershell

Write-Host "🚀 Deploying YouTube AI Assistant to the Web..." -ForegroundColor Green

# Add all changes
Write-Host "📦 Adding files to Git..." -ForegroundColor Yellow
git add .

# Commit changes
$commitMessage = "Deploy: Enable web interface with real AI processing"
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m $commitMessage

# Push to GitHub
Write-Host "⬆️ Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "✅ Code pushed to GitHub successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to vercel.com and sign up with GitHub"
Write-Host "2. Import your 'Agent-For-YT-Video' repository"
Write-Host "3. Add environment variable: GEMINI_API_KEY = $env:GEMINI_API_KEY"
Write-Host "4. Deploy! 🚀"
Write-Host ""
Write-Host "📖 Full guide: See DEPLOYMENT_WEB.md" -ForegroundColor Magenta
Write-Host "🎯 Your app will be live at: https://your-project-name.vercel.app" -ForegroundColor Green
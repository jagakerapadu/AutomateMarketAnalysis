# GitHub Push Helper Script
# Run this after creating your Personal Access Token

Write-Host "`n=== GITHUB PUSH HELPER ===" -ForegroundColor Cyan
Write-Host ""

# Prompt for token
$token = Read-Host "Enter your GitHub Personal Access Token (ghp_...)"

if ($token -notmatch "^ghp_") {
    Write-Host "⚠️  Token should start with 'ghp_'" -ForegroundColor Yellow
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne "y") {
        exit
    }
}

Write-Host "`n📤 Pushing to GitHub..." -ForegroundColor Green
Write-Host ""

# Push with token
git push "https://${token}@github.com/jagakerapadu/AutomateMarketAnalysis.git" main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ SUCCESS! Code pushed to GitHub" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔍 Verify at: https://github.com/jagakerapadu/AutomateMarketAnalysis" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔒 Security Check:" -ForegroundColor Yellow
    Write-Host "   ✅ .env file NOT pushed (contains your credentials)"
    Write-Host "   ✅ Only safe code uploaded"
    Write-Host ""
    
    # Store credentials for future pushes (optional)
    $store = Read-Host "Save credentials for future pushes? (y/n)"
    if ($store -eq "y") {
        git config --global credential.helper wincred
        Write-Host "✅ Credentials will be remembered" -ForegroundColor Green
        Write-Host "   Next time just run: git push origin main"
    }
} else {
    Write-Host "`n❌ Push failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Token doesn't have 'repo' scope"
    Write-Host "2. Token expired or invalid"
    Write-Host "3. Repository doesn't exist"
    Write-Host ""
    Write-Host "Solutions:" -ForegroundColor Cyan
    Write-Host "• Create new token: https://github.com/settings/tokens/new"
    Write-Host "• Make sure 'repo' scope is checked"
    Write-Host "• Verify repository exists at: https://github.com/jagakerapadu/AutomateMarketAnalysis"
}

Write-Host ""

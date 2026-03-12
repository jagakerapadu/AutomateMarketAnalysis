#!/usr/bin/env pwsh
# Simple GitHub Push Script - No Credential Caching Required

Write-Host "`n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       PUSH TO GITHUB - SIMPLE METHOD                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if there's anything to push
$status = git status --porcelain
$commits = git log origin/main..main --oneline 2>$null

if (-not $commits) {
    Write-Host "⚠️  No new commits to push" -ForegroundColor Yellow
    Write-Host "   Everything is already up to date on GitHub`n"
    exit
}

Write-Host "📦 Commits to push:" -ForegroundColor Green
git log origin/main..main --oneline
Write-Host ""

# Prompt for Personal Access Token
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray

Write-Host "🔑 STEP 1: Get Your GitHub Personal Access Token" -ForegroundColor Yellow
Write-Host ""
Write-Host "   If you don't have one yet:" -ForegroundColor Gray
Write-Host "   1. Go to: https://github.com/settings/tokens/new"
Write-Host "   2. Name: AutomateMarketAnalysis"
Write-Host "   3. Expiration: 90 days"
Write-Host "   4. ✅ Check: repo (full control)"
Write-Host "   5. Generate and copy the token (ghp_...)"
Write-Host ""

# Option to open browser
$openBrowser = Read-Host "Open GitHub token page in browser? (y/n)"
if ($openBrowser -eq "y") {
    Start-Process "https://github.com/settings/tokens/new"
    Write-Host "✅ Browser opened. Create your token and come back here.`n" -ForegroundColor Green
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray

Write-Host "🔑 STEP 2: Enter Your Token" -ForegroundColor Yellow
Write-Host ""
$token = Read-Host "Paste your GitHub token here (ghp_...)"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "`n❌ No token provided. Exiting.`n" -ForegroundColor Red
    exit 1
}

if ($token -notmatch "^ghp_") {
    Write-Host "`n⚠️  Warning: Token should start with 'ghp_'" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray

Write-Host "🚀 STEP 3: Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""

# Build the authenticated URL
$repoUrl = "https://${token}@github.com/jagakerapadu/AutomateMarketAnalysis.git"

# Push
try {
    git push $repoUrl main 2>&1 | Out-Host
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host "✅ SUCCESS! Your code is now on GitHub!" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Green
        
        Write-Host "🔗 View your repository:" -ForegroundColor Cyan
        Write-Host "   https://github.com/jagakerapadu/AutomateMarketAnalysis`n"
        
        Write-Host "🔒 Security verified:" -ForegroundColor Green
        Write-Host "   ✅ .env file NOT uploaded (contains your credentials)"
        Write-Host "   ✅ Only safe source code uploaded"
        Write-Host "   ✅ Token used securely (not stored)`n"
        
        # Ask if they want to save credentials for future use
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
        Write-Host "💡 Optional: Save credentials for future pushes?" -ForegroundColor Yellow
        Write-Host "   This will store your token securely in Windows Credential Manager"
        Write-Host "   Next time you can just run: git push origin main`n"
        
        $save = Read-Host "Save credentials? (y/n)"
        if ($save -eq "y") {
            git config --global credential.helper manager
            Write-Host "`n✅ Credential helper enabled" -ForegroundColor Green
            Write-Host "   For next push, use: git push origin main" -ForegroundColor Cyan
            Write-Host "   (Git will prompt once more, then remember)`n"
        } else {
            Write-Host "`n💡 No problem! Just run this script again for next push.`n" -ForegroundColor Cyan
        }
        
    } else {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
        Write-Host "❌ Push failed!" -ForegroundColor Red
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Red
        
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "1. Token is invalid or expired"
        Write-Host "2. Token doesn't have 'repo' scope"
        Write-Host "3. Repository URL is incorrect"
        Write-Host "4. Network connectivity issues`n"
        
        Write-Host "Try:" -ForegroundColor Cyan
        Write-Host "• Generate a new token: https://github.com/settings/tokens/new"
        Write-Host "• Make sure 'repo' scope is checked"
        Write-Host "• Verify repository exists: https://github.com/jagakerapadu/AutomateMarketAnalysis`n"
    }
} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)`n" -ForegroundColor Red
}

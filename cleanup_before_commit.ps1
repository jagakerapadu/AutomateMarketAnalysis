# ============================================
# Pre-Commit Cleanup Script
# ============================================
# Removes temporary and one-time analysis files

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PRE-COMMIT CLEANUP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Files to remove (temporary/one-time analysis)
$filesToRemove = @(
    "analyze_march13_trading.py",
    "MARCH13_2026_TRADING_REPORT.md"
)

# Check what exists
Write-Host "Checking for temporary files..." -ForegroundColor Yellow
Write-Host ""

$foundFiles = @()
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        $foundFiles += $file
        Write-Host "  Found: $file" -ForegroundColor Red
    }
}

if ($foundFiles.Count -eq 0) {
    Write-Host "  No temporary files found. Ready to commit!" -ForegroundColor Green
    exit 0
}

# Ask for confirmation
Write-Host ""
Write-Host "$($foundFiles.Count) temporary file(s) found." -ForegroundColor Yellow
$response = Read-Host "Delete these files? (yes/no)"

if ($response -eq "yes" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Deleting files..." -ForegroundColor Yellow
    
    foreach ($file in $foundFiles) {
        try {
            Remove-Item $file -Force
            git rm --cached $file 2>$null
            Write-Host "  Deleted: $file" -ForegroundColor Green
        }
        catch {
            Write-Host "  Could not delete: $file" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Cleanup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review changes: git status"
    Write-Host "  2. Commit: git add . ; git commit -m 'message'"
    Write-Host "  3. Push: git push"
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "Cleanup cancelled. Files kept." -ForegroundColor Yellow
    Write-Host "Note: These files will be committed if you proceed." -ForegroundColor Yellow
    Write-Host ""
}


# Restart All Trading Services
# This script stops all running trading engines and restarts them with updated code

Write-Host ""
Write-Host "=" * 70
Write-Host "RESTARTING TRADING SERVICES"  
Write-Host "=" * 70
Write-Host ""

# Stop all trading engines
Write-Host "Stopping all trading engine processes..."
$stopped = 0

# Find and stop options trading processes
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdline -match 'options_trading|run_trading|data_fetcher') {
        Write-Host "  Stopping PID $($_.Id): $cmdline"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $stopped++
    }
}

Write-Host ""
Write-Host "[OK] Stopped $stopped process(es)"
Write-Host ""

# Wait a moment for processes to fully terminate
Start-Sleep -Seconds 2

Write-Host "Starting services with updated code..."
Write-Host ""

# Start data fetcher
Write-Host "[1/3] Starting options data updater (every 5 min)..."
Start-Process -FilePath "py" -ArgumentList "run_options_data_updater.py" -WindowStyle Normal
Start-Sleep -Seconds 1

# Start stock data fetcher  
Write-Host "[2/3] Starting stock data fetcher..."
if (Test-Path "run_data_fetcher.py") {
    Start-Process -FilePath "py" -ArgumentList "run_data_fetcher.py" -WindowStyle Normal
    Start-Sleep -Seconds 1
}

# Start options trading engine
Write-Host "[3/3] Starting options trading engine..."
if (Test-Path "run_options_trading.py") {
    Start-Process -FilePath "py" -ArgumentList "run_options_trading.py" -WindowStyle Normal
} elseif (Test-Path "start_options_trading.py") {
    Start-Process -FilePath "py" -ArgumentList "start_options_trading.py" -WindowStyle Normal
}

Write-Host ""
Write-Host "=" * 70
Write-Host "[OK] All services restarted!"
Write-Host "=" * 70
Write-Host ""
Write-Host "Services running:"
Write-Host "  1. Options Data Updater (updates prices every 5 min)"
Write-Host "  2. Stock Data Fetcher (fetches stock prices)"
Write-Host "  3. Options Trading Engine (executes trades)"
Write-Host ""
Write-Host "Check status: py check_options_status.py"
Write-Host ""

@echo off
REM Auto-start Paper Trading Engine at 9:00 AM daily
REM This script launches the paper trading engine in the background

cd /d C:\Share_Market\jagakerapadu\AutomateMarketAnalysis

echo Starting Paper Trading Engine...
echo Time: %date% %time%

REM Start in minimized window
start "Paper Trading Engine" /MIN py start_paper_trading.py

echo Paper Trading Engine started!
echo Check logs in the minimized window

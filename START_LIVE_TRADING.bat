@echo off
REM Quick Start Paper Trading for 9 AM
echo.
echo ================================================
echo  PAPER TRADING - LIVE START
echo ================================================
echo.
echo Time: %time%
echo.
echo Starting paper trading engine...
echo This will run until market closes at 3:30 PM
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

cd /d C:\Share_Market\jagakerapadu\AutomateMarketAnalysis
py start_paper_trading.py

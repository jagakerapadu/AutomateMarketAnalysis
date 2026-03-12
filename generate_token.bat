@echo off
REM Zerodha Kite Token Generator - Windows Batch Script
echo.
echo ============================================================
echo   Zerodha Kite Token Generator
echo ============================================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Error: .env file not found!
    echo Please create .env from .env.example first
    echo.
    pause
    exit /b 1
)

REM Run the Python script
py scripts\generate_kite_token.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   Token generation completed successfully!
    echo ============================================================
    echo.
) else (
    echo.
    echo ============================================================
    echo   Token generation failed. Check the error above.
    echo ============================================================
    echo.
)

pause

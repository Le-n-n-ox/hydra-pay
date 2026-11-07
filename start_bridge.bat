@echo off
title HYDRA PAY BRIDGE
cd /d "%~dp0"
echo ==========================================
echo   HYDRA PAY - laptop bridge
echo   Sends card taps to the cloud dashboard.
echo   Keep this window open while serving.
echo ==========================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
)
python -m pip install -q pyserial requests python-dotenv
python bridge.py %*
pause

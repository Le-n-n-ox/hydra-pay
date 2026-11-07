@echo off
title RFID Pay Launcher
cd /d "%~dp0"

echo ==========================================
echo   RFID PAY - Card + M-Pesa + WhatsApp
echo ==========================================

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
)

:: 2. Check ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ngrok not found. Install it and run: ngrok config add-authtoken YOUR_TOKEN
    pause
    exit /b 1
)

:: 3. Check keys
if not exist ".env" (
    echo [WARNING] No .env file - WhatsApp, AI and voice notes will be OFF.
    pause
)
if not exist "mpesa_config.json" echo [WARNING] No mpesa_config.json - M-Pesa prompts will not work.

:: 4. Install requirements
echo Installing requirements...
python -m pip install -q pyserial flask requests python-dotenv

:: 5. Is port 8000 already taken (old dashboard still running)?
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Something is already using port 8000. Close old RFID PAY windows first,
    echo           or the new one cannot start and ngrok will say Bad Gateway.
    pause
)

:: 6. Is an old ngrok (e.g. AquaTrace on port 5000) running? Free ngrok allows only one.
tasklist /FI "IMAGENAME eq ngrok.exe" | find /I "ngrok.exe" >nul
if not errorlevel 1 (
    echo [WARNING] ngrok is already running ^(maybe AquaTrace^). Close that NGROK window first.
    pause
)

:: 7. Start ngrok and the dashboard/bot in their own windows (kept open)
echo Starting ngrok...
start "NGROK" cmd /k ngrok http 127.0.0.1:8000
echo Starting RFID Pay (dashboard + WhatsApp bot)...
start "RFID PAY" cmd /k python dashboard.py

:: 8. Wait for ngrok and read its HTTPS URL
set NGROK_URL=
set TRIES=0
:waitloop
set /a TRIES+=1
timeout /t 2 /nobreak >nul
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0get_ngrok_url.ps1"') do set NGROK_URL=%%i
if "%NGROK_URL%"=="" if %TRIES% LSS 10 goto waitloop

echo.
if "%NGROK_URL%"=="" (
    echo [!] Could not read the ngrok URL. Look at the NGROK window and copy the https link.
) else (
    echo ==========================================
    echo  The bot sets this in UltraMsg by itself.
    echo  If WhatsApp doesn't reply, paste it into
    echo  ULTRAMSG ^> Settings ^> Webhook URL:
    echo.
    echo    %NGROK_URL%/webhook
    echo.
    echo ==========================================
    echo %NGROK_URL%/webhook| clip
    echo (Already copied to your clipboard)
)

:: 9. Check the dashboard itself is answering
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/login -TimeoutSec 5).StatusCode | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo.
    echo [!!] RFID Pay is NOT answering on port 8000, so ngrok will show "Bad Gateway".
    echo      Look at the RFID PAY window - the red error text there is the reason.
) else (
    echo [OK] RFID Pay is running.  Dashboard: http://localhost:8000
)
echo.
echo Keep the NGROK and RFID PAY windows open. You can close this one.
pause

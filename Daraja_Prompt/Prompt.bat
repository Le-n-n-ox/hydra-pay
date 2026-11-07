@echo off
title M-Pesa Prompt
cd /d "%~dp0"
:again
echo 1) Send payment prompt
echo 2) Price quote
echo 3) Wallet balance
echo 4) Create wallet (first time only)
echo 5) Get test USDT (test mode only)
set CHOICE=
set /p CHOICE=Choose (1-5):
if "%CHOICE%"=="2" (python prompt.py quote
) else if "%CHOICE%"=="3" (python wallet.py balance
) else if "%CHOICE%"=="4" (python wallet.py new
) else if "%CHOICE%"=="5" (python wallet.py setup-test
) else (python prompt.py)
echo.
set MORE=
set /p MORE=Again? (y/n):
if /i "%MORE%"=="y" goto again

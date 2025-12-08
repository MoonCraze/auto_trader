@echo off
REM Quick Start Script for Auto Trader Bot Multi-User System
REM This script helps launch all required services

echo ================================================
echo    AUTO TRADER BOT - MULTI-USER SYSTEM
echo ================================================
echo.

:menu
echo Choose an option:
echo.
echo 1. Initialize Database (First Time Setup)
echo 2. Create Demo Users
echo 3. Start WebSocket Server (Port 8765)
echo 4. Start API Server (Port 8000)
echo 5. Start Frontend (Port 5173)
echo 6. Show Demo Wallet Addresses
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto init_db
if "%choice%"=="2" goto demo_users
if "%choice%"=="3" goto ws_server
if "%choice%"=="4" goto api_server
if "%choice%"=="5" goto frontend
if "%choice%"=="6" goto show_wallets
if "%choice%"=="7" goto end
goto menu

:init_db
echo.
echo [Initializing Database...]
python database.py
echo.
pause
goto menu

:demo_users
echo.
echo [Creating Demo Users...]
python test_setup.py
echo.
pause
goto menu

:ws_server
echo.
echo [Starting WebSocket Server on port 8765...]
echo Press Ctrl+C to stop
python websocket_server.py
goto menu

:api_server
echo.
echo [Starting API Server on port 8000...]
echo Press Ctrl+C to stop
python api_server.py
goto menu

:frontend
echo.
echo [Starting Frontend...]
cd bot-ui-ts
npm run dev
cd ..
goto menu

:show_wallets
echo.
echo ================================================
echo           DEMO WALLET ADDRESSES
echo ================================================
echo.
type DEMO_WALLETS.md
echo.
pause
goto menu

:end
echo.
echo Thanks for using Auto Trader Bot!
echo.
exit

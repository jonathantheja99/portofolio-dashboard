@echo off
REM ============================================================
REM  Portfolio Dashboard - one-click start
REM  1. pulls the latest version from GitHub (if this is a git clone)
REM  2. builds the .exe only when the app code changed (or first run)
REM  3. copies your watchlist + config.local.js next to the exe
REM  4. creates a Desktop shortcut (first run) and launches the app
REM ============================================================
setlocal
title Portfolio Dashboard

REM Run from a temp copy, so "git pull" can safely update this very file.
if /i not "%~1"=="--from-temp" (
  copy /Y "%~f0" "%TEMP%\portfolio-dashboard-start.bat" >nul
  "%TEMP%\portfolio-dashboard-start.bat" --from-temp "%~dp0"
)
set "ROOT=%~2"
cd /d "%ROOT%"

set "EXE=dist\PortfolioDashboard.exe"
set "STAMP=dist\.build-stamp"
set "WANT=nogit"

echo [1/4] Checking GitHub for updates...
where git >nul 2>&1
if not errorlevel 1 if exist ".git" (
  git pull --ff-only --quiet
  if errorlevel 1 echo       Couldn't update from GitHub - using the copy you have.
  for /f %%h in ('git log -1 --format^=%%H -- dashboard.py requirements.txt build.bat') do set "WANT=%%h"
)

set "HAVE="
if exist "%STAMP%" set /p HAVE=<"%STAMP%"
set "NEED=0"
if not exist "%EXE%" set "NEED=1"
if not "%WANT%"=="nogit" if not "%WANT%"=="%HAVE%" set "NEED=1"

if "%NEED%"=="1" (
  echo [2/4] Building the app - the first time takes a minute or two...
  where python >nul 2>&1
  if errorlevel 1 (
    echo.
    echo Python not found. Install Python 3.10+ from python.org and tick "Add python.exe to PATH".
    pause
    exit /b 1
  )
  taskkill /im PortfolioDashboard.exe /f >nul 2>&1
  call build.bat
  if errorlevel 1 goto :fail
  (echo %WANT%)>"%STAMP%"
) else (
  echo [2/4] App is already up to date.
)

echo [3/4] Copying your watchlist and settings...
copy /Y dashboard.html dist\dashboard.html >nul
if exist config.local.js copy /Y config.local.js dist\config.local.js >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$l = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Portfolio Dashboard.lnk';" ^
  "if (-not (Test-Path $l)) {" ^
  "  $s = (New-Object -ComObject WScript.Shell).CreateShortcut($l);" ^
  "  $s.TargetPath = '%ROOT%start-dashboard.bat'; $s.WorkingDirectory = '%ROOT%'; $s.WindowStyle = 7;" ^
  "  $s.IconLocation = '%ROOT%dist\PortfolioDashboard.exe,0'; $s.Save();" ^
  "  Write-Host '      Desktop shortcut created: Portfolio Dashboard' }"

echo [4/4] Launching...
taskkill /im PortfolioDashboard.exe /f >nul 2>&1
start "" "%EXE%"
exit /b 0

:fail
echo.
echo Build failed - scroll up to see the error.
pause
exit /b 1

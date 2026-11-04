@echo off
REM Builds dist\PortfolioDashboard.exe (single file, no console window).
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller || goto :error
python -m PyInstaller --noconfirm --onefile --windowed --name PortfolioDashboard ^
  --add-data "dashboard.html;." dashboard.py || goto :error
REM A copy next to the exe overrides the bundled one, so you can edit your watchlist without rebuilding.
copy /Y dashboard.html dist\dashboard.html >nul
if exist config.local.js copy /Y config.local.js dist\config.local.js >nul
echo.
echo Done: dist\PortfolioDashboard.exe
goto :eof
:error
echo Build failed.
exit /b 1

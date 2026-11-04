@echo off
REM Run from source without a console window.
cd /d "%~dp0"
start "" pythonw dashboard.py

@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if not errorlevel 1 (
    python main.py
) else (
    py -3 main.py
)
echo.
pause

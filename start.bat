@echo off
echo ============================================
echo   EduAI Platform - Python FastAPI
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

echo [2/3] Activating venv and installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/3] Starting EduAI Platform...
echo.
echo ============================================
echo   Open: http://localhost:8000
echo   API Docs: http://localhost:8000/api/docs
echo ============================================
echo.
python main.py
pause

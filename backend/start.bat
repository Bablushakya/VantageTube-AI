@echo off
REM VantageTube AI - Backend Startup Script (Windows)

echo ========================================
echo   VantageTube AI - Backend Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file with your Supabase credentials.
    echo You can copy from .env.example
    echo.
    pause
    exit /b 1
)

REM Test connection
echo [2/3] Testing connections...
python test_connection.py
if errorlevel 1 (
    echo.
    echo [WARNING] Connection tests had some issues, but continuing anyway...
    echo The server might still work. Check the errors above if you have problems.
    echo.
    timeout /t 3 >nul
)

REM Start server
echo.
echo [3/3] Starting FastAPI server...
echo.
echo Server will start at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

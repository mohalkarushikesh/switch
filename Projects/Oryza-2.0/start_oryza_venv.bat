@echo off
echo ========================================================
echo.
echo    ORYZA - AI-POWERED WEALTH MANAGEMENT PLATFORM
echo.
echo ========================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

echo Starting Oryza Platform with Virtual Environment...
echo.

REM Kill any existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul

timeout /t 2 /nobreak >nul

REM Create virtual environment if it doesn't exist
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    cd backend
    python -m venv venv
    cd ..
    echo Virtual environment created.
)

REM Install backend dependencies first
echo Installing backend dependencies...
start "Backend Setup" /wait cmd /c "cd backend && venv\Scripts\activate && pip install bcrypt fastapi uvicorn pydantic python-jose passlib python-multipart && exit"

REM Start backend with virtual environment
echo [1/2] Starting Backend API with venv (Port 8889)...
start "Oryza Backend API" cmd /k "cd backend && venv\Scripts\activate && python test_api_for_frontend.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if backend started
netstat -an | find ":8889" | find "LISTENING" >nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Backend may not have started yet on port 8889
    echo Continuing anyway...
)

echo.
echo [2/2] Starting Frontend (Port 3000)...
start "Oryza Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================================
echo.
echo    ORYZA PLATFORM IS STARTING UP!
echo.
echo    Two new windows will open:
echo    1. Backend API window (Python with venv)
echo    2. Frontend window (React)
echo.
echo    The frontend will take a moment to compile...
echo    It will automatically open in your browser when ready!
echo.
echo    Services:
echo    - Frontend:    http://localhost:3000
echo    - Backend API: http://localhost:8889
echo.
echo    Login Credentials:
echo    - Email: test@example.com  Password: test123
echo    - Email: test@oryza.com    Password: test@123
echo.
echo    Press any key to stop all services...
echo.
echo ========================================================
echo.

pause > nul

REM Kill the processes when done
echo.
echo Stopping services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul
echo Services stopped.
echo. 
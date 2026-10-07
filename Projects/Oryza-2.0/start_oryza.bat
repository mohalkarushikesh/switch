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

echo Starting Oryza Platform...
echo.

REM Kill any existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8002') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8006') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul

timeout /t 2 /nobreak >nul

REM Check if virtual environment exists
if not exist "venv" (
    echo ERROR: Virtual environment not found at .\venv
    echo Please create it by running: python -m venv venv
    echo Then install dependencies: venv\Scripts\activate && pip install -r backend\requirements.txt
    pause
    exit /b 1
)

REM Start websocket-service (8002)
echo [1/4] Starting WebSocket Service (Port 8002)...
start "Oryza WebSocket Service" cmd /k "venv\Scripts\activate && python -m uvicorn backend.services.websocket-service.src.main:app --host 0.0.0.0 --port 8002 --reload"

REM Start market-service (8006)
echo [2/4] Starting Market Service (Port 8006)...
start "Oryza Market Service" cmd /k "venv\Scripts\activate && python -m uvicorn backend.services.market-service.src.main:app --host 0.0.0.0 --port 8006 --reload"

REM Start test API (8889) - proxies to market-service
echo [3/4] Starting Backend Test API (Port 8889)...
start "Oryza Backend API" cmd /k "set MARKET_SERVICE_URL=http://localhost:8006 && venv\Scripts\activate && python -m uvicorn backend.test_api_for_frontend:app --host 0.0.0.0 --port 8889 --reload"

echo Waiting for backend services to start...
timeout /t 5 /nobreak >nul

REM Check if services started
for %%P in (8002 8006 8889) do (
  netstat -an | find ":%%P" | find "LISTENING" >nul
  if %ERRORLEVEL% NEQ 0 (
      echo WARNING: Service may not have started yet on port %%P
  )
)

REM Fix frontend dependencies
echo Fixing frontend dependencies...
cd frontend
if exist "node_modules" (
    echo Installing ajv fix...
    call npm install ajv@^8.0.0 ajv-keywords@^5.0.0 --save --legacy-peer-deps
)
cd ..

echo.
echo [4/4] Starting Frontend (Port 3000)...
start "Oryza Frontend" cmd /k "venv\Scripts\activate && cd frontend && npm start"

echo.
echo ========================================================
echo.
echo    ORYZA PLATFORM IS STARTING UP!
echo.
echo    Four windows will open:
echo    1. WebSocket Service (Python)   - http://localhost:8002
echo    2. Market Service (Python)      - http://localhost:8006
echo    3. Backend API (Python, proxy)  - http://localhost:8889
echo    4. Frontend (React)              - http://localhost:3000
echo.
echo    The frontend will take a moment to compile...
echo    It will automatically open in your browser when ready!
echo.
echo ========================================================
echo.

pause > nul

REM Kill the processes when done
echo.
echo Stopping services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8002') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8006') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul
echo Services stopped.
echo. 
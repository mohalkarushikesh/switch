@echo off
echo Starting Oryza Demo (Simple Mode)...
echo ===================================

REM Kill any existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 2>nul

echo.
echo Starting Backend Test API...
start "Backend API" cmd /k "venv\Scripts\activate && cd backend && python test_api_for_frontend.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak

echo.
echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo ===================================
echo Demo is starting up!
echo.
echo Services will be available at:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8889
echo.
echo Login with:
echo   Email: test@oryza.com
echo   Password: test@123
echo.
echo Press any key to stop the demo...
pause > nul

REM Kill the processes when done
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8889') do taskkill /F /PID %%a
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a 
@echo off
echo Starting Oryza Services Without Docker...
echo =========================================

REM Kill any existing processes on our ports
echo Killing processes on ports 8080-8005...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8002') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8003') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8004') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8005') do taskkill /F /PID %%a 2>nul

echo.
echo Starting Backend Services...
echo ===========================

REM Start Auth Service
echo Starting Auth Service on port 8001...
start "Auth Service" cmd /k "cd backend\services\auth-service && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && cd src && python main.py"

REM Start WebSocket Service
echo Starting WebSocket Service on port 8002...
start "WebSocket Service" cmd /k "cd backend\services\websocket-service && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && cd src && python main.py"

REM Start Portfolio Service
echo Starting Portfolio Service on port 8003...
start "Portfolio Service" cmd /k "cd backend\services\portfolio-service && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && cd src && python main.py"

REM Start Trading Service
echo Starting Trading Service on port 8004...
start "Trading Service" cmd /k "cd backend\services\trading-service && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && cd src && python main.py"

REM Start Market Service
echo Starting Market Data Service on port 8005...
start "Market Service" cmd /k "cd backend\services\market-service && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && cd src && python main.py"

timeout /t 10 /nobreak

REM Start API Gateway (needs other services running first)
echo Starting API Gateway on port 8080...
start "API Gateway" cmd /k "cd backend\services\api-gateway && venv\Scripts\activate && cd src && python main_gateway.py"

echo.
echo Starting Frontend...
echo ===================
timeout /t 5 /nobreak
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo =========================================
echo All services starting up...
echo.
echo Services will be available at:
echo - Frontend: http://localhost:3000
echo - API Gateway: http://localhost:8080
echo - Auth Service: http://localhost:8001
echo - WebSocket: ws://localhost:8002
echo - Portfolio: http://localhost:8003
echo - Trading: http://localhost:8004
echo - Market Data: http://localhost:8005
echo.
echo Press any key to exit (services will continue running)...
pause > nul 
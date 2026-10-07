@echo off
echo ==========================================
echo Oryza API Keys Setup Script
echo ==========================================
echo.

REM Check if .env exists
if exist .env (
    echo WARNING: .env file already exists!
    echo.
    set /p overwrite="Do you want to overwrite it? (y/n): "
    if /i not "%overwrite%"=="y" (
        echo Setup cancelled.
        exit /b 1
    )
)

echo Creating .env file with demo values...
echo.

REM Create .env file
(
echo # Oryza Environment Configuration
echo # Generated on %date% %time%
echo.
echo # ==========================================
echo # ESSENTIAL API KEYS - Get these first!
echo # ==========================================
echo.
echo # Alpha Vantage - Free key at: https://www.alphavantage.co/support/#api-key
echo REACT_APP_ALPHA_VANTAGE_API_KEY=demo
echo.
echo # NewsAPI - Free key at: https://newsapi.org/register  
echo REACT_APP_NEWS_API_KEY=YOUR_NEWSAPI_KEY_HERE
echo.
echo # ==========================================
echo # SECURITY - Generate these!
echo # ==========================================
echo.
echo JWT_SECRET_KEY=CHANGE_THIS_TO_A_VERY_LONG_RANDOM_STRING
echo JWT_REFRESH_SECRET_KEY=CHANGE_THIS_TO_ANOTHER_RANDOM_STRING
echo.
echo # ==========================================
echo # DATABASE (Docker defaults^)
echo # ==========================================
echo.
echo DATABASE_URL=postgresql://oryza_user:oryza_password@localhost:5432/oryza_db
echo MONGODB_URL=mongodb://oryza_user:oryza_password@localhost:27017/oryza_db
echo REDIS_URL=redis://localhost:6379/0
echo.
echo # ==========================================
echo # SERVICE URLS (Don't change for local^)
echo # ==========================================
echo.
echo API_GATEWAY_URL=http://localhost:8080
echo MARKET_SERVICE_URL=http://localhost:8005
echo NEWS_SERVICE_URL=http://localhost:8006
echo.
echo # Environment
echo NODE_ENV=development
echo DEBUG=true
) > .env

echo .env file created successfully!
echo.

REM Create frontend .env if it doesn't exist
if not exist frontend\.env (
    echo Creating frontend\.env...
    copy .env frontend\.env >nul
    echo frontend\.env created!
)

echo ==========================================
echo NEXT STEPS:
echo ==========================================
echo.
echo 1. Get your FREE API keys:
echo    - Alpha Vantage: https://www.alphavantage.co/support/#api-key
echo    - NewsAPI: https://newsapi.org/register
echo.
echo 2. Edit .env file and replace placeholder values
echo.
echo 3. Generate secure JWT secrets by running:
echo    node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
echo.
echo 4. Start the application:
echo    - Run: start_oryza.bat
echo    - Or: docker-compose up -d
echo.
echo ==========================================
echo.
echo Press any key to open .env file in notepad...
pause >nul
notepad .env 
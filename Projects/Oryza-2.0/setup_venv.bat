@echo off
echo ========================================================
echo.
echo    ORYZA - VIRTUAL ENVIRONMENT SETUP
echo.
echo ========================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

REM Create virtual environment
if exist "venv" (
    echo Virtual environment already exists at .\venv
    echo.
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate and install dependencies
echo Activating virtual environment and installing dependencies...
echo.

call venv\Scripts\activate

echo Installing backend dependencies from requirements.txt...
pip install -r backend\requirements.txt

echo.
echo Installing additional packages that might be missing...
pip install aiofiles python-dotenv websockets requests beautifulsoup4 lxml alpha-vantage newsapi-python matplotlib seaborn

echo.
echo ========================================================
echo.
echo    VIRTUAL ENVIRONMENT SETUP COMPLETE!
echo.
echo    You can now run: start_oryza.bat
echo.
echo ========================================================
echo.

pause 
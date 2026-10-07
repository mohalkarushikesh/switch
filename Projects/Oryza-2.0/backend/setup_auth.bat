@echo off
echo Setting up authentication dependencies...
echo.

REM Install bcrypt for password hashing
echo Installing bcrypt...
pip install bcrypt

REM Install PyJWT for token generation
echo Installing PyJWT...
pip install PyJWT

REM Test database setup
echo.
echo Testing database setup...
cd /d "%~dp0"
python test_database.py

echo.
echo Setup complete!
echo You can now run start_oryza.bat to start the application.
echo.
pause 
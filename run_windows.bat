@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PYTHON=py) else (set PYTHON=python)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Created .env configuration file.
    echo Open .env and enter your MySQL password in DB_PASSWORD.
    echo Save the file, then double-click run_windows.bat again.
    echo.
    pause
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    %PYTHON% -m venv .venv
    if errorlevel 1 goto error
)

echo Installing / checking Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo Starting CogniPlan at http://127.0.0.1:5000
".venv\Scripts\python.exe" server.py
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo Setup failed. Read the error above and check Python installation / internet access.
pause
exit /b 1

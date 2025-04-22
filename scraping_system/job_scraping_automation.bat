@echo off
setlocal enabledelayedexpansion

REM Set working directory and environment paths
set WORK_DIR=C:\working\job_rcm\job_rcm_code
set ENV_DIR=%WORK_DIR%\env
set SCRIPT_DIR=%WORK_DIR%\job_scraping\scraping_system
set PYTHON_EXE=%ENV_DIR%\Scripts\python.exe

REM Display start message
echo Starting job scraping automation...
echo Working directory: %WORK_DIR%
echo Python interpreter: %PYTHON_EXE%
echo.

REM Check if Python interpreter exists
if not exist "%PYTHON_EXE%" (
    echo Python interpreter not found at %PYTHON_EXE%
    echo Exiting.
    pause
    exit /b 1
)

REM Change to script directory
cd /d %SCRIPT_DIR%
if %ERRORLEVEL% neq 0 (
    echo Failed to change directory to %SCRIPT_DIR%. Exiting.
    pause
    exit /b 1
)

REM Run script with the virtual environment's Python directly
echo Running update_scrape.py with virtual environment Python...
"%PYTHON_EXE%" update_scrape.py
if %ERRORLEVEL% neq 0 (
    echo Script execution failed with error code %ERRORLEVEL%.
) else (
    echo Script executed successfully.
)

echo.
echo Job scraping automation completed.
pause
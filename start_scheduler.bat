@echo off
echo Starting Zikr scheduler at %date% %time%

:: Change to the script's directory
cd /d "%~dp0"

:: Create logs directory if it doesn't exist
mkdir logs 2>nul

:: Log startup
echo [%date% %time%] Scheduler starting up >> logs\startup_log.txt

:: Direct path to Python in conda environment
set PYTHON_PATH=C:\Users\USCS\miniconda3\envs\azkar-bot\python.exe

:: Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo [%date% %time%] ERROR: Python not found at %PYTHON_PATH% >> logs\startup_log.txt
    echo Python not found at specified path. Please check the path in the script.
    exit /b 1
)

:: Run the scheduler without daemon mode (better for Windows Task Scheduler)
echo [%date% %time%] Running command: "%PYTHON_PATH%" -m interfaces.cli scheduler --start >> logs\startup_log.txt

"%PYTHON_PATH%" -m interfaces.cli scheduler --start
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERROR: Scheduler failed with exit code %ERRORLEVEL% >> logs\startup_log.txt
    echo Scheduler failed to start. Check logs for details.
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Scheduler script completed with code %ERRORLEVEL% >> logs\startup_log.txt
exit /b 0
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ========================================
echo       Traffic and Motion Analytics
echo ========================================
echo.

set "PYTHON_CMD="
if exist "venv\Scripts\python.exe" (
    call "venv\Scripts\activate.bat"
    set "PYTHON_CMD=python"
) else if exist ".venv\Scripts\python.exe" (
    call ".venv\Scripts\activate.bat"
    set "PYTHON_CMD=python"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 set "PYTHON_CMD=py"
    )
)

if "%PYTHON_CMD%"=="" (
    echo Python not found. Please install Python 3.8+ or add to PATH.
    pause
    exit /b 1
)

:: check packages
"%PYTHON_CMD%" -c "import cv2, numpy, pandas" >nul 2>&1
if !errorlevel! neq 0 (
    echo Installing requirements...
    "%PYTHON_CMD%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
)

set "HAS_INPUT=0"
for %%A in (%*) do (
    if "%%A"=="--input" set "HAS_INPUT=1"
    if "%%A"=="-i" set "HAS_INPUT=1"
)

if not "%~1"=="" (
    if not "%~1"=="--no-display" (
        if not "%~1"=="--output-video" (
            if not "%~1"=="-o" (
                if not "%~1"=="--save-csv" (
                    if not "%~1"=="-c" (
                        set "HAS_INPUT=1"
                    )
                )
            )
        )
    )
)

set "INPUT_ARG="

if "!HAS_INPUT!"=="0" (
    echo Choose video source:
    echo   [1] sample_traffic.mp4 [Default]
    echo   [2] Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4
    echo   [3] Live Webcam
    echo   [4] Custom path or drag and drop video
    echo.
    set "CHOICE="
    set /p "CHOICE=Select [1-4] (default 1): "
    echo.

    set "CHOICE_CLEAN="
    for /f "tokens=1" %%C in ("!CHOICE!") do set "CHOICE_CLEAN=%%C"

    if "!CHOICE_CLEAN!"=="1" (
        set "INPUT_ARG=--input "sample_traffic.mp4""
    ) else if "!CHOICE_CLEAN!"=="2" (
        set "INPUT_ARG=--input "Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4""
    ) else if "!CHOICE_CLEAN!"=="3" (
        set "INPUT_ARG=--input 0"
    ) else if "!CHOICE_CLEAN!"=="4" (
        set /p "CUSTOM_PATH=Enter video path: "
        for /f "usebackq delims=" %%I in ('!CUSTOM_PATH!') do set "CUSTOM_PATH=%%~I"
        if not "!CUSTOM_PATH!"=="" (
            set "INPUT_ARG=--input "!CUSTOM_PATH!""
        ) else (
            set "INPUT_ARG=--input "sample_traffic.mp4""
        )
    ) else if "!CHOICE_CLEAN!"=="" (
        set "INPUT_ARG=--input "sample_traffic.mp4""
    ) else (
        for /f "usebackq delims=" %%I in ('!CHOICE!') do set "CUSTOM_PATH=%%~I"
        set "INPUT_ARG=--input "!CUSTOM_PATH!""
    )
)

"%PYTHON_CMD%" main.py !INPUT_ARG! %*
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% neq 0 (
    echo.
    pause
) else if "%~1"=="" (
    echo.
    pause
)

exit /b %EXIT_CODE%

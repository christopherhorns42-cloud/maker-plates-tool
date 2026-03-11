@echo off
echo ============================================
echo  Maker Plates Generator - First Time Setup
echo ============================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

pip install flask reportlab ezdxf

echo.
echo ============================================
echo  Setup complete! Run start.bat to launch.
echo ============================================
pause

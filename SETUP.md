@echo off
echo ========================================
echo Relationship Compatibility Predictor
echo Automated Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Installing dependencies...
pip install Flask==3.0.0 Werkzeug==3.0.1 scikit-learn==1.3.2 numpy==1.26.2 pandas==2.1.3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/6] Creating project folders...
if not exist utils mkdir utils
if not exist data mkdir data
if not exist models mkdir models
if not exist templates mkdir templates
if not exist static\css mkdir static\css
if not exist static\js mkdir static\js

echo [5/6] Creating utils __init__.py...
type nul > utils\__init__.py

echo [6/6] Setup complete!
echo.
echo ========================================
echo SETUP SUCCESSFUL!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure all .py, .html, .css, and .js files are in their correct folders
echo 2. Run: python app.py
echo 3. Open browser: http://localhost:5000
echo.
echo To activate virtual environment later:
echo   venv\Scripts\activate
echo.
echo To deactivate:
echo   deactivate
echo.
pause

@echo off
echo ========================================
echo PII Detection Software Setup
echo ========================================

REM Check Python version
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or 3.11 from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Download spaCy model
echo.
echo Downloading spaCy model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo WARNING: Failed to download spaCy model
    echo You may need to run: python -m spacy download en_core_web_sm manually
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To run the PII detection tool:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run analysis: python main.py -i sample_data/test_data.csv -o report.json
echo.
echo To deactivate virtual environment: deactivate
echo.
pause

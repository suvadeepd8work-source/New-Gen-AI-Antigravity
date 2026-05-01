@echo off
echo ==================================================
echo AI Restaurant Recommendation Service - Startup Script
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from the Microsoft Store or python.org to run this project.
    pause
    exit /b
)

echo.
echo [*] Installing all required Python dependencies...
pip install pandas datasets pytest fastapi uvicorn groq pydantic python-dotenv httpx streamlit requests

echo.
echo [*] Phase 1: Downloading and Cleaning Zomato Dataset...
cd phase1
python data_preparation.py
cd ..

echo.
echo [*] Phase 2: Setting up SQLite Database...
cd phase2
python database_setup.py
cd ..

echo.
echo [*] Phase 3: Starting FastAPI Backend Server in a new window...
cd phase3
start cmd /k "title FastAPI Backend && python main.py"
cd ..

echo.
echo [*] Phase 5: Starting Streamlit Frontend in a new window...
start cmd /k "title Streamlit Frontend && streamlit run phase5/streamlit_app.py"

echo.
echo ==================================================
echo SUCCESS! Everything is running.
echo FastAPI Backend is on http://localhost:8000
echo Streamlit UI is opening in your default web browser...
echo ==================================================
pause

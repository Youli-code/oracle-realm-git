@echo off
echo === Activating the Oracle ===
cd /d "C:\Users\Youli\AI KB Management"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Uvicorn API server
start "FastAPI Oracle Server" cmd /k "uvicorn main:app --host localhost --port 8000"

REM Start local web server for frontend
start "Frontend Server (Port 5500)" cmd /k "python -m http.server 5500"

REM Open browser to the index page
start http://localhost:5500/index.html

echo === All systems go. Oracle is online. ===

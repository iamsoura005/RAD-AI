@echo off
cd /d "%~dp0"
echo Starting RadiAI Backend...
echo.
echo Make sure you set your GEMINI_API_KEY in .env
echo.
if exist "%~dp0..\.venv\Scripts\python.exe" (
	"%~dp0..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) else (
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
)
pause

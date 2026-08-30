@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo First run detected. Starting setup...
  powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
)
if not exist .venv\Scripts\python.exe (
  echo Setup failed. Please read the message above.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m app.main
if errorlevel 1 pause

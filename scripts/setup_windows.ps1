$ErrorActionPreference = "Stop"

Write-Host "[1/4] Checking Python..."
python --version

Write-Host "[2/4] Creating virtual environment..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "[3/4] Installing project..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e .

Write-Host "[4/4] Checking FFmpeg..."
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "FFmpeg was not found in PATH. Install FFmpeg, then re-open this terminal."
} else {
    & .\.venv\Scripts\python.exe -m app.doctor
}

Write-Host "Setup finished. Run run_windows.bat to launch the desktop app."

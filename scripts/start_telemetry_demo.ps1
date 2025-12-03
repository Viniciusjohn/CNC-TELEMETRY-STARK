# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found! Please install Python."
    exit 1
}

# Check for Node
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js (npm) not found! Please install Node.js."
    exit 1
}

$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
Set-Location $PROJECT_ROOT

Write-Host "=== CNC Telemetry Demo Launcher ===" -ForegroundColor Cyan

# --- Backend Setup ---
Write-Host "`n[1/4] Setting up Backend..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

$PYTHON_EXE = ".\.venv\Scripts\python.exe"
$PIP_EXE = ".\.venv\Scripts\pip.exe"

if (-not (Test-Path $PYTHON_EXE)) {
    # Fallback for some systems where Scripts might be lowercase or different
    $PYTHON_EXE = ".\.venv\bin\python"
    $PIP_EXE = ".\.venv\bin\pip"
}

Write-Host "Installing/Updating Python dependencies..."
& $PIP_EXE install -r backend/requirements.txt | Out-Null

# --- Frontend Setup ---
Write-Host "`n[2/4] Setting up Frontend..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node modules (first run only)..."
    npm install
}

# --- Start Services ---
Write-Host "`n[3/4] Starting Services..." -ForegroundColor Yellow

# Start Backend in a NEW window so it runs in background relative to this script
Write-Host "Starting Backend (Port 8000) in a new window..."
$backendProc = Start-Process -FilePath $PYTHON_EXE -ArgumentList "-m backend.main" -PassThru

# Open Browser slightly delayed
Write-Host "`n[4/4] Launching Browser..." -ForegroundColor Yellow
Start-ThreadJob -ScriptBlock {
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:5173"
} | Out-Null

# Start Frontend in THIS window (Blocking)
Write-Host "Starting Frontend (Port 5173)..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the demo." -ForegroundColor Gray

# Use npm.cmd explicitly
if ($IsWindows) {
    npm.cmd run dev
} else {
    npm run dev
}

# Cleanup (runs when user Ctrl+C)
Stop-Process -Id $backendProc.Id -ErrorAction SilentlyContinue
Write-Host "Demo stopped."

# Check for Python
try {
    $pyVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python execution failed" }
} catch {
    # Try to self-heal PATH for common Winget installs
    Write-Host "Python not found in current PATH. Checking common locations..." -ForegroundColor Yellow
    $potentialPaths = @(
        "$env:LOCALAPPDATA\Microsoft\WindowsApps",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:ProgramFiles\Python311",
        "$env:ProgramFiles\Python312"
    )
    
    foreach ($path in $potentialPaths) {
        if (Test-Path "$path\python.exe") {
            Write-Host "Found Python at $path. Adding to PATH..." -ForegroundColor Green
            $env:Path = "$path;$env:Path"
            break
        }
    }

    try {
        $pyVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Still failed" }
    } catch {
        Write-Error "Python not found! Please install Python."
        Write-Host "Try installing via Winget: winget install Python.Python.3.11" -ForegroundColor Gray
        exit 1
    }
}

# Check for Node
try {
    $npmVersion = npm.cmd --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "NPM execution failed" }
} catch {
     # Try to self-heal PATH for Node
    Write-Host "Node/NPM not found. Checking common locations..." -ForegroundColor Yellow
    $nodePath = "$env:ProgramFiles\nodejs"
    if (Test-Path "$nodePath\npm.cmd") {
        Write-Host "Found Node at $nodePath. Adding to PATH..." -ForegroundColor Green
        $env:Path = "$nodePath;$env:Path"
    }
    
    try {
        $npmVersion = npm.cmd --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Still failed" }
    } catch {
        Write-Error "Node.js (npm) not found! Please install Node.js."
        Write-Host "Try installing via Winget: winget install OpenJS.NodeJS" -ForegroundColor Gray
        exit 1
    }
}

$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
Set-Location $PROJECT_ROOT

Write-Host "=== CNC Telemetry Demo Launcher ===" -ForegroundColor Cyan

# --- Backend Setup ---
Write-Host "`n[1/4] Setting up Backend..." -ForegroundColor Yellow
$PYTHON_EXE = ".\.venv\Scripts\python.exe"
$PIP_EXE = ".\.venv\Scripts\pip.exe"

# Validate existing venv
if (Test-Path ".venv") {
    if (Test-Path $PYTHON_EXE) {
        try {
            & $PYTHON_EXE --version | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Venv python broken" }
        } catch {
            Write-Host "Existing virtual environment is broken. Recreating..." -ForegroundColor Red
            Remove-Item -Path ".venv" -Recurse -Force
        }
    } else {
        Write-Host "Existing virtual environment incomplete. Recreating..." -ForegroundColor Red
        Remove-Item -Path ".venv" -Recurse -Force
    }
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

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

# Use npm.cmd explicitly on Windows
if ($IsWindows) {
    npm.cmd run dev
} else {
    npm run dev
}

# Cleanup (runs when user Ctrl+C)
Stop-Process -Id $backendProc.Id -ErrorAction SilentlyContinue
Write-Host "Demo stopped."

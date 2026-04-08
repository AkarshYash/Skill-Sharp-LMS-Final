Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  EduAI Platform - Python FastAPI" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Check Python
try { $v = python --version; Write-Host "[OK] $v" -ForegroundColor Green }
catch { Write-Host "[ERROR] Python not found. Install from https://python.org" -ForegroundColor Red; exit 1 }

# Create venv
if(!(Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate and install
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& "venv\Scripts\activate.ps1"
pip install -r requirements.txt --quiet

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  Open: http://localhost:8000" -ForegroundColor White
Write-Host "  API:  http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "============================================`n" -ForegroundColor Green

python main.py

# Windows bootstrap script — equivalent to `make bootstrap`
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$VENV = '.venv'

Write-Host 'Creating virtual environment...'
py -3.13 -m venv $VENV

Write-Host 'Upgrading pip...'
& "$VENV\Scripts\pip.exe" install --upgrade pip

Write-Host 'Installing dependencies...'
& "$VENV\Scripts\pip.exe" install -r requirements.txt -r requirements-dev.txt

Write-Host 'Installing pre-commit hooks...'
& "$VENV\Scripts\pre-commit.exe" install

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example -- add your API keys.'
}

if (-not (Test-Path 'workspace')) {
    New-Item -ItemType Directory -Path 'workspace' | Out-Null
}

Write-Host ''
Write-Host 'Bootstrap complete.'
Write-Host 'Edit .env and add GEMINI_API_KEY and API_KEY before running.'
Write-Host ''
Write-Host 'Run tests:   .venv\Scripts\pytest tests\ --cov=app --cov-fail-under=80'
Write-Host 'Run server:  .venv\Scripts\uvicorn app.main:app --reload'

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host " Basketball Calendar Sync"
Write-Host "====================================="
Write-Host ""

if (!(Test-Path ".\credentials\credentials.json")) {
    Write-Host "ERROR: credentials.json not found."
    Write-Host ""
    Write-Host "Put your Google OAuth file here:"
    Write-Host "  credentials\credentials.json"
    exit 1
}

if (!(Test-Path ".\credentials\token.json")) {
    Write-Host "Google token not found."
    Write-Host "Starting one-time OAuth..."
    Write-Host ""

    python auth.py

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "Building Docker image..."
docker compose build

Write-Host ""
Write-Host "Starting basketball calendar worker..."
docker compose up -d

Write-Host ""
Write-Host "Worker started."
Write-Host ""
Write-Host "Logs:"
docker compose logs --tail=30

Write-Host ""
Write-Host "Follow live logs with:"
Write-Host "  docker compose logs -f"
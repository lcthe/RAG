# Start RAG Web Application
param(
    [switch]$StartInfra,
    [switch]$StartBackend,
    [switch]$StartFrontend,
    [switch]$All
)

$ROOT = Split-Path -Parent $PSScriptRoot

if ($StartInfra -or $All) {
    Write-Host "[1/3] Starting Redis..." -ForegroundColor Cyan
    docker-compose -f "$ROOT/docker-compose.yml" up -d
    Write-Host "  Redis OK (port 6379)" -ForegroundColor Green
}

if ($StartBackend -or $All) {
    Write-Host "[2/3] Starting FastAPI backend on :18762..." -ForegroundColor Cyan
    $env:PYTHONPATH = "$ROOT/.."
    $env:TRANSFORMERS_OFFLINE = "1"
    $env:HF_HUB_OFFLINE = "1"
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "uvicorn", "web_app.backend.app.main:app", "--host", "127.0.0.1", "--port", "18762" -WorkingDirectory "$ROOT/.."
    Write-Host "  Backend started (port 18762)" -ForegroundColor Green
}

if ($StartFrontend -or $All) {
    Write-Host "[3/3] Starting Next.js frontend on :19123..." -ForegroundColor Cyan
    Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c", "cd /d $ROOT/frontend && npm run dev"
    Write-Host "  Frontend started (port 19123)" -ForegroundColor Green
}

if (-not ($StartInfra -or $StartBackend -or $StartFrontend -or $All)) {
    Write-Host "Usage: .\scripts\start.ps1 -All"
    Write-Host ""
    Write-Host "Ports:"
    Write-Host "  Frontend (Chat)     http://localhost:19123"
    Write-Host "  Admin Panel         http://localhost:19123/admin"
    Write-Host "  Backend API         http://localhost:18762/api/health"
    Write-Host "  Redis               port 6379"
    Write-Host ""
    Write-Host "Tech Stack: Next.js + FastAPI + ChromaDB + Redis"
    Write-Host "Theme: MaxKB (Purple & White / 紫白主题)"
}

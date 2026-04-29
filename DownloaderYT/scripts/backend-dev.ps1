param(
    [string]$ServerHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
Set-Location $backendDir

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "No se encontro .venv en $projectRoot. Crea/activa el entorno virtual antes de ejecutar."
}

& $pythonPath -m alembic upgrade head
& $pythonPath -m uvicorn app.main:app --host $ServerHost --port $Port --reload

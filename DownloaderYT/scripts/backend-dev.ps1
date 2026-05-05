param(
    [string]$ServerHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
Set-Location $backendDir

$pythonCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $backendDir ".venv\Scripts\python.exe")
)

$pythonPath = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $pythonPath) {
    throw (
        "No se encontro entorno virtual. Rutas probadas:`n - {0}`n - {1}`nCrea/activa el entorno virtual antes de ejecutar." -f $pythonCandidates[0], $pythonCandidates[1]
    )
}

& $pythonPath -m alembic upgrade head
& $pythonPath -m uvicorn app.main:app --host $ServerHost --port $Port --reload

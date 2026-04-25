param(
    [string]$Keyword = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    throw "No se encontro .venv en $projectRoot. Crea/activa el entorno virtual antes de ejecutar."
}

Set-Location $backendDir

$argsList = @("-m", "pytest", "-q", "tests")
if ($Keyword -ne "") {
    $argsList += @("-k", $Keyword)
}

& $pythonPath @argsList


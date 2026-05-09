param(
    [ValidateSet("incremental", "full")]
    [string]$Mode = "incremental",
    [int]$Limit = 100,
    [switch]$Quick,
    [switch]$UseGlobalPython
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

function Get-PythonCommand {
    param([switch]$PreferGlobal)

    if (-not $PreferGlobal -and (Test-Path $venvPython)) {
        return $venvPython
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return "py -3"
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return "python"
    }

    throw "Nenhum interpretador Python encontrado. Instale Python ou crie o .venv."
}

function Invoke-Python {
    param(
        [string]$PythonCmd,
        [string[]]$PythonArgs
    )

    if ($PythonCmd -eq "py -3") {
        & py -3 @PythonArgs
    } else {
        & $PythonCmd @PythonArgs
    }
}

$pythonCmd = Get-PythonCommand -PreferGlobal:$UseGlobalPython
Write-Host "[run_etl] Python selecionado: $pythonCmd"

if ($Quick) {
    if ($Limit -eq 100) {
        $Limit = 3
    }
    $env:ETL_REQUEST_DELAY = "0.05"
    Write-Host "[run_etl] Quick mode ativo: limit=$Limit"
    Write-Host "[run_etl] Quick mode ativo: ETL_REQUEST_DELAY=$($env:ETL_REQUEST_DELAY)s"
}

if (-not (Test-Path (Join-Path $scriptDir ".env"))) {
    Write-Warning "Arquivo .env não encontrado. O ETL pode falhar na conexão com o banco."
    Write-Warning "Crie .env com DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD e DB_SCHEMA."
}

$importCheck = @"
import importlib.util
mods = ["requests", "dotenv", "psycopg"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
raise SystemExit(1 if missing else 0)
"@

$importsOk = $true
try {
    if ($pythonCmd -eq "py -3") {
        $importCheck | py -3 -c "import sys; exec(sys.stdin.read())" | Out-Null
    } else {
        $importCheck | & $pythonCmd -c "import sys; exec(sys.stdin.read())" | Out-Null
    }
} catch {
    $importsOk = $false
}

if (-not $importsOk) {
    Write-Host "[run_etl] Dependências ausentes. Instalando requirements.txt..."
    if ($pythonCmd -eq "py -3") {
        py -3 -m pip install -r requirements.txt
    } else {
        & $pythonCmd -m pip install -r requirements.txt
    }
}

Write-Host "[run_etl] Executando ETL: mode=$Mode limit=$Limit"
Invoke-Python -PythonCmd $pythonCmd -PythonArgs @("main.py", "--mode", $Mode, "--limit", "$Limit")

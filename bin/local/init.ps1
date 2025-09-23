# Requires: Python 3.12 installed (via python.org or Store), uv, git
# Run: powershell -ExecutionPolicy Bypass -File .\bin\local\init.ps1

$ErrorActionPreference = "Stop"

# Choose a Python 3.12 interpreter
$PYTHON_VERSION = "3.12"

if (Get-Command py -ErrorAction SilentlyContinue) {
  # Use the Python launcher with separate args
  $pythonExe = "py"
  $pythonArgs = @("-$PYTHON_VERSION")
} else {
  # Fallback to python.exe on PATH
  $pythonExe = "python"
  $pythonArgs = @()
}

# Helper to run python with the preset args
function Invoke-Python {
  param([Parameter(ValueFromRemainingArguments=$true)] $Rest)
  & $pythonExe @($pythonArgs + $Rest)
}

# Version check
$ver = Invoke-Python -c "import sys;print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
if ($LASTEXITCODE -ne 0 -or $ver -ne "3.12") {
  throw "Python 3.12 not found. Install it, or install the 'py' launcher."
}

# Create venv (example)
if (-not (Test-Path .venv)) {
  Invoke-Python -m venv .venv
}

# Activate and continue...
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install uv pre-commit

# Sync local environment (PowerShell port below)
. .\bin\local\sync-python-env.ps1

# Install pre-commit
python -m pip install pre-commit
python -m pre_commit install
Write-Host "Environment ready: $ENV_NAME"
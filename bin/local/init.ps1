# Run: powershell -ExecutionPolicy Bypass -File .\bin\local\init.ps1

$ErrorActionPreference = "Stop"

# 1. Define python version and environment name
$PYTHON_VERSION = "3.12"
$PROJECT_NAME = Split-Path -Leaf (Get-Location)
$ENV_NAME = "$PROJECT_NAME-$PYTHON_VERSION"
$VENV_PATH = Join-Path -Path $PWD -ChildPath ".venv"

Write-Host "Project: $PROJECT_NAME"
Write-Host "Virtual environment: $ENV_NAME"
Write-Host "Virtual environment path: $VENV_PATH"

# Create venv if it doesn't exist
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment at $VENV_PATH..."
    python -m venv $VENV_PATH
} else {
    Write-Host "Virtual environment already exists at $VENV_PATH"
}

# 2. Create virtual environment if it doesn't exist
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment at $VENV_PATH..."
    python -m venv $VENV_PATH
} else {
    Write-Host "Virtual environment already exists at $VENV_PATH"
}

# 3. Activate the virtual environment
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    & $activateScript
} else {
    throw "Activation script not found at $activateScript"
}

# 4. Upgrade pip and install essential tools inside venv
python -m pip install --upgrade pip
python -m pip install pip-tools pre-commit

# 5. Sync local environment (PowerShell port below)
. .\bin\local\sync-python-env.ps1

# 6. Install pre-commit hooks
python -m pre_commit install
Write-Host "Environment ready: $ENV_NAME"

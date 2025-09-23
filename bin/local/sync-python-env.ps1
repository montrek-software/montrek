$ErrorActionPreference = "Stop"

Write-Host "Syncing Python environment with uv..."

# Create/refresh a venv (uv manages .venv by default)
uv venv

# Combine all requirements.in files into one
$temporary_requirements_file = "all_requirements.in"
if (Test-Path $temporary_requirements_file) { Remove-Item $temporary_requirements_file }
Get-ChildItem -Recurse -Filter requirements.in | ForEach-Object {
  Get-Content $_.FullName
  ""
} | Set-Content $temporary_requirements_file -Encoding utf8

# Compile and sync using uv
uv pip compile $temporary_requirements_file --output-file requirements.txt
uv pip sync requirements.txt

Remove-Item $temporary_requirements_file -ErrorAction SilentlyContinue
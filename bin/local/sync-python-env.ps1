$ErrorActionPreference = "Stop"


# Combine all requirements.in files into one
$temporary_requirements_file = "all_requirements.in"
if (Test-Path $temporary_requirements_file) { Remove-Item $temporary_requirements_file }
Get-ChildItem -Recurse -Filter requirements.in | ForEach-Object {
  Get-Content $_.FullName
  ""
} | Set-Content $temporary_requirements_file -Encoding utf8

# Compile and sync using uv
python -m piptools compile $temporary_requirements_file --output-file requirements.txt
python -m piptools sync requirements.txt

Remove-Item $temporary_requirements_file -ErrorAction SilentlyContinue
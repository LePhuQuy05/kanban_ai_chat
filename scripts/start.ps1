docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Output "App started at http://127.0.0.1:8000"

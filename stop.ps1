$ErrorActionPreference = "Stop"

docker compose down
Write-Host "Containers stopped. PostgreSQL data is preserved." -ForegroundColor Yellow


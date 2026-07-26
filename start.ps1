$ErrorActionPreference = "Stop"

docker compose up --build -d
docker compose ps

Write-Host ""
Write-Host "408 Local OJ is ready at http://localhost:3000" -ForegroundColor Green


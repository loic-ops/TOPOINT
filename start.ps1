# Script PowerShell de démarrage pour Windows (plus robuste)
# Utilisation : ./start.ps1

$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=== Pointage ==="
Write-Host ""

# 1. Virtualenv
if (-Not (Test-Path "$DIR\venv")) {
    Write-Host "Création du virtualenv..."
    python -m venv "$DIR\venv"
}

# Activer virtualenv
& "$DIR\venv\Scripts\Activate.ps1"

# 2. Dépendances
Write-Host "Installation des dépendances Python..."
python -m pip install -q -r "$DIR\backend\requirements.txt"

# 3. Build frontends
if (-Not (Test-Path "$DIR\mobile-app\dist")) {
    Write-Host "Build mobile app..."
    Set-Location "$DIR\mobile-app"
    npm install
    npm run build
}

if (-Not (Test-Path "$DIR\admin-app\dist")) {
    Write-Host "Build admin app..."
    Set-Location "$DIR\admin-app"
    npm install
    npm run build
}

# 4. Seed base
Set-Location "$DIR\backend"
if (-Not (Test-Path "$DIR\backend\data.db")) {
    Write-Host "Création de la base de données..."
    python seed.py
}

# 5. IP locale
$IP = (Get-NetIPAddress -AddressFamily IPv4 -PrefixLength 24 | Select-Object -First 1).IPAddress
if ([string]::IsNullOrEmpty($IP)) { $IP = "localhost" }

Write-Host ""
Write-Host "=========================================="
Write-Host "  SERVEUR PRÊT"
Write-Host ""
Write-Host "  Mobile : http://$IP:8000/mobile/"
Write-Host "  Admin  : http://$IP:8000/admin/"
Write-Host "  API    : http://$IP:8000/api/health"
Write-Host ""
Write-Host "  Depuis un téléphone :"
Write-Host "  - Connecte-toi au même Wi-Fi"
Write-Host "  - Ouvre http://$IP:8000/mobile/"
Write-Host "=========================================="
Write-Host ""

Set-Location "$DIR\backend"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

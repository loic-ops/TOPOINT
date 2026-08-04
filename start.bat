@echo off
setlocal enabledelayedexpansion

REM Script de démarrage pour Windows

echo.
echo === Pointage ===
echo.

set DIR=%~dp0

REM 1. Virtualenv
if not exist "%DIR%venv" (
    echo Création du virtualenv...
    python -m venv "%DIR%venv"
)

call "%DIR%venv\Scripts\activate.bat"

REM 2. Dépendances
echo Installation des dépendances Python...
pip install -q -r "%DIR%backend\requirements.txt"

REM 3. Build frontends
if not exist "%DIR%mobile-app\dist" (
    echo Build mobile app...
    cd /d "%DIR%mobile-app" && call npm install && call npm run build
)
if not exist "%DIR%admin-app\dist" (
    echo Build admin app...
    cd /d "%DIR%admin-app" && call npm install && call npm run build
)

REM 4. Seed base
cd /d "%DIR%backend"
if not exist "%DIR%backend\data.db" (
    echo Création de la base de données...
    python seed.py
)

REM 5. IP locale
for /f "delims=" %%A in ('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 -PrefixLength 24 | Select-Object -First 1 -ExpandProperty IPAddress"') do set "LOCAL_IP=%%A"
if "!LOCAL_IP!"=="" set LOCAL_IP=localhost

echo.
echo ==========================================
echo   SERVEUR PRÊT
echo.
echo   Mobile : http://!LOCAL_IP!:8000/mobile/
echo   Admin  : http://!LOCAL_IP!:8000/admin/
echo   API    : http://!LOCAL_IP!:8000/api/health
echo.
echo   Depuis un téléphone :
echo   - Connecte-toi au même Wi-Fi
echo   - Ouvre http://!LOCAL_IP!:8000/mobile/
echo ==========================================
echo.

cd /d "%DIR%backend"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

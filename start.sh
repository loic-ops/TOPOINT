#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===   Pointage ==="
echo ""

# 1. Virtualenv
if [ ! -d "$DIR/venv" ]; then
    echo "Création du virtualenv..."
    /opt/homebrew/bin/python3.12 -m venv "$DIR/venv"
fi
source "$DIR/venv/bin/activate"

# 2. Dépendances
pip install -q -r "$DIR/backend/requirements.txt"

# 3. Build frontends
if [ ! -d "$DIR/mobile-app/dist" ]; then
    echo "Build mobile app..."
    cd "$DIR/mobile-app" && npm install && npm run build
fi
if [ ! -d "$DIR/admin-app/dist" ]; then
    echo "Build admin app..."
    cd "$DIR/admin-app" && npm install && npm run build
fi

# 4. Seed base
cd "$DIR/backend"
if [ ! -f "$DIR/backend/data.db" ]; then
    echo "Création de la base de données..."
    python seed.py
fi

# 5. IP locale
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "localhost")

echo ""
echo "=========================================="
echo "  SERVEUR PRÊT"
echo ""
echo "  Mobile : http://${LOCAL_IP}:8000/mobile/"
echo "  Admin  : http://${LOCAL_IP}:8000/admin/"
echo "  API    : http://${LOCAL_IP}:8000/api/health"
echo ""
echo "  Depuis un téléphone :"
echo "  → Connecte-toi au même Wi-Fi"
echo "  → Ouvre http://${LOCAL_IP}:8000/mobile/"
echo "=========================================="
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Scénario de test —   Pointage

## Prérequis

- Python 3.11+
- Node.js 18+
- ngrok (`brew install ngrok`)
- 1 ou 2 téléphones (iOS ou Android)
- Mac connecté au Wi-Fi entreprise (2.4GHz ou 5GHz)

---

## Étape 1 : Démarrer le serveur

```bash
cd /Users/DART/Documents/TOPOINT
./start.sh
```

Le serveur démarre sur `http://0.0.0.0:8000`.

**URLs locales :**
- Mobile app : `http://<IP_MAC>:8000/mobile/`
- Admin app : `http://<IP_MAC>:8000/admin/`
- API health : `http://<IP_MAC>:8000/api/health`

**Comptes de test :**

| Matricule | PIN | Rôle |
|---|---|---|
| ADMIN001 | 1234 | Admin |
| EMP0001 | 1111 | Cuisine |
| EMP0002 | 2222 | Service |

---

## Étape 2 : Test local (même réseau)

1. Ouvre `http://localhost:8000/mobile/` sur ton Mac
2. Tu dois voir l'écran de connexion PIN
3. Connecte-toi avec `ADMIN001` / `1234`
4. Teste Check In → Pause → Check Out
5. Ouvre `http://localhost:8000/admin/` → Dashboard

---

## Étape 3 : Test réseau local (téléphone Wi-Fi)

### Trouver l'IP locale de ton Mac

```bash
ipconfig getifaddr en0
# Ex: 192.168.1.42
```

### Depuis le téléphone (même Wi-Fi que le Mac)

1. Ouvre Safari/Chrome → `http://192.168.1.42:8000/mobile/`
2. Ajoute à l'écran d'accueil (PWA)
3. Connecte-toi → Check In
4. Vérifie que le pointage apparaît dans l'admin

---

## Étape 4 : Test tunnel ngrok (accès depuis 4G/externe)

### Démarrer ngrok

```bash
ngrok http 8000
```

ngrok donne une URL publique : `https://xxxx.ngrok.io`

### Depuis le téléphone (mode 4G ou autre Wi-Fi)

1. Désactive le Wi-Fi, active la 4G (ou connecte-toi à un autre réseau)
2. Ouvre `https://xxxx.ngrok.io/mobile/`
3. **Résultat attendu :** l'écran affiche "Connexion au réseau de l'entreprise requise"
4. Le pointage est **bloqué** car tu n'es pas sur le bon réseau

### Test bypass (dev uniquement)

Si tu veux tester depuis l'extérieur en dev :
```bash
NETWORK_CHECK_BYPASS=true ./start.sh
```
⚠️ Ne jamais utiliser ça en prod.

---

## Étape 5 : Test rate-limiting PIN

1. Va sur `http://localhost:8000/mobile/`
2. Entree un mauvais PIN 5 fois de suite
3. **Résultat attendu :** message "Trop de tentatives, réessayez dans 5 minutes"
4. Le 6e essai est bloqué même avec le bon PIN

---

## Étape 6 : Test admin complet

1. Connecte-toi sur `http://localhost:8000/admin/` (ADMIN001 / 1234)
2. **Dashboard** → vérifie les KPIs (0 présents au début)
3. **Employés** → crée un nouvel employé (PIN: 9999)
4. **Présences du jour** → devrait afficher les employés en "Absent"
5. Sur le mobile : connecte-toi avec le nouvel employé → Check In
6. Sur l'admin → rafraîchis → l'employé est maintenant "En poste"
7. **Forcer la sortie** → clique sur le bouton → confirm
8. **Historique pointages** → vérifie que le pointage apparaît avec le statut "Terminé"

---

## Étape 7 : Test auto-détection réseau

```bash
# Vérifier les subnets auto-détectés
curl http://localhost:8000/api/network/status
```

Réponse attendue :
```json
{
  "allowed": true,
  "client_ip": "192.168.x.x",
  "message": "Réseau autorisé"
}
```

Pour forcer un override :
```bash
ALLOWED_SUBNETS=192.168.1.0/24 ./start.sh
```

---

## Déploiement production (bare metal)

```bash
# Sur le serveur de l'entreprise
git clone <repo>
cd TOPOINT

# Python
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Build frontends
cd mobile-app && npm install && npm run build && cd ..
cd admin-app && npm install && npm run build && cd ..

# Seed
cd backend && python seed.py

# Lancer (auto-détecte le réseau)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Le serveur protège automatiquement le réseau sur lequel il tourne.

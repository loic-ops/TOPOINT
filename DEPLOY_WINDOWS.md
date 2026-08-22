# Déploiement sur Windows

> **Branche `deploy-local`** : déploiement local Docker (app + PostgreSQL local),
> indépendant de la version en ligne (branche `main` → Render).

## Prérequis
- Docker Desktop pour Windows installé et démarré

## Démarrage avec Docker (recommandé)

```powershell
git checkout deploy-local
docker compose up -d --build
```

L'app démarre en mode local (`DEPLOY_MODE=local`) avec une base PostgreSQL
locale persistante (volume `pgdata`).

### Accès

- **Mobile** : http://IP-du-serveur:8000/
- **Admin** : http://IP-du-serveur:8000/admin/
- **API health** : http://IP-du-serveur:8000/api/health

> Trouve l'IP LAN du serveur avec `ipconfig` (ligne "Adresse IPv4").
> Les employés doivent être connectés au **même réseau (WiFi bureaux)** pour pointer.

### Vérification de l'IP des employés (aux bureaux / à distance)

Chaque pointage enregistre l'IP source de l'appareil et un indicateur
« Aux bureaux » / « À distance » visible dans l'admin (colonne *Lieu / IP*).

- La plage de référence est détectée automatiquement depuis le réseau du serveur.
- En conteneur Docker, il est recommandé de la définir explicitement dans un
  fichier `.env` à côté du `docker-compose.yml` :

```
ALLOWED_SUBNETS=192.168.1.0/24
SECRET_KEY=une-cle-secrete
POSTGRES_PASSWORD=topoint-local
```

(remplace `192.168.1.0/24` par la plage réelle du réseau bureaux — visible via `ipconfig`)

- **Diagnostic** : connecte-toi en admin sur
  `http://IP-du-serveur:8000/api/admin/network-status` pour voir l'IP que le
  serveur observe et la plage de référence détectée.

> ⚠️ **Important — Docker Desktop et IP source** : selon la version de Docker
> Desktop, l'IP des appareils clients peut apparaître comme celle de la passerelle
> Docker (NAT) au lieu de leur vraie IP LAN. Dans ce cas :
> 1. Vérifie avec `/api/admin/network-status` depuis un téléphone sur le WiFi bureaux ;
> 2. Si l'IP affichée n'est pas l'IP réelle du téléphone (paramètres WiFi),
>    utilise le démarrage natif ci-dessous (sans Docker) qui préserve les vraies IPs.

> ⚠️ **Ne jamais configurer de port-forwarding** sur le routeur vers le port 8000 :
> l'app doit rester joignable uniquement depuis le réseau local.

### Démarrage natif (sans Docker — préserve les vraies IPs clientes)

- Python 3.10+ et Node.js 18+ accessibles en ligne de commande

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

Le script gère virtualenv, dépendances, build des frontends et démarrage du serveur.

## Troubleshooting

### Port 8000 déjà utilisé
```powershell
netstat -ano | findstr :8000
docker compose down
```

### Réinitialiser la base locale
```powershell
docker compose down
docker volume rm topoint_pgdata
docker compose up -d --build
```

### Voir les logs
```powershell
docker compose logs -f app
```

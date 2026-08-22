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

> ⚠️ **Important — Docker Desktop et IP source (NAT)** : en mode standard
> (bridge + ports publiés), Docker Desktop NATe toutes les connexions entrantes :
> l'app voit la passerelle interne (ex. `192.168.65.1`) au lieu de la vraie IP
> de chaque téléphone → le lieu « Aux bureaux / À distance » reste
> « Indéterminé ». Deux solutions pour obtenir les vraies IPs :
>
> 1. **Mode host networking (recommandé)** — activer dans Docker Desktop :
>    Settings → Resources → Network → **Enable host networking** (4.34+),
>    redémarrer Docker, puis :
>    ```powershell
>    docker compose -f docker-compose.yml -f docker-compose.hostnet.yml up -d --build
>    ```
>    L'app partage alors le réseau de la machine et voit les vraies IPs clientes.
>
> 2. **Démarrage natif (sans Docker)** — `.\start.ps1` — garantit les vraies IPs.
>
> **Vérification** : depuis un téléphone sur le WiFi bureaux, ouvre
> `http://IP-du-serveur:8000/api/admin/network-status` (connecté en admin) :
> `client_ip` doit être l'IP réelle du téléphone (voir dans ses réglages WiFi).
> Si c'est une IP du type `192.168.65.1`, le NAT est encore actif.

> ⚠️ **Ne jamais configurer de port-forwarding** sur le routeur vers le port 8000 :
> l'app doit rester joignable uniquement depuis le réseau local.

### Démarrage natif (sans Docker — préserve les vraies IPs clientes)

> ⚠️ Vérifie d'abord qu'aucun ancien serveur n'occupe le port 8000 :
> ```powershell
> netstat -ano | findstr :8000
> ```
> (un processus `uvicorn` ou `python` qui écouterait encore doit être terminé
> via le Gestionnaire des tâches, sinon c'est lui qui répond à la place)

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

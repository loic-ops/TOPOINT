# Déploiement sur Windows

## Prérequis
- Python 3.10+ installé et accessible via `python` en ligne de commande
- Node.js 18+ avec `npm` en ligne de commande
- Git (pour cloner le projet)

## Options de démarrage

### Option 1 : Double-cliquer `start.bat` (plus simple)
Le script batch gère automatiquement :
- Création et activation du virtualenv
- Installation des dépendances Python
- Build des apps mobiles et admin
- Initialisation de la base de données
- Démarrage du serveur

**Inconvénient** : Les erreurs d'affichage peuvent être confuses si terminé trop vite.

### Option 2 : Terminal/CMD
```cmd
cd C:\chemin\vers\TOPOINT
start.bat
```

### Option 3 : PowerShell (recommandé pour meilleur affichage)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

> ⚠️ Si tu as une erreur `"cannot be loaded because running scripts is disabled"`, exécute :
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## Troubleshooting

### Erreur : `python` non reconnu
```
À corriger : ajouter Python au PATH Windows
1. Cherche "Variables d'environnement" dans le menu Démarrer
2. Clique "Variables d'environnement"
3. Sous "Variables système", clique "Modifier le PATH"
4. Ajoute le dossier d'installation de Python (ex: C:\Users\YourUser\AppData\Local\Programs\Python\Python312)
```

### Erreur : `npm` non reconnu
```
Faut installer Node.js depuis https://nodejs.org (LTS recommandé)
```

### Erreur lors du build des apps
```
cd mobile-app
npm install
npm run build

cd ..\admin-app
npm install
npm run build
```

### Erreur d'accès à la base de données
```
Supprime les fichiers :
- backend\data.db
- backend\data.db-shm
- backend\data.db-wal

Puis relance start.bat
```

### Port 8000 déjà utilisé
```
Modifie le port dans app.py ou termine les processus Python actifs
```

## Accès

- **Mobile** : http://tonIP:8000/mobile/
- **Admin** : http://tonIP:8000/admin/
- **API** : http://tonIP:8000/api/health

> Trouve ton IP locale avec : `ipconfig` (cherche IPv4)

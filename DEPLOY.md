# Déploiement démo —   Pointage

Guide pas-à-pas pour déployer la version démo 100% gratuite :
- **Backend** → Render Web Service (Python, gratuit)
- **Base de données** → Supabase (Postgres gratuit, permanent)
- **Frontend mobile (PWA)** → Render Static Site (gratuit)
- **Frontend admin** → Render Static Site (gratuit)

---

## Prérequis

- Compte gratuit [Render](https://render.com)
- Compte gratuit [Supabase](https://supabase.com)
- Git pushé sur GitHub/GitLab

---

## 1. Base de données — Supabase

1. Créer un nouveau projet sur [Supabase](https://supabase.com)
2. Choisir un mot de passe fort pour la DB (le garder !)
3. Aller dans **Settings** → **Database** et noter les deux URLs :

### URL directe (port 5432) — pour les migrations Alembic uniquement

```
postgresql://postgres.xxxxx:VOTRE_MOT_DE_PASSE@db.xxxxx.supabase.co:5432/postgres
```

> **Usage** : `alembic upgrade head` uniquement. Jamais par l'app en runtime.

### URL pooler PgBouncer (port 6543) — pour l'app en runtime

```
postgresql://postgres.xxxxx:VOTRE_MOT_DE_PASSE@aws-0-eu-west.pooler.supabase.com:6543/postgres
```

> **Usage** : la variable `DATABASE_URL` de l'app FastAPI. Le pooler gère le pooling de connexions.

> **Important** : en mode transaction (défaut), PgBouncer ferme les connexions à la fin de chaque transaction. SQLAlchemy doit utiliser `NullPool` pour éviter les erreurs "prepared statement already exists". C'est déjà configuré dans `database.py` quand `DEPLOY_MODE=demo`.

---

## 2. Déploiement via Blueprint (render.yaml)

Le fichier `render.yaml` à la racine du repo déclare les 3 services d'un coup.

### Étape A : Push le repo

```bash
git add .
git commit -m "feat: monorepo Render + Supabase"
git push
```

### Étape B : Créer le Blueprint

1. Aller sur [Render Dashboard](https://dashboard.render.com)
2. **New** → **Blueprint** → connecter le repo GitHub/GitLab
3. Render détecte `render.yaml` et propose de créer les 3 services
4. Cliquer **Apply** pour créer tout d'un coup

### Étape C : Saisir les variables d'environnement

Render crée les services avec les variables marquées `sync: false` vides. Il faut les remplir manuellement.

#### Service `topointage-api` (Web Service)

| Variable | Valeur |
|---|---|
| `DATABASE_URL` | URL **pooler** Supabase (port 6543) |
| `DATABASE_URL_DIRECT` | URL **directe** Supabase (port 5432) |
| `SECRET_KEY` | (généré automatiquement par Render) |
| `CORS_ORIGINS` | `https://topointage-mobile.onrender.com,https://topointage-admin.onrender.com` |

#### Service `topointage-mobile` (Static Site)

| Variable | Valeur |
|---|---|
| `VITE_API_URL` | `https://topointage-api.onrender.com` |

#### Service `topointage-admin` (Static Site)

| Variable | Valeur |
|---|---|
| `VITE_API_URL` | `https://topointage-api.onrender.com` |

### Étape D : Redéployer

Après avoir saisi les variables, cliquer **Manual Deploy** sur chaque service pour déclencher un build avec les bonnes variables.

---

## 3. Déploiement manuel (sans Blueprint)

Si vous préférez créer les services un par un :

### Backend — Web Service

1. **New** → **Web Service** → connecter le repo
2. Paramètres :
   - **Name** : `topointage-api`
   - **Runtime** : Python
   - **Root Directory** : `backend`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan** : Free
3. Variables d'environnement (onglet **Environment**) :

| Variable | Valeur |
|---|---|
| `DEPLOY_MODE` | `demo` |
| `SECRET_KEY` | (générer une clé aléatoire) |
| `DATABASE_URL` | URL pooler Supabase (port 6543) |
| `DATABASE_URL_DIRECT` | URL directe Supabase (port 5432) |
| `PYTHON_VERSION` | `3.12` |
| `TOKEN_EXPIRE_MINUTES` | `60` |
| `CORS_ORIGINS` | (à remplir après déploiement des frontends) |

### Frontend mobile — Static Site

1. **New** → **Static Site** → connecter le repo
2. Paramètres :
   - **Name** : `topointage-mobile`
   - **Root Directory** : `frontend-mobile`
   - **Build Command** : `npm install && npm run build`
   - **Publish Directory** : `dist`
   - **Plan** : Free
3. Variables d'environnement :

| Variable | Valeur |
|---|---|
| `VITE_API_URL` | `https://topointage-api.onrender.com` |
| `VITE_BASE_PATH` | `/` |

### Frontend admin — Static Site

Même procédure avec :
- **Name** : `topointage-admin`
- **Root Directory** : `frontend-admin`
- **Publish Directory** : `dist`
- **VITE_API_URL** : `https://topointage-api.onrender.com`
- **VITE_BASE_PATH** : `/`

---

## 4. Migrations de la base de données

### Première mise en production

Le backend crée automatiquement les tables au démarrage (`Base.metadata.create_all` dans le lifespan FastAPI). Pas besoin d'Alembic pour la première fois.

### Migrations futures (Alembic)

Utiliser **uniquement** l'URL directe (port 5432) pour les migrations :

```bash
# Depuis un poste local avec Alembic configuré
export DATABASE_URL_DIRECT="postgresql://postgres.xxxxx:password@db.xxxxx.supabase.co:5432/postgres"
alembic upgrade head
```

> **Attention** : ne jamais lancer `alembic upgrade head` sur l'URL pooler (port 6543). Le pooler en mode transaction ne supporte pas les `prepared statements` utilisés par certaines opérations Alembic.

### Seed de l'admin par défaut

Le backend crée les tables automatiquement au démarrage, mais pas l'admin. Il faut seed manuellement :

1. Dashboard Render → service `topointage-api` → **Shell**
2. Exécuter :

```bash
cd /app/backend
python -c "
from app.database import SessionLocal, Base, engine
from app.models import Employee
from app.utils import generate_salt, hash_pin
Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Employee).count() == 0:
    salt = generate_salt()
    emp = Employee(
        matricule='ADMIN001', first_name='Admin', last_name=' ',
        role='admin', pin_hash=hash_pin('1234', salt),
        salt=salt, is_active=True,
    )
    db.add(emp); db.commit()
    print('Admin cree : ADMIN001 / PIN 1234')
else:
    print('Deja seede.')
db.close()
"
```

---

## 5. Vérification

### Health check

```bash
curl https://topointage-api.onrender.com/health
# → {"status":"ok","version":"2.0.0"}
```

### Test DB

```bash
curl https://topointage-api.onrender.com/api/health
# → {"status":"ok","version":"2.0.0"}
```

### Test frontends

Ouvrir dans le navigateur :
- `https://topointage-mobile.onrender.com` → écran de login PIN
- `https://topointage-admin.onrender.com` → écran de login admin

### Identifiants par défaut

- **Admin** : `ADMIN001` / PIN `1234`

---

## 6. Finaliser le CORS

Après déploiement des 2 frontends, mettre à jour `CORS_ORIGINS` sur le service backend :

1. Dashboard Render → `topointage-api` → **Environment**
2. Modifier `CORS_ORIGINS` :
   ```
   https://topointage-mobile.onrender.com,https://topointage-admin.onrender.com
   ```
3. **Save** → le service redémarre automatiquement

---

## Récapitulatif des URLs

| Service | URL |
|---|---|
| Backend API | `https://topointage-api.onrender.com` |
| Health check | `https://topointage-api.onrender.com/health` |
| PWA mobile | `https://topointage-mobile.onrender.com` |
| Admin | `https://topointage-admin.onrender.com` |

---

## Comportement du plan gratuit Render

- **Spin-down** : après 15 min d'inactivité, le service backend s'arrête
- **Cold start** : le premier accès après un spin-down prend 30-60 secondes
- **Les static sites** (frontends) ne sont pas affectés par le spin-down
- **La base Supabase** est permanente (ne dort jamais)

> Pour éviter le spin-down en prod, passer au plan Starter ($7/mois).

---

## Connexion directe vs pooler — Résumé

| | Direct (port 5432) | Pooler PgBouncer (port 6543) |
|---|---|---|
| **Host** | `db.xxxxx.supabase.co` | `aws-0-eu-west.pooler.supabase.com` |
| **Usage** | Migrations Alembic uniquement | App FastAPI en runtime |
| **Pooling** | Connexion directe | Mode transaction |
| **SQLAlchemy** | Pool classique (pool_size=5) | **NullPool** (pas de pool côté app) |
| **Variable d'env** | `DATABASE_URL_DIRECT` | `DATABASE_URL` |

---

## Retour en mode local

Lancer le backend avec SQLite (par défaut si `DATABASE_URL` n'est pas défini) :

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le `DEPLOY_MODE=local` (par défaut) réactive la vérification réseau et la config CORS locale. Les frontends sont servis par le backend sur `/mobile/` et `/admin/` si les dossiers `dist/` existent.

---

## Structure du monorepo

```
pointage/
├── backend/                    → Render Web Service
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py           # DEPLOY_MODE, DATABASE_URL, CORS_ORIGINS...
│   │   ├── database.py         # NullPool si Supabase pooler
│   │   ├── middleware/
│   │   │   ├── __init__.py     # get_current_employee, require_admin
│   │   │   └── network.py      # verify_local_network (désactivé en demo)
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── utils/
│   │   └── services/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── frontend-admin/             → Render Static Site
│   ├── src/
│   ├── public/_redirects       # SPA mode pour Render
│   ├── .env.example
│   ├── vite.config.js
│   └── package.json
│
├── frontend-mobile/            → Render Static Site
│   ├── src/
│   ├── public/
│   │   ├── _redirects          # SPA mode pour Render
│   │   └── manifest.json       # PWA manifest
│   ├── .env.example
│   ├── vite.config.js
│   └── package.json
│
├── render.yaml                 # Blueprint : 3 services Render
├── DEPLOY.md
├── README.md
└── .gitignore
```

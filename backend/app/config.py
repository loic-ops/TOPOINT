import os


class Settings:
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── Base de données ──────────────────────────────────────
    # DATABASE_URL : connexion pooler (runtime app) — port 6543 Supabase
    # DATABASE_URL_DIRECT : connexion directe (Alembic migrations) — port 5432
    DB_URL: str = os.getenv("DATABASE_URL") or os.getenv("DB_URL", "")
    DB_URL_DIRECT: str = os.getenv("DATABASE_URL_DIRECT", "")

    # ── Sécurité ─────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
    PIN_MAX_ATTEMPTS: int = 5
    PIN_LOCKOUT_MINUTES: int = 5

    # ── Déploiement ──────────────────────────────────────────
    # "local" = LAN avec vérif réseau | "demo" = cloud, pas de vérif réseau
    DEPLOY_MODE: str = os.getenv("DEPLOY_MODE", "local")

    # Sous-réseaux autorisés (virgules), vide = auto-détection locale
    ALLOWED_SUBNETS: list[str] = [
        s.strip() for s in os.getenv("ALLOWED_SUBNETS", "").split(",") if s.strip()
    ]

    # ── CORS ─────────────────────────────────────────────────
    # En local : "*" | En demo : lister les origines Render des frontends
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "").split(",")
        if o.strip()
    ] or (["*"] if os.getenv("DEPLOY_MODE", "local") == "local" else ["*"])

    def __init__(self):
        if not self.DB_URL:
            self.DB_URL = f"sqlite:///{os.path.join(self.BASE_DIR, 'data.db')}"
        elif self.DB_URL.startswith("postgres://"):
            self.DB_URL = self.DB_URL.replace("postgres://", "postgresql://", 1)

        # Normaliser aussi l'URL directe pour les migrations
        if self.DB_URL_DIRECT and self.DB_URL_DIRECT.startswith("postgres://"):
            self.DB_URL_DIRECT = self.DB_URL_DIRECT.replace("postgres://", "postgresql://", 1)


settings = Settings()

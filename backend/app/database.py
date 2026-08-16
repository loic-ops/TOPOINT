from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# ── Configuration du moteur SQLAlchemy ──────────────────────
#
# Deux modes de connexion Supabase :
#   1. POOLER (PgBouncer, port 6543) — utilisé par l'app en runtime
#      → NullPool pour éviter les conflits avec le pooling de PgBouncer
#      → lire DATABASE_URL
#   2. DIRECT (port 5432) — utilisé uniquement pour les migrations Alembic
#      → lire DATABASE_URL_DIRECT
#
# En local (SQLite ou PostgreSQL local), on garde le comportement classique
# avec un pool de connexions SQLAlchemy.
# ──────────────────────────────────────────────────────────────

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if settings.DB_URL.startswith("sqlite"):
    # SQLite : pas de pool, check_same_thread obligatoire
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
elif settings.DEPLOY_MODE == "demo":
    # Mode cloud (Supabase) : on passe par le pooler PgBouncer
    # NullPool = pas de pool côté SQLAlchemy (PgBouncer gère le pool)
    # Évite les erreurs "prepared statement already exists"
    engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL local : pool classique
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_engine(settings.DB_URL, **engine_kwargs)

if settings.DB_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

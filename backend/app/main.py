import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, pointage, settings as settings_router

BASE_DIR = Path(settings.BASE_DIR)
FRONTEND_MOBILE_DIR = BASE_DIR.parent / "frontend-mobile" / "dist"
FRONTEND_ADMIN_DIR = BASE_DIR.parent / "frontend-admin" / "dist"


async def _auto_close_loop():
    from app.routers.settings import _auto_close_pointages
    from app.database import SessionLocal
    while True:
        await asyncio.sleep(300)
        db = SessionLocal()
        try:
            _auto_close_pointages(db)
        except Exception:
            pass
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    task = asyncio.create_task(_auto_close_loop())
    yield
    task.cancel()


def _run_migrations():
    from sqlalchemy import text
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text(
            "ALTER TABLE pointages ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


app = FastAPI(title="  Pointage", version="2.0.0", lifespan=lifespan)

# CORS — en mode demo, les origines Render des frontends sont configurées
# via la variable CORS_ORIGINS. En local, on autorise tout.
_cors_origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=(_cors_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pointage.router)
app.include_router(admin.router)
app.include_router(settings_router.router)


# Health check pour Render (racine) et pour l'app (/api/health)
@app.get("/health")
def health_root():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Service des fichiers statiques ──────────────────────────
# En Docker : les frontends existent dans le container → on les sert
# Sans Docker (Render sans Dockerfile) : pas de dist/ → endpoint JSON

if FRONTEND_MOBILE_DIR.exists():
    app.mount("/mobile/assets", StaticFiles(directory=FRONTEND_MOBILE_DIR / "assets"), name="mobile-assets")

    @app.get("/mobile/{full_path:path}")
    def serve_mobile(full_path: str):
        file_path = FRONTEND_MOBILE_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_MOBILE_DIR / "index.html")

    @app.get("/")
    def root():
        return FileResponse(FRONTEND_MOBILE_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": "  Pointage API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health",
        }


if FRONTEND_ADMIN_DIR.exists():
    app.mount("/admin/assets", StaticFiles(directory=FRONTEND_ADMIN_DIR / "assets"), name="admin-assets")

    @app.get("/admin/{full_path:path}")
    def serve_admin(full_path: str):
        file_path = FRONTEND_ADMIN_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_ADMIN_DIR / "index.html")

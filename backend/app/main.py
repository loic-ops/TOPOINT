import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, pointage

BASE_DIR = Path(settings.BASE_DIR)
MOBILE_DIR = BASE_DIR.parent / "mobile-app" / "dist"
ADMIN_DIR = BASE_DIR.parent / "admin-app" / "dist"

app = FastAPI(title="  Pointage", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pointage.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


if MOBILE_DIR.exists():
    app.mount("/mobile/assets", StaticFiles(directory=MOBILE_DIR / "assets"), name="mobile-assets")

    @app.get("/mobile/{full_path:path}")
    def serve_mobile(full_path: str):
        file_path = MOBILE_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(MOBILE_DIR / "index.html")

    @app.get("/")
    def root():
        return FileResponse(MOBILE_DIR / "index.html")


if ADMIN_DIR.exists():
    app.mount("/admin/assets", StaticFiles(directory=ADMIN_DIR / "assets"), name="admin-assets")

    @app.get("/admin/{full_path:path}")
    def serve_admin(full_path: str):
        file_path = ADMIN_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(ADMIN_DIR / "index.html")

import calendar
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware import require_admin
from app.models import Employee, Pointage, CompanySettings

router = APIRouter(prefix="/api/admin/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "work_start_hour": {"value": "08:00", "description": "Heure de debut de la journee"},
    "work_end_hour": {"value": "17:00", "description": "Heure de fin de la journee"},
    "max_work_hours": {"value": "8", "description": "Duree max de travail (heures)"},
    "max_break_minutes": {"value": "60", "description": "Duree max de pause (minutes)"},
    "auto_close_enabled": {"value": "true", "description": "Fermeture auto des pointages"},
    "auto_close_after_minutes": {"value": "720", "description": "Fermer apres X minutes (12h = 720)"},
}


def get_setting(db: Session, key: str) -> str:
    row = db.query(CompanySettings).filter(CompanySettings.key == key).first()
    if row:
        return row.value
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]["value"]
    return ""


def get_all_settings(db: Session) -> dict:
    result = {}
    for key, meta in DEFAULT_SETTINGS.items():
        row = db.query(CompanySettings).filter(CompanySettings.key == key).first()
        result[key] = {
            "value": row.value if row else meta["value"],
            "description": meta["description"],
        }
    extras = db.query(CompanySettings).filter(
        CompanySettings.key.notin_(list(DEFAULT_SETTINGS.keys()))
    ).all()
    for row in extras:
        result[row.key] = {
            "value": row.value,
            "description": row.description or "",
        }
    return result


class SettingsUpdate(BaseModel):
    settings: dict[str, str]


@router.get("")
def read_settings(
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_all_settings(db)


@router.put("")
def update_settings(
    body: SettingsUpdate,
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    for key, value in body.settings.items():
        row = db.query(CompanySettings).filter(CompanySettings.key == key).first()
        if row:
            row.value = str(value)
            row.updated_at = datetime.utcnow()
        else:
            desc = DEFAULT_SETTINGS.get(key, {}).get("description", "")
            db.add(CompanySettings(key=key, value=str(value), description=desc))
    db.commit()
    return {"detail": "Parametres mis a jour"}


@router.post("/auto-close")
def trigger_auto_close(
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    closed = _auto_close_pointages(db)
    return {"detail": f"{closed} pointage(s) ferme(s) automatiquement"}


def _auto_close_pointages(db: Session) -> int:
    enabled = get_setting(db, "auto_close_enabled")
    if enabled != "true":
        return 0

    max_minutes = int(get_setting(db, "auto_close_after_minutes"))
    max_work = float(get_setting(db, "max_work_hours"))
    max_break = int(get_setting(db, "max_break_minutes"))
    now = datetime.utcnow()

    open_pointages = (
        db.query(Pointage)
        .filter(Pointage.status.in_(["in_progress", "on_break"]))
        .all()
    )

    closed = 0
    for p in open_pointages:
        elapsed_minutes = (now - p.clock_in).total_seconds() / 60
        should_close = False

        if elapsed_minutes >= max_minutes:
            should_close = True

        work_seconds = (now - p.clock_in).total_seconds() - (p.total_break_seconds or 0)
        if work_seconds / 3600 >= max_work:
            should_close = True

        if p.status == "on_break" and p.break_start:
            break_minutes = (now - p.break_start).total_seconds() / 60
            if break_minutes >= max_break:
                should_close = True

        if should_close:
            if p.break_start and not p.break_end:
                p.break_end = now
                p.total_break_seconds += int((p.break_end - p.break_start).total_seconds())
            p.clock_out = now
            p.status = "completed"
            closed += 1

    if closed:
        db.commit()

    return closed

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Employee, PinAttempt
from app.schemas import PinLoginRequest, TokenResponse, EmployeeResponse
from app.utils import create_session_token, hash_pin
from app.utils.ip import get_client_ip

router = APIRouter(prefix="/api/auth", tags=["auth"])


def check_rate_limit(db: Session, ip: str):
    cutoff = datetime.utcnow() - timedelta(minutes=settings.PIN_LOCKOUT_MINUTES)
    recent = (
        db.query(PinAttempt)
        .filter(PinAttempt.ip == ip, PinAttempt.timestamp >= cutoff, PinAttempt.success == False)
        .count()
    )
    if recent >= settings.PIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de tentatives. Réessayez dans {settings.PIN_LOCKOUT_MINUTES} minutes.",
        )


@router.post("/pin", response_model=TokenResponse)
def login_pin(body: PinLoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    check_rate_limit(db, client_ip)

    matricule = body.matricule.strip().upper()
    pin = body.pin.strip()

    if not matricule or not pin:
        raise HTTPException(400, "Matricule et PIN requis")

    employee = db.query(Employee).filter(Employee.matricule == matricule).first()

    attempt = PinAttempt(
        employee_id=employee.id if employee else None,
        ip=client_ip,
        matricule=matricule,
        success=False,
    )

    if not employee:
        db.add(attempt)
        db.commit()
        raise HTTPException(404, "Employé introuvable")

    if not employee.is_active:
        db.add(attempt)
        db.commit()
        raise HTTPException(403, "Compte désactivé")

    if hash_pin(pin, employee.salt) != employee.pin_hash:
        db.add(attempt)
        db.commit()
        raise HTTPException(401, "PIN incorrect")

    attempt.success = True
    db.add(attempt)
    db.commit()

    token = create_session_token(employee.id)
    return TokenResponse(
        access_token=token,
        employee=EmployeeResponse.model_validate(employee),
    )

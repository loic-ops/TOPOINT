from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.utils import verify_session_token

security = HTTPBearer(auto_error=False)


def get_current_employee(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Employee:
    if not credentials:
        raise HTTPException(status_code=401, detail="Non authentifié")

    employee_id = verify_session_token(credentials.credentials)
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Employé introuvable")
    if not employee.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    return employee


def require_admin(
    employee: Employee = Depends(get_current_employee),
) -> Employee:
    if employee.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return employee

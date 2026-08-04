from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware import get_current_employee, require_admin
from app.models import Employee, Pointage
from app.schemas import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    PointageResponse,
    DashboardResponse,
)
from app.utils import generate_salt, hash_pin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardResponse)
def admin_dashboard(
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total = db.query(Employee).filter(Employee.is_active == True).count()

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    all_employees = db.query(Employee).filter(Employee.is_active == True).order_by(Employee.last_name).all()
    employees = [EmployeeResponse.model_validate(e) for e in all_employees]

    today_pointages_raw = (
        db.query(Pointage)
        .filter(Pointage.clock_in >= today_start)
        .order_by(Pointage.clock_in.desc())
        .all()
    )
    today_pointages = [PointageResponse.model_validate(p) for p in today_pointages_raw]

    present_now = 0
    on_break = 0
    completed = 0
    absent = 0
    flagged = 0
    employee_statuses: dict[int, str] = {}

    for emp in all_employees:
        emp_pointages = [p for p in today_pointages_raw if p.employee_id == emp.id]

        if not emp_pointages:
            employee_statuses[emp.id] = "absent"
            absent += 1
        elif emp_pointages[0].status == "on_break":
            employee_statuses[emp.id] = "on_break"
            on_break += 1
        elif emp_pointages[0].status == "in_progress":
            employee_statuses[emp.id] = "present"
            present_now += 1
        elif emp_pointages[0].status == "flagged":
            employee_statuses[emp.id] = "flagged"
            flagged += 1
        else:
            employee_statuses[emp.id] = "completed"
            completed += 1

    return DashboardResponse(
        total_employees=total,
        present_now=present_now,
        on_break=on_break,
        absent=absent,
        completed=completed,
        flagged=flagged,
        today_pointages=today_pointages,
        employees=employees,
        employee_statuses=employee_statuses,
    )


@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees(
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).order_by(Employee.last_name, Employee.first_name).all()
    return [EmployeeResponse.model_validate(e) for e in employees]


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(
    body: EmployeeCreate,
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if len(body.pin) < 4:
        raise HTTPException(400, "Le PIN doit contenir au moins 4 chiffres")

    if body.matricule:
        existing = db.query(Employee).filter(Employee.matricule == body.matricule).first()
        if existing:
            raise HTTPException(400, "Ce matricule existe déjà")
        matricule = body.matricule.strip().upper()
    else:
        count = db.query(Employee).count()
        matricule = f"EMP{count + 1:04d}"

    salt = generate_salt()
    employee = Employee(
        matricule=matricule,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        role=body.role,
        pin_hash=hash_pin(body.pin, salt),
        salt=salt,
        hourly_rate=body.hourly_rate,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(404, "Employé introuvable")

    if body.first_name is not None:
        employee.first_name = body.first_name.strip()
    if body.last_name is not None:
        employee.last_name = body.last_name.strip()
    if body.role is not None:
        employee.role = body.role
    if body.is_active is not None:
        employee.is_active = body.is_active
    if body.hourly_rate is not None:
        employee.hourly_rate = body.hourly_rate
    if body.pin and len(body.pin) >= 4:
        salt = generate_salt()
        employee.salt = salt
        employee.pin_hash = hash_pin(body.pin, salt)

    db.commit()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.get("/pointages")
def list_pointages(
    request: Request,
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Pointage)

    if employee_id:
        query = query.filter(Pointage.employee_id == employee_id)
    if date_from:
        query = query.filter(Pointage.clock_in >= date_from)
    if date_to:
        query = query.filter(Pointage.clock_in <= date_to + "T23:59:59")
    if status:
        query = query.filter(Pointage.status == status)

    pointages = query.order_by(Pointage.clock_in.desc()).limit(1000).all()

    result = []
    for p in pointages:
        emp = db.query(Employee).filter(Employee.id == p.employee_id).first()
        duration = None
        if p.clock_out:
            duration = int((p.clock_out - p.clock_in).total_seconds())
        result.append({
            "id": p.id,
            "employee_id": p.employee_id,
            "employee_name": f"{emp.first_name} {emp.last_name}" if emp else "",
            "matricule": emp.matricule if emp else "",
            "clock_in": p.clock_in.isoformat(),
            "clock_out": p.clock_out.isoformat() if p.clock_out else None,
            "break_start": p.break_start.isoformat() if p.break_start else None,
            "break_end": p.break_end.isoformat() if p.break_end else None,
            "total_break_seconds": p.total_break_seconds,
            "duration_seconds": duration,
            "source_ip": p.source_ip,
            "status": p.status,
        })

    return result


@router.post("/pointages/{pointage_id}/force-clockout", response_model=PointageResponse)
def force_clockout(
    pointage_id: int,
    request: Request,
    admin: Employee = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pointage = db.query(Pointage).filter(Pointage.id == pointage_id).first()
    if not pointage:
        raise HTTPException(404, "Pointage introuvable")
    if pointage.status == "completed":
        raise HTTPException(400, "Pointage déjà terminé")

    if pointage.break_start and not pointage.break_end:
        pointage.break_end = datetime.utcnow()
        pointage.total_break_seconds += int(
            (pointage.break_end - pointage.break_start).total_seconds()
        )

    pointage.clock_out = datetime.utcnow()
    pointage.status = "completed"
    db.commit()
    db.refresh(pointage)
    return pointage

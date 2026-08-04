from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware import get_current_employee
from app.models import Employee, Pointage
from app.schemas import (
    ClockInRequest,
    PointageResponse,
    CurrentStatusResponse,
)
from app.utils import create_session_token

router = APIRouter(prefix="/api/pointage", tags=["pointage"])


def get_current_pointage(db: Session, employee_id: int) -> Pointage | None:
    return (
        db.query(Pointage)
        .filter(
            Pointage.employee_id == employee_id,
            Pointage.status.in_(["in_progress", "on_break"]),
        )
        .order_by(Pointage.clock_in.desc())
        .first()
    )


def has_clocked_today(db: Session, employee_id: int) -> bool:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Pointage)
        .filter(
            Pointage.employee_id == employee_id,
            Pointage.clock_in >= today_start,
        )
        .first()
        is not None
    )


@router.post("/clock-in", response_model=PointageResponse)
def clock_in(
    body: ClockInRequest,
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    existing = get_current_pointage(db, employee.id)
    if existing:
        raise HTTPException(400, "Un pointage est déjà en cours")

    if has_clocked_today(db, employee.id):
        raise HTTPException(400, "Vous avez déjà pointé aujourd'hui")

    client_ip = request.client.host if request.client else "unknown"

    pointage = Pointage(
        employee_id=employee.id,
        clock_in=datetime.utcnow(),
        source_ip=client_ip,
        device_fingerprint=body.device_fingerprint,
        status="in_progress",
    )
    db.add(pointage)
    db.commit()
    db.refresh(pointage)
    return pointage


@router.post("/clock-out", response_model=PointageResponse)
def clock_out(
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    pointage = get_current_pointage(db, employee.id)
    if not pointage:
        raise HTTPException(400, "Aucun pointage en cours")

    pointage.clock_out = datetime.utcnow()

    if pointage.break_start and not pointage.break_end:
        pointage.break_end = datetime.utcnow()

    if pointage.break_start and pointage.break_end:
        pointage.total_break_seconds += int(
            (pointage.break_end - pointage.break_start).total_seconds()
        )

    pointage.status = "completed"
    db.commit()
    db.refresh(pointage)
    return pointage


@router.post("/break/start", response_model=PointageResponse)
def break_start(
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    pointage = get_current_pointage(db, employee.id)
    if not pointage:
        raise HTTPException(400, "Aucun pointage en cours")
    if pointage.status == "on_break":
        raise HTTPException(400, "Déjà en pause")
    if pointage.break_start and not pointage.break_end:
        raise HTTPException(400, "Pause déjà en cours")

    if pointage.break_start and pointage.break_end:
        pointage.total_break_seconds += int(
            (pointage.break_end - pointage.break_start).total_seconds()
        )

    pointage.break_start = datetime.utcnow()
    pointage.break_end = None
    pointage.status = "on_break"
    db.commit()
    db.refresh(pointage)
    return pointage


@router.post("/break/end", response_model=PointageResponse)
def break_end(
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    pointage = get_current_pointage(db, employee.id)
    if not pointage:
        raise HTTPException(400, "Aucun pointage en cours")
    if pointage.status != "on_break":
        raise HTTPException(400, "Pas en pause actuellement")
    if not pointage.break_start:
        raise HTTPException(400, "Aucune pause en cours")

    pointage.break_end = datetime.utcnow()
    pointage.total_break_seconds += int(
        (pointage.break_end - pointage.break_start).total_seconds()
    )
    pointage.break_start = None
    pointage.break_end = None
    pointage.status = "in_progress"
    db.commit()
    db.refresh(pointage)
    return pointage


@router.get("/current", response_model=CurrentStatusResponse)
def get_current_status(
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    pointage = get_current_pointage(db, employee.id)
    if not pointage:
        return CurrentStatusResponse(
            status="completed",
            pointage=None,
            clock_in=None,
            break_start=None,
            elapsed_seconds=0,
            break_elapsed_seconds=0,
        )

    now = datetime.utcnow()
    elapsed = int((now - pointage.clock_in).total_seconds())

    break_elapsed = 0
    if pointage.status == "on_break" and pointage.break_start:
        break_elapsed = int((now - pointage.break_start).total_seconds())

    return CurrentStatusResponse(
        status=pointage.status,
        pointage=PointageResponse.model_validate(pointage),
        clock_in=pointage.clock_in,
        break_start=pointage.break_start,
        elapsed_seconds=elapsed,
        break_elapsed_seconds=break_elapsed,
    )


@router.get("/timesheet")
def get_timesheet(
    employee_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    request: Request = None,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    query = db.query(Pointage)

    if employee_id:
        query = query.filter(Pointage.employee_id == employee_id)
    elif employee.role != "admin":
        query = query.filter(Pointage.employee_id == employee.id)

    if from_date:
        query = query.filter(Pointage.clock_in >= from_date)
    if to_date:
        query = query.filter(Pointage.clock_in <= to_date + "T23:59:59")

    pointages = query.order_by(Pointage.clock_in.desc()).limit(500).all()

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

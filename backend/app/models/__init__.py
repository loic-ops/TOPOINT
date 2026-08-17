from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CompanySettings(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricule = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="employe")
    pin_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    hourly_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pointages = relationship("Pointage", back_populates="employee")


class Pointage(Base):
    __tablename__ = "pointages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    clock_in = Column(DateTime, nullable=False)
    clock_out = Column(DateTime, nullable=True)
    break_start = Column(DateTime, nullable=True)
    break_end = Column(DateTime, nullable=True)
    total_break_seconds = Column(Integer, default=0, nullable=False)
    source_ip = Column(String(45), nullable=False)
    device_fingerprint = Column(String(256), nullable=True)
    status = Column(String(20), default="in_progress", nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="pointages")


class PinAttempt(Base):
    __tablename__ = "pin_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    ip = Column(String(45), nullable=False)
    matricule = Column(String(20), nullable=True)
    success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

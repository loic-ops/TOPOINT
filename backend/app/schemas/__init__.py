from datetime import datetime

from pydantic import BaseModel


class PinLoginRequest(BaseModel):
    matricule: str
    pin: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee: "EmployeeResponse"


class ClockInRequest(BaseModel):
    device_fingerprint: str | None = None


class ClockOutRequest(BaseModel):
    pass


class BreakStartRequest(BaseModel):
    pass


class BreakEndRequest(BaseModel):
    pass


class PointageResponse(BaseModel):
    id: int
    employee_id: int
    clock_in: datetime
    clock_out: datetime | None
    break_start: datetime | None
    break_end: datetime | None
    total_break_seconds: int
    source_ip: str
    is_in_office: bool | None = None
    clock_out_ip: str | None = None
    clock_out_in_office: bool | None = None
    status: str

    class Config:
        from_attributes = True


class CurrentStatusResponse(BaseModel):
    status: str  # "in_progress", "on_break", "completed"
    pointage: PointageResponse | None
    clock_in: datetime | None = None
    break_start: datetime | None = None
    elapsed_seconds: int = 0
    break_elapsed_seconds: int = 0


class EmployeeResponse(BaseModel):
    id: int
    matricule: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    hourly_rate: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    matricule: str | None = None
    first_name: str
    last_name: str
    role: str = "employe"
    pin: str
    hourly_rate: float | None = None


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    hourly_rate: float | None = None
    pin: str | None = None


class NetworkStatusResponse(BaseModel):
    allowed: bool
    client_ip: str
    message: str


class DashboardResponse(BaseModel):
    total_employees: int
    present_now: int
    on_break: int
    absent: int
    completed: int
    flagged: int
    today_pointages: list[PointageResponse]
    employees: list[EmployeeResponse]
    employee_statuses: dict[int, str]


class PointageListResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    matricule: str
    clock_in: datetime
    clock_out: datetime | None
    break_start: datetime | None
    break_end: datetime | None
    total_break_seconds: int
    duration_seconds: int | None
    source_ip: str
    is_in_office: bool | None = None
    clock_out_ip: str | None = None
    clock_out_in_office: bool | None = None
    status: str

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()

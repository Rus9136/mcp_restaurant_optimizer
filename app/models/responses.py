from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Dict, Any


class ForecastItem(BaseModel):
    date: date
    predicted_sales: float


class ForecastResponse(BaseModel):
    data: List[ForecastItem]


class HourlySalesItem(BaseModel):
    date: date
    hour: int
    sales_amount: float


class HourlySalesResponse(BaseModel):
    data: List[HourlySalesItem]


class PlanVsFactItem(BaseModel):
    date: date
    predicted_sales: float
    actual_sales: float
    error: float
    error_percentage: float


class PlanVsFactResponse(BaseModel):
    data: List[PlanVsFactItem]


class ShiftInfo(BaseModel):
    date: date
    payroll_for_shift: float
    schedule_name: str
    work_hours: float


class EmployeePayroll(BaseModel):
    employee_name: str
    payroll_total: float
    shifts: List[ShiftInfo]


class PayrollResponse(BaseModel):
    success: bool
    data: List[EmployeePayroll]


class DepartmentInfo(BaseModel):
    object_name: str
    object_company: str
    hall_area: Optional[float] = None
    kitchen_area: Optional[float] = None
    seats_count: Optional[int] = None


class ErrorDetail(BaseModel):
    type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
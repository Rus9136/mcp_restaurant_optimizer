from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from uuid import UUID


class ForecastRequest(BaseModel):
    department_id: UUID = Field(..., description="UUID подразделения")
    date_start: date = Field(..., description="Дата начала периода")
    date_end: date = Field(..., description="Дата окончания периода")
    
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'date_start' in info.data and v < info.data['date_start']:
            raise ValueError('date_end должна быть больше или равна date_start')
        return v


class HourlySalesRequest(BaseModel):
    department_id: UUID = Field(..., description="UUID подразделения")
    date_start: date = Field(..., description="Дата начала периода")
    date_end: date = Field(..., description="Дата окончания периода")
    
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'date_start' in info.data and v < info.data['date_start']:
            raise ValueError('date_end должна быть больше или равна date_start')
        return v


class PlanVsFactRequest(BaseModel):
    department_id: UUID = Field(..., description="UUID подразделения")
    date_start: date = Field(..., description="Дата начала периода")
    date_end: date = Field(..., description="Дата окончания периода")
    
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'date_start' in info.data and v < info.data['date_start']:
            raise ValueError('date_end должна быть больше или равна date_start')
        return v


class PayrollRequest(BaseModel):
    department_id: UUID = Field(..., description="UUID подразделения")
    date_start: date = Field(..., description="Дата начала периода")
    date_end: date = Field(..., description="Дата окончания периода")
    
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'date_start' in info.data and v < info.data['date_start']:
            raise ValueError('date_end должна быть больше или равна date_start')
        return v


class DepartmentInfoRequest(BaseModel):
    department_id: UUID = Field(..., description="UUID подразделения")
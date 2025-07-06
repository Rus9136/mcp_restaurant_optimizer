from fastapi import APIRouter, Depends
from typing import List
from datetime import date
from loguru import logger

from app.models.requests import (
    ForecastRequest,
    HourlySalesRequest,
    PlanVsFactRequest,
    PayrollRequest,
    DepartmentInfoRequest
)
from app.models.responses import (
    ForecastResponse,
    HourlySalesResponse,
    PlanVsFactResponse,
    PayrollResponse,
    DepartmentInfo,
    ForecastItem,
    HourlySalesItem,
    PlanVsFactItem
)
from app.services.http_client import HTTPClient
from app.utils.cache import cache_manager
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])
settings = get_settings()


@router.post("/forecast", response_model=ForecastResponse)
@cache_manager.cached(ttl=settings.cache_ttl)
async def get_forecast(request: ForecastRequest):
    """
    Получить прогноз продаж по дням для указанного подразделения
    """
    logger.info(f"Запрос прогноза для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    async with HTTPClient() as client:
        params = {
            "from_date": request.date_start.isoformat(),
            "to_date": request.date_end.isoformat(),
            "department_id": str(request.department_id)
        }
        
        data = await client.get_aqniet("forecast/batch", params=params)
        
        # Преобразуем ответ в наш формат
        forecast_items = [
            ForecastItem(
                date=item["date"],
                predicted_sales=item["predicted_sales"]
            )
            for item in data
        ]
        
        return ForecastResponse(data=forecast_items)


@router.post("/hourly_sales", response_model=HourlySalesResponse)
@cache_manager.cached(ttl=settings.cache_ttl)
async def get_hourly_sales(request: HourlySalesRequest):
    """
    Получить почасовые продажи для указанного подразделения
    """
    logger.info(f"Запрос почасовых продаж для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    async with HTTPClient() as client:
        params = {
            "from_date": request.date_start.isoformat(),
            "to_date": request.date_end.isoformat(),
            "department_id": str(request.department_id)
        }
        
        data = await client.get_aqniet("sales/hourly", params=params)
        
        # Преобразуем ответ в наш формат
        sales_items = [
            HourlySalesItem(
                date=item["date"],
                hour=item["hour"],
                sales_amount=item["sales_amount"]
            )
            for item in data
        ]
        
        return HourlySalesResponse(data=sales_items)


@router.post("/plan_vs_fact", response_model=PlanVsFactResponse)
@cache_manager.cached(ttl=settings.cache_ttl)
async def get_plan_vs_fact(request: PlanVsFactRequest):
    """
    Получить сравнение прогноза и факта продаж
    """
    logger.info(f"Запрос план/факт для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    async with HTTPClient() as client:
        params = {
            "from_date": request.date_start.isoformat(),
            "to_date": request.date_end.isoformat(),
            "department_id": str(request.department_id)
        }
        
        data = await client.get_aqniet("forecast/comparison", params=params)
        
        # Преобразуем ответ в наш формат
        comparison_items = [
            PlanVsFactItem(
                date=item["date"],
                predicted_sales=item["predicted_sales"],
                actual_sales=item["actual_sales"],
                error=item["error"],
                error_percentage=item["error_percentage"]
            )
            for item in data
        ]
        
        return PlanVsFactResponse(data=comparison_items)


@router.post("/payroll", response_model=PayrollResponse)
async def get_payroll(request: PayrollRequest):
    """
    Получить ФОТ сотрудников и график работы.
    Не кэшируется, так как данные могут часто меняться.
    """
    logger.info(f"Запрос ФОТ для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    async with HTTPClient() as client:
        params = {
            "department_id": str(request.department_id),
            "from_date": request.date_start.isoformat(),
            "to_date": request.date_end.isoformat()
        }
        
        data = await client.get_madlen("admin/payroll/attendance", params=params)
        
        # Возвращаем данные как есть, они уже в нужном формате
        return PayrollResponse(**data)


@router.post("/department_info", response_model=DepartmentInfo)
@cache_manager.cached(ttl=settings.cache_ttl * 2)  # Кэшируем на час
async def get_department_info(request: DepartmentInfoRequest):
    """
    Получить информацию о подразделении
    """
    logger.info(f"Запрос информации о подразделении department_id={request.department_id}")
    
    async with HTTPClient() as client:
        endpoint = f"admin/departments/{request.department_id}"
        data = await client.get_madlen(endpoint)
        
        # Возвращаем данные как есть, они уже в нужном формате
        return DepartmentInfo(**data)
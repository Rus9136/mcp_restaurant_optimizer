from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import List, AsyncGenerator
from datetime import date, datetime
import json
import asyncio
import os
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
from app.core.exceptions import ExternalAPIError

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
    
    try:
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
    except Exception as e:
        raise ExternalAPIError(
            message=str(e),
            endpoint="forecast/batch"
        )


@router.post("/hourly_sales", response_model=HourlySalesResponse)
@cache_manager.cached(ttl=settings.cache_ttl)
async def get_hourly_sales(request: HourlySalesRequest):
    """
    Получить почасовые продажи для указанного подразделения
    """
    logger.info(f"Запрос почасовых продаж для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    try:
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
    except Exception as e:
        raise ExternalAPIError(
            message=str(e),
            endpoint="sales/hourly"
        )


@router.post("/plan_vs_fact", response_model=PlanVsFactResponse)
@cache_manager.cached(ttl=settings.cache_ttl)
async def get_plan_vs_fact(request: PlanVsFactRequest):
    """
    Получить сравнение прогноза и факта продаж
    """
    logger.info(f"Запрос план/факт для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    try:
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
    except Exception as e:
        raise ExternalAPIError(
            message=str(e),
            endpoint="forecast/comparison"
        )


@router.post("/payroll", response_model=PayrollResponse)
async def get_payroll(request: PayrollRequest):
    """
    Получить ФОТ сотрудников и график работы.
    Не кэшируется, так как данные могут часто меняться.
    """
    logger.info(f"Запрос ФОТ для department_id={request.department_id}, "
                f"период: {request.date_start} - {request.date_end}")
    
    try:
        async with HTTPClient() as client:
            params = {
                "department_id": str(request.department_id),
                "from_date": request.date_start.isoformat(),
                "to_date": request.date_end.isoformat()
            }
            
            data = await client.get_madlen("admin/payroll/attendance", params=params)
            
            # Возвращаем данные как есть, они уже в нужном формате
            return PayrollResponse(**data)
    except Exception as e:
        raise ExternalAPIError(
            message=str(e),
            endpoint="admin/payroll/attendance"
        )


@router.post("/department_info", response_model=DepartmentInfo)
@cache_manager.cached(ttl=settings.cache_ttl * 2)  # Кэшируем на час
async def get_department_info(request: DepartmentInfoRequest):
    """
    Получить информацию о подразделении
    """
    logger.info(f"Запрос информации о подразделении department_id={request.department_id}")
    
    try:
        async with HTTPClient() as client:
            endpoint = f"admin/departments/{request.department_id}"
            data = await client.get_madlen(endpoint)
            
            # Возвращаем данные как есть, они уже в нужном формате
            return DepartmentInfo(**data)
    except Exception as e:
        raise ExternalAPIError(
            message=str(e),
            endpoint=f"admin/departments/{request.department_id}"
        )


async def generate_sse_stream() -> AsyncGenerator[str, None]:
    """
    Генератор потока SSE с бизнес-данными
    """
    # Пример department_id для демонстрации
    demo_department_id = "4cb558ca-a8bc-4b81-871e-043f65218c50"
    
    counter = 0
    while True:
        try:
            counter += 1
            timestamp = datetime.now().isoformat()
            
            # Генерируем разные типы событий
            if counter % 4 == 1:
                # Событие прогноза продаж
                event_data = {
                    "event_type": "forecast_update",
                    "timestamp": timestamp,
                    "department_id": demo_department_id,
                    "data": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "predicted_sales": 150000.0 + (counter * 1000),
                        "confidence": 0.85
                    }
                }
            elif counter % 4 == 2:
                # Событие почасовых продаж
                event_data = {
                    "event_type": "hourly_sales_update",
                    "timestamp": timestamp,
                    "department_id": demo_department_id,
                    "data": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "hour": datetime.now().hour,
                        "sales_amount": 5000.0 + (counter * 100),
                        "transactions_count": 45 + counter
                    }
                }
            elif counter % 4 == 3:
                # Событие сравнения план/факт
                event_data = {
                    "event_type": "plan_vs_fact_update",
                    "timestamp": timestamp,
                    "department_id": demo_department_id,
                    "data": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "predicted_sales": 150000.0,
                        "actual_sales": 145000.0 + (counter * 500),
                        "error_percentage": round((counter * 0.1) - 3.33, 2)
                    }
                }
            else:
                # Событие состояния системы
                event_data = {
                    "event_type": "system_status",
                    "timestamp": timestamp,
                    "data": {
                        "active_departments": 5,
                        "total_daily_sales": 750000.0 + (counter * 10000),
                        "api_response_time_ms": 120 + (counter % 50),
                        "cache_hit_rate": 0.75 + (counter % 20) * 0.01
                    }
                }
            
            # Форматируем как SSE
            sse_data = f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            logger.info(f"Отправляем SSE событие: {event_data['event_type']}")
            yield sse_data
            
            # Ждём 3 секунды между событиями
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Ошибка генерации SSE события: {e}")
            # Отправляем событие об ошибке
            error_event = {
                "event_type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": str(e),
                    "error_type": "stream_generation_error"
                }
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            await asyncio.sleep(5)


@router.get("/sse")
async def stream_sse():
    """
    Server-Sent Events endpoint для потокового получения бизнес-данных
    
    Этот endpoint предоставляет реальное время обновления данных:
    - Прогнозы продаж
    - Почасовые продажи
    - Сравнение план/факт
    - Статус системы
    
    Формат: text/event-stream
    Не требует авторизации для совместимости с Deep Research
    """
    logger.info("Запущен SSE поток для клиента")
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/sse-test", response_class=HTMLResponse)
async def sse_test_page():
    """
    Страница для тестирования SSE endpoint
    """
    # Читаем HTML файл для тестирования
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_sse.html")
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>SSE Test Page Not Found</title></head>
                <body>
                    <h1>SSE Test Page Not Found</h1>
                    <p>The test HTML file was not found.</p>
                    <p>You can test the SSE endpoint directly at: <a href="/api/v1/mcp/sse">/api/v1/mcp/sse</a></p>
                </body>
            </html>
            """,
            status_code=404
        )
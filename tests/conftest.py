import pytest
import sys
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

# Добавляем корневую директорию в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.config import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Тестовые настройки приложения"""
    return Settings(
        app_name="MCP Restaurant Optimizer Test",
        app_version="0.1.0-test",
        aqniet_base_url="https://test-aqniet.com",
        madlen_base_url="https://test-madlen.com",
        aqniet_api_key="test-aqniet-key",
        madlen_api_key="test-madlen-key",
        cache_ttl=1800,
        debug=True
    )


@pytest.fixture
async def client():
    """HTTP клиент для тестирования API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_request_data():
    """Валидные данные для тестовых запросов"""
    return {
        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
        "date_start": "2025-07-01",
        "date_end": "2025-07-31"
    }


@pytest.fixture
def invalid_request_data():
    """Невалидные данные для тестовых запросов"""
    return {
        "department_id": "invalid-uuid",
        "date_start": "2025-07-31",
        "date_end": "2025-07-01"  # date_end < date_start
    }


@pytest.fixture
def mock_forecast_response():
    """Мок ответа для эндпоинта прогноза"""
    return [
        {"date": "2025-07-01", "predicted_sales": 150000.0},
        {"date": "2025-07-02", "predicted_sales": 175000.0},
        {"date": "2025-07-03", "predicted_sales": 200000.0}
    ]


@pytest.fixture
def mock_hourly_sales_response():
    """Мок ответа для эндпоинта почасовых продаж"""
    return [
        {"date": "2025-07-01", "hour": 10, "sales_amount": 5000.0},
        {"date": "2025-07-01", "hour": 11, "sales_amount": 7500.0},
        {"date": "2025-07-01", "hour": 12, "sales_amount": 12000.0}
    ]


@pytest.fixture
def mock_plan_vs_fact_response():
    """Мок ответа для эндпоинта план/факт"""
    return [
        {
            "date": "2025-07-01",
            "predicted_sales": 150000.0,
            "actual_sales": 145000.0,
            "error": -5000.0,
            "error_percentage": -3.33
        },
        {
            "date": "2025-07-02",
            "predicted_sales": 175000.0,
            "actual_sales": 180000.0,
            "error": 5000.0,
            "error_percentage": 2.86
        }
    ]


@pytest.fixture
def mock_payroll_response():
    """Мок ответа для эндпоинта ФОТ"""
    return {
        "success": True,
        "data": [
            {
                "employee_name": "Иванов Иван",
                "payroll_total": 45000.0,
                "shifts": [
                    {
                        "date": "2025-07-01",
                        "payroll_for_shift": 2250.0,
                        "schedule_name": "2/2 дневная",
                        "work_hours": 12.0
                    },
                    {
                        "date": "2025-07-03",
                        "payroll_for_shift": 2250.0,
                        "schedule_name": "2/2 дневная",
                        "work_hours": 12.0
                    }
                ]
            },
            {
                "employee_name": "Петров Петр",
                "payroll_total": 40000.0,
                "shifts": [
                    {
                        "date": "2025-07-01",
                        "payroll_for_shift": 2000.0,
                        "schedule_name": "5/2",
                        "work_hours": 8.0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_department_info_response():
    """Мок ответа для эндпоинта информации о подразделении"""
    return {
        "object_name": "Ресторан Центральный",
        "object_company": "ООО Рестораны",
        "hall_area": 250.5,
        "kitchen_area": 75.0,
        "seats_count": 120
    }


@pytest.fixture
def mock_http_client_success(
    mock_forecast_response, 
    mock_hourly_sales_response,
    mock_plan_vs_fact_response, 
    mock_payroll_response,
    mock_department_info_response
):
    """Мок HTTPClient для успешных запросов"""
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        
        # Настройка ответов для разных эндпоинтов
        async def mock_get_aqniet(endpoint, **kwargs):
            if endpoint == "forecast/batch":
                return mock_forecast_response
            elif endpoint == "sales/hourly":
                return mock_hourly_sales_response
            elif endpoint == "forecast/comparison":
                return mock_plan_vs_fact_response
            return []
        
        async def mock_get_madlen(endpoint, **kwargs):
            if endpoint.startswith("admin/payroll/attendance"):
                return mock_payroll_response
            elif endpoint.startswith("admin/departments/"):
                return mock_department_info_response
            return {}
        
        mock_client.get_aqniet = mock_get_aqniet
        mock_client.get_madlen = mock_get_madlen
        
        # Мокаем конструктор HTTPClient
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        yield mock_client


@pytest.fixture
def mock_http_client_error():
    """Мок HTTPClient для имитации ошибок внешних API"""
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        
        # Настройка исключений для всех методов
        mock_client.get_aqniet.side_effect = Exception("Aqniet API недоступен")
        mock_client.get_madlen.side_effect = Exception("Madlen API недоступен")
        
        # Мокаем конструктор HTTPClient
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        yield mock_client


@pytest.fixture
def disable_cache():
    """Отключение кеширования для тестов"""
    with patch('app.utils.cache.cache_manager.cached') as mock_cached:
        # Возвращаем декоратор, который просто возвращает функцию без изменений
        mock_cached.return_value = lambda func: func
        yield
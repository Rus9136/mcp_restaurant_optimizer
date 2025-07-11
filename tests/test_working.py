import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.mark.asyncio
async def test_forecast_with_mock():
    """Тест forecast с правильными моками"""
    mock_data = [
        {"date": "2025-07-01", "predicted_sales": 150000.0},
        {"date": "2025-07-02", "predicted_sales": 175000.0}
    ]
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        # Отключаем кэш и очищаем его
        with patch('app.utils.cache.cache_manager.cached', lambda **kwargs: lambda func: func):
            # Очищаем кэш перед тестом
            from app.utils.cache import cache_manager
            cache_manager.clear()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mcp/forecast",
                    json={
                        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                        "date_start": "2025-07-01",
                        "date_end": "2025-07-31"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert len(data["data"]) == 2
                assert data["data"][0]["predicted_sales"] == 150000.0


@pytest.mark.asyncio
async def test_forecast_invalid_uuid():
    """Тест forecast с невалидным UUID"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/forecast",
            json={
                "department_id": "invalid-uuid",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_forecast_api_error():
    """Тест forecast с ошибкой внешнего API"""
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.side_effect = Exception("API недоступен")
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        # Отключаем кэш и очищаем его
        with patch('app.utils.cache.cache_manager.cached', lambda **kwargs: lambda func: func):
            # Очищаем кэш перед тестом
            from app.utils.cache import cache_manager
            cache_manager.clear()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mcp/forecast",
                    json={
                        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                        "date_start": "2025-07-01",
                        "date_end": "2025-07-31"
                    }
                )
                
                assert response.status_code == 502
                data = response.json()
                assert "error" in data
                assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_hourly_sales_with_mock():
    """Тест hourly_sales с правильными моками"""
    mock_data = [
        {"date": "2025-07-01", "hour": 10, "sales_amount": 5000.0},
        {"date": "2025-07-01", "hour": 11, "sales_amount": 7500.0}
    ]
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        with patch('app.utils.cache.cache_manager.cached', lambda **kwargs: lambda func: func):
            # Очищаем кэш перед тестом
            from app.utils.cache import cache_manager
            cache_manager.clear()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mcp/hourly_sales",
                    json={
                        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                        "date_start": "2025-07-01",
                        "date_end": "2025-07-31"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert len(data["data"]) == 2
                assert data["data"][0]["hour"] == 10
                assert data["data"][0]["sales_amount"] == 5000.0


@pytest.mark.asyncio
async def test_plan_vs_fact_with_mock():
    """Тест plan_vs_fact с правильными моками"""
    mock_data = [
        {
            "date": "2025-07-01",
            "predicted_sales": 150000.0,
            "actual_sales": 145000.0,
            "error": -5000.0,
            "error_percentage": -3.33
        }
    ]
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        with patch('app.utils.cache.cache_manager.cached', lambda **kwargs: lambda func: func):
            # Очищаем кэш перед тестом
            from app.utils.cache import cache_manager
            cache_manager.clear()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mcp/plan_vs_fact",
                    json={
                        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                        "date_start": "2025-07-01",
                        "date_end": "2025-07-31"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert len(data["data"]) == 1
                assert data["data"][0]["error"] == -5000.0


@pytest.mark.asyncio
async def test_payroll_with_mock():
    """Тест payroll с правильными моками"""
    mock_data = {
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
                    }
                ]
            }
        ]
    }
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_madlen.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/mcp/payroll",
                json={
                    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                    "date_start": "2025-07-01",
                    "date_end": "2025-07-31"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["employee_name"] == "Иванов Иван"


@pytest.mark.asyncio
async def test_department_info_with_mock():
    """Тест department_info с правильными моками"""
    mock_data = {
        "object_name": "Ресторан Центральный",
        "object_company": "ООО Рестораны",
        "hall_area": 250.5,
        "kitchen_area": 75.0,
        "seats_count": 120
    }
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_madlen.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        with patch('app.utils.cache.cache_manager.cached', lambda **kwargs: lambda func: func):
            # Очищаем кэш перед тестом
            from app.utils.cache import cache_manager
            cache_manager.clear()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mcp/department_info",
                    json={
                        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["object_name"] == "Ресторан Центральный"
                assert data["hall_area"] == 250.5


@pytest.mark.asyncio
async def test_missing_fields():
    """Тест с отсутствующими полями"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/mcp/forecast", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        required_fields = {"department_id", "date_start", "date_end"}
        error_fields = {error["loc"][-1] for error in data["detail"]}
        assert required_fields.issubset(error_fields)


@pytest.mark.asyncio
async def test_invalid_date_range():
    """Тест с некорректным диапазоном дат"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/forecast",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-31",
                "date_end": "2025-07-01"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "date_end"
        assert "date_end должна быть больше или равна date_start" in error_detail["msg"]
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_forecast_with_mocked_success():
    """Тест успешного forecast с моком внешнего API"""
    mock_data = [
        {"date": "2025-07-01", "predicted_sales": 150000.0},
        {"date": "2025-07-02", "predicted_sales": 175000.0}
    ]
    
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
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
            assert data["data"][0]["date"] == "2025-07-01"
            assert data["data"][0]["predicted_sales"] == 150000.0


@pytest.mark.asyncio
async def test_forecast_with_mocked_error():
    """Тест forecast с моком ошибки внешнего API"""
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.side_effect = Exception("API недоступен")
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
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
            assert "API недоступен" in data["error"]["message"]


@pytest.mark.asyncio
async def test_hourly_sales_with_mocked_success():
    """Тест успешного hourly_sales с моком внешнего API"""
    mock_data = [
        {"date": "2025-07-01", "hour": 10, "sales_amount": 5000.0},
        {"date": "2025-07-01", "hour": 11, "sales_amount": 7500.0}
    ]
    
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
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
async def test_payroll_with_mocked_success():
    """Тест успешного payroll с моком внешнего API"""
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
    
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
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
            assert data["data"][0]["payroll_total"] == 45000.0


@pytest.mark.asyncio
async def test_department_info_with_mocked_success():
    """Тест успешного department_info с моком внешнего API"""
    mock_data = {
        "object_name": "Ресторан Центральный",
        "object_company": "ООО Рестораны",
        "hall_area": 250.5,
        "kitchen_area": 75.0,
        "seats_count": 120
    }
    
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_madlen.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
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
            assert data["object_company"] == "ООО Рестораны"
            assert data["hall_area"] == 250.5
            assert data["seats_count"] == 120


@pytest.mark.asyncio
async def test_plan_vs_fact_with_mocked_success():
    """Тест успешного plan_vs_fact с моком внешнего API"""
    mock_data = [
        {
            "date": "2025-07-01",
            "predicted_sales": 150000.0,
            "actual_sales": 145000.0,
            "error": -5000.0,
            "error_percentage": -3.33
        }
    ]
    
    with patch('app.services.http_client.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = mock_data
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
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
            assert data["data"][0]["predicted_sales"] == 150000.0
            assert data["data"][0]["actual_sales"] == 145000.0
            assert data["data"][0]["error"] == -5000.0
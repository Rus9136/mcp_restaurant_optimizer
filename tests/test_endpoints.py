import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_forecast_endpoint():
    """Тест эндпоинта forecast"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/forecast",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        # Ожидаем либо успех, либо ошибку внешнего API
        assert response.status_code in [200, 502]
        data = response.json()
        
        if response.status_code == 200:
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_forecast_invalid_uuid():
    """Тест с невалидным UUID"""
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
async def test_forecast_invalid_date_range():
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


@pytest.mark.asyncio
async def test_hourly_sales_endpoint():
    """Тест эндпоинта hourly_sales"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        # Ожидаем либо успех, либо ошибку внешнего API
        assert response.status_code in [200, 502]
        data = response.json()
        
        if response.status_code == 200:
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_plan_vs_fact_endpoint():
    """Тест эндпоинта plan_vs_fact"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        # Ожидаем либо успех, либо ошибку внешнего API
        assert response.status_code in [200, 502]
        data = response.json()
        
        if response.status_code == 200:
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_payroll_endpoint():
    """Тест эндпоинта payroll"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/payroll",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        # Ожидаем либо успех, либо ошибку внешнего API
        assert response.status_code in [200, 502]
        data = response.json()
        
        if response.status_code == 200:
            assert "success" in data
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_department_info_endpoint():
    """Тест эндпоинта department_info"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/department_info",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
            }
        )
        
        # Ожидаем либо успех, либо ошибку внешнего API
        assert response.status_code in [200, 502]
        data = response.json()
        
        if response.status_code == 200:
            assert "object_name" in data
            assert "object_company" in data
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_department_info_invalid_uuid():
    """Тест с невалидным UUID для department_info"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/department_info",
            json={
                "department_id": "invalid-uuid"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_missing_required_fields():
    """Тест с отсутствующими обязательными полями"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/forecast",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Проверяем, что есть ошибки для всех обязательных полей
        required_fields = {"department_id", "date_start", "date_end"}
        error_fields = {error["loc"][-1] for error in data["detail"]}
        assert required_fields.issubset(error_fields)
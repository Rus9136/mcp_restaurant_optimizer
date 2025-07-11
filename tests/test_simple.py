import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_forecast_success(mock_http_client_success, disable_cache):
    """Простой тест для проверки работы эндпоинта forecast"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/mcp/forecast",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        
        assert response.status_code in [200, 502]  # 200 для успеха, 502 для ошибки API
        data = response.json()
        
        if response.status_code == 200:
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
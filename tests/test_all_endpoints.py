import pytest


@pytest.mark.asyncio
async def test_forecast_success(client, valid_request_data, mock_http_client_success, disable_cache):
    """Тест успешного получения прогноза продаж"""
    response = await client.post("/api/v1/mcp/forecast", json=valid_request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    
    for item in data["data"]:
        assert "date" in item
        assert "predicted_sales" in item
        assert isinstance(item["predicted_sales"], (int, float))


@pytest.mark.asyncio
async def test_forecast_invalid_uuid(client, disable_cache):
    """Тест с невалидным UUID для forecast"""
    request_data = {
        "department_id": "invalid-uuid",
        "date_start": "2025-07-01",
        "date_end": "2025-07-31"
    }
    
    response = await client.post("/api/v1/mcp/forecast", json=request_data)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_forecast_external_api_error(client, valid_request_data, mock_http_client_error, disable_cache):
    """Тест обработки ошибки внешнего API для forecast"""
    response = await client.post("/api/v1/mcp/forecast", json=valid_request_data)
    
    assert response.status_code == 502
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_hourly_sales_success(client, valid_request_data, mock_http_client_success, disable_cache):
    """Тест успешного получения почасовых продаж"""
    response = await client.post("/api/v1/mcp/hourly_sales", json=valid_request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    
    for item in data["data"]:
        assert "date" in item
        assert "hour" in item
        assert "sales_amount" in item
        assert isinstance(item["hour"], int)
        assert 0 <= item["hour"] <= 23
        assert isinstance(item["sales_amount"], (int, float))


@pytest.mark.asyncio
async def test_hourly_sales_invalid_uuid(client, disable_cache):
    """Тест с невалидным UUID для hourly_sales"""
    request_data = {
        "department_id": "invalid-uuid",
        "date_start": "2025-07-01",
        "date_end": "2025-07-31"
    }
    
    response = await client.post("/api/v1/mcp/hourly_sales", json=request_data)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_plan_vs_fact_success(client, valid_request_data, mock_http_client_success, disable_cache):
    """Тест успешного получения план/факт"""
    response = await client.post("/api/v1/mcp/plan_vs_fact", json=valid_request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    
    for item in data["data"]:
        assert "date" in item
        assert "predicted_sales" in item
        assert "actual_sales" in item
        assert "error" in item
        assert "error_percentage" in item


@pytest.mark.asyncio
async def test_plan_vs_fact_invalid_date_range(client, disable_cache):
    """Тест с некорректным диапазоном дат для plan_vs_fact"""
    request_data = {
        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
        "date_start": "2025-07-31",
        "date_end": "2025-07-01"  # date_end < date_start
    }
    
    response = await client.post("/api/v1/mcp/plan_vs_fact", json=request_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    error_detail = data["detail"][0]
    assert error_detail["loc"][-1] == "date_end"
    assert "date_end должна быть больше или равна date_start" in error_detail["msg"]


@pytest.mark.asyncio
async def test_payroll_success(client, valid_request_data, mock_http_client_success):
    """Тест успешного получения данных ФОТ"""
    response = await client.post("/api/v1/mcp/payroll", json=valid_request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    
    for employee in data["data"]:
        assert "employee_name" in employee
        assert "payroll_total" in employee
        assert "shifts" in employee
        assert isinstance(employee["shifts"], list)


@pytest.mark.asyncio
async def test_payroll_external_api_error(client, valid_request_data, mock_http_client_error):
    """Тест обработки ошибки внешнего API для payroll"""
    response = await client.post("/api/v1/mcp/payroll", json=valid_request_data)
    
    assert response.status_code == 502
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_department_info_success(client, mock_http_client_success, disable_cache):
    """Тест успешного получения информации о подразделении"""
    request_data = {"department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"}
    
    response = await client.post("/api/v1/mcp/department_info", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "object_name" in data
    assert "object_company" in data
    assert data["object_name"] == "Ресторан Центральный"
    assert data["object_company"] == "ООО Рестораны"


@pytest.mark.asyncio
async def test_department_info_invalid_uuid(client, disable_cache):
    """Тест с невалидным UUID для department_info"""
    request_data = {"department_id": "invalid-uuid"}
    
    response = await client.post("/api/v1/mcp/department_info", json=request_data)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_missing_required_fields(client, disable_cache):
    """Тест с отсутствующими обязательными полями"""
    response = await client.post("/api/v1/mcp/forecast", json={})
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    required_fields = {"department_id", "date_start", "date_end"}
    error_fields = {error["loc"][-1] for error in data["detail"]}
    assert required_fields.issubset(error_fields)


@pytest.mark.asyncio
async def test_api_connection_error(client, valid_request_data):
    """Тест обработки ошибки подключения к внешнему API"""
    from unittest.mock import patch, AsyncMock
    from httpx import ConnectError
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.side_effect = ConnectError("API недоступен")
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        response = await client.post("/api/v1/mcp/forecast", json=valid_request_data)
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "external_api_error"
        assert "API недоступен" in data["error"]["message"]


@pytest.mark.asyncio
async def test_empty_api_response(client, valid_request_data):
    """Тест обработки пустого ответа от внешнего API"""
    from unittest.mock import patch, AsyncMock
    
    with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
        mock_client = AsyncMock()
        mock_client.get_aqniet.return_value = []
        mock_http_client.return_value.__aenter__.return_value = mock_client
        mock_http_client.return_value.__aexit__.return_value = None
        
        response = await client.post("/api/v1/mcp/forecast", json=valid_request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"] == []
import pytest


@pytest.mark.asyncio
async def test_forecast_success(client, valid_request_data, 
                              mock_http_client_success, disable_cache):
    """Тест успешного получения прогноза продаж"""
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=valid_request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверка структуры ответа
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    
    # Проверка структуры элементов
    for item in data["data"]:
        assert "date" in item
        assert "predicted_sales" in item
        assert isinstance(item["predicted_sales"], (int, float))


@pytest.mark.asyncio
async def test_forecast_invalid_uuid(client, disable_cache):
        """Тест с невалидным UUID подразделения"""
        request_data = {
            "department_id": "invalid-uuid-format",
            "date_start": "2025-07-01",
            "date_end": "2025-07-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/forecast",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
@pytest.mark.asyncio
async def test_forecast_invalid_date_range(client, disable_cache):
    """Тест с некорректным диапазоном дат (date_end < date_start)"""
    request_data = {
        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
        "date_start": "2025-07-31",
        "date_end": "2025-07-01"
    }
    
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=request_data
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Проверяем, что ошибка связана с валидацией date_end
    error_detail = data["detail"][0]
    assert error_detail["loc"][-1] == "date_end"
    assert "date_end должна быть больше или равна date_start" in error_detail["msg"]


@pytest.mark.asyncio
async def test_forecast_missing_required_fields(client, disable_cache):
    """Тест с отсутствующими обязательными полями"""
    request_data = {
        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
        # Отсутствуют date_start и date_end
    }
    
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=request_data
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) >= 2  # Должны быть ошибки для date_start и date_end


@pytest.mark.asyncio
async def test_forecast_invalid_date_format(client, disable_cache):
    """Тест с некорректным форматом даты"""
    request_data = {
        "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
        "date_start": "01.07.2025",  # Неправильный формат
        "date_end": "2025-07-31"
    }
    
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=request_data
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_forecast_external_api_error(client, valid_request_data,
                                         mock_http_client_error, disable_cache):
    """Тест обработки ошибки внешнего API"""
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=valid_request_data
    )
    
    assert response.status_code == 502
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "external_api_error"


@pytest.mark.asyncio
async def test_forecast_empty_body(client, disable_cache):
    """Тест с пустым телом запроса"""
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


@pytest.mark.asyncio
async def test_forecast_data_transformation(client, valid_request_data,
                                          mock_http_client_success, disable_cache):
    """Тест корректного преобразования данных из внешнего API"""
    response = await client.post(
        "/api/v1/mcp/forecast",
        json=valid_request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем, что данные корректно преобразованы
    assert data["data"][0]["date"] == "2025-07-01"
    assert data["data"][0]["predicted_sales"] == 150000.0
    assert data["data"][1]["date"] == "2025-07-02"
    assert data["data"][1]["predicted_sales"] == 175000.0
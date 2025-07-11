import pytest


@pytest.mark.asyncio
class TestHourlySalesEndpoint:
    """Тесты для эндпоинта /api/v1/mcp/hourly_sales"""
    
    async def test_hourly_sales_success(self, client, valid_request_data,
                                       mock_http_client_success, disable_cache):
        """Тест успешного получения почасовых продаж"""
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
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
            assert "hour" in item
            assert "sales_amount" in item
            assert isinstance(item["hour"], int)
            assert 0 <= item["hour"] <= 23  # Час должен быть от 0 до 23
            assert isinstance(item["sales_amount"], (int, float))
            assert item["sales_amount"] >= 0  # Продажи не могут быть отрицательными
    
    async def test_hourly_sales_invalid_uuid(self, client, disable_cache):
        """Тест с невалидным UUID подразделения"""
        request_data = {
            "department_id": "not-a-valid-uuid",
            "date_start": "2025-07-01",
            "date_end": "2025-07-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Проверяем, что ошибка связана с department_id
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "department_id"
    
    async def test_hourly_sales_invalid_date_range(self, client, disable_cache):
        """Тест с некорректным диапазоном дат"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025-07-15",
            "date_end": "2025-07-10"  # date_end < date_start
        }
        
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "date_end"
        assert "date_end должна быть больше или равна date_start" in error_detail["msg"]
    
    async def test_hourly_sales_missing_fields(self, client, disable_cache):
        """Тест с отсутствующими обязательными полями"""
        request_data = {
            "date_start": "2025-07-01"
            # Отсутствуют department_id и date_end
        }
        
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Должны быть ошибки для отсутствующих полей
        missing_fields = {"department_id", "date_end"}
        error_fields = {error["loc"][-1] for error in data["detail"]}
        assert missing_fields.issubset(error_fields)
    
    async def test_hourly_sales_external_api_error(self, client, valid_request_data,
                                                  mock_http_client_error, disable_cache):
        """Тест обработки ошибки внешнего API"""
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=valid_request_data
        )
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "external_api_error"
        assert "Aqniet API недоступен" in data["error"]["message"]
    
    async def test_hourly_sales_data_transformation(self, client, valid_request_data,
                                                   mock_http_client_success, disable_cache):
        """Тест корректного преобразования данных из внешнего API"""
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=valid_request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем корректность преобразования данных
        assert len(data["data"]) == 3
        
        # Проверяем первый элемент
        first_item = data["data"][0]
        assert first_item["date"] == "2025-07-01"
        assert first_item["hour"] == 10
        assert first_item["sales_amount"] == 5000.0
        
        # Проверяем второй элемент
        second_item = data["data"][1]
        assert second_item["date"] == "2025-07-01"
        assert second_item["hour"] == 11
        assert second_item["sales_amount"] == 7500.0
    
    async def test_hourly_sales_same_date_range(self, client,
                                               mock_http_client_success, disable_cache):
        """Тест с одинаковыми датами начала и конца (один день)"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025-07-01",
            "date_end": "2025-07-01"  # Тот же день
        }
        
        response = await client.post(
            "/api/v1/mcp/hourly_sales",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
import pytest


@pytest.mark.asyncio
class TestDepartmentInfoEndpoint:
    """Тесты для эндпоинта /api/v1/mcp/department_info"""
    
    async def test_department_info_success(self, client,
                                         mock_http_client_success, disable_cache):
        """Тест успешного получения информации о подразделении"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
        }
        
        response = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверка обязательных полей
        assert "object_name" in data
        assert "object_company" in data
        
        assert isinstance(data["object_name"], str)
        assert isinstance(data["object_company"], str)
        
        # Проверка опциональных полей
        if "hall_area" in data:
            assert isinstance(data["hall_area"], (int, float))
            assert data["hall_area"] > 0
        
        if "kitchen_area" in data:
            assert isinstance(data["kitchen_area"], (int, float))
            assert data["kitchen_area"] > 0
        
        if "seats_count" in data:
            assert isinstance(data["seats_count"], int)
            assert data["seats_count"] > 0
    
    async def test_department_info_invalid_uuid(self, client, disable_cache):
        """Тест с невалидным UUID подразделения"""
        request_data = {
            "department_id": "invalid-uuid-format"
        }
        
        response = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "department_id"
    
    async def test_department_info_missing_field(self, client, disable_cache):
        """Тест с отсутствующим обязательным полем"""
        response = await client.post(
            "/api/v1/mcp/department_info",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Проверяем, что ошибка для department_id
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "department_id"
        assert error_detail["type"] == "missing"
    
    async def test_department_info_external_api_error(self, client,
                                                    mock_http_client_error, disable_cache):
        """Тест обработки ошибки внешнего API"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
        }
        
        response = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "external_api_error"
        assert "Madlen API недоступен" in data["error"]["message"]
    
    async def test_department_info_data_transformation(self, client,
                                                     mock_http_client_success, disable_cache):
        """Тест корректного преобразования данных из внешнего API"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
        }
        
        response = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем корректность данных
        assert data["object_name"] == "Ресторан Центральный"
        assert data["object_company"] == "ООО Рестораны"
        assert data["hall_area"] == 250.5
        assert data["kitchen_area"] == 75.0
        assert data["seats_count"] == 120
    
    async def test_department_info_with_nulls(self, client, disable_cache):
        """Тест с null значениями для опциональных полей"""
        from unittest.mock import patch, AsyncMock
        
        # Мокаем HTTPClient для возврата ответа с null значениями
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_madlen.return_value = {
                "object_name": "Кафе Быстрое",
                "object_company": "ИП Петров",
                "hall_area": None,
                "kitchen_area": None,
                "seats_count": None
            }
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            request_data = {
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
            }
            
            response = await client.post(
                "/api/v1/mcp/department_info",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["object_name"] == "Кафе Быстрое"
            assert data["object_company"] == "ИП Петров"
            assert data["hall_area"] is None
            assert data["kitchen_area"] is None
            assert data["seats_count"] is None
    
    async def test_department_info_double_cache(self, client,
                                              mock_http_client_success, disable_cache):
        """Тест двойного TTL кэширования (1 час вместо 30 минут)"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
        }
        
        # Делаем два запроса подряд
        response1 = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        response2 = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Данные должны быть идентичными (из кэша)
        assert response1.json() == response2.json()
    
    async def test_department_info_empty_body(self, client, disable_cache):
        """Тест с пустым телом запроса (null)"""
        response = await client.post(
            "/api/v1/mcp/department_info",
            content="null",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_department_info_extra_fields(self, client,
                                               mock_http_client_success, disable_cache):
        """Тест с дополнительными полями в запросе (должны игнорироваться)"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "extra_field": "should be ignored",
            "another_field": 123
        }
        
        response = await client.post(
            "/api/v1/mcp/department_info",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "object_name" in data
        assert "extra_field" not in data
        assert "another_field" not in data
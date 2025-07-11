import pytest
from httpx import ReadTimeout, ConnectError


@pytest.mark.asyncio
class TestAPIErrors:
    """Интеграционные тесты для проверки обработки ошибок внешних API"""
    
    async def test_aqniet_connection_error(self, client, valid_request_data):
        """Тест обработки ошибки подключения к Aqniet API"""
        from unittest.mock import patch, AsyncMock
        
        # Мокаем HTTPClient для имитации ошибки подключения
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_aqniet.side_effect = ConnectError("Не удалось подключиться к Aqniet API")
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            # Тестируем эндпоинт forecast
            response = await client.post(
                "/api/v1/mcp/forecast",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
            assert "Не удалось подключиться к Aqniet API" in data["error"]["message"]
    
    async def test_aqniet_timeout_error(self, client, valid_request_data):
        """Тест обработки таймаута при запросе к Aqniet API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_aqniet.side_effect = ReadTimeout("Превышено время ожидания ответа от Aqniet API")
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            # Тестируем эндпоинт hourly_sales
            response = await client.post(
                "/api/v1/mcp/hourly_sales",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
            assert "Превышено время ожидания" in data["error"]["message"]
    
    async def test_madlen_connection_error(self, client, valid_request_data):
        """Тест обработки ошибки подключения к Madlen API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_madlen.side_effect = ConnectError("Не удалось подключиться к Madlen API")
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            # Тестируем эндпоинт payroll
            response = await client.post(
                "/api/v1/mcp/payroll",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
            assert "Не удалось подключиться к Madlen API" in data["error"]["message"]
    
    async def test_invalid_response_format(self, client, valid_request_data):
        """Тест обработки некорректного формата ответа от внешнего API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            # Возвращаем строку вместо ожидаемого списка
            mock_client.get_aqniet.return_value = "Invalid response format"
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            # Тестируем эндпоинт plan_vs_fact
            response = await client.post(
                "/api/v1/mcp/plan_vs_fact",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
    
    async def test_partial_data_error(self, client, valid_request_data):
        """Тест обработки частично некорректных данных от внешнего API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            # Возвращаем данные с отсутствующими полями
            mock_client.get_aqniet.return_value = [
                {"date": "2025-07-01"},  # Отсутствует predicted_sales
                {"predicted_sales": 150000.0}  # Отсутствует date
            ]
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            response = await client.post(
                "/api/v1/mcp/forecast",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
    
    async def test_empty_api_response(self, client, valid_request_data):
        """Тест обработки пустого ответа от внешнего API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_aqniet.return_value = []
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            response = await client.post(
                "/api/v1/mcp/forecast",
                json=valid_request_data
            )
            
            # Пустой ответ - это валидный случай
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"] == []
    
    async def test_api_returns_error_status(self, client, valid_request_data):
        """Тест обработки ошибочного статуса от внешнего API"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            # Имитируем, что внешний API вернул ошибку
            mock_client.get_madlen.side_effect = Exception("403 Forbidden: Недостаточно прав")
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            request_data = {"department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"}
            
            response = await client.post(
                "/api/v1/mcp/department_info",
                json=request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
            assert "403 Forbidden" in data["error"]["message"]
    
    async def test_network_error_retry(self, client, valid_request_data):
        """Тест повторной попытки при сетевой ошибке"""
        from unittest.mock import patch, AsyncMock
        
        call_count = 0
        
        async def mock_get_aqniet(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectError("Временная сетевая ошибка")
            return [{"date": "2025-07-01", "predicted_sales": 150000.0}]
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_aqniet = mock_get_aqniet
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            response = await client.post(
                "/api/v1/mcp/forecast",
                json=valid_request_data
            )
            
            # Первый вызов должен вернуть ошибку (нет встроенного retry)
            assert response.status_code == 502
            assert call_count == 1
    
    async def test_malformed_json_response(self, client, valid_request_data):
        """Тест обработки некорректного JSON в ответе"""
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            # Возвращаем None вместо ожидаемых данных
            mock_client.get_aqniet.return_value = None
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            response = await client.post(
                "/api/v1/mcp/hourly_sales",
                json=valid_request_data
            )
            
            assert response.status_code == 502
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "external_api_error"
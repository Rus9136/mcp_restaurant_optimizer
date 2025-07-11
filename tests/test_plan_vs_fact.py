import pytest


@pytest.mark.asyncio
class TestPlanVsFactEndpoint:
    """Тесты для эндпоинта /api/v1/mcp/plan_vs_fact"""
    
    async def test_plan_vs_fact_success(self, client, valid_request_data,
                                       mock_http_client_success, disable_cache):
        """Тест успешного получения сравнения план/факт"""
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=valid_request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверка структуры ответа
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        
        # Проверка структуры элементов
        for item in data["data"]:
            assert "date" in item
            assert "predicted_sales" in item
            assert "actual_sales" in item
            assert "error" in item
            assert "error_percentage" in item
            
            # Проверка типов данных
            assert isinstance(item["predicted_sales"], (int, float))
            assert isinstance(item["actual_sales"], (int, float))
            assert isinstance(item["error"], (int, float))
            assert isinstance(item["error_percentage"], (int, float))
            
            # Проверка корректности расчета ошибки
            expected_error = item["actual_sales"] - item["predicted_sales"]
            assert abs(item["error"] - expected_error) < 0.01  # Допустимая погрешность
    
    async def test_plan_vs_fact_invalid_uuid(self, client, disable_cache):
        """Тест с невалидным UUID подразделения"""
        request_data = {
            "department_id": "12345",  # Невалидный UUID
            "date_start": "2025-07-01",
            "date_end": "2025-07-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "department_id"
    
    async def test_plan_vs_fact_invalid_date_range(self, client, disable_cache):
        """Тест с некорректным диапазоном дат"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025-08-01",
            "date_end": "2025-07-01"  # date_end < date_start
        }
        
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "date_end"
        assert "date_end должна быть больше или равна date_start" in error_detail["msg"]
    
    async def test_plan_vs_fact_all_fields_missing(self, client, disable_cache):
        """Тест с отсутствием всех обязательных полей"""
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Проверяем наличие ошибок для всех обязательных полей
        required_fields = {"department_id", "date_start", "date_end"}
        error_fields = {error["loc"][-1] for error in data["detail"]}
        assert required_fields == error_fields
    
    async def test_plan_vs_fact_external_api_error(self, client, valid_request_data,
                                                  mock_http_client_error, disable_cache):
        """Тест обработки ошибки внешнего API"""
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=valid_request_data
        )
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "external_api_error"
        assert "Aqniet API недоступен" in data["error"]["message"]
    
    async def test_plan_vs_fact_data_transformation(self, client, valid_request_data,
                                                   mock_http_client_success, disable_cache):
        """Тест корректного преобразования данных из внешнего API"""
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=valid_request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем корректность преобразования данных
        assert len(data["data"]) == 2
        
        # Проверяем первый элемент (недовыполнение плана)
        first_item = data["data"][0]
        assert first_item["date"] == "2025-07-01"
        assert first_item["predicted_sales"] == 150000.0
        assert first_item["actual_sales"] == 145000.0
        assert first_item["error"] == -5000.0
        assert first_item["error_percentage"] == -3.33
        
        # Проверяем второй элемент (перевыполнение плана)
        second_item = data["data"][1]
        assert second_item["date"] == "2025-07-02"
        assert second_item["predicted_sales"] == 175000.0
        assert second_item["actual_sales"] == 180000.0
        assert second_item["error"] == 5000.0
        assert second_item["error_percentage"] == 2.86
    
    async def test_plan_vs_fact_future_dates(self, client,
                                            mock_http_client_success, disable_cache):
        """Тест с будущими датами (прогноз без фактических данных)"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2026-01-01",
            "date_end": "2026-01-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=request_data
        )
        
        # API должен принять запрос, даже если даты в будущем
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    async def test_plan_vs_fact_invalid_date_format(self, client, disable_cache):
        """Тест с некорректным форматом даты"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025/07/01",  # Неправильный разделитель
            "date_end": "2025-07-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/plan_vs_fact",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "date_start"
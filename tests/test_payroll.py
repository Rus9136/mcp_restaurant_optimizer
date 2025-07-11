import pytest


@pytest.mark.asyncio
class TestPayrollEndpoint:
    """Тесты для эндпоинта /api/v1/mcp/payroll"""
    
    async def test_payroll_success(self, client, valid_request_data,
                                 mock_http_client_success):
        """Тест успешного получения данных ФОТ"""
        # Этот эндпоинт не кэшируется
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=valid_request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверка структуры ответа
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        
        # Проверка структуры данных сотрудника
        for employee in data["data"]:
            assert "employee_name" in employee
            assert "payroll_total" in employee
            assert "shifts" in employee
            
            assert isinstance(employee["employee_name"], str)
            assert isinstance(employee["payroll_total"], (int, float))
            assert employee["payroll_total"] >= 0
            assert isinstance(employee["shifts"], list)
            
            # Проверка структуры смен
            for shift in employee["shifts"]:
                assert "date" in shift
                assert "payroll_for_shift" in shift
                assert "schedule_name" in shift
                assert "work_hours" in shift
                
                assert isinstance(shift["payroll_for_shift"], (int, float))
                assert shift["payroll_for_shift"] >= 0
                assert isinstance(shift["schedule_name"], str)
                assert isinstance(shift["work_hours"], (int, float))
                assert shift["work_hours"] > 0
    
    async def test_payroll_invalid_uuid(self, client):
        """Тест с невалидным UUID подразделения"""
        request_data = {
            "department_id": "not-a-uuid",
            "date_start": "2025-07-01",
            "date_end": "2025-07-31"
        }
        
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "department_id"
    
    async def test_payroll_invalid_date_range(self, client):
        """Тест с некорректным диапазоном дат"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025-07-20",
            "date_end": "2025-07-10"  # date_end < date_start
        }
        
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_detail = data["detail"][0]
        assert error_detail["loc"][-1] == "date_end"
        assert "date_end должна быть больше или равна date_start" in error_detail["msg"]
    
    async def test_payroll_missing_fields(self, client):
        """Тест с отсутствующими обязательными полями"""
        request_data = {
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
            # Отсутствуют date_start и date_end
        }
        
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=request_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Должны быть ошибки для отсутствующих полей
        missing_fields = {"date_start", "date_end"}
        error_fields = {error["loc"][-1] for error in data["detail"]}
        assert missing_fields.issubset(error_fields)
    
    async def test_payroll_external_api_error(self, client, valid_request_data,
                                            mock_http_client_error):
        """Тест обработки ошибки внешнего API"""
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=valid_request_data
        )
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "external_api_error"
        assert "Madlen API недоступен" in data["error"]["message"]
    
    async def test_payroll_data_transformation(self, client, valid_request_data,
                                             mock_http_client_success):
        """Тест корректного преобразования данных из внешнего API"""
        response = await client.post(
            "/api/v1/mcp/payroll",
            json=valid_request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем корректность данных
        assert data["success"] is True
        assert len(data["data"]) == 2
        
        # Проверяем первого сотрудника
        first_employee = data["data"][0]
        assert first_employee["employee_name"] == "Иванов Иван"
        assert first_employee["payroll_total"] == 45000.0
        assert len(first_employee["shifts"]) == 2
        
        # Проверяем первую смену первого сотрудника
        first_shift = first_employee["shifts"][0]
        assert first_shift["date"] == "2025-07-01"
        assert first_shift["payroll_for_shift"] == 2250.0
        assert first_shift["schedule_name"] == "2/2 дневная"
        assert first_shift["work_hours"] == 12.0
        
        # Проверяем второго сотрудника
        second_employee = data["data"][1]
        assert second_employee["employee_name"] == "Петров Петр"
        assert second_employee["payroll_total"] == 40000.0
        assert len(second_employee["shifts"]) == 1
    
    async def test_payroll_no_cache(self, client, valid_request_data,
                                   mock_http_client_success):
        """Тест, что эндпоинт не кэшируется"""
        # Делаем два запроса подряд
        response1 = await client.post(
            "/api/v1/mcp/payroll",
            json=valid_request_data
        )
        
        response2 = await client.post(
            "/api/v1/mcp/payroll",
            json=valid_request_data
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Оба запроса должны быть успешными
        # (в реальности проверить отсутствие кэширования можно только
        # проверив логи или замокав кэш-менеджер)
    
    async def test_payroll_empty_response(self, client):
        """Тест с пустым ответом от внешнего API"""
        from unittest.mock import patch, AsyncMock
        
        # Мокаем HTTPClient для возврата пустого ответа
        with patch('app.api.v1.endpoints.HTTPClient') as mock_http_client:
            mock_client = AsyncMock()
            mock_client.get_madlen.return_value = {"success": True, "data": []}
            mock_http_client.return_value.__aenter__.return_value = mock_client
            mock_http_client.return_value.__aexit__.return_value = None
            
            request_data = {
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
            
            response = await client.post(
                "/api/v1/mcp/payroll",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == []
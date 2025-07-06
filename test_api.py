#!/usr/bin/env python3
"""
Скрипт для тестирования MCP API эндпоинтов
"""

import asyncio
import httpx
from datetime import date, timedelta
from pprint import pprint

BASE_URL = "http://localhost:8003"

# Тестовые данные
TEST_DEPARTMENT_ID = "4cb558ca-a8bc-4b81-871e-043f65218c50"
TEST_DATE_START = date.today()
TEST_DATE_END = TEST_DATE_START + timedelta(days=7)


async def test_forecast():
    """Тестирование прогноза продаж"""
    print("\n=== Тестирование /api/v1/mcp/forecast ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/forecast",
            json={
                "department_id": TEST_DEPARTMENT_ID,
                "date_start": TEST_DATE_START.isoformat(),
                "date_end": TEST_DATE_END.isoformat()
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Получено записей: {len(data['data'])}")
            if data['data']:
                print("Первая запись:")
                pprint(data['data'][0])
        else:
            print("Ошибка:")
            pprint(response.json())


async def test_hourly_sales():
    """Тестирование почасовых продаж"""
    print("\n=== Тестирование /api/v1/mcp/hourly_sales ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/hourly_sales",
            json={
                "department_id": TEST_DEPARTMENT_ID,
                "date_start": TEST_DATE_START.isoformat(),
                "date_end": TEST_DATE_END.isoformat()
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Получено записей: {len(data['data'])}")
            if data['data']:
                print("Первые 3 записи:")
                for i, item in enumerate(data['data'][:3]):
                    pprint(item)
        else:
            print("Ошибка:")
            pprint(response.json())


async def test_plan_vs_fact():
    """Тестирование сравнения план/факт"""
    print("\n=== Тестирование /api/v1/mcp/plan_vs_fact ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/plan_vs_fact",
            json={
                "department_id": TEST_DEPARTMENT_ID,
                "date_start": TEST_DATE_START.isoformat(),
                "date_end": TEST_DATE_END.isoformat()
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Получено записей: {len(data['data'])}")
            if data['data']:
                print("Первая запись:")
                pprint(data['data'][0])
        else:
            print("Ошибка:")
            pprint(response.json())


async def test_payroll():
    """Тестирование ФОТ и графиков"""
    print("\n=== Тестирование /api/v1/mcp/payroll ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/payroll",
            json={
                "department_id": TEST_DEPARTMENT_ID,
                "date_start": TEST_DATE_START.isoformat(),
                "date_end": TEST_DATE_END.isoformat()
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['data']:
                print(f"Получено сотрудников: {len(data['data'])}")
                print("Первый сотрудник:")
                emp = data['data'][0]
                print(f"  Имя: {emp['employee_name']}")
                print(f"  Общий ФОТ: {emp['payroll_total']}")
                print(f"  Количество смен: {len(emp['shifts'])}")
                if emp['shifts']:
                    print("  Первая смена:")
                    pprint(emp['shifts'][0])
        else:
            print("Ошибка:")
            pprint(response.json())


async def test_department_info():
    """Тестирование информации о подразделении"""
    print("\n=== Тестирование /api/v1/mcp/department_info ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/department_info",
            json={
                "department_id": TEST_DEPARTMENT_ID
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            pprint(data)
        else:
            print("Ошибка:")
            pprint(response.json())


async def test_invalid_request():
    """Тестирование обработки ошибок"""
    print("\n=== Тестирование обработки ошибок ===")
    
    async with httpx.AsyncClient() as client:
        # Неверный UUID
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/forecast",
            json={
                "department_id": "invalid-uuid",
                "date_start": TEST_DATE_START.isoformat(),
                "date_end": TEST_DATE_END.isoformat()
            }
        )
        
        print(f"Status при неверном UUID: {response.status_code}")
        pprint(response.json())
        
        # Неверный диапазон дат
        response = await client.post(
            f"{BASE_URL}/api/v1/mcp/forecast",
            json={
                "department_id": TEST_DEPARTMENT_ID,
                "date_start": TEST_DATE_END.isoformat(),
                "date_end": TEST_DATE_START.isoformat()
            }
        )
        
        print(f"\nStatus при неверном диапазоне дат: {response.status_code}")
        pprint(response.json())


async def main():
    """Запуск всех тестов"""
    print("Запуск тестов MCP API...")
    print(f"URL: {BASE_URL}")
    print(f"Department ID: {TEST_DEPARTMENT_ID}")
    print(f"Период: {TEST_DATE_START} - {TEST_DATE_END}")
    
    # Проверка доступности сервера
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print("❌ Сервер недоступен!")
                return
            print("✅ Сервер доступен")
    except Exception as e:
        print(f"❌ Не удалось подключиться к серверу: {e}")
        return
    
    # Запуск тестов
    tests = [
        test_forecast,
        test_hourly_sales,
        test_plan_vs_fact,
        test_payroll,
        test_department_info,
        test_invalid_request
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
        
        # Небольшая пауза между тестами
        await asyncio.sleep(0.5)
    
    print("\n✅ Все тесты завершены")


if __name__ == "__main__":
    asyncio.run(main())
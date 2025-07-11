#!/usr/bin/env python3
"""
Тестовый клиент для SSE endpoint
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

import httpx
from loguru import logger


class SSEClient:
    """
    Клиент для подключения к SSE потоку
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/api/v1/mcp/sse"
        self.is_connected = False
        self.event_handlers = {}
        
    def add_event_handler(self, event_type: str, handler):
        """
        Добавляет обработчик для конкретного типа событий
        """
        self.event_handlers[event_type] = handler
        
    async def connect(self, department_id: str = None, interval: int = 5):
        """
        Подключается к SSE потоку
        """
        params = {"interval": interval}
        if department_id:
            params["department_id"] = department_id
            
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Подключение к SSE: {self.sse_url}")
                
                async with client.stream("GET", self.sse_url, params=params) as response:
                    if response.status_code != 200:
                        logger.error(f"Ошибка подключения: {response.status_code}")
                        return
                    
                    logger.info("Успешно подключен к SSE потоку")
                    self.is_connected = True
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])  # Убираем "data: "
                                await self._handle_event(data)
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка декодирования JSON: {e}")
                                
        except Exception as e:
            logger.error(f"Ошибка SSE соединения: {e}")
        finally:
            self.is_connected = False
            logger.info("SSE соединение закрыто")
    
    async def _handle_event(self, data: Dict[str, Any]):
        """
        Обрабатывает полученное событие
        """
        event_type = data.get("type")
        timestamp = data.get("timestamp")
        
        logger.info(f"Получено событие: {event_type} в {timestamp}")
        
        # Вызываем зарегистрированный обработчик
        if event_type in self.event_handlers:
            try:
                await self.event_handlers[event_type](data)
            except Exception as e:
                logger.error(f"Ошибка в обработчике {event_type}: {e}")
        else:
            # Обработчик по умолчанию
            await self._default_handler(data)
    
    async def _default_handler(self, data: Dict[str, Any]):
        """
        Обработчик по умолчанию для всех событий
        """
        event_type = data.get("type", "unknown")
        event_data = data.get("data", {})
        
        print(f"\n{'='*50}")
        print(f"Событие: {event_type.upper()}")
        print(f"Время: {data.get('timestamp')}")
        print(f"Подразделение: {data.get('department_id')}")
        print(f"Данные:")
        
        if event_type == "sales":
            print(f"  💰 Общие продажи: {event_data.get('total_sales', 0):,.2f} руб")
            print(f"  📊 Транзакций: {event_data.get('total_transactions', 0)}")
            print(f"  💳 Средний чек: {event_data.get('average_check', 0):,.2f} руб")
            
            if "top_dishes" in event_data:
                print("  🍽️ Топ блюд:")
                for dish in event_data["top_dishes"]:
                    print(f"    - {dish['name']}: {dish['count']} шт")
                    
        elif event_type == "bookings":
            print(f"  📅 Бронирований сегодня: {event_data.get('total_bookings_today', 0)}")
            print(f"  ✅ Подтверждено: {event_data.get('confirmed_bookings', 0)}")
            print(f"  ⏳ Ожидает: {event_data.get('pending_bookings', 0)}")
            print(f"  ❌ Отменено: {event_data.get('cancelled_bookings', 0)}")
            print(f"  👥 Средний размер группы: {event_data.get('average_party_size', 0)}")
            
        elif event_type == "occupancy":
            print(f"  🏢 Загрузка зала: {event_data.get('current_occupancy_percent', 0)}%")
            print(f"  🪑 Занято столов: {event_data.get('occupied_tables', 0)}/{event_data.get('total_tables', 0)}")
            print(f"  ⏰ Очередь: {event_data.get('waiting_queue', 0)} человек")
            
        elif event_type == "shifts":
            print(f"  👨‍💼 Сотрудников сегодня: {event_data.get('total_staff_today', 0)}")
            print(f"  🔄 Сейчас работает: {event_data.get('currently_working', 0)}")
            print(f"  ☕ На перерыве: {event_data.get('on_break', 0)}")
            
            if "departments" in event_data:
                print("  🏢 По отделам:")
                for dept, info in event_data["departments"].items():
                    print(f"    - {dept}: {info['working']}/{info['planned']}")
                    
        elif event_type == "connection":
            print(f"  🔗 {event_data.get('message', 'Подключен')}")
            
        elif event_type == "error":
            print(f"  ❌ Ошибка: {event_data.get('message', 'Неизвестная ошибка')}")
            
        print(f"{'='*50}\n")


# Пример использования
async def main():
    """
    Основная функция для демонстрации работы SSE клиента
    """
    client = SSEClient("http://localhost:8003")  # Или ваш домен
    
    # Добавляем специальный обработчик для событий продаж
    async def sales_handler(data):
        sales_data = data.get("data", {})
        total_sales = sales_data.get("total_sales", 0)
        
        if total_sales > 100000:
            logger.warning(f"🚨 Высокие продажи: {total_sales:,.2f} руб!")
        
        # Можно отправить уведомление, сохранить в БД и т.д.
        print(f"📈 Обработчик продаж: {total_sales:,.2f} руб")
    
    # Добавляем обработчик для событий загрузки
    async def occupancy_handler(data):
        occupancy_data = data.get("data", {})
        occupancy_percent = occupancy_data.get("current_occupancy_percent", 0)
        
        if occupancy_percent > 90:
            logger.warning(f"🚨 Высокая загрузка зала: {occupancy_percent}%!")
        elif occupancy_percent < 30:
            logger.info(f"📉 Низкая загрузка зала: {occupancy_percent}%")
        
        print(f"🏢 Обработчик загрузки: {occupancy_percent}%")
    
    # Регистрируем обработчики
    client.add_event_handler("sales", sales_handler)
    client.add_event_handler("occupancy", occupancy_handler)
    
    try:
        # Подключаемся к SSE потоку
        await client.connect(
            department_id="4cb558ca-a8bc-4b81-871e-043f65218c50",
            interval=3  # Интервал 3 секунды
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, отключаемся...")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    # Настройка логирования
    logger.add(
        "sse_client.log",
        rotation="10 MB",
        retention="7 days",
        format="{time} | {level} | {message}"
    )
    
    print("SSE Test Client")
    print("===============")
    print("Подключение к SSE потоку...")
    print("Для выхода нажмите Ctrl+C")
    print()
    
    # Запускаем клиент
    asyncio.run(main())
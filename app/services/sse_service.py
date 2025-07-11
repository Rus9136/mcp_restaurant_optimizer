"""
SSE Service для потоковой передачи данных ресторанной аналитики
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger

from app.services.http_client import HTTPClient
from app.core.config import get_settings

# Импорт для работы с базой данных (опционально)
try:
    from app.services.database_integration import DatabaseSSEProvider, CachedDatabaseSSEProvider
    DATABASE_INTEGRATION_AVAILABLE = True
except ImportError:
    DATABASE_INTEGRATION_AVAILABLE = False
    # Заглушки для классов, если модуль недоступен
    class DatabaseSSEProvider:
        pass
    class CachedDatabaseSSEProvider:
        pass


class SSEService:
    """
    Сервис для генерации Server-Sent Events с данными ресторанной аналитики
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.active_connections: Dict[str, bool] = {}
        self._demo_mode = False  # Продакшен режим по умолчанию
        self._db_provider = None
        
        # Инициализация провайдера базы данных
        self._initialize_database_provider()
        
        if self._db_provider:
            logger.info("SSE Service initialized in production mode with database integration")
        else:
            logger.warning("SSE Service initialized in fallback mode - using external APIs and demo data")
    
    def _initialize_database_provider(self):
        """Инициализация провайдера базы данных"""
        try:
            if DATABASE_INTEGRATION_AVAILABLE and hasattr(self.settings, 'database_url') and self.settings.database_url:
                database_type = getattr(self.settings, 'database_type', 'postgresql')
                cache_ttl = getattr(self.settings, 'sse_cache_ttl', 30)
                
                self._db_provider = CachedDatabaseSSEProvider(
                    db_url=self.settings.database_url,
                    db_type=database_type,
                    cache_ttl=cache_ttl
                )
                logger.info(f"Database provider initialized: {database_type}")
            else:
                logger.warning("Database integration not available or not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize database provider: {e}")
            self._db_provider = None
        
    async def generate_sse_stream(
        self, 
        client_id: str,
        department_id: Optional[str] = None,
        interval: int = 5
    ) -> AsyncGenerator[str, None]:
        """
        Генерирует SSE поток с данными ресторанной аналитики
        
        Args:
            client_id: Уникальный ID клиента
            department_id: ID подразделения (опционально)
            interval: Интервал между событиями в секундах
        """
        self.active_connections[client_id] = True
        
        try:
            # Отправляем событие подключения
            yield self._format_sse_event({
                "type": "connection",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "message": "Connected to MCP SSE stream"
            })
            
            counter = 0
            
            while self.active_connections.get(client_id, False):
                counter += 1
                
                try:
                    # Генерируем разные типы событий циклически
                    event_type = counter % 4
                    
                    if event_type == 0:
                        # Событие продаж
                        event_data = await self._get_sales_event(department_id)
                    elif event_type == 1:
                        # Событие бронирований
                        event_data = await self._get_bookings_event(department_id)
                    elif event_type == 2:
                        # Событие загрузки
                        event_data = await self._get_occupancy_event(department_id)
                    else:
                        # Событие смен
                        event_data = await self._get_shifts_event(department_id)
                    
                    yield self._format_sse_event(event_data)
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Ошибка генерации SSE события: {e}")
                    # Отправляем событие об ошибке
                    error_event = {
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "client_id": client_id
                    }
                    yield self._format_sse_event(error_event)
                    await asyncio.sleep(interval)
                    
        except asyncio.CancelledError:
            logger.info(f"SSE соединение для клиента {client_id} было отменено")
        finally:
            # Очищаем соединение
            self.active_connections.pop(client_id, None)
            logger.info(f"Клиент {client_id} отключился от SSE потока")
    
    def _format_sse_event(self, data: Dict) -> str:
        """
        Форматирует данные в SSE формат
        """
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    def _create_error_event(self, event_type: str, source: str, error_message: str, department_id: str) -> Dict:
        """
        Создает событие об ошибке в правильном SSE формате
        """
        return {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "department_id": department_id,
            "data": {
                "event_type": event_type,
                "source": source,
                "error": error_message,
                "fallback_available": True
            }
        }
    
    async def _get_sales_event(self, department_id: Optional[str] = None) -> Dict:
        """
        Получает данные о продажах
        """
        if self._demo_mode:
            return self._generate_demo_sales_data(department_id)
        
        dept_id = department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50"
        
        # Сначала пытаемся получить данные из базы данных
        if self._db_provider:
            try:
                return await self._db_provider.get_real_sales_data(dept_id)
            except Exception as db_error:
                logger.warning(f"Database error for sales data: {db_error}")
                return self._create_error_event("sales", "database", str(db_error), dept_id)
        
        # Fallback на внешние API
        try:
            async with HTTPClient() as client:
                now = datetime.now()
                hour_ago = now - timedelta(hours=1)
                
                params = {
                    "from_date": hour_ago.date().isoformat(),
                    "to_date": now.date().isoformat(),
                    "department_id": dept_id
                }
                
                sales_data = await client.get_aqniet("sales/hourly", params=params)
                
                # Проверяем, что данные получены
                if not sales_data:
                    logger.warning("Empty sales data from Aqniet API")
                    return self._create_error_event("sales", "api", "No data received from Aqniet API", dept_id)
                
                # Агрегируем данные
                total_sales = sum(item.get("sales_amount", 0) for item in sales_data)
                total_transactions = sum(item.get("transactions_count", 0) for item in sales_data)
                
                return {
                    "type": "sales",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": dept_id,
                    "data": {
                        "total_sales": total_sales,
                        "total_transactions": total_transactions,
                        "average_check": total_sales / total_transactions if total_transactions > 0 else 0,
                        "period": "last_hour",
                        "currency": "RUB",
                        "source": "aqniet_api"
                    }
                }
                
        except Exception as api_error:
            logger.error(f"Ошибка получения данных о продажах из API: {api_error}")
            return self._create_error_event("sales", "api", str(api_error), dept_id)
    
    async def _get_bookings_event(self, department_id: Optional[str] = None) -> Dict:
        """
        Получает данные о бронированиях
        """
        if self._demo_mode:
            return self._generate_demo_bookings_data(department_id)
        
        dept_id = department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50"
        
        # Пытаемся получить данные из базы данных
        if self._db_provider:
            try:
                return await self._db_provider.get_real_bookings_data(dept_id)
            except Exception as db_error:
                logger.warning(f"Database error for bookings data: {db_error}")
                return self._create_error_event("bookings", "database", str(db_error), dept_id)
        
        # Fallback на внешние API
        try:
            async with HTTPClient() as client:
                bookings_data = await client.get_madlen("bookings/today", {
                    "department_id": dept_id
                })
                
                if not bookings_data:
                    logger.warning("Empty bookings data from Madlen API")
                    return self._create_error_event("bookings", "api", "No data received from Madlen API", dept_id)
                
                return {
                    "type": "bookings",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": dept_id,
                    "data": {
                        **bookings_data,
                        "source": "madlen_api"
                    }
                }
        except Exception as api_error:
            logger.error(f"Ошибка получения данных о бронированиях: {api_error}")
            return self._create_error_event("bookings", "api", str(api_error), dept_id)
    
    async def _get_occupancy_event(self, department_id: Optional[str] = None) -> Dict:
        """
        Получает данные о загрузке зала
        """
        if self._demo_mode:
            return self._generate_demo_occupancy_data(department_id)
        
        dept_id = department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50"
        
        # Пытаемся получить данные из базы данных
        if self._db_provider:
            try:
                return await self._db_provider.get_real_occupancy_data(dept_id)
            except Exception as db_error:
                logger.warning(f"Database error for occupancy data: {db_error}")
                return self._create_error_event("occupancy", "database", str(db_error), dept_id)
        
        # Fallback на внешние API (IoT датчики, POS система, камеры)
        try:
            async with HTTPClient() as client:
                occupancy_data = await client.get_madlen("occupancy/current", {
                    "department_id": dept_id
                })
                
                if not occupancy_data:
                    logger.warning("Empty occupancy data from Madlen API")
                    return self._create_error_event("occupancy", "api", "No data received from Madlen API", dept_id)
                
                return {
                    "type": "occupancy",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": dept_id,
                    "data": {
                        **occupancy_data,
                        "source": "madlen_api"
                    }
                }
        except Exception as api_error:
            logger.error(f"Ошибка получения данных о загрузке: {api_error}")
            return self._create_error_event("occupancy", "api", str(api_error), dept_id)
    
    async def _get_shifts_event(self, department_id: Optional[str] = None) -> Dict:
        """
        Получает данные о сменах сотрудников
        """
        if self._demo_mode:
            return self._generate_demo_shifts_data(department_id)
        
        dept_id = department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50"
        
        # Пытаемся получить данные из базы данных (HR система)
        if self._db_provider:
            try:
                # Здесь можно добавить метод get_real_shifts_data в DatabaseSSEProvider
                # Пока используем внешний API
                pass
            except Exception as db_error:
                logger.warning(f"Database error for shifts data: {db_error}")
                return self._create_error_event("shifts", "database", str(db_error), dept_id)
        
        # Запрос к HR системе через API
        try:
            async with HTTPClient() as client:
                shifts_data = await client.get_madlen("shifts/current", {
                    "department_id": dept_id
                })
                
                if not shifts_data:
                    logger.warning("Empty shifts data from Madlen API")
                    return self._create_error_event("shifts", "api", "No data received from Madlen API", dept_id)
                
                return {
                    "type": "shifts",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": dept_id,
                    "data": {
                        **shifts_data,
                        "source": "madlen_api"
                    }
                }
        except Exception as api_error:
            logger.error(f"Ошибка получения данных о сменах: {api_error}")
            return self._create_error_event("shifts", "api", str(api_error), dept_id)
    
    def _generate_demo_sales_data(self, department_id: Optional[str] = None) -> Dict:
        """
        Генерирует демо данные о продажах
        """
        import random
        
        current_hour = datetime.now().hour
        base_sales = 50000 + (current_hour * 5000)  # Больше продаж в обеденное время
        
        return {
            "type": "sales",
            "timestamp": datetime.now().isoformat(),
            "department_id": department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "data": {
                "total_sales": base_sales + random.randint(-10000, 15000),
                "total_transactions": random.randint(50, 200),
                "average_check": random.randint(800, 1500),
                "period": "last_hour",
                "currency": "RUB",
                "top_dishes": [
                    {"name": "Борщ", "count": random.randint(10, 30)},
                    {"name": "Салат Цезарь", "count": random.randint(5, 25)},
                    {"name": "Стейк", "count": random.randint(3, 15)}
                ]
            }
        }
    
    def _generate_demo_bookings_data(self, department_id: Optional[str] = None) -> Dict:
        """
        Генерирует демо данные о бронированиях
        """
        import random
        
        return {
            "type": "bookings",
            "timestamp": datetime.now().isoformat(),
            "department_id": department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "data": {
                "total_bookings_today": random.randint(20, 80),
                "confirmed_bookings": random.randint(15, 60),
                "pending_bookings": random.randint(2, 10),
                "cancelled_bookings": random.randint(0, 5),
                "next_booking_time": (datetime.now() + timedelta(minutes=random.randint(15, 120))).isoformat(),
                "peak_hours": ["12:00-14:00", "19:00-21:00"],
                "average_party_size": round(random.uniform(2.0, 4.5), 1)
            }
        }
    
    def _generate_demo_occupancy_data(self, department_id: Optional[str] = None) -> Dict:
        """
        Генерирует демо данные о загрузке зала
        """
        import random
        
        current_hour = datetime.now().hour
        
        # Симуляция загрузки по времени дня
        if 11 <= current_hour <= 14:  # Обеденное время
            base_occupancy = random.randint(70, 95)
        elif 18 <= current_hour <= 21:  # Ужин
            base_occupancy = random.randint(60, 90)
        else:  # Остальное время
            base_occupancy = random.randint(20, 60)
        
        return {
            "type": "occupancy",
            "timestamp": datetime.now().isoformat(),
            "department_id": department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "data": {
                "current_occupancy_percent": base_occupancy,
                "total_tables": 45,
                "occupied_tables": int(45 * base_occupancy / 100),
                "available_tables": 45 - int(45 * base_occupancy / 100),
                "waiting_queue": random.randint(0, 8),
                "average_visit_duration": random.randint(45, 120),
                "hall_zones": {
                    "main_hall": {"occupancy": random.randint(50, 100), "tables": 30},
                    "vip_zone": {"occupancy": random.randint(30, 80), "tables": 8},
                    "terrace": {"occupancy": random.randint(20, 70), "tables": 7}
                }
            }
        }
    
    def _generate_demo_shifts_data(self, department_id: Optional[str] = None) -> Dict:
        """
        Генерирует демо данные о сменах сотрудников
        """
        import random
        
        return {
            "type": "shifts",
            "timestamp": datetime.now().isoformat(),
            "department_id": department_id or "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "data": {
                "current_shift": {
                    "start_time": "09:00",
                    "end_time": "21:00",
                    "type": "day_shift"
                },
                "total_staff_today": random.randint(12, 18),
                "currently_working": random.randint(8, 15),
                "on_break": random.randint(1, 3),
                "departments": {
                    "kitchen": {"working": random.randint(3, 6), "planned": 6},
                    "service": {"working": random.randint(4, 8), "planned": 8},
                    "bar": {"working": random.randint(1, 2), "planned": 2},
                    "management": {"working": random.randint(1, 2), "planned": 2}
                },
                "next_shift_change": (datetime.now() + timedelta(hours=random.randint(1, 8))).isoformat(),
                "overtime_hours": random.randint(0, 4)
            }
        }
    
    def disconnect_client(self, client_id: str):
        """
        Отключает клиента от SSE потока
        """
        if client_id in self.active_connections:
            self.active_connections[client_id] = False
            logger.info(f"Клиент {client_id} отключен от SSE потока")
    
    def get_active_connections_count(self) -> int:
        """
        Возвращает количество активных соединений
        """
        return sum(1 for active in self.active_connections.values() if active)


# Создаем глобальный экземпляр сервиса
sse_service = SSEService()
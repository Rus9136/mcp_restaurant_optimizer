"""
Примеры интеграции SSE с базой данных
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

# Примеры с разными ORM/драйверами
try:
    import asyncpg  # PostgreSQL
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False


class DatabaseSSEProvider:
    """
    Провайдер данных для SSE из базы данных
    """
    
    def __init__(self, db_url: str, db_type: str = "postgresql"):
        self.db_url = db_url
        self.db_type = db_type
        self._connection = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Настройка соединения с БД"""
        if self.db_type == "postgresql" and ASYNCPG_AVAILABLE:
            self._connection = None  # Будет создано при первом использовании
        elif self.db_type == "sqlalchemy" and SQLALCHEMY_AVAILABLE:
            self._engine = create_async_engine(self.db_url)
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )
        elif self.db_type == "mongodb" and MOTOR_AVAILABLE:
            self._client = AsyncIOMotorClient(self.db_url)
            self._db = self._client.mcp_restaurant
    
    async def get_real_sales_data(self, department_id: str) -> Dict:
        """
        Получение реальных данных о продажах из БД
        """
        if self.db_type == "postgresql":
            return await self._get_postgresql_sales(department_id)
        elif self.db_type == "sqlalchemy":
            return await self._get_sqlalchemy_sales(department_id)
        elif self.db_type == "mongodb":
            return await self._get_mongodb_sales(department_id)
        else:
            raise NotImplementedError(f"Database type {self.db_type} not supported")
    
    async def _get_postgresql_sales(self, department_id: str) -> Dict:
        """
        Пример получения данных через asyncpg (PostgreSQL)
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg not installed")
        
        try:
            if not self._connection:
                self._connection = await asyncpg.connect(self.db_url)
            
            # Получаем данные за последний час
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            query = '''
                SELECT 
                    SUM(amount) as total_sales,
                    COUNT(*) as total_transactions,
                    AVG(amount) as average_check
                FROM sales 
                WHERE department_id = $1 
                AND created_at >= $2 
                AND created_at <= $3
            '''
            
            result = await self._connection.fetchrow(
                query, department_id, hour_ago, now
            )
            
            # Получаем топ блюд
            top_dishes_query = '''
                SELECT 
                    dish_name,
                    COUNT(*) as count
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.department_id = $1
                AND o.created_at >= $2
                GROUP BY dish_name
                ORDER BY count DESC
                LIMIT 5
            '''
            
            top_dishes = await self._connection.fetch(
                top_dishes_query, department_id, hour_ago
            )
            
            return {
                "type": "sales",
                "timestamp": datetime.now().isoformat(),
                "department_id": department_id,
                "data": {
                    "total_sales": float(result["total_sales"] or 0),
                    "total_transactions": int(result["total_transactions"] or 0),
                    "average_check": float(result["average_check"] or 0),
                    "period": "last_hour",
                    "currency": "RUB",
                    "top_dishes": [
                        {"name": row["dish_name"], "count": row["count"]}
                        for row in top_dishes
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения данных из PostgreSQL: {e}")
            raise
    
    async def _get_sqlalchemy_sales(self, department_id: str) -> Dict:
        """
        Пример получения данных через SQLAlchemy
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("sqlalchemy not installed")
        
        try:
            async with self._session_factory() as session:
                # Получаем данные за последний час
                now = datetime.now()
                hour_ago = now - timedelta(hours=1)
                
                # Основная статистика продаж
                sales_query = text('''
                    SELECT 
                        SUM(amount) as total_sales,
                        COUNT(*) as total_transactions,
                        AVG(amount) as average_check
                    FROM sales 
                    WHERE department_id = :department_id 
                    AND created_at >= :hour_ago 
                    AND created_at <= :now
                ''')
                
                result = await session.execute(
                    sales_query, 
                    {
                        "department_id": department_id,
                        "hour_ago": hour_ago,
                        "now": now
                    }
                )
                sales_data = result.fetchone()
                
                # Топ блюд
                top_dishes_query = text('''
                    SELECT 
                        dish_name,
                        COUNT(*) as count
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.department_id = :department_id
                    AND o.created_at >= :hour_ago
                    GROUP BY dish_name
                    ORDER BY count DESC
                    LIMIT 5
                ''')
                
                dishes_result = await session.execute(
                    top_dishes_query,
                    {"department_id": department_id, "hour_ago": hour_ago}
                )
                top_dishes = dishes_result.fetchall()
                
                return {
                    "type": "sales",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": department_id,
                    "data": {
                        "total_sales": float(sales_data.total_sales or 0),
                        "total_transactions": int(sales_data.total_transactions or 0),
                        "average_check": float(sales_data.average_check or 0),
                        "period": "last_hour",
                        "currency": "RUB",
                        "top_dishes": [
                            {"name": row.dish_name, "count": row.count}
                            for row in top_dishes
                        ]
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения данных через SQLAlchemy: {e}")
            raise
    
    async def _get_mongodb_sales(self, department_id: str) -> Dict:
        """
        Пример получения данных через MongoDB
        """
        if not MOTOR_AVAILABLE:
            raise ImportError("motor not installed")
        
        try:
            # Получаем данные за последний час
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            sales_collection = self._db.sales
            
            # Агрегация данных о продажах
            pipeline = [
                {
                    "$match": {
                        "department_id": department_id,
                        "created_at": {
                            "$gte": hour_ago,
                            "$lte": now
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_sales": {"$sum": "$amount"},
                        "total_transactions": {"$sum": 1},
                        "average_check": {"$avg": "$amount"}
                    }
                }
            ]
            
            sales_data = await sales_collection.aggregate(pipeline).to_list(1)
            
            # Топ блюд
            top_dishes_pipeline = [
                {
                    "$match": {
                        "department_id": department_id,
                        "created_at": {"$gte": hour_ago}
                    }
                },
                {"$unwind": "$items"},
                {
                    "$group": {
                        "_id": "$items.dish_name",
                        "count": {"$sum": "$items.quantity"}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            top_dishes = await sales_collection.aggregate(top_dishes_pipeline).to_list(5)
            
            sales_result = sales_data[0] if sales_data else {
                "total_sales": 0,
                "total_transactions": 0,
                "average_check": 0
            }
            
            return {
                "type": "sales",
                "timestamp": datetime.now().isoformat(),
                "department_id": department_id,
                "data": {
                    "total_sales": float(sales_result.get("total_sales", 0)),
                    "total_transactions": int(sales_result.get("total_transactions", 0)),
                    "average_check": float(sales_result.get("average_check", 0)),
                    "period": "last_hour",
                    "currency": "RUB",
                    "top_dishes": [
                        {"name": dish["_id"], "count": dish["count"]}
                        for dish in top_dishes
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения данных из MongoDB: {e}")
            raise
    
    async def get_real_bookings_data(self, department_id: str) -> Dict:
        """
        Получение реальных данных о бронированиях
        """
        try:
            if self.db_type == "postgresql":
                if not self._connection:
                    self._connection = await asyncpg.connect(self.db_url)
                
                query = '''
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(party_size) as avg_party_size
                    FROM bookings 
                    WHERE department_id = $1 
                    AND DATE(booking_date) = CURRENT_DATE
                    GROUP BY status
                '''
                
                results = await self._connection.fetch(query, department_id)
                
                # Следующее бронирование
                next_booking_query = '''
                    SELECT booking_time
                    FROM bookings
                    WHERE department_id = $1
                    AND booking_date >= CURRENT_DATE
                    AND status = 'confirmed'
                    ORDER BY booking_date, booking_time
                    LIMIT 1
                '''
                
                next_booking = await self._connection.fetchrow(next_booking_query, department_id)
                
                # Преобразуем результаты
                booking_stats = {result["status"]: result["count"] for result in results}
                avg_party_size = results[0]["avg_party_size"] if results else 2.0
                
                return {
                    "type": "bookings",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": department_id,
                    "data": {
                        "total_bookings_today": sum(booking_stats.values()),
                        "confirmed_bookings": booking_stats.get("confirmed", 0),
                        "pending_bookings": booking_stats.get("pending", 0),
                        "cancelled_bookings": booking_stats.get("cancelled", 0),
                        "next_booking_time": next_booking["booking_time"].isoformat() if next_booking else None,
                        "average_party_size": float(avg_party_size) if avg_party_size else 2.0
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения данных о бронированиях: {e}")
            raise
    
    async def get_real_occupancy_data(self, department_id: str) -> Dict:
        """
        Получение реальных данных о загрузке зала
        """
        try:
            if self.db_type == "postgresql":
                if not self._connection:
                    self._connection = await asyncpg.connect(self.db_url)
                
                # Получаем информацию о столах
                query = '''
                    SELECT 
                        COUNT(*) as total_tables,
                        SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied_tables,
                        SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_tables
                    FROM tables 
                    WHERE department_id = $1
                '''
                
                result = await self._connection.fetchrow(query, department_id)
                
                # Очередь ожидания
                queue_query = '''
                    SELECT COUNT(*) as waiting_count
                    FROM waiting_queue
                    WHERE department_id = $1
                    AND status = 'waiting'
                '''
                
                queue_result = await self._connection.fetchrow(queue_query, department_id)
                
                total_tables = result["total_tables"]
                occupied_tables = result["occupied_tables"]
                occupancy_percent = (occupied_tables / total_tables * 100) if total_tables > 0 else 0
                
                return {
                    "type": "occupancy",
                    "timestamp": datetime.now().isoformat(),
                    "department_id": department_id,
                    "data": {
                        "current_occupancy_percent": round(occupancy_percent, 1),
                        "total_tables": total_tables,
                        "occupied_tables": occupied_tables,
                        "available_tables": result["available_tables"],
                        "waiting_queue": queue_result["waiting_count"]
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения данных о загрузке: {e}")
            raise
    
    async def close(self):
        """Закрытие соединения с БД"""
        if self.db_type == "postgresql" and self._connection:
            await self._connection.close()
        elif self.db_type == "sqlalchemy" and hasattr(self, '_engine'):
            await self._engine.dispose()
        elif self.db_type == "mongodb" and hasattr(self, '_client'):
            self._client.close()


# Пример использования с кешированием
class CachedDatabaseSSEProvider(DatabaseSSEProvider):
    """
    Провайдер данных с кешированием для уменьшения нагрузки на БД
    """
    
    def __init__(self, db_url: str, db_type: str = "postgresql", cache_ttl: int = 30):
        super().__init__(db_url, db_type)
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    async def get_real_sales_data(self, department_id: str) -> Dict:
        """
        Получение данных с кешированием
        """
        cache_key = f"sales_{department_id}"
        now = datetime.now()
        
        # Проверяем кеш
        if cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if (now - cache_time).total_seconds() < self.cache_ttl:
                # Обновляем timestamp для актуальности
                cached_data["timestamp"] = now.isoformat()
                return cached_data
        
        # Получаем свежие данные
        data = await super().get_real_sales_data(department_id)
        
        # Кешируем
        self._cache[cache_key] = (data, now)
        
        return data
    
    def clear_cache(self):
        """Очистка кеша"""
        self._cache.clear()
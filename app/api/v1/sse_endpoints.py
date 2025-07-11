"""
SSE Endpoints для потоковой передачи данных
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.services.sse_service import sse_service
from app.core.config import get_settings
from app.core.exceptions import ValidationError

router = APIRouter(prefix="/api/v1/mcp", tags=["SSE"])
settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_client_id(request: Request) -> str:
    """
    Генерирует уникальный ID клиента на основе IP и заголовков
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Создаем уникальный ID клиента
    client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{client_ip}_{user_agent}"))
    return client_id


async def validate_sse_access(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    department_id: Optional[str] = Query(None, description="ID подразделения для фильтрации данных")
) -> dict:
    """
    Валидация доступа к SSE endpoint
    
    В продакшене здесь можно добавить:
    - Проверку JWT токена
    - Проверку API ключа
    - Проверку rate limiting
    - Проверку доступа к конкретному подразделению
    """
    client_ip = request.client.host
    
    # Базовая проверка IP (можно настроить whitelist)
    if settings.environment == "production":
        # В продакшене можно добавить проверку токена
        if not credentials and not _is_internal_request(request):
            raise HTTPException(
                status_code=401,
                detail="Authentication required for SSE access"
            )
        
        # Проверка токена (если есть)
        if credentials:
            # Здесь должна быть проверка JWT или API ключа
            # await validate_token(credentials.credentials)
            pass
    
    # Валидация department_id
    if department_id:
        try:
            uuid.UUID(department_id)
        except ValueError:
            raise ValidationError("Invalid department_id format")
    
    logger.info(f"SSE доступ разрешен для IP: {client_ip}, department_id: {department_id}")
    
    return {
        "client_ip": client_ip,
        "department_id": department_id,
        "authenticated": credentials is not None
    }


def _is_internal_request(request: Request) -> bool:
    """
    Проверяет, является ли запрос внутренним
    """
    client_ip = request.client.host
    internal_ips = ["127.0.0.1", "::1", "localhost"]
    
    # Проверка внутренних IP
    if client_ip in internal_ips:
        return True
    
    # Проверка приватных сетей
    if client_ip.startswith(("192.168.", "10.", "172.")):
        return True
    
    return False


@router.get("/sse")
async def stream_restaurant_data(
    request: Request,
    interval: int = Query(5, ge=1, le=60, description="Интервал между событиями в секундах"),
    client_id: str = Depends(get_current_client_id),
    access_info: dict = Depends(validate_sse_access)
):
    """
    Server-Sent Events endpoint для потоковой передачи данных ресторанной аналитики
    
    Возвращает события в реальном времени:
    - **sales**: Данные о продажах
    - **bookings**: Информация о бронированиях  
    - **occupancy**: Загрузка зала
    - **shifts**: Данные о сменах сотрудников
    
    **Параметры:**
    - `interval`: Интервал между событиями (1-60 секунд)
    - `department_id`: ID подразделения для фильтрации (опционально)
    
    **Авторизация:**
    - Внутренние запросы: без авторизации
    - Внешние запросы: требуется Bearer token
    
    **Формат событий:**
    ```
    data: {"type": "sales", "timestamp": "2025-07-11T10:00:00", "data": {...}}
    
    data: {"type": "bookings", "timestamp": "2025-07-11T10:00:05", "data": {...}}
    ```
    """
    logger.info(f"Новое SSE соединение: client_id={client_id}, IP={access_info['client_ip']}")
    
    # Создаем SSE поток
    async def event_stream():
        try:
            async for event in sse_service.generate_sse_stream(
                client_id=client_id,
                department_id=access_info["department_id"],
                interval=interval
            ):
                yield event
        except Exception as e:
            logger.error(f"Ошибка в SSE потоке для клиента {client_id}: {e}")
            # Отправляем событие об ошибке и закрываем соединение
            error_event = f"data: {{\"type\": \"error\", \"message\": \"Stream error: {str(e)}\"}}\n\n"
            yield error_event
    
    # Возвращаем StreamingResponse с правильными заголовками
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Cache-Control",
            "Access-Control-Expose-Headers": "Content-Type",
            "X-Accel-Buffering": "no",  # Отключаем буферизацию nginx
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.options("/sse")
async def sse_options():
    """
    CORS preflight для SSE endpoint
    """
    return {
        "methods": ["GET", "OPTIONS"],
        "headers": ["Authorization", "Content-Type", "Cache-Control"]
    }


@router.get("/sse/status")
async def sse_status():
    """
    Статус SSE сервиса
    """
    return {
        "status": "active",
        "active_connections": sse_service.get_active_connections_count(),
        "service": "MCP Restaurant SSE",
        "version": "1.0.0",
        "endpoints": {
            "stream": "/api/v1/mcp/sse",
            "status": "/api/v1/mcp/sse/status"
        }
    }


@router.post("/sse/disconnect/{client_id}")
async def disconnect_sse_client(
    client_id: str,
    access_info: dict = Depends(validate_sse_access)
):
    """
    Принудительное отключение SSE клиента
    """
    try:
        uuid.UUID(client_id)
    except ValueError:
        raise ValidationError("Invalid client_id format")
    
    sse_service.disconnect_client(client_id)
    
    return {
        "message": f"Client {client_id} disconnected",
        "active_connections": sse_service.get_active_connections_count()
    }
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.core.config import get_settings
from app.core.exceptions import MCPError
from app.api.v1.endpoints import router as v1_router
from app.api.v1.sse_endpoints import router as sse_router

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if get_settings().debug else "INFO"
)

# Контекстный менеджер для жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MCP Restaurant Optimizer API")
    yield
    logger.info("Shutting down MCP Restaurant Optimizer API")

# Создание приложения
app = FastAPI(
    title="MCP Restaurant Optimizer",
    description="FastAPI сервер для оптимизации графиков ресторана через MCP интерфейс",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(v1_router)
app.include_router(sse_router)

# Глобальный обработчик ошибок
@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

# Общий обработчик непредвиденных ошибок
@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "Внутренняя ошибка сервера",
                "details": {
                    "error": str(exc) if get_settings().debug else "Internal server error"
                }
            }
        }
    )

# Корневой эндпоинт
@app.get("/")
async def root():
    return {
        "service": "MCP Restaurant Optimizer",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Healthcheck
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "mcp-restaurant-optimizer"
    }
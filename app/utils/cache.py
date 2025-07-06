from functools import wraps
from typing import Any, Callable, Optional
import hashlib
import json
from datetime import datetime, timedelta
from cachetools import TTLCache
from loguru import logger


class CacheManager:
    def __init__(self, ttl: int = 1800, maxsize: int = 100):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def cached(self, ttl: Optional[int] = None):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                cache_key = self._generate_key(func.__name__, *args, **kwargs)
                
                # Проверяем кэш
                if cache_key in self.cache:
                    logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                    return self.cache[cache_key]
                
                # Вызываем функцию
                logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
                result = await func(*args, **kwargs)
                
                # Сохраняем в кэш
                self.cache[cache_key] = result
                logger.debug(f"Cached result for {func.__name__} with key {cache_key}")
                
                return result
            
            return wrapper
        return decorator
    
    def invalidate(self, func_name: str, *args, **kwargs):
        cache_key = self._generate_key(func_name, *args, **kwargs)
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"Invalidated cache for {func_name} with key {cache_key}")
    
    def clear(self):
        self.cache.clear()
        logger.debug("Cache cleared")


# Глобальный экземпляр для использования
cache_manager = CacheManager()
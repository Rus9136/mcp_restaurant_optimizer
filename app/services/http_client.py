import httpx
from typing import Optional, Dict, Any
from loguru import logger
from app.core.config import get_settings
from app.core.exceptions import ExternalAPIError


class HTTPClient:
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.api_timeout),
            headers={
                "User-Agent": "MCP-Restaurant-Optimizer/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def get_aqniet(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.settings.aqniet_api_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.settings.aqniet_api_token}"
        }
        
        try:
            logger.debug(f"GET {url} with params: {params}")
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout при обращении к {url}")
            raise ExternalAPIError(
                message=f"Таймаут при обращении к aqniet.site",
                endpoint=url,
                timeout=True
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка {e.response.status_code} при обращении к {url}")
            raise ExternalAPIError(
                message=f"Ошибка при обращении к aqniet.site",
                endpoint=url,
                status_code=e.response.status_code,
                details={"response_text": e.response.text[:200]}
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обращении к {url}: {str(e)}")
            raise ExternalAPIError(
                message=f"Неожиданная ошибка при обращении к aqniet.site",
                endpoint=url,
                details={"error": str(e)}
            )
    
    async def get_madlen(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.settings.madlen_api_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"GET {url} with params: {params}")
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout при обращении к {url}")
            raise ExternalAPIError(
                message=f"Таймаут при обращении к madlen.space",
                endpoint=url,
                timeout=True
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка {e.response.status_code} при обращении к {url}")
            raise ExternalAPIError(
                message=f"Ошибка при обращении к madlen.space",
                endpoint=url,
                status_code=e.response.status_code,
                details={"response_text": e.response.text[:200]}
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обращении к {url}: {str(e)}")
            raise ExternalAPIError(
                message=f"Неожиданная ошибка при обращении к madlen.space",
                endpoint=url,
                details={"error": str(e)}
            )
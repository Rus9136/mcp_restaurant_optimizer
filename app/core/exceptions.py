from typing import Optional, Dict, Any
from fastapi import HTTPException


class MCPError(HTTPException):
    def __init__(
        self, 
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        error_body = {
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {}
            }
        }
        super().__init__(status_code=status_code, detail=error_body)


class ExternalAPIError(MCPError):
    def __init__(
        self,
        message: str,
        endpoint: str,
        status_code: Optional[int] = None,
        timeout: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "endpoint": endpoint,
            "timeout": timeout,
            **(details or {})
        }
        if status_code:
            error_details["status_code"] = status_code
            
        super().__init__(
            error_type="external_api_error",
            message=message,
            details=error_details,
            status_code=502  # Bad Gateway
        )


class ValidationError(MCPError):
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
            
        super().__init__(
            error_type="validation_error",
            message=message,
            details=details,
            status_code=400  # Bad Request
        )
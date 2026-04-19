"""Request logging middleware."""
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.request_id import get_or_create_request_id

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        start_time = time.time()
        request_id = get_or_create_request_id(request)

        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
        )

        return response

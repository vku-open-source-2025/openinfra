"""Middleware that ensures every request has a request id."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.request_id import get_or_create_request_id, set_request_id_header


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request id to request state and response headers."""

    async def dispatch(self, request: Request, call_next):
        request_id = get_or_create_request_id(request)
        response = await call_next(request)
        set_request_id_header(response, request_id)
        return response

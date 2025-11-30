"""Error handling middleware."""
import logging
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        logger.warning(f"Validation error: {e.errors()}", extra={"request_id": request_id})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "validation_error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Invalid request parameters",
                "errors": e.errors(),
                "request_id": request_id
            }
        )
    except AppException as e:
        logger.error(
            f"Application error: {e.detail}",
            extra={"request_id": request_id, "error_code": e.error_code}
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "type": "application_error",
                "title": e.__class__.__name__,
                "status": e.status_code,
                "detail": e.detail,
                "error_code": e.error_code,
                "request_id": request_id
            },
            headers=e.headers
        )
    except StarletteHTTPException as e:
        logger.error(f"HTTP error: {e.detail}", extra={"request_id": request_id})
        return JSONResponse(
            status_code=e.status_code,
            content={
                "type": "http_error",
                "title": "HTTP Error",
                "status": e.status_code,
                "detail": e.detail,
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.exception(f"Unhandled error: {str(e)}", extra={"request_id": request_id})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "internal_error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred. Please contact support.",
                "request_id": request_id
            }
        )

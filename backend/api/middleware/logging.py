"""Request/response logging middleware.

Logs method, path, status code, duration, and request ID
for every HTTP request.
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("sownia.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log request details and response status with timing.

        Adds a unique X-Request-ID header to each request/response.
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"(client: {request.client.host if request.client else 'unknown'})"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] ← {response.status_code} "
                f"({duration_ms:.1f}ms)"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] ✗ Error after {duration_ms:.1f}ms: {e}"
            )
            raise


def setup_logging(app: FastAPI) -> None:
    """Add logging middleware to the FastAPI application.

    Also configures the root logger format for the application.

    Args:
        app: FastAPI application instance.
    """
    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add middleware
    app.add_middleware(LoggingMiddleware)

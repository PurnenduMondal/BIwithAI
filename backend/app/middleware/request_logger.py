from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests with timing information
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        
        # Log request
        logger.info(f"Request started: {method} {url} from {client_ip}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log response
            logger.info(
                f"Request completed: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration_ms}ms"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(duration_ms)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log error
            logger.error(
                f"Request failed: {method} {url} - "
                f"Error: {str(e)} - "
                f"Duration: {duration_ms}ms",
                exc_info=True
            )
            raise

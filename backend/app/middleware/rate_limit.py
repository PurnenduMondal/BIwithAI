from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Tuple
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    Tracks requests per IP address with a sliding window.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Store: {ip: [(timestamp, count_in_minute, count_in_hour)]}
        self.request_history: Dict[str, list] = {}
        self.cleanup_interval = 3600  # Clean up every hour
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/api/docs", "/api/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(client_ip)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record request
        self._record_request(client_ip)
        
        # Periodic cleanup
        self._cleanup_old_records()
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limits
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        
        if client_ip not in self.request_history:
            return True, 0
        
        requests = self.request_history[client_ip]
        
        # Count requests in last minute
        minute_ago = current_time - 60
        requests_last_minute = sum(1 for ts in requests if ts >= minute_ago)
        
        if requests_last_minute >= self.requests_per_minute:
            # Calculate retry after (seconds until oldest request expires)
            oldest_in_window = min([ts for ts in requests if ts >= minute_ago])
            retry_after = int(60 - (current_time - oldest_in_window)) + 1
            return False, retry_after
        
        # Count requests in last hour
        hour_ago = current_time - 3600
        requests_last_hour = sum(1 for ts in requests if ts >= hour_ago)
        
        if requests_last_hour >= self.requests_per_hour:
            # Calculate retry after (seconds until oldest request expires)
            oldest_in_window = min([ts for ts in requests if ts >= hour_ago])
            retry_after = int(3600 - (current_time - oldest_in_window)) + 1
            return False, retry_after
        
        return True, 0
    
    def _record_request(self, client_ip: str):
        """Record a request for rate limiting"""
        current_time = time.time()
        
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        self.request_history[client_ip].append(current_time)
        
        # Keep only last hour of requests
        hour_ago = current_time - 3600
        self.request_history[client_ip] = [
            ts for ts in self.request_history[client_ip] if ts >= hour_ago
        ]
    
    def _cleanup_old_records(self):
        """Periodically clean up old rate limit records"""
        current_time = time.time()
        
        # Only cleanup once per interval
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        logger.info("Cleaning up rate limit records...")
        
        hour_ago = current_time - 3600
        
        # Remove old requests and empty IP records
        ips_to_remove = []
        for ip, requests in self.request_history.items():
            # Filter out old requests
            self.request_history[ip] = [ts for ts in requests if ts >= hour_ago]
            
            # Mark empty records for removal
            if not self.request_history[ip]:
                ips_to_remove.append(ip)
        
        # Remove empty records
        for ip in ips_to_remove:
            del self.request_history[ip]
        
        self.last_cleanup = current_time
        logger.info(f"Cleanup complete. Active IPs: {len(self.request_history)}")

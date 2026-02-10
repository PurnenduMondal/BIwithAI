from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class TenantResolverMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and store tenant/organization context from request.
    
    Extracts subdomain from:
    1. X-Organization-Subdomain header (sent by frontend)
    2. Host header (for subdomain-based routing)
    
    Stores the subdomain in request.state for use by dependency injection.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Try to get subdomain from custom header first (for API calls from frontend)
        subdomain = request.headers.get("X-Organization-Subdomain")
        
        # Fallback to extracting from Host header if not provided
        if not subdomain:
            host = request.headers.get("host", "")
            # Extract subdomain from host (e.g., acme.localhost:8000 -> acme)
            if host and '.' in host:
                parts = host.split('.')
                # Check if it's a subdomain (not just localhost or an IP)
                if len(parts) >= 2 and parts[0] not in ['localhost', 'www', '127']:
                    subdomain = parts[0].split(':')[0]  # Remove port if present
        
        # Store subdomain in request state for access by dependencies
        request.state.subdomain = subdomain
        
        response = await call_next(request)
        return response

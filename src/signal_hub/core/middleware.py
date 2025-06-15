"""Middleware for Signal Hub server."""

import time
import uuid
import asyncio
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager

from ..utils.logging import get_logger, LogContext
from ..utils.metrics import (
    request_counter,
    request_duration,
    active_connections,
    error_counter,
)

logger = get_logger(__name__)


class RequestContext:
    """Context for a single request."""
    
    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.metadata: Dict[str, Any] = {}
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_time * 1000


class LoggingMiddleware:
    """Middleware for request logging."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Dict[str, Any], handler: Callable) -> Any:
        """Process request with logging."""
        # Create request context
        request_id = request.get("id") or str(uuid.uuid4())
        ctx = RequestContext(request_id)
        
        # Extract method name
        method = request.get("method", "unknown")
        
        # Log request start
        with LogContext(self.logger, request_id=request_id, method=method):
            self.logger.info(
                f"Request started: {method}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "params": request.get("params", {}),
                }
            )
            
            try:
                # Process request
                response = await handler(request)
                
                # Log success
                self.logger.info(
                    f"Request completed: {method}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "duration_ms": ctx.elapsed_ms,
                        "status": "success",
                    }
                )
                
                return response
                
            except Exception as e:
                # Log error
                self.logger.error(
                    f"Request failed: {method}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "duration_ms": ctx.elapsed_ms,
                        "status": "error",
                        "error": str(e),
                    },
                    exc_info=True,
                )
                raise


class MetricsMiddleware:
    """Middleware for metrics collection."""
    
    async def __call__(self, request: Dict[str, Any], handler: Callable) -> Any:
        """Process request with metrics collection."""
        # Extract method name
        method = request.get("method", "unknown")
        
        # Track active connections
        active_connections.inc()
        
        try:
            # Time the request
            with request_duration.time(method=method, status="success"):
                response = await handler(request)
            
            # Track success
            request_counter.inc(method=method, status="success")
            
            return response
            
        except Exception as e:
            # Track error
            request_counter.inc(method=method, status="error")
            error_counter.inc(
                type=type(e).__name__,
                operation=method
            )
            raise
            
        finally:
            # Decrement active connections
            active_connections.dec()


class RateLimitMiddleware:
    """Middleware for rate limiting."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, list] = {}
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Dict[str, Any], handler: Callable) -> Any:
        """Process request with rate limiting."""
        # For now, use a simple in-memory rate limiter
        # In production, use Redis
        
        # Get client identifier (simplified for now)
        client_id = "default"  # TODO: Extract from request context
        
        # Clean old requests
        current_time = time.time()
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if current_time - t < 60
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.max_requests:
            self.logger.warning(
                f"Rate limit exceeded for client {client_id}",
                extra={"client_id": client_id, "limit": self.max_requests}
            )
            raise Exception("Rate limit exceeded")
        
        # Track request
        self.requests[client_id].append(current_time)
        
        # Process request
        return await handler(request)


class CacheMiddleware:
    """Middleware for caching responses."""
    
    def __init__(self, cache_ttl: int = 300):
        self.cache: Dict[str, tuple] = {}
        self.cache_ttl = cache_ttl
        self.logger = get_logger(__name__)
    
    def _get_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key from request."""
        method = request.get("method", "")
        params = request.get("params", {})
        
        # Simple cache key generation
        import json
        params_str = json.dumps(params, sort_keys=True)
        return f"{method}:{params_str}"
    
    async def __call__(self, request: Dict[str, Any], handler: Callable) -> Any:
        """Process request with caching."""
        # Only cache certain methods
        method = request.get("method", "")
        if not method.startswith("search_"):
            return await handler(request)
        
        # Check cache
        cache_key = self._get_cache_key(request)
        current_time = time.time()
        
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                self.logger.debug(
                    f"Cache hit for {method}",
                    extra={"method": method, "cache_key": cache_key}
                )
                # Track cache hit
                from ..utils.metrics import cache_hits
                cache_hits.inc(cache_type="response")
                return response
        
        # Cache miss
        from ..utils.metrics import cache_misses
        cache_misses.inc(cache_type="response")
        
        # Process request
        response = await handler(request)
        
        # Store in cache
        self.cache[cache_key] = (response, current_time)
        
        # Clean old cache entries periodically
        if len(self.cache) > 1000:
            # Remove expired entries
            self.cache = {
                k: v for k, v in self.cache.items()
                if current_time - v[1] < self.cache_ttl
            }
        
        return response


class MiddlewareStack:
    """Stack of middleware to process requests."""
    
    def __init__(self):
        self.middleware: list = []
    
    def add(self, middleware: Any) -> None:
        """Add middleware to the stack."""
        self.middleware.append(middleware)
    
    async def __call__(self, request: Dict[str, Any], handler: Callable) -> Any:
        """Process request through middleware stack."""
        # Build the handler chain
        async def process(req: Dict[str, Any]) -> Any:
            return await handler(req)
        
        # Wrap handler with middleware in reverse order
        wrapped_handler = process
        for mw in reversed(self.middleware):
            # Create a new scope for each middleware
            current_mw = mw
            current_handler = wrapped_handler
            
            async def new_handler(req: Dict[str, Any]) -> Any:
                return await current_mw(req, current_handler)
            
            wrapped_handler = new_handler
        
        # Execute the wrapped handler
        return await wrapped_handler(request)


def create_middleware_stack(
    enable_logging: bool = True,
    enable_metrics: bool = True,
    enable_rate_limiting: bool = True,
    enable_caching: bool = True,
    rate_limit: int = 60,
    cache_ttl: int = 300,
) -> MiddlewareStack:
    """Create a configured middleware stack."""
    stack = MiddlewareStack()
    
    if enable_logging:
        stack.add(LoggingMiddleware())
    
    if enable_metrics:
        stack.add(MetricsMiddleware())
    
    if enable_rate_limiting:
        stack.add(RateLimitMiddleware(rate_limit))
    
    if enable_caching:
        stack.add(CacheMiddleware(cache_ttl))
    
    return stack
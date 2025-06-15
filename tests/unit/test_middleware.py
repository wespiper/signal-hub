"""Tests for middleware functionality."""

import pytest
import asyncio
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch

from signal_hub.core.middleware import (
    RequestContext,
    LoggingMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
    CacheMiddleware,
    MiddlewareStack,
    create_middleware_stack,
)
from signal_hub.utils.metrics import request_counter, active_connections, get_collector


class TestRequestContext:
    """Test request context."""
    
    def test_request_context_creation(self):
        """Test creating request context."""
        ctx = RequestContext()
        
        assert ctx.request_id is not None
        assert ctx.start_time > 0
        assert ctx.metadata == {}
    
    def test_request_context_with_id(self):
        """Test request context with custom ID."""
        ctx = RequestContext("custom-id")
        
        assert ctx.request_id == "custom-id"
    
    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        ctx = RequestContext()
        
        # Sleep a bit
        time.sleep(0.01)
        
        assert ctx.elapsed_time > 0.01
        assert ctx.elapsed_ms > 10


class TestLoggingMiddleware:
    """Test logging middleware."""
    
    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test logging successful request."""
        middleware = LoggingMiddleware()
        
        # Mock handler
        async def handler(request):
            return {"result": "success"}
        
        # Mock request
        request = {
            "id": "test-123",
            "method": "test_method",
            "params": {"foo": "bar"}
        }
        
        # Execute
        with patch.object(middleware.logger, "info") as mock_info:
            result = await middleware(request, handler)
        
        # Check result
        assert result == {"result": "success"}
        
        # Check logging
        assert mock_info.call_count == 2
        
        # First call - request start
        first_call = mock_info.call_args_list[0]
        assert "Request started: test_method" in first_call[0][0]
        
        # Second call - request complete
        second_call = mock_info.call_args_list[1]
        assert "Request completed: test_method" in second_call[0][0]
    
    @pytest.mark.asyncio
    async def test_failed_request(self):
        """Test logging failed request."""
        middleware = LoggingMiddleware()
        
        # Mock handler that fails
        async def handler(request):
            raise ValueError("Test error")
        
        # Mock request
        request = {
            "id": "test-456",
            "method": "failing_method",
            "params": {}
        }
        
        # Execute
        with patch.object(middleware.logger, "error") as mock_error:
            with pytest.raises(ValueError):
                await middleware(request, handler)
        
        # Check error logging
        assert mock_error.call_count == 1
        assert "Request failed: failing_method" in mock_error.call_args[0][0]


class TestMetricsMiddleware:
    """Test metrics middleware."""
    
    @pytest.mark.asyncio
    async def test_successful_request_metrics(self):
        """Test metrics for successful request."""
        middleware = MetricsMiddleware()
        
        # Reset metrics
        collector = get_collector()
        
        # Mock handler
        async def handler(request):
            await asyncio.sleep(0.01)
            return {"result": "success"}
        
        # Mock request
        request = {
            "method": "search_code",
            "params": {}
        }
        
        # Get initial values
        initial_count = request_counter.get(method="search_code", status="success")
        initial_active = active_connections.get()
        
        # Execute
        result = await middleware(request, handler)
        
        # Check result
        assert result == {"result": "success"}
        
        # Check metrics
        assert request_counter.get(method="search_code", status="success") == initial_count + 1
        assert active_connections.get() == initial_active  # Should be back to initial
    
    @pytest.mark.asyncio
    async def test_failed_request_metrics(self):
        """Test metrics for failed request."""
        middleware = MetricsMiddleware()
        
        # Mock handler that fails
        async def handler(request):
            raise ValueError("Test error")
        
        # Mock request
        request = {
            "method": "failing_method",
            "params": {}
        }
        
        # Get initial values
        initial_error_count = request_counter.get(method="failing_method", status="error")
        
        # Execute
        with pytest.raises(ValueError):
            await middleware(request, handler)
        
        # Check metrics
        assert request_counter.get(method="failing_method", status="error") == initial_error_count + 1


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests(self):
        """Test rate limit allows requests under limit."""
        middleware = RateLimitMiddleware(max_requests_per_minute=5)
        
        # Mock handler
        async def handler(request):
            return {"result": "success"}
        
        # Mock request
        request = {"method": "test", "params": {}}
        
        # Execute multiple requests under limit
        for i in range(5):
            result = await middleware(request, handler)
            assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess_requests(self):
        """Test rate limit blocks excess requests."""
        middleware = RateLimitMiddleware(max_requests_per_minute=2)
        
        # Mock handler
        async def handler(request):
            return {"result": "success"}
        
        # Mock request
        request = {"method": "test", "params": {}}
        
        # Execute requests up to limit
        await middleware(request, handler)
        await middleware(request, handler)
        
        # Next request should be blocked
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await middleware(request, handler)
    
    @pytest.mark.asyncio
    async def test_rate_limit_time_window(self):
        """Test rate limit resets after time window."""
        # Use very short window for testing
        middleware = RateLimitMiddleware(max_requests_per_minute=1)
        
        # Mock handler
        async def handler(request):
            return {"result": "success"}
        
        # Mock request
        request = {"method": "test", "params": {}}
        
        # First request should succeed
        await middleware(request, handler)
        
        # Manually clear old requests (simulate time passing)
        middleware.requests["default"] = []
        
        # Next request should succeed
        result = await middleware(request, handler)
        assert result == {"result": "success"}


class TestCacheMiddleware:
    """Test cache middleware."""
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss."""
        middleware = CacheMiddleware(cache_ttl=300)
        
        # Mock handler
        call_count = 0
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"result": f"response-{call_count}"}
        
        # Mock request
        request = {
            "method": "search_code",
            "params": {"query": "test"}
        }
        
        # First call - cache miss
        result = await middleware(request, handler)
        assert result == {"result": "response-1"}
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache hit."""
        middleware = CacheMiddleware(cache_ttl=300)
        
        # Mock handler
        call_count = 0
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"result": f"response-{call_count}"}
        
        # Mock request
        request = {
            "method": "search_code",
            "params": {"query": "test"}
        }
        
        # First call - cache miss
        result1 = await middleware(request, handler)
        assert result1 == {"result": "response-1"}
        assert call_count == 1
        
        # Second call - cache hit
        result2 = await middleware(request, handler)
        assert result2 == {"result": "response-1"}  # Same response
        assert call_count == 1  # Handler not called again
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self):
        """Test cache TTL expiration."""
        middleware = CacheMiddleware(cache_ttl=0.01)  # Very short TTL
        
        # Mock handler
        call_count = 0
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"result": f"response-{call_count}"}
        
        # Mock request
        request = {
            "method": "search_code",
            "params": {"query": "test"}
        }
        
        # First call
        result1 = await middleware(request, handler)
        assert call_count == 1
        
        # Wait for TTL to expire
        await asyncio.sleep(0.02)
        
        # Second call - should be cache miss
        result2 = await middleware(request, handler)
        assert result2 == {"result": "response-2"}
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_only_for_search_methods(self):
        """Test cache only applies to search methods."""
        middleware = CacheMiddleware(cache_ttl=300)
        
        # Mock handler
        call_count = 0
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"result": f"response-{call_count}"}
        
        # Non-search method - should not cache
        request = {
            "method": "index_code",
            "params": {"path": "/test"}
        }
        
        # Multiple calls
        await middleware(request, handler)
        await middleware(request, handler)
        
        # Handler should be called each time
        assert call_count == 2


class TestMiddlewareStack:
    """Test middleware stack."""
    
    @pytest.mark.asyncio
    async def test_empty_stack(self):
        """Test empty middleware stack."""
        stack = MiddlewareStack()
        
        # Mock handler
        async def handler(request):
            return {"result": "success"}
        
        # Request
        request = {"method": "test"}
        
        # Should just call handler
        result = await stack(request, handler)
        assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_single_middleware(self):
        """Test stack with single middleware."""
        stack = MiddlewareStack()
        
        # Mock middleware
        class TestMiddleware:
            async def __call__(self, request, handler):
                request["modified"] = True
                return await handler(request)
        
        stack.add(TestMiddleware())
        
        # Mock handler
        async def handler(request):
            return {"modified": request.get("modified", False)}
        
        # Request
        request = {"method": "test"}
        
        # Execute
        result = await stack(request, handler)
        assert result == {"modified": True}
    
    @pytest.mark.asyncio
    async def test_multiple_middleware_order(self):
        """Test middleware execution order."""
        stack = MiddlewareStack()
        execution_order = []
        
        # Create middleware that records execution
        class OrderMiddleware:
            def __init__(self, name):
                self.name = name
            
            async def __call__(self, request, handler):
                execution_order.append(f"{self.name}-before")
                result = await handler(request)
                execution_order.append(f"{self.name}-after")
                return result
        
        # Add middleware
        stack.add(OrderMiddleware("first"))
        stack.add(OrderMiddleware("second"))
        
        # Mock handler
        async def handler(request):
            execution_order.append("handler")
            return {}
        
        # Execute
        await stack({"method": "test"}, handler)
        
        # Check order - middleware execute in LIFO order
        assert execution_order == [
            "second-before",
            "first-before",
            "handler",
            "first-after",
            "second-after"
        ]


class TestCreateMiddlewareStack:
    """Test middleware stack creation."""
    
    def test_create_full_stack(self):
        """Test creating full middleware stack."""
        stack = create_middleware_stack(
            enable_logging=True,
            enable_metrics=True,
            enable_rate_limiting=True,
            enable_caching=True,
            rate_limit=100,
            cache_ttl=600
        )
        
        assert isinstance(stack, MiddlewareStack)
        assert len(stack.middleware) == 4
    
    def test_create_partial_stack(self):
        """Test creating partial middleware stack."""
        stack = create_middleware_stack(
            enable_logging=True,
            enable_metrics=False,
            enable_rate_limiting=False,
            enable_caching=True
        )
        
        assert isinstance(stack, MiddlewareStack)
        assert len(stack.middleware) == 2
    
    def test_create_empty_stack(self):
        """Test creating empty middleware stack."""
        stack = create_middleware_stack(
            enable_logging=False,
            enable_metrics=False,
            enable_rate_limiting=False,
            enable_caching=False
        )
        
        assert isinstance(stack, MiddlewareStack)
        assert len(stack.middleware) == 0
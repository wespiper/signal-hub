"""Tests for monitoring functionality."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock

from signal_hub.core.monitoring import (
    MonitoringService,
    get_monitoring_service,
    handle_monitoring_tool,
    MONITORING_TOOLS,
)
from signal_hub.utils.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_collector,
)


class TestMetrics:
    """Test metric types."""
    
    def test_counter(self):
        """Test counter metric."""
        counter = Counter("test_counter", "Test counter")
        
        # Initial value
        assert counter.get() == 0
        
        # Increment
        counter.inc()
        assert counter.get() == 1
        
        # Increment with amount
        counter.inc(5)
        assert counter.get() == 6
        
        # Labels
        counter.inc(method="GET", status="200")
        assert counter.get(method="GET", status="200") == 1
        
        # Cannot decrement
        with pytest.raises(ValueError):
            counter.inc(-1)
    
    def test_gauge(self):
        """Test gauge metric."""
        gauge = Gauge("test_gauge", "Test gauge")
        
        # Initial value
        assert gauge.get() == 0
        
        # Set value
        gauge.set(42)
        assert gauge.get() == 42
        
        # Increment
        gauge.inc(8)
        assert gauge.get() == 50
        
        # Decrement
        gauge.dec(10)
        assert gauge.get() == 40
        
        # Labels
        gauge.set(100, type="connections")
        assert gauge.get(type="connections") == 100
    
    def test_histogram(self):
        """Test histogram metric."""
        histogram = Histogram("test_histogram", "Test histogram")
        
        # Observe values
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)
        histogram.observe(2.0)
        
        # Collect metrics
        metrics = histogram.collect()
        
        # Should have count and sum
        count_metric = next(m for m in metrics if m.name == "test_histogram_count")
        assert count_metric.value == 4
        
        sum_metric = next(m for m in metrics if m.name == "test_histogram_sum")
        assert sum_metric.value == 3.6
        
        # Should have buckets
        bucket_metrics = [m for m in metrics if m.name == "test_histogram_bucket"]
        assert len(bucket_metrics) > 0
    
    def test_histogram_timer(self):
        """Test histogram timer context manager."""
        histogram = Histogram("test_timer", "Test timer")
        
        with histogram.time():
            time.sleep(0.01)
        
        metrics = histogram.collect()
        count_metric = next(m for m in metrics if m.name == "test_timer_count")
        assert count_metric.value == 1
        
        sum_metric = next(m for m in metrics if m.name == "test_timer_sum")
        assert sum_metric.value > 0.01


class TestMetricsCollector:
    """Test metrics collector."""
    
    def test_register_unregister(self):
        """Test metric registration."""
        collector = MetricsCollector()
        counter = Counter("test", "Test metric")
        
        # Register
        collector.register(counter)
        metrics = collector.collect_all()
        assert any(m.name == "test" for m in metrics)
        
        # Unregister
        collector.unregister("test")
        metrics = collector.collect_all()
        assert not any(m.name == "test" for m in metrics)
    
    def test_prometheus_format(self):
        """Test Prometheus format output."""
        collector = MetricsCollector()
        
        # Register metrics
        counter = Counter("requests_total", "Total requests")
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="201")
        collector.register(counter)
        
        gauge = Gauge("connections", "Active connections")
        gauge.set(42)
        collector.register(gauge)
        
        # Get Prometheus format
        output = collector.format_prometheus()
        
        # Check format
        assert "# HELP requests_total" in output
        assert "# TYPE requests_total" in output
        assert 'requests_total{method="GET",status="200"} 1' in output
        assert 'requests_total{method="POST",status="201"} 1' in output
        assert "connections" in output
        assert "42" in output


class TestMonitoringService:
    """Test monitoring service."""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        service = MonitoringService()
        health = await service.health_check()
        
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "uptime" in health
        assert "version" in health
    
    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """Test readiness check."""
        service = MonitoringService()
        
        # Mock check methods
        service._check_embeddings = MagicMock(return_value=True)
        service._check_vector_store = MagicMock(return_value=True)
        service._check_cache = MagicMock(return_value=True)
        
        readiness = await service.readiness_check()
        
        assert readiness["ready"] is True
        assert readiness["checks"]["server"] is True
        assert "timestamp" in readiness
    
    @pytest.mark.asyncio
    async def test_get_metrics_prometheus(self):
        """Test Prometheus metrics format."""
        service = MonitoringService()
        
        # Add some metrics
        from signal_hub.utils.metrics import request_counter
        request_counter.inc(method="GET", status="200")
        
        metrics = await service.get_metrics("prometheus")
        
        assert isinstance(metrics, str)
        assert "signal_hub_requests_total" in metrics
    
    @pytest.mark.asyncio
    async def test_get_metrics_json(self):
        """Test JSON metrics format."""
        service = MonitoringService()
        
        # Add some metrics
        from signal_hub.utils.metrics import request_counter
        request_counter.inc(method="GET", status="200")
        
        metrics = await service.get_metrics("json")
        
        assert isinstance(metrics, str)
        data = json.loads(metrics)
        assert isinstance(data, list)
        assert any(m["name"] == "signal_hub_requests_total" for m in data)
    
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Test system info."""
        service = MonitoringService()
        
        with patch("psutil.cpu_percent", return_value=50.0):
            with patch("psutil.virtual_memory") as mock_mem:
                mock_mem.return_value = MagicMock(
                    total=8 * 1024 * 1024 * 1024,
                    available=4 * 1024 * 1024 * 1024,
                    percent=50.0
                )
                
                info = await service.get_system_info()
                
                assert "platform" in info
                assert "cpu" in info
                assert "memory" in info
                assert info["cpu"]["percent"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_debug_info(self):
        """Test debug info."""
        service = MonitoringService()
        
        debug = await service.get_debug_info()
        
        assert "config" in debug
        assert "loaded_plugins" in debug
        assert "feature_flags" in debug
        assert "cache_stats" in debug


class TestMonitoringTools:
    """Test monitoring tools."""
    
    def test_monitoring_tools_defined(self):
        """Test monitoring tools are properly defined."""
        assert len(MONITORING_TOOLS) == 3
        
        tool_names = [tool["name"] for tool in MONITORING_TOOLS]
        assert "signal_hub_health" in tool_names
        assert "signal_hub_metrics" in tool_names
        assert "signal_hub_system_info" in tool_names
    
    @pytest.mark.asyncio
    async def test_handle_health_tool(self):
        """Test health tool handler."""
        result = await handle_monitoring_tool("signal_hub_health", {})
        
        assert "status" in result
        assert "timestamp" in result
        assert "uptime" in result
    
    @pytest.mark.asyncio
    async def test_handle_metrics_tool(self):
        """Test metrics tool handler."""
        # JSON format
        result = await handle_monitoring_tool(
            "signal_hub_metrics",
            {"format": "json"}
        )
        
        assert isinstance(result, list)
        
        # Prometheus format
        result = await handle_monitoring_tool(
            "signal_hub_metrics",
            {"format": "prometheus"}
        )
        
        assert "metrics" in result
        assert "format" in result
        assert result["format"] == "prometheus"
    
    @pytest.mark.asyncio
    async def test_handle_system_info_tool(self):
        """Test system info tool handler."""
        with patch("psutil.cpu_percent", return_value=50.0):
            result = await handle_monitoring_tool("signal_hub_system_info", {})
            
            assert "platform" in result
            assert "cpu" in result
    
    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Test handling unknown tool."""
        with pytest.raises(ValueError, match="Unknown monitoring tool"):
            await handle_monitoring_tool("unknown_tool", {})


def test_global_monitoring_service():
    """Test global monitoring service."""
    service1 = get_monitoring_service()
    service2 = get_monitoring_service()
    
    assert service1 is service2  # Should be singleton


def test_global_metrics_collector():
    """Test global metrics collector."""
    collector1 = get_collector()
    collector2 = get_collector()
    
    assert collector1 is collector2  # Should be singleton
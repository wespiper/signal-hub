"""Unit tests for feature flags system."""

import pytest
from signal_hub.core.features import (
    Edition,
    Feature,
    FeatureFlags,
    get_edition,
    is_feature_enabled,
    require_feature,
)


class TestEdition:
    """Test Edition enum."""
    
    def test_edition_values(self):
        """Test edition enum values."""
        assert Edition.BASIC.value == "basic"
        assert Edition.PRO.value == "pro"
        assert Edition.ENTERPRISE.value == "enterprise"
    
    def test_edition_comparison(self):
        """Test edition level comparison."""
        assert Edition.BASIC < Edition.PRO
        assert Edition.PRO < Edition.ENTERPRISE
        assert Edition.BASIC < Edition.ENTERPRISE


class TestFeatureFlags:
    """Test FeatureFlags functionality."""
    
    def test_basic_edition_features(self, edition_basic):
        """Test features available in Basic edition."""
        flags = FeatureFlags()
        
        # Basic features should be enabled
        assert flags.is_enabled(Feature.BASIC_SEARCH)
        assert flags.is_enabled(Feature.BASIC_ROUTING)
        assert flags.is_enabled(Feature.BASIC_CACHING)
        
        # Pro features should be disabled
        assert not flags.is_enabled(Feature.ML_ROUTING)
        assert not flags.is_enabled(Feature.LEARNING_ALGORITHMS)
        assert not flags.is_enabled(Feature.ADVANCED_ANALYTICS)
    
    def test_pro_edition_features(self, edition_pro):
        """Test features available in Pro edition."""
        flags = FeatureFlags()
        
        # All Basic features should be enabled
        assert flags.is_enabled(Feature.BASIC_SEARCH)
        assert flags.is_enabled(Feature.BASIC_ROUTING)
        
        # Pro features should be enabled
        assert flags.is_enabled(Feature.ML_ROUTING)
        assert flags.is_enabled(Feature.LEARNING_ALGORITHMS)
        assert flags.is_enabled(Feature.ADVANCED_ANALYTICS)
        
        # Enterprise features should be disabled
        assert not flags.is_enabled(Feature.TEAM_MANAGEMENT)
        assert not flags.is_enabled(Feature.SSO_INTEGRATION)
    
    def test_early_access_enables_all(self, early_access):
        """Test early access mode enables all features."""
        flags = FeatureFlags()
        
        # All features should be enabled
        for feature in Feature:
            assert flags.is_enabled(feature)
    
    def test_manual_override(self, edition_basic):
        """Test manual feature override."""
        flags = FeatureFlags()
        
        # Manually enable a Pro feature
        flags.set_override(Feature.ML_ROUTING, True)
        assert flags.is_enabled(Feature.ML_ROUTING)
        
        # Manually disable a Basic feature
        flags.set_override(Feature.BASIC_SEARCH, False)
        assert not flags.is_enabled(Feature.BASIC_SEARCH)
        
        # Clear overrides
        flags.clear_overrides()
        assert not flags.is_enabled(Feature.ML_ROUTING)
        assert flags.is_enabled(Feature.BASIC_SEARCH)


class TestFeatureDecorator:
    """Test require_feature decorator."""
    
    def test_allowed_feature_execution(self, edition_basic):
        """Test decorator allows execution when feature is enabled."""
        
        @require_feature(Feature.BASIC_SEARCH)
        def search_function():
            return "search results"
        
        # Should execute normally
        result = search_function()
        assert result == "search results"
    
    def test_blocked_feature_execution(self, edition_basic):
        """Test decorator blocks execution when feature is disabled."""
        
        @require_feature(Feature.ML_ROUTING)
        def ml_routing_function():
            return "ml routing"
        
        # Should raise FeatureNotEnabledError
        with pytest.raises(Exception) as exc_info:
            ml_routing_function()
        
        assert "not enabled" in str(exc_info.value).lower()
    
    def test_decorator_with_early_access(self, early_access):
        """Test decorator works with early access."""
        
        @require_feature(Feature.ENTERPRISE_DEPLOYMENT)
        def enterprise_function():
            return "enterprise feature"
        
        # Should execute with early access
        result = enterprise_function()
        assert result == "enterprise feature"


class TestHelperFunctions:
    """Test module-level helper functions."""
    
    def test_get_edition(self, edition_pro):
        """Test get_edition function."""
        edition = get_edition()
        assert edition == Edition.PRO
    
    def test_is_feature_enabled(self, edition_basic):
        """Test is_feature_enabled function."""
        assert is_feature_enabled(Feature.BASIC_CACHING)
        assert not is_feature_enabled(Feature.SMART_CACHING)
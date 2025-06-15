"""Tests for escalation system."""

import pytest

from signal_hub.routing.models import Query, ModelType
from signal_hub.routing.escalation.escalator import EscalationManager
from signal_hub.routing.escalation.parser import EscalationParser


class TestEscalationParser:
    """Test escalation hint parser."""
    
    def test_extract_hint_opus(self):
        """Test extracting @opus hint."""
        parser = EscalationParser()
        
        result = parser.extract_hint("@opus Analyze this complex architecture")
        assert result is not None
        
        cleaned_query, escalation = result
        assert cleaned_query == "Analyze this complex architecture"
        assert escalation.requested_model == ModelType.OPUS
        
    def test_extract_hint_sonnet(self):
        """Test extracting @sonnet hint."""
        parser = EscalationParser()
        
        result = parser.extract_hint("Explain this @sonnet in detail")
        assert result is not None
        
        cleaned_query, escalation = result
        assert cleaned_query == "Explain this in detail"
        assert escalation.requested_model == ModelType.SONNET
        
    def test_extract_hint_case_insensitive(self):
        """Test case insensitive hints."""
        parser = EscalationParser()
        
        result = parser.extract_hint("@OPUS uppercase test")
        assert result is not None
        _, escalation = result
        assert escalation.requested_model == ModelType.OPUS
        
        result = parser.extract_hint("@Sonnet mixed case")
        assert result is not None
        _, escalation = result
        assert escalation.requested_model == ModelType.SONNET
        
    def test_no_hint(self):
        """Test query without hint."""
        parser = EscalationParser()
        
        result = parser.extract_hint("Normal query without hints")
        assert result is None
        
    def test_has_hint(self):
        """Test hint detection."""
        parser = EscalationParser()
        
        assert parser.has_hint("@opus test") is True
        assert parser.has_hint("@sonnet test") is True
        assert parser.has_hint("no hint here") is False


class TestEscalationManager:
    """Test escalation manager."""
    
    def test_explicit_escalation(self):
        """Test explicit model preference."""
        manager = EscalationManager()
        
        query = Query(
            text="Test query",
            preferred_model=ModelType.OPUS
        )
        
        override = manager.check_escalation(query)
        assert override is not None
        assert override.model == ModelType.OPUS
        assert override.source == "explicit"
        
    def test_inline_escalation(self):
        """Test inline hint escalation."""
        manager = EscalationManager()
        
        query = Query(text="@sonnet Explain this code")
        
        override = manager.check_escalation(query)
        assert override is not None
        assert override.model == ModelType.SONNET
        assert override.source == "inline"
        assert query.text == "Explain this code"  # Hint removed
        
    def test_session_escalation(self):
        """Test session-level escalation."""
        manager = EscalationManager()
        
        # Set session escalation
        manager.escalate_session(
            session_id="test-session",
            model=ModelType.OPUS,
            duration_minutes=30
        )
        
        # Check query with session
        query = Query(text="Normal query")
        override = manager.check_escalation(query, session_id="test-session")
        
        assert override is not None
        assert override.model == ModelType.OPUS
        assert override.source == "session"
        
    def test_escalation_priority(self):
        """Test escalation priority (explicit > session > inline)."""
        manager = EscalationManager()
        
        # Set session escalation
        manager.escalate_session("test-session", ModelType.SONNET)
        
        # Query with both explicit and inline
        query = Query(
            text="@haiku Test query",
            preferred_model=ModelType.OPUS
        )
        
        override = manager.check_escalation(query, session_id="test-session")
        
        # Explicit should win
        assert override.model == ModelType.OPUS
        assert override.source == "explicit"
        
    def test_metrics(self):
        """Test escalation metrics."""
        manager = EscalationManager()
        
        # Generate some escalations
        manager.check_escalation(Query(text="@opus Test"))
        manager.check_escalation(Query(text="Normal", preferred_model=ModelType.SONNET))
        manager.escalate_session("session1", ModelType.OPUS)
        manager.check_escalation(Query(text="Session query"), session_id="session1")
        
        metrics = manager.get_metrics()
        
        assert metrics["total_escalations"] == 3
        assert metrics["inline_escalations"] == 1
        assert metrics["explicit_escalations"] == 1
        assert metrics["session_escalations"] == 1
        assert metrics["active_sessions"] == 1
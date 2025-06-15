"""Models for escalation system."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

from signal_hub.routing.models import ModelType


class EscalationType(str, Enum):
    """Types of escalation."""
    INLINE = "inline"       # @model in query
    EXPLICIT = "explicit"   # escalate_query tool
    SESSION = "session"     # Session-level escalation


@dataclass
class EscalationRequest:
    """Request for model escalation."""
    requested_model: ModelType
    escalation_type: EscalationType
    reason: Optional[str] = None
    duration: Optional[str] = None  # "single", "session"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ModelOverride:
    """Model override from escalation."""
    model: ModelType
    source: str  # "session", "inline", "explicit"
    reason: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "model": self.model.value,
            "source": self.source,
            "reason": self.reason
        }
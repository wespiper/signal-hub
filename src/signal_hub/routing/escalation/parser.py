"""Parser for inline escalation hints."""

import re
import logging
from typing import Optional, Tuple

from signal_hub.routing.models import ModelType
from signal_hub.routing.escalation.models import EscalationRequest, EscalationType

logger = logging.getLogger(__name__)


class EscalationParser:
    """Parse escalation hints from queries."""
    
    # Pattern to match @model hints
    HINT_PATTERN = re.compile(
        r'@(haiku|sonnet|opus)\b',
        re.IGNORECASE
    )
    
    def extract_hint(self, query: str) -> Optional[Tuple[str, EscalationRequest]]:
        """Extract escalation hint from query.
        
        Args:
            query: Query text possibly containing @model hint
            
        Returns:
            Tuple of (cleaned_query, escalation_request) or None
        """
        match = self.HINT_PATTERN.search(query)
        
        if not match:
            return None
            
        # Extract model name
        model_name = match.group(1).upper()
        
        # Map to ModelType
        try:
            if model_name == "HAIKU":
                model = ModelType.HAIKU
            elif model_name == "SONNET":
                model = ModelType.SONNET
            elif model_name == "OPUS":
                model = ModelType.OPUS
            else:
                logger.warning(f"Unknown model hint: {model_name}")
                return None
        except Exception as e:
            logger.error(f"Error parsing model hint: {e}")
            return None
            
        # Remove hint from query
        cleaned_query = self.HINT_PATTERN.sub('', query).strip()
        
        # Create escalation request
        escalation = EscalationRequest(
            requested_model=model,
            escalation_type=EscalationType.INLINE,
            reason=f"Inline hint @{model_name.lower()}",
            duration="single"
        )
        
        logger.debug(f"Extracted hint: @{model_name.lower()} -> {model.display_name}")
        
        return cleaned_query, escalation
        
    def has_hint(self, query: str) -> bool:
        """Check if query contains escalation hint.
        
        Args:
            query: Query text
            
        Returns:
            True if hint found
        """
        return bool(self.HINT_PATTERN.search(query))
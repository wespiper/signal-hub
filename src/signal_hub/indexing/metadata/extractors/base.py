"""Base extractor utilities."""

import logging
from typing import List, Set

logger = logging.getLogger(__name__)


def extract_dependencies_from_imports(imports: List[str]) -> Set[str]:
    """Extract top-level package names from import statements.
    
    Args:
        imports: List of import module names
        
    Returns:
        Set of top-level package names
    """
    dependencies = set()
    
    for module in imports:
        if not module:
            continue
            
        # Skip relative imports
        if module.startswith('.'):
            continue
            
        # Extract top-level package
        parts = module.split('.')
        if parts[0]:
            dependencies.add(parts[0])
            
    return dependencies
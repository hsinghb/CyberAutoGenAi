"""Model Context Management."""

from typing import Dict, Any, List, Optional
from .types import ContextType, ContextWindow, SecurityContext
import json

class ModelContext:
    """Manages context for model interactions."""
    
    def __init__(self, max_context_size: int = 4096):
        self.max_context_size = max_context_size
        self.context_windows: Dict[ContextType, ContextWindow] = {}
        self.security_contexts: Dict[str, SecurityContext] = {}
        
    def add_context(self, context_type: ContextType, content: Dict[str, Any], 
                   metadata: Dict[str, Any] = None):
        """Add context to a specific context type window."""
        if context_type not in self.context_windows:
            self.context_windows[context_type] = ContextWindow(
                max_tokens=self.max_context_size,
                content=[],
                metadata={}
            )
            
        window = self.context_windows[context_type]
        window.content.append(content)
        
        # Update metadata if provided
        if metadata:
            window.metadata.update(metadata)
            
        # Maintain context window size
        self._trim_context_window(context_type)
    
    def get_context(self, context_type: ContextType) -> List[Dict[str, Any]]:
        """Get all context for a specific type."""
        if context_type in self.context_windows:
            return self.context_windows[context_type].content
        return []
    
    def add_security_context(self, target_id: str, context: SecurityContext):
        """Add security-specific context."""
        self.security_contexts[target_id] = context
    
    def get_security_context(self, target_id: str) -> Optional[SecurityContext]:
        """Get security context for a specific target."""
        return self.security_contexts.get(target_id)
    
    def _trim_context_window(self, context_type: ContextType):
        """Ensure context window doesn't exceed max size."""
        window = self.context_windows[context_type]
        current_size = sum(len(json.dumps(c)) for c in window.content)
        
        while current_size > self.max_context_size and window.content:
            removed = window.content.pop(0)
            current_size -= len(json.dumps(removed))
    
    def clear_context(self, context_type: Optional[ContextType] = None):
        """Clear context for a specific type or all contexts."""
        if context_type:
            if context_type in self.context_windows:
                del self.context_windows[context_type]
        else:
            self.context_windows.clear()
            self.security_contexts.clear() 
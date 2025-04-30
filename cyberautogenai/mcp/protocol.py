"""Model Context Protocol Handler."""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from .types import ContextType, ModelResponse, SecurityContext
from .context import ModelContext

class MCPHandler:
    """Handles model context protocol operations."""
    
    def __init__(self):
        self.context_manager = ModelContext()
        self.handlers: Dict[ContextType, List[Callable]] = {}
        
    async def process_security_analysis(self, 
                                      target_type: str,
                                      target_value: str,
                                      apis: List[str]) -> ModelResponse:
        """Process a security analysis request."""
        # Create security context
        context = SecurityContext(
            target_type=target_type,
            target_value=target_value
        )
        
        # Add to context manager
        target_id = f"{target_type}:{target_value}"
        self.context_manager.add_security_context(target_id, context)
        
        # Add analysis request to context window
        self.context_manager.add_context(
            ContextType.SECURITY_ANALYSIS,
            {
                "type": "analysis_request",
                "target": {
                    "type": target_type,
                    "value": target_value
                },
                "apis": apis
            }
        )
        
        # Process with handlers
        responses = []
        if ContextType.SECURITY_ANALYSIS in self.handlers:
            for handler in self.handlers[ContextType.SECURITY_ANALYSIS]:
                response = await handler(context)
                responses.append(response)
        
        # Combine responses and update context
        combined_response = self._combine_responses(responses)
        self.context_manager.add_context(
            ContextType.SECURITY_ANALYSIS,
            {
                "type": "analysis_response",
                "response": combined_response.to_dict()
            }
        )
        
        return combined_response
    
    def register_handler(self, context_type: ContextType, 
                        handler: Callable[..., ModelResponse]):
        """Register a handler for a specific context type."""
        if context_type not in self.handlers:
            self.handlers[context_type] = []
        self.handlers[context_type].append(handler)
    
    def _combine_responses(self, responses: List[ModelResponse]) -> ModelResponse:
        """Combine multiple model responses into a single response."""
        if not responses:
            return ModelResponse(
                content="No analysis available",
                confidence=0.0,
                metadata={},
                context_type=ContextType.SECURITY_ANALYSIS
            )
        
        # Combine content and metadata
        combined_content = "\n".join(r.content for r in responses)
        combined_metadata = {}
        combined_references = []
        total_confidence = 0.0
        
        for response in responses:
            combined_metadata.update(response.metadata)
            if response.references:
                combined_references.extend(response.references)
            total_confidence += response.confidence
        
        average_confidence = total_confidence / len(responses)
        
        return ModelResponse(
            content=combined_content,
            confidence=average_confidence,
            metadata=combined_metadata,
            context_type=ContextType.SECURITY_ANALYSIS,
            references=combined_references
        ) 
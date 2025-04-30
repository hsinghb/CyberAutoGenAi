from typing import Dict, Any, Optional
import logging
import re
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ChatAgent(BaseAgent):
    """Agent that handles natural language processing and extraction of security-relevant information."""
    
    def __init__(self):
        super().__init__()
        self.patterns = {
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'domain': r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
            'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'hash': r'\b[a-fA-F0-9]{32,64}\b'
        }

    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a natural language message and extract security-relevant information.
        
        Args:
            message: The natural language message to process
            
        Returns:
            Dict containing extracted entities and analysis type
        """
        logger.info(f"Processing message: {message}")
        
        # Extract entities from message
        entities = self._extract_entities(message)
        
        # Determine analysis type
        analysis_type = self._determine_analysis_type(message, entities)
        
        result = {
            'raw_input': message,
            'entities': entities,
            'analysis_type': analysis_type
        }
        
        logger.debug(f"Processed result: {result}")
        return result

    def _extract_entities(self, text: str) -> Dict[str, list]:
        """Extract various types of entities from text."""
        entities = {}
        
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities

    def _determine_analysis_type(self, message: str, entities: Dict[str, list]) -> str:
        """Determine type of security analysis needed based on message content."""
        message = message.lower()
        
        # Keywords for different types of analysis
        analysis_keywords = {
            'threat_intel': ['threat', 'malicious', 'suspicious', 'reputation'],
            'vulnerability': ['vulnerability', 'cve', 'exploit', 'patch'],
            'network': ['port', 'service', 'scan', 'open'],
            'malware': ['malware', 'virus', 'ransomware', 'infection']
        }
        
        # Score each analysis type based on keywords and entities
        scores = {analysis_type: 0 for analysis_type in analysis_keywords}
        
        # Check for keywords
        for analysis_type, keywords in analysis_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    scores[analysis_type] += 1
        
        # Consider entities
        if entities.get('ip'):
            scores['network'] += 2
            scores['threat_intel'] += 1
        if entities.get('domain'):
            scores['threat_intel'] += 2
        if entities.get('hash'):
            scores['malware'] += 2
        
        # Get analysis type with highest score
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Default to basic security analysis if no clear type determined
        return 'security_analysis' 
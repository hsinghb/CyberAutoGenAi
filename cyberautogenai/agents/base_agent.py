"""Base intelligent security agent with AutoGen integration."""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import autogen
from datetime import datetime
from ..config.code_execution_config import code_execution_config
from ..config.agent_config import get_openai_config
from ..utils.logger import logger
import asyncio
import openai
from openai import AsyncOpenAI

class SecurityAgent(ABC):
    """Base class for all security agents."""
    
    def __init__(self, api_key: str = None):
        """Initialize security agent."""
        self.api_key = api_key
        logger.info(f"Initializing {self.__class__.__name__}")
        
        if not api_key:
            logger.warning(f"{self.__class__.__name__} initialized without API key")

    @abstractmethod
    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        pass

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the provided data."""
        pass

    async def _check_api_access(self) -> bool:
        """Check API key."""
        if not self.api_key:
            logger.error(f"{self.__class__.__name__}: Missing API key")
            return False
        return True

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

class BaseSecurityAgent(SecurityAgent):
    """Intelligent base security agent with natural language understanding."""
    
    def __init__(self, name: str, expertise: str, api_key: str = None):
        """Initialize intelligent security agent."""
        super().__init__(api_key)
        self.name = name
        self.expertise = expertise
        self.config_list = get_openai_config()
        
        # Create intelligent assistant for this agent
        self.assistant = autogen.AssistantAgent(
            name=f"{name}_assistant",
            system_message=self._get_system_message(),
            llm_config={"config_list": self.config_list}
        )
        
        # Create user proxy for code execution
        self.user_proxy = autogen.UserProxyAgent(
            name=f"{name}_proxy",
            human_input_mode="NEVER",
            code_execution_config=code_execution_config
        )

    def _get_system_message(self) -> str:
        """Generate specialized system message based on agent expertise."""
        return f"""You are an expert {self.expertise} security analyst. Your capabilities include:
        1. Understanding and interpreting security-related queries in natural language
        2. Analyzing {self.expertise}-specific data and patterns
        3. Providing detailed threat assessments and recommendations
        4. Collaborating with other specialized security agents
        5. Maintaining context across multiple interactions
        
        Focus area: {self.expertise}
        """

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data with AI assistance."""
        try:
            prompt = f"""
            Please validate this security analysis request:
            {data}
            
            Check for:
            1. Required fields
            2. Data format
            3. Potential security concerns
            """
            
            response = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=prompt
            )
            
            # Extract validation result from response
            validation_result = self._parse_validation_response(response)
            return validation_result.get("is_valid", False)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with AI assistance."""
        try:
            if not await self.validate_input(data):
                raise ValueError("Invalid input data")

            prompt = f"""
            Please analyze this security-related data:
            {data}
            
            Provide:
            1. Threat assessment
            2. Risk level
            3. Recommendations
            4. Required actions
            """
            
            response = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=prompt
            )
            
            return self._parse_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            raise

    def _parse_validation_response(self, response: Any) -> Dict[str, Any]:
        """Parse validation response from AI."""
        if hasattr(response, 'messages') and response.messages:
            content = response.messages[-1]["content"].lower()
            return {
                "is_valid": "valid" in content and "invalid" not in content,
                "message": response.messages[-1]["content"]
            }
        return {"is_valid": False, "message": "Invalid response format"}

    def _parse_analysis_response(self, response: Any) -> Dict[str, Any]:
        """Parse and structure analysis response from AI."""
        if hasattr(response, 'messages') and response.messages:
            return {
                "timestamp": self._get_timestamp(),
                "analysis": response.messages[-1]["content"],
                "metadata": {
                    "agent": self.name,
                    "expertise": self.expertise
                }
            }
        return {
            "timestamp": self._get_timestamp(),
            "analysis": str(response),
            "metadata": {
                "agent": self.name,
                "expertise": self.expertise
            }
        }

class BaseAgent:
    """Base agent for processing user input and orchestrating security analysis."""
    
    def __init__(self, openai_key: str = None):
        self.openai_key = openai_key
        if openai_key:
            self.client = AsyncOpenAI(api_key=openai_key)

    async def process_input(self, prompt: str) -> Dict[str, Any]:
        """Process user input using AI."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security analysis assistant. Help analyze security-related queries."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return {
                "content": response.choices[0].message.content,
                "role": "assistant"
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            raise 
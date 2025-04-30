"""Base class for ReAct agents with state management."""
from typing import Dict, Any, List, Optional
import uuid
from abc import ABC, abstractmethod
from ..state.db_manager import StateManager
from ..utils.logger import logger
from ..utils.quota_manager import QuotaManager
from ..exceptions import ValidationError, ProcessingError

class ReActAgent(ABC):
    """Base class for ReAct agents with state persistence."""
    
    def __init__(self, agent_id: str, state_manager: StateManager, quota_manager: Optional[QuotaManager] = None):
        self.agent_id = agent_id
        self.state_manager = state_manager
        self.quota_manager = quota_manager or QuotaManager()
        self.current_conversation_id = None
        self.thought_history = []
        logger.info(f"Initializing ReAct agent: {agent_id}")

    async def think(
        self,
        observation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the ReAct thought process."""
        try:
            # Check quota before thinking
            can_process = await self.quota_manager.check_quota(self.agent_id)
            if not can_process:
                raise ProcessingError(f"Quota exceeded for {self.agent_id}")

            # Load relevant memories
            memories = await self.recall(
                memory_type="analysis",
                min_relevance=0.7
            )

            # Generate thought based on observation, context, and memories
            thought = await self._generate_thought(observation, context)
            
            # Decide on next action
            action = await self._decide_action(thought)
            
            # Check quota before executing action
            can_process_action = await self.quota_manager.check_quota(f"{self.agent_id}_action")
            if not can_process_action:
                raise ProcessingError(f"Action quota exceeded for {self.agent_id}")
                
            action_result = await self._execute_action(action)
            
            # Make observation
            new_observation = await self._make_observation(action_result)
            
            # Save thought process
            thought_record = {
                "thought": thought,
                "action": action,
                "action_result": str(action_result),
                "observation": new_observation,
                "timestamp": str(uuid.uuid4())
            }
            
            self.thought_history.append(thought_record)
            
            await self.state_manager.save_react_thought(
                self.agent_id,
                thought,
                action,
                str(action_result),
                new_observation,
                self.current_conversation_id or str(uuid.uuid4())
            )
            
            # Update quota usage
            await self.quota_manager.increment_usage(self.agent_id)
            await self.quota_manager.increment_usage(f"{self.agent_id}_action")
            
            return thought_record

        except Exception as e:
            logger.error(f"ReAct thinking process failed: {str(e)}")
            raise ProcessingError(f"Thinking failed: {str(e)}")

    @abstractmethod
    async def _generate_thought(
        self,
        observation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a thought based on observation and context."""
        pass

    @abstractmethod
    async def _decide_action(self, thought: str) -> str:
        """Decide on next action based on thought."""
        pass

    @abstractmethod
    async def _execute_action(self, action: str) -> Any:
        """Execute the decided action."""
        pass

    @abstractmethod
    async def _make_observation(self, action_result: Any) -> str:
        """Make observation based on action result."""
        pass

    async def remember(
        self,
        memory_type: str,
        content: Dict[str, Any],
        relevance_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store a memory."""
        await self.state_manager.save_memory(
            self.agent_id,
            memory_type,
            content,
            relevance_score,
            metadata
        )

    async def recall(
        self,
        memory_type: Optional[str] = None,
        min_relevance: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recall relevant memories."""
        return await self.state_manager.get_relevant_memories(
            self.agent_id,
            memory_type,
            min_relevance,
            limit
        )

    async def save_state(
        self,
        state_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """Save current agent state."""
        await self.state_manager.save_agent_state(
            self.agent_id,
            state_data,
            context
        )

    async def load_state(self) -> Optional[Dict[str, Any]]:
        """Load agent's previous state."""
        return await self.state_manager.get_agent_state(self.agent_id)

    async def update_task(
        self,
        task_id: str,
        status: str,
        current_step: str,
        progress: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update task execution state."""
        await self.state_manager.update_task_state(
            task_id,
            self.agent_id,
            status,
            current_step,
            progress,
            metadata
        ) 
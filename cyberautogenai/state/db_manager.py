"""SQLite state management for ReAct agents."""
import sqlite3
from typing import Dict, Any, List, Optional
import json
import datetime
from contextlib import contextmanager

class StateManager:
    """Manages persistent state for ReAct agents using SQLite."""
    
    def __init__(self, db_path: str = "data/agent_state.db"):
        self.db_path = db_path
        self.setup_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def setup_database(self):
        """Initialize the database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables for different types of state data
            cursor.executescript("""
                -- Agent State table
                CREATE TABLE IF NOT EXISTS agent_state (
                    agent_id TEXT PRIMARY KEY,
                    state_data TEXT,
                    last_updated TIMESTAMP,
                    context TEXT
                );

                -- Conversation History table
                CREATE TABLE IF NOT EXISTS conversation_history (
                    conversation_id TEXT,
                    message_id TEXT,
                    timestamp TIMESTAMP,
                    sender_id TEXT,
                    recipient_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    PRIMARY KEY (conversation_id, message_id)
                );

                -- ReAct Thought Process table
                CREATE TABLE IF NOT EXISTS react_thoughts (
                    thought_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    timestamp TIMESTAMP,
                    thought TEXT,
                    action TEXT,
                    action_result TEXT,
                    observation TEXT,
                    conversation_id TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversation_history(conversation_id)
                );

                -- Agent Memory table
                CREATE TABLE IF NOT EXISTS agent_memory (
                    memory_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    memory_type TEXT,
                    content TEXT,
                    timestamp TIMESTAMP,
                    relevance_score REAL,
                    metadata TEXT
                );

                -- Task State table
                CREATE TABLE IF NOT EXISTS task_state (
                    task_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    status TEXT,
                    current_step TEXT,
                    progress REAL,
                    start_time TIMESTAMP,
                    last_updated TIMESTAMP,
                    metadata TEXT
                );
            """)
            conn.commit()

    async def save_agent_state(
        self,
        agent_id: str,
        state_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """Save agent's current state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_state
                (agent_id, state_data, last_updated, context)
                VALUES (?, ?, ?, ?)
            """, (
                agent_id,
                json.dumps(state_data),
                datetime.datetime.utcnow().isoformat(),
                json.dumps(context) if context else None
            ))
            conn.commit()

    async def get_agent_state(
        self,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve agent's state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT state_data, context
                FROM agent_state
                WHERE agent_id = ?
            """, (agent_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "state_data": json.loads(row["state_data"]),
                    "context": json.loads(row["context"]) if row["context"] else None
                }
            return None

    async def save_react_thought(
        self,
        agent_id: str,
        thought: str,
        action: str,
        action_result: str,
        observation: str,
        conversation_id: str
    ):
        """Save ReAct thought process."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO react_thoughts
                (thought_id, agent_id, timestamp, thought, action,
                 action_result, observation, conversation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{agent_id}_{datetime.datetime.utcnow().isoformat()}",
                agent_id,
                datetime.datetime.utcnow().isoformat(),
                thought,
                action,
                action_result,
                observation,
                conversation_id
            ))
            conn.commit()

    async def get_react_thoughts(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve ReAct thought process history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT *
                FROM react_thoughts
                WHERE agent_id = ?
            """
            params = [agent_id]
            
            if conversation_id:
                query += " AND conversation_id = ?"
                params.append(conversation_id)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    async def save_memory(
        self,
        agent_id: str,
        memory_type: str,
        content: Dict[str, Any],
        relevance_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save agent memory."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_memory
                (memory_id, agent_id, memory_type, content,
                 timestamp, relevance_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{agent_id}_{datetime.datetime.utcnow().isoformat()}",
                agent_id,
                memory_type,
                json.dumps(content),
                datetime.datetime.utcnow().isoformat(),
                relevance_score,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()

    async def get_relevant_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        min_relevance: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for an agent."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT *
                FROM agent_memory
                WHERE agent_id = ?
                AND relevance_score >= ?
            """
            params = [agent_id, min_relevance]
            
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)
                
            query += " ORDER BY relevance_score DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [
                {
                    **dict(row),
                    'content': json.loads(row['content']),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None
                }
                for row in cursor.fetchall()
            ]

    async def update_task_state(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        current_step: str,
        progress: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update task execution state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO task_state
                (task_id, agent_id, status, current_step, progress,
                 start_time, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                agent_id,
                status,
                current_step,
                progress,
                datetime.datetime.utcnow().isoformat(),
                datetime.datetime.utcnow().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit() 
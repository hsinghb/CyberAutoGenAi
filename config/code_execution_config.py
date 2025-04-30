"""Configuration for code execution in AutoGen."""

code_execution_config = {
    "use_docker": False,  # Disable Docker usage
    "work_dir": "workspace",  # Directory for code execution
    "timeout": 60,  # Timeout in seconds
    "stream_output": True  # Stream output in real-time
} 
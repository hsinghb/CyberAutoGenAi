"""Setup project directory structure."""
import os
import sys
from pathlib import Path

def setup_project_structure():
    """Create necessary project directories."""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Define required directories
    directories = [
        'logs',
        'config',
        'workspace',
        'cyberautogenai/utils',
        'cyberautogenai/agents',
        'cyberautogenai/mcp',
        'cyberautogenai/api',
        'cyberautogenai/ui',
        'cyberautogenai/config',
        'cyberautogenai/exceptions',
    ]
    
    # Create directories
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create necessary __init__.py files
    init_locations = [
        'cyberautogenai',
        'cyberautogenai/utils',
        'cyberautogenai/agents',
        'cyberautogenai/mcp',
        'cyberautogenai/api',
        'cyberautogenai/ui',
        'cyberautogenai/config',
        'cyberautogenai/exceptions',
    ]
    
    for location in init_locations:
        init_file = project_root / location / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")

if __name__ == "__main__":
    try:
        setup_project_structure()
        print("Project structure setup completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        sys.exit(1) 
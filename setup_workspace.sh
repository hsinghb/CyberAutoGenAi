#!/bin/bash

# Create workspace directory if it doesn't exist
mkdir -p workspace

# Set proper permissions
chmod 755 workspace

# Create necessary subdirectories
mkdir -p workspace/logs
mkdir -p workspace/temp
mkdir -p workspace/output

echo "Workspace setup completed successfully!" 
#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but could not be found."
    exit 1
fi

# Check if required packages are installed
python3 -c "import redis, websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required Python packages..."
    pip3 install redis websockets
fi

# Start the dashboard server
echo "Starting the monitoring dashboard server..."
python3 dashboard_server_pubsub.py
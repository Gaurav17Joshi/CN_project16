# Redis Notification System

This is a real-time notification system that monitors files and displays notifications via a web dashboard.

## System Components

### Client (File Monitor)
- Monitors a directory for new files
- Sends notifications to Redis when changes are detected
- Uses the Watchdog library for file system monitoring

### Server (Dashboard)
- HTTP server that displays event notifications
- WebSocket server for real-time updates
- Redis subscriber for receiving notifications

## Features
- Real-time dashboard updates via WebSockets
- Fallback 15-second refresh for reliability
- Filter events by time
- Priority-based event highlighting
- Modular code organization

## File Structure

- `dashboard_server.py` - Main server with HTTP and WebSocket functionality
- `template_handler.py` - HTML template handling
- `event_manager.py` - Event logging and retrieval
- `websocket_handler.py` - WebSocket compatibility layer
- `index.html` - Dashboard HTML template
- `styles.css` - Dashboard styling
- `dashboard.js` - Client-side JavaScript for real-time updates
- `start_server.sh` - Server startup script

## Setup Instructions

1. Install required packages:
   ```
   pip install redis websockets watchdog
   ```

2. Configure Redis connection:
   - Edit `REDIS_HOST` and `REDIS_PORT` in `dashboard_server.py`
   - Also update the same settings in `file_monitor_client.py`

3. Start the dashboard server:
   ```
   ./start_server.sh
   ```

4. Start the file monitor client in a separate terminal:
   ```
   python file_monitor_client.py
   ```

5. Access the dashboard:
   Open a web browser and go to http://localhost:8000

## Troubleshooting

### WebSocket Connection Issues
- Check that port 8001 is accessible
- The status indicator in the bottom-right corner shows connection status
- The system has a fallback 15-second refresh if WebSockets fail

### Redis Connection Issues
- Verify Redis is running and accessible
- Check firewall settings if connecting to a remote Redis server

## Architecture Notes

The system has been designed with modularity in mind:
- Core server logic is separate from template rendering
- WebSocket handling uses a compatibility layer
- Event logging is decoupled from the server
- Static files are served from a dedicated folder

This makes the code easier to maintain and extend with new features.
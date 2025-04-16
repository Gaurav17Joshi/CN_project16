# Real-Time Distributed Monitoring System

**CN Project: Group 16**
**Project Title:** Websocket and Push Notification Integration for System Monitoring

**Team Members:**

| Name          | ID        |
|---------------|-----------|
| Gaurav Joshi  | 21110065  |
| Husain Malwat | 21110117  |
| Mitansh Patel | 24120033  |

This project implements a distributed system for monitoring various client-side events (like file changes, USB connections, Bluetooth status, OSQuery results) and displaying them on a real-time web dashboard. It uses Redis as a message broker (Pub/Sub for real-time, Lists for potential queuing) and WebSockets to push updates instantly to the dashboard.

## Features

-   **Real-Time Dashboard:** Web interface updates instantly via WebSockets when new events arrive.
-   **Multiple Client Monitors:** Includes various standalone Python clients (`*_client.py`) for monitoring different system aspects (Files, USB, Bluetooth, OSQuery, etc.).
-   **Persistent Logging:** The server logs all received events to `events.log`.
-   **Time Filtering:** View all events or filter events that occurred after a specific time ("Show From Now").
-   **Modular Server:** Server logic is split into dedicated handlers for HTTP requests, WebSocket connections, event management, and HTML templating.

## Project Structure

```plaintext
.
├── dashboard_server_pubsub.py  # <<< MAIN SERVER (Pub/Sub + WebSocket + HTTP)
├── event_manager.py          # <<< Server: Handles event logging/retrieval
├── template_handler.py       # <<< Server: Generates HTML dashboard from template
├── websocket_handler.py      # <<< Server: Manages WebSocket connections & broadcasting
│
├── dashboard.js              # <<< Frontend: WebSocket client & auto-refresh logic
├── index.html                # Frontend: Base HTML structure (used by template_handler)
├── styles.css                # Frontend: Dashboard CSS styling
│
├── file_monitor_client.py    # Client: Monitors file system events (using watchdog)
├── notification_client.py    # Client: Template with multiple task examples (File, USB, CPU, BT)
├── mfile_monitor_client.py   # Client: Similar to notification_client (includes BT monitor)
├── osquery_monitor_client.py # Client: Periodically monitors an OSQuery table
│
├── simple_setup.py           # Utility: Clears Redis queues (monitoring:high/low)
├── dashboard_server_queue.py # Alternative server implementation (polls Redis queues)
├── static/                   # Folder for served static files (created by server)
├── events.log                # Log file for all received events (created by server)
└── README.md                 # This file
```

## Key Server Files

- **dashboard_server_pubsub.py**: The core application. It orchestrates the HTTP server, WebSocket server, and Redis Pub/Sub listener thread.

- **websocket_handler.py**: Manages all WebSocket logic, including client connections and broadcasting refresh messages.

- **event_manager.py**: Handles writing incoming events (with added server timestamp) to events.log and reading/filtering events from the log file.

- **template_handler.py**: Responsible for reading the index.html template and dynamically generating the final HTML page with event data.

- **dashboard.js**: Essential client-side script running in the browser. Connects to the WebSocket server, listens for "refresh" messages, and reloads the page.

## Prerequisites

### Operating System
- Linux recommended (some clients like USB/Bluetooth monitoring rely on Linux tools/libraries like pyudev, dbus).

### Software
- Python 3.x
- Redis Server (running and accessible)
- pip (Python package installer)

### Python Libraries

#### Server Core
```
pip install redis websockets
```

#### Client (choose based on need)
- **File Monitor**: 
  ```
  pip install redis watchdog
  ```

- **USB Monitor** (Linux): 
  ```
  pip install redis pyudev
  ```

- **Bluetooth Monitor** (Linux, may need system dependencies like python3-gi, libdbus-1-dev): 
  ```
  pip install redis dbus-python PyGObject
  ```

- **CPU Monitor**: 
  ```
  pip install redis psutil
  ```

- **OSQuery Monitor** (requires osqueryd running): 
  ```
  pip install redis osquery-python
  ```

## Setup Instructions

1. **Clone Repository**: Get the project files.

2. **Install Dependencies**: Install redis and websockets for the server. Install additional libraries based only on the specific client(s) you intend to run.

3. **Configure Redis**:
   - Edit `REDIS_HOST` / `REDIS_PORT` in `dashboard_server_pubsub.py`.
   - Edit `REDIS_HOST` / `REDIS_PORT` in the specific `*_client.py` file(s) you plan to use, ensuring they match the server configuration.

4. **Ensure Redis is Running**: Start your Redis server instance.

5. **(Optional) Clear Redis Queues**: Run `python simple_setup.py` if you want to clear the monitoring:high and monitoring:low lists in Redis before starting. This does not affect the events.log.

## Running the System

1. **Start the Dashboard Server**:
   ```bash
   python dashboard_server_pubsub.py
   ```
   (Keep this terminal running)

2. **Start a Client**: In a separate terminal, choose and run one client script, e.g.:
   ```bash
   # Example: Start the file monitor
   python file_monitor_client.py
   ```
   (Keep this terminal running)

3. **Access the Dashboard**: Open your web browser to `http://<SERVER_IP>:8000` (e.g., `http://localhost:8000` or `http://10.7.40.88:8000`).
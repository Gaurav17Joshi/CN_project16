# Real-Time Distributed Monitoring System

- Group 16

This project implements a distributed system for monitoring various client-side events (like file changes, USB connections, Bluetooth status, CPU usage, or osquery results) and displaying them on a real-time web dashboard. It utilizes Redis as a message broker for decoupling, buffering (via Lists/Queues), and real-time notifications (via Pub/Sub).

## Features

*   **Distributed Clients:** Multiple client scripts provided for monitoring different system aspects.
*   **Real-Time Dashboard:** Web interface updates instantly when new events arrive using WebSockets.
*   **Persistent Event Logging:** The server logs all received events to `events.log` for historical data.
*   **Time Filtering:** Dashboard allows viewing all events or only events occurring after a specific time ("Show From Now").
*   **Redis Integration:** Uses Redis Lists for potential prioritized queuing (though the primary dashboard server uses Pub/Sub) and Redis Pub/Sub for broadcasting real-time notifications.
*   **Modular Server Design:** Server logic is broken down into handlers for templates, events, and WebSockets.
*   **Example Monitoring Tasks:** Includes clients for File Monitoring (`watchdog`), USB Monitoring (`pyudev`), Bluetooth Monitoring (`dbus`), CPU Monitoring (`psutil`), and periodic OSQuery Table Export (`osquery-python`).

## Architecture Overview

1.  **Clients (`*_client.py`)**: Various client scripts monitor specific system events. Each client runs independently.
    *   When an event occurs, the client formats a JSON message with details (timestamp, priority, event data).
    *   The client sends this message to **two** places in Redis:
        *   **Redis List (Queue):** Pushed onto `monitoring:high` or `monitoring:low` using `LPUSH` for potential reliable, queued processing by other types of consumers (not the primary dashboard server in this setup).
        *   **Redis Pub/Sub Channel:** Published to `monitoring:notifications` using `PUBLISH` for immediate broadcast.
2.  **Redis (Broker)**: Acts as the central message hub.
    *   Stores messages in the `monitoring:high`/`monitoring:low` lists (queues).
    *   Broadcasts messages sent to the `monitoring:notifications` channel to all active subscribers.
3.  **Dashboard Server (`dashboard_server_pubsub.py`)**: The main server component.
    *   **Redis Subscriber:** Listens to the `monitoring:notifications` Pub/Sub channel.
    *   **Event Logger (`event_manager.py`):** Receives messages from the subscriber, adds a server timestamp, and appends the full JSON event to `events.log`.
    *   **WebSocket Server (`websocket_handler.py`):** Manages WebSocket connections with browsers. When a new event is logged, it broadcasts a "refresh" message to all connected browsers.
    *   **HTTP Server (`http.server` + `DashboardHTTPRequestHandler`):** Serves the HTML dashboard (`index.html`, `styles.css`, `dashboard.js`). When requested, it reads `events.log`, applies time filters if specified in the URL, and generates the HTML (`template_handler.py`) to display events.
4.  **Web Browser (Dashboard UI)**:
    *   Loads the HTML, CSS, and JavaScript.
    *   `dashboard.js` establishes a WebSocket connection to the server.
    *   When it receives the "refresh" message via WebSocket, it automatically reloads the page to show the latest events from the log.
    *   Includes fallback timed refresh and connection status indicators.

*(Note: `dashboard_server_queue.py` exists as an alternative server implementation that polls Redis queues instead of using Pub/Sub for its primary event source, but the main setup described uses `dashboard_server_pubsub.py`)*

## File Structure

*   **Client Scripts (`*_client.py`)**:
    *   `file_monitor_client.py`: Monitors file system events (create, delete, modify, move) using `watchdog`.
    *   `notification_client.py`: A generic template containing multiple *commented-out* monitoring tasks (File, USB, CPU, Bluetooth). You need to uncomment *one* task section within this file to use it.
    *   `mfile_monitor_client.py`: *Seems similar to `notification_client.py`, potentially includes Bluetooth.* (Review needed if different).
    *   `osquery_monitor_client.py`: Periodically queries a configured OSQuery table and sends the results.
    *   ***IMPORTANT: You should choose and run only ONE client script at a time per machine/monitoring instance, depending on what you want to monitor.***
*   **Server Scripts**:
    *   `dashboard_server_pubsub.py`: **Main dashboard server.** Uses Redis Pub/Sub for real-time events. (Recommended for use with the WebSockets).
    *   `dashboard_server_queue.py`: Alternative server using Redis Queue polling.
    *   `event_manager.py`: Handles logging events to `events.log` and retrieving them.
    *   `template_handler.py`: Generates the HTML for the dashboard using templates.
    *   `websocket_handler.py`: Manages WebSocket connections and broadcasting.
*   **Frontend Files**:
    *   `index.html`: Basic HTML structure for the dashboard (used by `template_handler.py`).
    *   `styles.css`: CSS for styling the dashboard.
    *   `dashboard.js`: Client-side JavaScript for WebSocket connection and automatic refresh.
*   **Configuration/Utilities**:
    *   `simple_setup.py`: Utility script to clear Redis queues (`monitoring:high`, `monitoring:low`) before starting.
*   **Output Files**:
    *   `events.log`: File where the server stores received event JSON data (created automatically).
    *   `static/`: Folder where static files (`index.html`, `styles.css`, `dashboard.js`) are copied/served from (created automatically by server).
*   **Documentation**:
    *   `README.md`: This file.

## Prerequisites

*   **Python 3.x**
*   **Redis Server:** Running and accessible from both client and server machines.
*   **pip:** Python package installer.
*   **Python Libraries:** Install based on the *client* and *server* you intend to run.
    *   **Server (`dashboard_server_pubsub.py`) Core:**
        ```bash
        pip install redis websockets
        ```
    *   **Client - File Monitoring (`file_monitor_client.py` or `notification_client.py` with File Task):**
        ```bash
        pip install redis watchdog
        ```
    *   **Client - USB Monitoring (`notification_client.py` with USB Task):** (Linux Only)
        ```bash
        pip install redis pyudev
        ```
    *   **Client - Bluetooth Monitoring (`notification_client.py`/`mfile_monitor_client.py` with Bluetooth Task):** (Linux Only, requires DBus setup)
        ```bash
        pip install redis dbus-python PyGObject
        # You might also need system packages like python3-gi, libdbus-1-dev, etc. (check your distro)
        ```
    *   **Client - CPU Monitoring (`notification_client.py` with CPU Task):**
        ```bash
        pip install redis psutil
        ```
    *   **Client - OSQuery Monitoring (`osquery_monitor_client.py`):**
        ```bash
        pip install redis osquery-python
        # Requires an osqueryd agent running on the client machine.
        ```

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```
2.  **Install Dependencies:** Install the core server libraries and the specific libraries needed for the **client script you intend to run** (see Prerequisites above).
3.  **Configure Redis Connection:**
    *   Open the **client script** you chose (e.g., `file_monitor_client.py`).
    *   Modify `REDIS_HOST` and `REDIS_PORT` to match your Redis server details.
    *   Open `dashboard_server_pubsub.py`.
    *   Modify `REDIS_HOST` and `REDIS_PORT` inside it to **match the client's settings**.
4.  **Ensure Redis Server is Running:** Start your Redis server if it's not already running.
5.  **(Optional) Clear Queues:** If you want to start with empty Redis queues (this does *not* affect the `events.log` file), run the setup script:
    ```bash
    python simple_setup.py
    ```

## Running the System

1.  **Start the Dashboard Server:** Open a terminal and run:
    ```bash
    python dashboard_server_pubsub.py
    ```
    Keep this terminal open. It will log connections and events.
2.  **Choose and Start ONE Client:** Open a *separate* terminal. Based on what you want to monitor, choose **one** client script and run it. Examples:
    *   To monitor file creations in the current directory:
        ```bash
        python file_monitor_client.py
    *   To monitor USB connections (Linux):
        ```bash
        # Make sure USBMonitorTask is uncommented inside notification_client.py
        python notification_client.py
        ```
    *   To monitor OSQuery 'users' table:
        ```bash
        # Ensure osqueryd is running
        python osquery_monitor_client.py
        ```
    Keep the client terminal open. It will log detected events and sent notifications.

## Usage

1.  **Access Dashboard:** Open a web browser and navigate to the address shown when starting the server (e.g., `http://<server_ip>:8000` or `http://localhost:8000`).
2.  **Real-Time Updates:** As the running client detects events, the dashboard should automatically refresh (within a fraction of a second) to display the new event at the top.
3.  **Filtering:**
    *   **Show All:** Click this button (or load the page initially) to see all events from the `events.log`.
    *   **Show From Now:** Click this button. The page will reload, showing only events that occurred *after* you clicked the button. The filter time is shown below the buttons.
    *   **Refresh Current View:** Manually trigger a page reload, preserving the current filter (if any).
4.  **Connection Status:** A small indicator at the bottom-right shows the status of the WebSocket connection used for real-time updates.

## Team

*   Gaurav Joshi - 21110065
*   Husain Malwat - 21110117
*   Mitansh Patel - 24120033

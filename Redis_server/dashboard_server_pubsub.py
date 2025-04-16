import json
import time
import redis
import threading
import asyncio
import websockets
import os
import shutil
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

# Import custom modules
from template_handler import TemplateHandler
from event_manager import EventManager
from websocket_handler import start_websocket_server, schedule_broadcast, connected_clients

#-------------------
# CONFIGURATION
#-------------------
# Redis connection settings
REDIS_HOST = '10.7.40.88'  # Match client's Redis host
# REDIS_HOST = 'localhost'  # Use if Redis is local
REDIS_PORT = 6379
REDIS_CHANNEL = 'monitoring:notifications'  # Channel to subscribe to

# Server settings
HTTP_HOST = '0.0.0.0'
HTTP_PORT = 8000
WEBSOCKET_HOST = '0.0.0.0'
WEBSOCKET_PORT = 8001  # Use a different port for WebSockets

# Static folder settings
STATIC_FOLDER = "static"
LOG_FILE = "events.log"

#-------------------
# GLOBAL VARIABLES
#-------------------
# Global variable for the event loop
websocket_loop = None
# The connected_clients set is now imported from websocket_handler

#-------------------
# HTTP SERVER
#-------------------
class DashboardHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.template_handler = TemplateHandler(STATIC_FOLDER)
        self.event_manager = EventManager(LOG_FILE)
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        start_time = time.time()
        parsed_path = urlparse(self.path)
        
        # Handle static file requests
        if parsed_path.path.startswith('/static/'):
            self.serve_static_file(parsed_path.path[8:])  
            return
            
        # Handle other known static files
        if parsed_path.path == '/dashboard.js':
            self.serve_static_file('dashboard.js')
            return
        if parsed_path.path == '/styles.css':
            self.serve_static_file('styles.css')
            return
        
        # Handle the main dashboard request
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            query_params = parse_qs(parsed_path.query)
            
            # Process filtering logic
            show_since_str = query_params.get('show_since', [None])[0]
            show_since_dt = None
            
            if show_since_str:
                try:
                    show_since_str = show_since_str.replace('Z', '+00:00')
                    show_since_dt = datetime.fromisoformat(show_since_str)
                    if show_since_dt.tzinfo is None:
                        show_since_dt = show_since_dt.astimezone(timezone.utc)
                    print(f"Filtering events since: {show_since_dt}")
                except ValueError:
                    print(f"Warning: Invalid 'show_since' timestamp format: {show_since_str}. Showing all events.")
                    show_since_dt = None
            
            # Get filtered events
            events = self.event_manager.get_events(show_since_dt)
            
            # Generate HTML response
            html_content = self.template_handler.render_dashboard(events, show_since_dt)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
            end_time = time.time()
            print(f"HTTP Request processed in {end_time - start_time:.4f} seconds. Displayed {len(events)} events.")
            return
            
        # If path not recognized, return 404
        self.send_error(404)
    
    def serve_static_file(self, filename):
        """Serve a static file from the static folder."""
        file_path = os.path.join(STATIC_FOLDER, filename)
        
        if not os.path.exists(file_path):
            self.send_error(404, f"File not found: {filename}")
            return
            
        # Determine content type based on file extension
        ext = os.path.splitext(filename)[1].lower()
        content_type = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
        }.get(ext, 'application/octet-stream')
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")


#-------------------
# WEBSOCKET SERVER
#-------------------
# Now using the compatibility layer from websocket_handler.py
# This handles different versions of the websockets library


#-------------------
# REDIS SUBSCRIBER
#-------------------
def redis_subscriber():
    """Listens to Redis Pub/Sub and appends messages to the log file."""
    event_manager = EventManager(LOG_FILE)
    
    print(f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT} for Pub/Sub...")
    while True:  # Keep trying to connect
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT,
                socket_connect_timeout=10, socket_timeout=None,
                decode_responses=True
            )
            redis_client.ping()
            print(f"Successfully connected to Redis for Pub/Sub.")
            pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(REDIS_CHANNEL)
            print(f"Subscribed to Redis channel: {REDIS_CHANNEL}")
            print("Waiting for messages to log...")

            for message in pubsub.listen():
                if message['type'] == 'message':
                    json_data = message['data']
                    try:
                        # Parse JSON to get message info for logging
                        parsed_data = json.loads(json_data)
                        event_msg = parsed_data.get('message', 'Unknown message')
                        
                        # Log the event
                        if event_manager.log_event(json_data):
                            print(f"Logged event: {event_msg}")
                            
                            # Trigger WebSocket broadcast for real-time updates
                            schedule_broadcast()
                        else:
                            print(f"Failed to log event: {event_msg}")
                            
                    except json.JSONDecodeError:
                        print(f"Invalid JSON received: {json_data[:200]}...")
                    except Exception as e:
                        print(f"Error processing message: {e} | Data: {json_data[:200]}...")

        except redis.exceptions.ConnectionError as e:
            print(f"Redis connection error in subscriber thread: {e}")
            print("Will attempt to reconnect in 15 seconds...")
            time.sleep(15)
        except Exception as e:
            print(f"Unexpected error in Redis subscriber thread: {e}")
            print("Restarting subscription attempt in 15 seconds...")
            time.sleep(15)


#-------------------
# SERVER SETUP FUNCTIONS
#-------------------
def setup_static_folder():
    """Ensure static folder exists and copy necessary files."""
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    
    # List of static files to copy from current directory
    static_files = {
        'index.html': 'index.html',
        'styles.css': 'styles.css',
        'dashboard.js': 'dashboard.js'
    }
    
    for src, dest in static_files.items():
        src_path = src
        dest_path = os.path.join(STATIC_FOLDER, dest)
        
        # If the file exists in the current directory, copy it to static folder
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dest_path)
                print(f"Copied {src_path} to {dest_path}")
            except Exception as e:
                print(f"Error copying {src_path} to {dest_path}: {e}")
        else:
            print(f"Warning: Static file {src_path} not found in current directory.")
    
    print(f"Static folder setup completed: {STATIC_FOLDER}")

async def start_main_websocket_server():
    """Starts the WebSocket server using the compatibility layer."""
    global websocket_loop
    websocket_loop = asyncio.get_running_loop()
    
    # Use the compatibility layer to start the WebSocket server
    server = await start_websocket_server(
        WEBSOCKET_HOST, 
        WEBSOCKET_PORT,
        websocket_loop
    )
    
    # Keep the server running
    await asyncio.Future()

def start_http_server():
    """Starts the HTTP server in a separate thread."""
    server_address = (HTTP_HOST, HTTP_PORT)
    httpd = HTTPServer(server_address, DashboardHTTPRequestHandler)
    print(f"Starting HTTP server on http://{HTTP_HOST}:{HTTP_PORT}")
    print(f"Serving dashboard, reading events from: {LOG_FILE}")
    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    http_thread.start()
    return httpd, http_thread

async def main_async():
    """Main async function to start all server components."""
    # Set up static files
    setup_static_folder()
    
    # Ensure log file exists
    try:
        Path(LOG_FILE).touch(exist_ok=True)
    except IOError as e:
        print(f"Warning: Could not touch log file '{LOG_FILE}': {e}")

    # Start Redis subscriber in a separate thread
    subscriber_thread = threading.Thread(target=redis_subscriber, daemon=True)
    subscriber_thread.start()

    # Start HTTP server in its own thread
    httpd, http_thread = start_http_server()

    # Start WebSocket server (runs in the current async context)
    websocket_server_task = asyncio.create_task(start_main_websocket_server())

    # Keep main process alive and handle shutdown
    try:
        await websocket_server_task
    except asyncio.CancelledError:
        print("WebSocket server task cancelled.")
    finally:
        print("\nShutting down servers...")
        httpd.shutdown()  # Signal HTTP server to stop
        http_thread.join(timeout=2)  # Wait briefly for HTTP thread
        print("HTTP server stopped.")
        # Subscriber thread is daemon, will exit automatically
        # WebSocket server stops when task is cancelled
        print("All servers shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nCtrl+C detected in main. Exiting.")
    except Exception as e:
        print(f"Unhandled exception in main: {e}")
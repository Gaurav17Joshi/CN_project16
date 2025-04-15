#!/usr/bin/env python
import json
import time
import redis
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Redis connection settings
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
# REDIS_CHANNEL = 'file_events'
REDIS_CHANNEL = 'monitoring:notifications'

# Server settings
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# In-memory storage for events (simple list)
file_events = []

# HTML template for the dashboard - using triple quotes and {{ for table_rows
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>File Monitor Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .refresh-btn {{
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <h1>File Monitor Dashboard</h1>
    <button class="refresh-btn" onclick="window.location.reload()">Refresh</button>
    <table>
        <thead>
            <tr>
                <th>File Name</th>
                <th>Time Added</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    <script>
        // Auto refresh every 10 seconds
        setTimeout(function() {{
            window.location.reload();
        }}, 10000);
    </script>
</body>
</html>
"""

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
        # Generate table rows from events
        table_rows = ""
        for event in file_events:
            # Check if the event has the expected structure
            if 'event_info' in event and 'type' in event['event_info']:
                # Check if it's a file creation event
                if event['event_info']['type'] == 'file_created':
                    if 'file_name' in event['event_info']:
                        file_name = event['event_info']['file_name']
                    elif 'file_path' in event['event_info']:
                        file_name = Path(event['event_info']['file_path']).name
                    else:
                        file_name = "Unknown file"
                
                   # Use 'time' instead of 'timestamp'
                    if 'time' in event:
                        time_str = datetime.fromisoformat(event['time']).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = "Unknown time"
                
                    table_rows += f"<tr><td>{file_name}</td><td>{time_str}</td></tr>"
    
        # Fill in template
        html_content = HTML_TEMPLATE.format(table_rows=table_rows)
    
        self.wfile.write(html_content.encode())

def redis_subscriber():
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        # Subscribe to channel
        pubsub = redis_client.pubsub()
        pubsub.subscribe(REDIS_CHANNEL)
        
        print(f"Subscribed to Redis channel: {REDIS_CHANNEL}")
        
        # Process messages
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    # Parse the message
                    event_data = json.loads(message['data'])
                    
                    # Add to in-memory storage
                    file_events.append(event_data)
                    
                    # Print to console
                    print(f"Event received: {event_data.get('message', 'Unknown message')}")
                    
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON message received")
                except Exception as e:
                    print(f"Error processing message: {e}")
    
    except redis.ConnectionError:
        print(f"Error: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
        print("Make sure Redis is running.")
    except Exception as e:
        print(f"Error in Redis subscriber: {e}")

def main():
    # Start Redis subscriber in a separate thread
    subscriber_thread = threading.Thread(target=redis_subscriber, daemon=True)
    subscriber_thread.start()
    
    # Start HTTP server
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting web dashboard server at http://localhost:{SERVER_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
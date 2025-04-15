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
REDIS_CHANNEL = 'monitoring:notifications'  # Channel to subscribe to

# Server settings
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# In-memory storage for events (simple list)
file_events = []

# HTML template for the dashboard with improved display
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 20px;
        }}
        .controls {{
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
        }}
        .refresh-btn {{
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .event-count {{
            font-size: 16px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
        }}
        .event-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        .event-card {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #4CAF50;
        }}
        .high {{
            border-left-color: #f44336;
        }}
        .medium {{
            border-left-color: #ff9800;
        }}
        .low {{
            border-left-color: #2196F3;
        }}
        .event-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .event-title {{
            font-size: 18px;
            font-weight: bold;
        }}
        .event-time {{
            color: #666;
        }}
        .event-body {{
            display: grid;
            grid-template-columns: 150px auto;
            row-gap: 8px;
            margin-bottom: 15px;
        }}
        .field-name {{
            font-weight: bold;
            color: #555;
        }}
        .field-value {{
            word-break: break-word;
        }}
        .event-info {{
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .event-info-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 120px auto;
            row-gap: 5px;
        }}
        .no-events {{
            text-align: center;
            padding: 40px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #666;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <h1>Monitoring Dashboard</h1>
    
    <div class="controls">
        <button class="refresh-btn" onclick="window.location.reload()">Refresh Now</button>
        <div class="event-count">{event_count} Event(s) Received</div>
    </div>
    
    {event_cards}
    
    <script>
        // Auto refresh every 10 seconds
        setTimeout(function() {{
            window.location.reload();
        }}, 10000);
    </script>
</body>
</html>
"""

# Template for each event card
EVENT_CARD_TEMPLATE = """
<div class="event-card {priority}">
    <div class="event-header">
        <div class="event-title">{message}</div>
        <div class="event-time">{time}</div>
    </div>
    <div class="event-body">
        <div class="field-name">Client Name:</div>
        <div class="field-value">{client_name}</div>
        
        <div class="field-name">Client ID:</div>
        <div class="field-value">{client_id}</div>
        
        <div class="field-name">Priority:</div>
        <div class="field-value">{priority}</div>
    </div>
    
    <div class="event-info">
        <div class="event-info-title">Event Details:</div>
        <div class="info-grid">
            {event_info_rows}
        </div>
    </div>
</div>
"""

class ImprovedHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Generate event cards
        event_cards = ""
        
        if not file_events:
            event_cards = '<div class="no-events">No events have been received yet</div>'
        else:
            # Sort events with newest first
            sorted_events = sorted(file_events, key=lambda x: x.get('time', ''), reverse=True)
            
            for event in sorted_events:
                # Format the time
                if 'time' in event:
                    try:
                        time_obj = datetime.fromisoformat(event['time'])
                        formatted_time = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        formatted_time = event['time']
                else:
                    formatted_time = "Unknown time"
                
                # Generate event info rows
                event_info_rows = ""
                event_info = event.get('event_info', {})
                
                if isinstance(event_info, dict):
                    for key, value in event_info.items():
                        event_info_rows += f'<div class="field-name">{key}:</div>'
                        event_info_rows += f'<div class="field-value">{value}</div>'
                else:
                    event_info_rows = f'<div class="field-value">{str(event_info)}</div>'
                
                # Create event card
                card = EVENT_CARD_TEMPLATE.format(
                    priority=event.get('priority', 'unknown').lower(),
                    message=event.get('message', 'Unknown event'),
                    time=formatted_time,
                    client_name=event.get('client_name', 'Unknown client'),
                    client_id=event.get('client_id', 'Unknown ID'),
                    event_info_rows=event_info_rows
                )
                
                event_cards += card
        
        # Fill in the main template
        html_content = HTML_TEMPLATE.format(
            event_count=len(file_events),
            event_cards=event_cards
        )
        
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
                    
                    # Debug: Print the full JSON message
                    print("\n----- RECEIVED JSON MESSAGE -----")
                    print(json.dumps(event_data, indent=2))
                    print("---------------------------------\n")
                    
                    # Add to in-memory storage
                    file_events.append(event_data)
                    
                    # Print simplified message to console
                    event_type = event_data.get('event_info', {}).get('type', 'unknown')
                    event_message = event_data.get('message', 'No message')
                    print(f"Event received: {event_type} - {event_message}")
                    
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
    httpd = HTTPServer(server_address, ImprovedHTTPRequestHandler)
    print(f"Starting web dashboard server at http://localhost:{SERVER_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()

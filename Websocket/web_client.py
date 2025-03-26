import asyncio
import websockets
import json
import os
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import time

# Global variables
WEB_SERVER_PORT = 8000
JSON_DIRECTORY = "json_data"
LATEST_JSON_FILE = "latest.json"

# Ensure the JSON directory exists
os.makedirs(JSON_DIRECTORY, exist_ok=True)

# Handler for the HTTP server
class JSONHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return SimpleHTTPRequestHandler.do_GET(self)

# Function to start the web server
def start_web_server():
    print(f"Starting web server on port {WEB_SERVER_PORT}...")
    try:
        # Create a simple HTTP server
        httpd = socketserver.TCPServer(("", WEB_SERVER_PORT), JSONHandler)
        print(f"Web server started at http://localhost:{WEB_SERVER_PORT}")
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Web server already running on port {WEB_SERVER_PORT}")
        else:
            print(f"Error starting web server: {e}")

# Create HTML file for JSON visualization
def create_html_file():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JSON Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        #json-display {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
            white-space: pre-wrap;
            overflow: auto;
        }
        .refresh-button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-bottom: 15px;
        }
        .refresh-button:hover {
            background-color: #45a049;
        }
        .timestamp {
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }
        .collapsible {
            background-color: #777;
            color: white;
            cursor: pointer;
            padding: 18px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
        }
        .active, .collapsible:hover {
            background-color: #555;
        }
        .content {
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f1f1f1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>OSquery Client Viewer</h1>
        <button class="refresh-button" onclick="refreshData()">Refresh Data</button>
        <div class="timestamp" id="timestamp"></div>
        
        <button type="button" class="collapsible">JSON Data (Click to expand/collapse)</button>
        <div class="content">
            <pre id="json-display">Loading JSON data...</pre>
        </div>
    </div>

    <script>
        // Function to fetch and display JSON data
        function fetchAndDisplayJSON() {
            fetch('/json_data/latest.json?' + new Date().getTime())
                .then(response => response.json())
                .then(data => {
                    document.getElementById('json-display').textContent = JSON.stringify(data, null, 2);
                    document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleString();
                })
                .catch(error => {
                    document.getElementById('json-display').textContent = 'Error loading JSON: ' + error;
                });
        }

        // Function to refresh data
        function refreshData() {
            fetchAndDisplayJSON();
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            fetchAndDisplayJSON();
            
            // Set up collapsible behavior
            var coll = document.getElementsByClassName("collapsible");
            for (var i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.display === "block") {
                        content.style.display = "none";
                    } else {
                        content.style.display = "block";
                    }
                });
            }
            
            // Open the collapsible by default
            document.getElementsByClassName("collapsible")[0].click();
        });
    </script>
</body>
</html>
"""
    with open("index.html", "w") as f:
        f.write(html_content)


# Function to open the browser
def open_browser():
    webbrowser.open(f"http://localhost:{WEB_SERVER_PORT}")

# WebSocket client function
async def chat_client():
    url = "ws://10.240.2.209:7890"  # Update this with your server address
    async with websockets.connect(url) as websocket:
        print("Connected to the chat server!")

        try:
            while True:
                # Get input from client-side user
                print("\nEnter your message or type 'exit' to disconnect:")
                message = input("You (Client): ")
                await websocket.send(message)
                
                # Exit if client sends "exit"
                if message.lower() == "exit":
                    print("You disconnected.")
                    break

                # Wait for a response from the server
                response = await websocket.recv()
                
                # Check if the response is a JSON string
                try:
                    json_response = json.loads(response)
                    if isinstance(json_response, dict) and "type" in json_response:
                        if json_response["type"] == "json_file":
                            print(f"\nReceived JSON file: {json_response['filename']}")
                            
                            # Save the JSON to the latest file
                            json_path = os.path.join(JSON_DIRECTORY, LATEST_JSON_FILE)
                            with open(json_path, 'w') as json_file:
                                json.dump(json_response['data'], json_file, indent=2)
                            
                            print(f"JSON saved to {json_path}")
                            print(f"View the JSON in your browser at http://localhost:{WEB_SERVER_PORT}")
                            
                            # Open the browser
                            open_browser()
                        else:
                            print(f"Server: {response}")
                    else:
                        print(f"Server: {response}")
                except json.JSONDecodeError:
                    print(f"Server: {response}")
                
                # Exit if server sends "exit"
                if response.lower() == "exit":
                    print("Server disconnected.")
                    break

        except websockets.ConnectionClosedError:
            print("Connection closed.")

# Main function to run all components
async def main():
    # Create the HTML file
    create_html_file()
    
    # Start the web server in a separate thread
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(1)
    
    # Start the WebSocket client
    await chat_client()

# Start the main program
if __name__ == "__main__":
    asyncio.run(main())
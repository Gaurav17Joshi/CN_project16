from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import json
import os

PORT = 8001
current_json_data = None
client_connected = False
lock = threading.Lock()

class SSEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global client_connected
        if self.path == '/events':
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            print("Client connected for SSE.")
            client_connected = True  # Signal that a client has connected
            try:
                while True:
                    with lock:
                        data = current_json_data
                    if data is not None:
                        sse_message = f"data: {data}\n\n"
                        self.wfile.write(sse_message.encode())
                        self.wfile.flush()
                        print("Sent JSON data to client.")
                    else:
                        print("No JSON data available to send.")
                    time.sleep(10)  # Wait 10 seconds between sends
            except Exception as e:
                print("Client disconnected or error:", e)
        else:
            self.send_response(404)
            self.end_headers()

def update_json_data():
    global current_json_data
    # Wait until a client connects
    print("Waiting for a client to connect before asking for JSON file path...")
    while not client_connected:
        time.sleep(1)
    # Once a client is connected, prompt for the JSON file path
    file_path = input("Client connected. Enter path of JSON file to send: ").strip()
    if not os.path.exists(file_path):
        print("File does not exist. Exiting updater.")
        return
    while True:
        try:
            with open(file_path, 'r') as f:
                json_content = json.load(f)
            json_str = json.dumps(json_content)
            with lock:
                current_json_data = json_str
            print("Updated JSON data from file.")
        except Exception as e:
            print("Error reading JSON file:", e)
        time.sleep(10)  # Update file every 10 seconds

def run_server():
    server = HTTPServer(('localhost', PORT), SSEHandler)
    print(f"SSE server running on http://localhost:{PORT}")
    server.serve_forever()

if __name__ == '__main__':
    updater_thread = threading.Thread(target=update_json_data, daemon=True)
    updater_thread.start()
    run_server()

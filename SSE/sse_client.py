import requests
import os
import json

SSE_URL = "http://localhost:8001/events"
RECEIVED_DIR = "received"
LATEST_FILE = "latest.json"

def sse_client():
    os.makedirs(RECEIVED_DIR, exist_ok=True)
    latest_path = os.path.join(RECEIVED_DIR, LATEST_FILE)
    headers = {'Cache-Control': 'no-cache'}
    
    print("Connecting to SSE server at", SSE_URL)
    try:
        with requests.get(SSE_URL, stream=True, headers=headers) as response:
            if response.status_code != 200:
                print("Failed to connect to SSE server. Status code:", response.status_code)
                return
            print("Connected to SSE server. Listening for events...")
            buffer = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data:"):
                        buffer += line[5:].strip()  # Remove the "data:" prefix
                else:
                    # Empty line indicates the end of an event
                    if buffer:
                        try:
                            data = json.loads(buffer)
                            with open(latest_path, "w") as f:
                                json.dump(data, f, indent=2)
                            print("Updated", latest_path, "with new JSON data.")
                        except Exception as e:
                            print("Error processing JSON:", e)
                        buffer = ""
    except Exception as e:
        print("Error connecting or reading from SSE server:", e)

if __name__ == '__main__':
    sse_client()

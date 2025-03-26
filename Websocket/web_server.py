import asyncio
import websockets
import json
import os

"""
To run this server, first check your ip:-
Run: ipconfig, then check en0 and inet
"""

# Function to handle communication with a client
async def chat_handler(websocket):
    print("Client connected!")
    
    try:
        while True:
            # Wait for a message from the client
            message = await websocket.recv()
            print(f"Client: {message}")

            # Exit if client sends "exit"
            if message.lower() == "exit":
                print("Client disconnected.")
                await websocket.close()
                break

            # Get input from server-side user
            print("\nOptions:")
            print("1. Send a text message")
            print("2. Send a JSON file")
            print("3. Exit")
            choice = input("Choose an option (1-3): ")

            if choice == "1":
                # Send a regular text message
                response = input("You (Server): ")
                await websocket.send(response)
                
                # Exit if server sends "exit"
                if response.lower() == "exit":
                    print("Server disconnected.")
                    await websocket.close()
                    break
                    
            elif choice == "2":
                # Send a JSON file
                file_path = input("Enter the path to the JSON file: ")
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as file:
                            try:
                                json_data = json.load(file)
                                # Create a message with type indicator
                                message = {
                                    "type": "json_file",
                                    "filename": os.path.basename(file_path),
                                    "data": json_data
                                }
                                await websocket.send(json.dumps(message))
                                print(f"JSON file '{os.path.basename(file_path)}' sent successfully.")
                                print("The client will display this JSON in a web browser.")
                            except json.JSONDecodeError:
                                print("Error: The file is not a valid JSON file.")
                                await websocket.send("Error: Could not process JSON file.")
                    else:
                        print("Error: File not found.")
                        await websocket.send("Error: File not found.")
                except Exception as e:
                    print(f"Error sending JSON file: {e}")
                    await websocket.send(f"Error sending JSON file: {str(e)}")
                    
            elif choice == "3":
                await websocket.send("exit")
                print("Server disconnected.")
                await websocket.close()
                break
            else:
                print("Invalid option. Please try again.")
                await websocket.send("Server: Invalid option selected.")

    except websockets.ConnectionClosedError:
        print("Connection closed.")

# Start WebSocket server
async def main():
    # Update this with your IP address
    server_ip = "10.240.2.209"
    server_port = 7890
    
    async with websockets.serve(chat_handler, server_ip, server_port):
        print(f"WebSocket Chat Server started on ws://{server_ip}:{server_port}")
        await asyncio.Future()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())
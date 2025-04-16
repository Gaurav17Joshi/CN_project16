#!/usr/bin/env python
import asyncio
import websockets
import inspect

# Dictionary of connected clients
connected_clients = set()

# Reference to the event loop for scheduling broadcasts
websocket_loop = None

async def handle_websocket(websocket, *args, **kwargs):
    """
    Universal WebSocket handler that adapts to different versions of the websockets library.
    
    Works with both:
    - Newer API: async def handler(websocket)
    - Older API: async def handler(websocket, path)
    """
    global connected_clients
    
    client_addr = getattr(websocket, 'remote_address', 'unknown')
    print(f"WebSocket client connected: {client_addr}")
    
    # Add to connected clients
    connected_clients.add(websocket)
    
    try:
        # Keep the connection open
        if hasattr(websocket, 'wait_closed'):
            # Newer versions of websockets
            await websocket.wait_closed()
        else:
            # Older versions - keep connection open with ping/pong
            while True:
                # Wait for the client to close the connection
                message = await websocket.recv()
                if message == "ping":
                    await websocket.send("pong")
                await asyncio.sleep(1)
    
    except websockets.exceptions.ConnectionClosedOK:
        print(f"WebSocket client connection closed normally: {client_addr}")
    except websockets.exceptions.ConnectionClosedError:
        print(f"WebSocket client connection closed abnormally: {client_addr}")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"WebSocket client disconnected: {client_addr}")

async def broadcast_message(message="refresh"):
    """
    Broadcast a message to all connected WebSocket clients.
    
    Args:
        message: The message to broadcast, defaults to "refresh"
    """
    if not connected_clients:
        print("No connected clients to broadcast to")
        return
        
    print(f"Broadcasting '{message}' to {len(connected_clients)} clients...")
    
    # Create tasks for sending to each client concurrently
    tasks = []
    failed_clients = []
    
    for client in list(connected_clients):
        try:
            tasks.append(client.send(message))
        except Exception as e:
            print(f"Error preparing to send to client: {e}")
            failed_clients.append(client)
    
    # Remove clients that failed during task preparation
    for failed in failed_clients:
        if failed in connected_clients:
            connected_clients.remove(failed)
    
    if not tasks:
        print("No messages were sent - all clients may be disconnected")
        return
        
    # Gather all sends
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for any errors during sending
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            try:
                # Get the client that caused the error
                client = list(connected_clients)[i]
                print(f"Failed to send to client: {result}")
                connected_clients.remove(client)
            except (IndexError, ValueError) as e:
                print(f"Error tracking failed client: {e}")

def schedule_broadcast(message="refresh"):
    """
    Schedule a broadcast on the event loop.
    
    Args:
        message: Message to broadcast, defaults to "refresh"
    """
    global websocket_loop
    
    if websocket_loop and websocket_loop.is_running():
        try:
            # Schedule the coroutine on the event loop
            future = asyncio.run_coroutine_threadsafe(
                broadcast_message(message), 
                websocket_loop
            )
            # Optionally wait for the result with a timeout
            # result = future.result(timeout=1)
        except Exception as e:
            print(f"Error scheduling broadcast: {e}")
    else:
        print("WebSocket loop not running, cannot schedule broadcast")

async def start_websocket_server(host, port, loop=None):
    """
    Start the WebSocket server with compatibility for different websockets versions.
    
    Args:
        host: Hostname to bind to
        port: Port to listen on
        loop: Optional event loop to use
    
    Returns:
        The WebSocket server object
    """
    global websocket_loop
    
    # Store the event loop for later use
    websocket_loop = loop or asyncio.get_running_loop()
    
    print(f"Starting WebSocket server on ws://{host}:{port}")
    
    # Check the WebSocket serve function signature to determine version
    sig = inspect.signature(websockets.serve)
    
    try:
        if len(sig.parameters) >= 3:
            # Newer websockets library
            server = await websockets.serve(handle_websocket, host, port)
        else:
            # Fallback for older versions
            server = await websockets.serve(
                lambda ws, path: handle_websocket(ws), 
                host, 
                port
            )
        
        print(f"WebSocket server started successfully on ws://{host}:{port}")
        return server
    except Exception as e:
        print(f"Failed to start WebSocket server: {e}")
        raise
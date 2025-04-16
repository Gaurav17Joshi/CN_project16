#!/usr/bin/env python
import json
import time
import os
import redis
import socket
import uuid
import threading
from datetime import datetime

#############################################################
# REDIS CONNECTION SETTINGS - DO NOT CHANGE UNLESS NEEDED
#############################################################
REDIS_HOST = '10.7.40.88'  # Remote Redis server IP
REDIS_PORT = 6379
HIGH_PRIORITY_QUEUE = 'monitoring:high'
LOW_PRIORITY_QUEUE = 'monitoring:low'

#############################################################
# CLIENT CUSTOMIZATION - CHANGE THESE SETTINGS
#############################################################
CLIENT_NAME = "MonitorClient-1"  # Change this to identify your client

#############################################################
# MONITORING TASK - REPLACE THIS WITH YOUR OWN MONITORING CODE
#############################################################

# EXAMPLE 1: FILE MONITORING IMPLEMENTATION

# To implement file monitoring, uncomment this code and install watchdog:

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileMonitorTask:
    def __init__(self, send_notification_callback):
        self.send_notification = send_notification_callback
        self.path_to_monitor = "."  # Change this to the directory you want to monitor
        
    def start(self):
        print(f"Starting file monitoring in {self.path_to_monitor}")
        event_handler = self.FileEventHandler(self.send_notification)
        observer = Observer()
        observer.schedule(event_handler, self.path_to_monitor, recursive=True)
        observer.start()
        return observer  # Return the observer so it can be stopped later
        
    class FileEventHandler(FileSystemEventHandler):
        def __init__(self, send_notification_callback):
            self.send_notification = send_notification_callback
            
        def on_created(self, event):
            if not event.is_directory:
                file_path = event.src_path
                file_name = os.path.basename(file_path)
                
                # Send high priority notification for new files
                self.send_notification(
                    priority="high",
                    message=f"New file detected: {file_name}",
                    event_info={
                        "type": "file_created",
                        "file_path": file_path,
                        "file_name": file_name
                    }
                )


# EXAMPLE 2: USB DEVICE MONITORING (Linux)
"""
# To implement USB monitoring on Linux, uncomment this code and install pyudev:
# pip install pyudev

import pyudev

class USBMonitorTask:
    def __init__(self, send_notification_callback):
        self.send_notification = send_notification_callback
        
    def start(self):
        print("Starting USB device monitoring")
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        
        # Create a thread to monitor USB events
        def monitor_usb_events():
            for device in iter(monitor.poll, None):
                if device.action == 'add':
                    # USB device connected
                    self.send_notification(
                        priority="high",
                        message=f"USB device connected: {device.get('ID_MODEL', 'Unknown device')}",
                        event_info={
                            "type": "usb_connected",
                            "vendor": device.get('ID_VENDOR', 'Unknown'),
                            "model": device.get('ID_MODEL', 'Unknown'),
                            "serial": device.get('ID_SERIAL_SHORT', 'Unknown')
                        }
                    )
                elif device.action == 'remove':
                    # USB device disconnected
                    self.send_notification(
                        priority="medium",
                        message=f"USB device disconnected: {device.get('ID_MODEL', 'Unknown device')}",
                        event_info={
                            "type": "usb_disconnected",
                            "vendor": device.get('ID_VENDOR', 'Unknown'),
                            "model": device.get('ID_MODEL', 'Unknown'),
                            "serial": device.get('ID_SERIAL_SHORT', 'Unknown')
                        }
                    )
        
        # Start the monitoring thread
        usb_thread = threading.Thread(target=monitor_usb_events, daemon=True)
        usb_thread.start()
        return usb_thread  # Return the thread so it can be joined later
"""

# EXAMPLE 3: CPU USAGE MONITORING
"""
# To implement CPU usage monitoring, uncomment this code and install psutil:
# pip install psutil

import psutil
import time

class CPUMonitorTask:
    def __init__(self, send_notification_callback):
        self.send_notification = send_notification_callback
        self.threshold = 80  # CPU usage percentage threshold for high priority alerts
        self.check_interval = 5  # Seconds between checks
        
    def start(self):
        print(f"Starting CPU usage monitoring (threshold: {self.threshold}%)")
        
        # Create a thread to monitor CPU
        def monitor_cpu():
            while True:
                cpu_percent = psutil.cpu_percent(interval=self.check_interval)
                
                # Determine priority based on CPU usage
                if cpu_percent >= self.threshold:
                    priority = "high"
                    message = f"High CPU usage detected: {cpu_percent}%"
                else:
                    priority = "low"
                    message = f"Current CPU usage: {cpu_percent}%"
                
                # Send notification
                self.send_notification(
                    priority=priority,
                    message=message,
                    event_info={
                        "type": "cpu_usage",
                        "usage_percent": cpu_percent,
                        "threshold": self.threshold,
                        "memory_usage": psutil.virtual_memory().percent
                    }
                )
                
                # Short sleep to prevent sending too many messages
                time.sleep(self.check_interval)
        
        # Start the monitoring thread
        cpu_thread = threading.Thread(target=monitor_cpu, daemon=True)
        cpu_thread.start()
        return cpu_thread  # Return the thread so it can be joined later
"""

# IMPLEMENT YOUR CUSTOM MONITORING TASK HERE
# Delete the examples above and implement your own monitoring logic
# Your class should have:
# 1. An __init__ method that takes a send_notification_callback parameter
# 2. A start method that begins monitoring and returns a thread or observer

class CustomMonitorTask:
    def __init__(self, send_notification_callback):
        self.send_notification = send_notification_callback
        
    def start(self):
        print("Starting custom monitoring")
        
        # Create a thread for your monitoring task
        def monitor_task():
            # This is just a placeholder example - replace with your monitoring code
            while True:
                # Example: Send a test notification every 10 seconds
                self.send_notification(
                    priority="high",
                    message="Test notification from custom monitor",
                    event_info={
                        "type": "test_event",
                        "details": "This is a placeholder. Replace with your monitoring code."
                    }
                )
                time.sleep(10)
        
        # Start the monitoring thread
        task_thread = threading.Thread(target=monitor_task, daemon=True)
        task_thread.start()
        return task_thread

#############################################################
# MESSAGE HANDLING - TYPICALLY NO NEED TO MODIFY BELOW
#############################################################

class NotificationClient:
    def __init__(self):
        self.client_id = f"{CLIENT_NAME}-{str(uuid.uuid4())[:8]}"
        
        # Connect to Redis
        print(f"Connecting to Redis server at {REDIS_HOST}:{REDIS_PORT}...")
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=True
        )
        
        # Test connection
        self.redis_client.ping()
        print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        
        # Send startup message
        self.send_notification(
            priority="low",
            message=f"{CLIENT_NAME} started monitoring",
            event_info={
                "type": "monitor_started",
                "hostname": socket.gethostname()
            }
        )
    
    def send_notification(self, priority, message, event_info):
        """Send a notification to the Redis server with the specified priority."""
        try:
            # Create the notification JSON with the required structure
            notification = {
                "client_name": CLIENT_NAME,
                "client_id": self.client_id,
                "time": datetime.now().isoformat(timespec='milliseconds'),
                "priority": priority,
                "message": message,
                "event_info": event_info
            }
            
            # Convert to JSON
            json_data = json.dumps(notification)

            print("\n----- SENDING JSON MESSAGE -----")
            print(json.dumps(notification, indent=2))  
            print("-------------------------------\n")
            
            # Determine queue based on priority
            if priority.lower() in ["high", "medium"]:
                queue = HIGH_PRIORITY_QUEUE
            else:
                queue = LOW_PRIORITY_QUEUE
            
            # Send to Redis
            self.redis_client.lpush(queue, json_data)
            
            # Also publish for real-time notifications
            self.redis_client.publish('monitoring:notifications', json_data)
            
            print(f"Sent {priority} priority notification: {message}")
            
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def start_monitoring(self):
        """Start the monitoring task."""
        try:
            # Create the monitoring task with the notification callback
            # task = CustomMonitorTask(self.send_notification)
            task = FileMonitorTask(self.send_notification)  
            
            # Start the task
            monitor_handle = task.start()
            
            # Keep the main thread alive until Ctrl+C
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                
                # Send shutdown message
                self.send_notification(
                    priority="low",
                    message=f"{CLIENT_NAME} stopped monitoring",
                    event_info={
                        "type": "monitor_stopped",
                        "hostname": socket.gethostname()
                    }
                )
                
                print("Monitoring stopped.")
                
        except Exception as e:
            print(f"Error in monitoring task: {e}")
            sys.exit(1)

#############################################################
# HOW TO CUSTOMIZE THIS MONITORING CLIENT
#############################################################
#
# This template provides a flexible framework for building different
# monitoring tools that all share the same notification system.
#
# TO CUSTOMIZE:
#
# 1. Change CLIENT_NAME at the top to identify your monitoring instance
#
# 2. IMPORTANT: Choose one of the example monitoring tasks OR create your own:
#    - Uncomment ONE of the example classes (FileMonitorTask, USBMonitorTask, etc.)
#    - OR replace the CustomMonitorTask class with your own implementation
#    - Make sure to install any required packages (watchdog, pyudev, psutil, etc.)
#
# 3. Find and replace CustomMonitorTask in the start_monitoring method with your chosen task
#
# 4. Inside your monitoring task, use the send_notification method to send alerts:
#    self.send_notification(
#        priority="high",  # Use "high", "medium", or "low"
#        message="Your alert message here",
#        event_info={
#            "type": "event_type_name",
#            # Add any other relevant information as key-value pairs
#        }
#    )
#
# 5. High and medium priority messages go to the HIGH_PRIORITY_QUEUE
#    Low priority messages go to the LOW_PRIORITY_QUEUE
#
#############################################################

def main():
    """Main function to run the notification client."""
    try:
        client = NotificationClient()
        client.start_monitoring()
    except redis.ConnectionError:
        print(f"Error: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
        print("Please check:")
        print("1. The Redis server is running at that IP")
        print("2. There are no firewall issues blocking the connection")
        print("3. The Redis server is configured to accept remote connections")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
#!/usr/bin/env python
import json
import time
import os
import redis
import socket
import uuid
import threading
from datetime import datetime
import osquery

#############################################################
# REDIS CONNECTION SETTINGS - DO NOT CHANGE UNLESS NEEDED
#############################################################
REDIS_HOST = 'localhost'  # Remote Redis server IP (or brokers ip)
REDIS_PORT = 6379
HIGH_PRIORITY_QUEUE = 'monitoring:high'
LOW_PRIORITY_QUEUE = 'monitoring:low'

#############################################################
# CLIENT CUSTOMIZATION - CHANGE THESE SETTINGS
#############################################################
CLIENT_NAME = "OSQueryTableMonitor"  # Change this to identify your client

#############################################################
# OSQUERY TABLE CONFIGURATION - CUSTOMIZE THESE SETTINGS
#############################################################
# Table to monitor
TABLE_NAME = "users"

# Columns to select from the table
TABLE_COLUMNS = ["uid", "gid", "username", "description"]

# Row limit
ROW_LIMIT = 5

# Optional WHERE clause (leave empty for no filter)
WHERE_CLAUSE = ""  # Example: "uid > 500"

# Optional ORDER BY clause (leave empty for default order)
ORDER_BY = "uid"  # Example: "uid DESC"

# Monitoring interval in seconds
MONITORING_INTERVAL = 15

#############################################################
# OSQUERY MONITORING TASK - MODIFY AS NEEDED
#############################################################

class OSQueryMonitorTask:
    def __init__(self, send_notification_callback):
        self.send_notification = send_notification_callback
        self.instance = None
    
    def start(self):
        # Build the query
        columns_str = ", ".join(TABLE_COLUMNS)
        query = f"SELECT {columns_str} FROM {TABLE_NAME}"
        
        if WHERE_CLAUSE:
            query += f" WHERE {WHERE_CLAUSE}"
        
        if ORDER_BY:
            query += f" ORDER BY {ORDER_BY}"
        
        if ROW_LIMIT > 0:
            query += f" LIMIT {ROW_LIMIT}"
        
        self.query = query
        
        print(f"Starting OSQuery monitoring for table: {TABLE_NAME}")
        print(f"Query: {self.query}")
        print(f"Interval: {MONITORING_INTERVAL} seconds")
        
        # Create OSQuery instance
        try:
            self.instance = osquery.SpawnInstance()
            self.instance.open()
            print("OSQuery instance started successfully")
        except Exception as e:
            print(f"Error starting OSQuery: {e}")
            self.send_notification(
                priority="high",
                message=f"OSQuery initialization error: {str(e)}",
                event_info={
                    "type": "osquery_error",
                    "error": str(e)
                }
            )
            return None
        
        # Create a thread for the monitoring task
        def monitor_osquery():
            cycle_count = 0
            
            while True:
                cycle_count += 1
                start_time = time.time()
                
                try:
                    # Execute the table query
                    self._query_table(cycle_count)
                        
                except Exception as e:
                    self.send_notification(
                        priority="medium",
                        message=f"Error during OSQuery monitoring cycle: {str(e)}",
                        event_info={
                            "type": "monitoring_error",
                            "error": str(e),
                            "cycle": cycle_count
                        }
                    )
                
                # Calculate sleep time to maintain the interval
                elapsed = time.time() - start_time
                sleep_time = max(0.1, MONITORING_INTERVAL - elapsed)
                
                print(f"Cycle {cycle_count} completed in {elapsed:.2f}s, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        # Start the monitoring thread
        osquery_thread = threading.Thread(target=monitor_osquery, daemon=True)
        osquery_thread.start()
        return osquery_thread
    
    def _query_table(self, cycle_count):
        """Query the specified table and send results as a notification."""
        try:
            # Execute the query
            start_time = time.time()
            result = self.instance.client.query(self.query)
            query_time = time.time() - start_time
            
            if result.status.code != 0:
                raise Exception(f"Query failed: {result.status.message}")
            
            # Process the results
            rows = result.response
            row_count = len(rows)
            
            # Prepare the event info
            event_info = {
                "type": "osquery_table_data",
                "table": TABLE_NAME,
                "columns": TABLE_COLUMNS,
                "query": self.query,
                "row_count": row_count,
                "query_time_ms": round(query_time * 1000, 2),
                "cycle": cycle_count,
                "data": rows
            }
            
            # Send the notification
            self.send_notification(
                priority="low",
                message=f"OSQuery {TABLE_NAME} - {row_count} rows",
                event_info=event_info
            )
            
        except Exception as e:
            self.send_notification(
                priority="medium",
                message=f"Error querying OSQuery table {TABLE_NAME}: {str(e)}",
                event_info={
                    "type": "osquery_error",
                    "table": TABLE_NAME,
                    "query": self.query,
                    "error": str(e),
                    "cycle": cycle_count
                }
            )

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
            message=f"{CLIENT_NAME} started monitoring table: {TABLE_NAME}",
            event_info={
                "type": "monitor_started",
                "hostname": socket.gethostname(),
                "table": TABLE_NAME,
                "columns": TABLE_COLUMNS,
                "interval_seconds": MONITORING_INTERVAL
            }
        )
    
    def send_notification(self, priority, message, event_info):
        """Send a notification to the Redis server with the specified priority."""
        try:
            # Create the notification JSON with the required structure
            notification = {
                "client_name": CLIENT_NAME,
                "client_id": self.client_id,
                "time": datetime.now().isoformat(),
                "priority": priority,
                "message": message,
                "event_info": event_info
            }
            
            # Convert to JSON
            json_data = json.dumps(notification)
            
            # Debug: Print the message info
            if priority != "low" or event_info.get("type") != "osquery_table_data":
                # Don't print low priority table data (too verbose)
                print("\n----- SENDING JSON MESSAGE -----")
                # Create a copy to modify for display
                debug_notification = notification.copy()
                if "data" in debug_notification.get("event_info", {}):
                    # Replace data with count for display purposes
                    debug_notification["event_info"]["data"] = f"[{len(debug_notification['event_info']['data'])} rows]"
                print(json.dumps(debug_notification, indent=2))
                print("-------------------------------\n")
            else:
                # For table data, print a simplified version
                print(f"Sending {TABLE_NAME} data: {len(event_info.get('data', [])) or 0} rows")
                
                # Print a sample of the data (first row only)
                if event_info.get('data') and len(event_info['data']) > 0:
                    print("Sample row:")
                    print(json.dumps(event_info['data'][0], indent=2))
            
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
            # Create the OSQuery monitoring task
            task = OSQueryMonitorTask(self.send_notification)
            
            # Start the task
            monitor_handle = task.start()
            
            if monitor_handle is None:
                print("Failed to start monitoring task. Exiting.")
                return
            
            # Keep the main thread alive until Ctrl+C
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                
                # Send shutdown message
                self.send_notification(
                    priority="low",
                    message=f"{CLIENT_NAME} stopped monitoring table: {TABLE_NAME}",
                    event_info={
                        "type": "monitor_stopped",
                        "hostname": socket.gethostname(),
                        "table": TABLE_NAME
                    }
                )
                
                print("Monitoring stopped.")
                
        except Exception as e:
            print(f"Error in monitoring task: {e}")
            import sys
            sys.exit(1)

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
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
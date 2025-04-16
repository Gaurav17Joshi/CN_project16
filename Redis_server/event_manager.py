#!/usr/bin/env python
import json
from datetime import datetime, timezone
import os
from pathlib import Path

class EventManager:
    """Manages event logging and retrieval."""
    
    def __init__(self, log_file="events.log"):
        """Initialize with path to the log file."""
        self.log_file = log_file
        
        # Ensure log file exists
        try:
            Path(log_file).touch(exist_ok=True)
        except IOError as e:
            print(f"Warning: Could not touch log file '{log_file}': {e}")
    
    def log_event(self, event_data):
        """Log an event to the log file."""
        try:
            # Add server timestamp to the event
            if isinstance(event_data, str):
                # Parse the JSON string
                event_dict = json.loads(event_data)
                # Add server timestamp
                event_dict['server_time'] = datetime.now(timezone.utc).isoformat()
                # Convert back to JSON string
                json_data = json.dumps(event_dict)
            else:
                # It's already a dictionary
                event_data['server_time'] = datetime.now(timezone.utc).isoformat()
                json_data = json.dumps(event_data)
                
            # Write to log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json_data + '\n')
            return True
        except Exception as e:
            print(f"Error writing to log file '{self.log_file}': {e}")
            return False
    
    def get_events(self, filter_time=None):
        """
        Get events from the log file.
        
        Args:
            filter_time: Optional datetime object to filter events after this time
            
        Returns:
            List of event dictionaries
        """
        display_events = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event_data = json.loads(line)
                        event_time_str = event_data.get('time')
                        
                        if not event_time_str:
                            print(f"Warning: Log line {line_num+1} missing 'time' field. Skipping.")
                            continue
                        
                        event_dt = None
                        try:
                            event_time_str = event_time_str.replace('Z', '+00:00')
                            event_dt = datetime.fromisoformat(event_time_str)
                            if event_dt.tzinfo is None:
                                event_dt = event_dt.astimezone(timezone.utc)
                        except ValueError:
                            print(f"Warning: Log line {line_num+1} has invalid 'time' format: {event_time_str}. Skipping.")
                            continue
                        
                        if filter_time and event_dt:
                            if event_dt > filter_time:
                                display_events.append(event_data)
                        else:
                            display_events.append(event_data)
                            
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON on log line {line_num+1}. Skipping: {line[:100]}...")
                    except Exception as e:
                        print(f"Error processing log line {line_num+1}: {e}. Skipping.")
        except FileNotFoundError:
            print(f"Log file '{self.log_file}' not found. Creating a new file.")
            Path(self.log_file).touch()
        except Exception as e:
            print(f"Error reading or processing log file '{self.log_file}': {e}")
        
        return display_events
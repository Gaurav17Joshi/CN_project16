# #!/usr/bin/env python
# import json
# from datetime import datetime, timezone
# # import time
# import os

# # Template for event cards
# EVENT_CARD_TEMPLATE = """
# <div class="event-card {priority}">
#     <div class="event-header">
#         <div class="event-title">{message}</div>
#         <div class="event-time">
#             <div><strong>Client Time:</strong> {client_time}</div>
#             <div><strong>Server Time:</strong> {server_time}</div>
#         </div>
#     </div>
#     <div class="event-body">
#         <div class="field-name">Client Name:</div>
#         <div class="field-value">{client_name}</div>

#         <div class="field-name">Client ID:</div>
#         <div class="field-value">{client_id}</div>

#         <div class="field-name">Priority:</div>
#         <div class="field-value" style="text-transform: capitalize;">{priority}</div>
#     </div>

#     <div class="event-info">
#         <div class="event-info-title">Event Details ({event_type}):</div>
#         <div class="info-grid">
#             {event_info_rows}
#         </div>
#     </div>
# </div>
# """

# class TemplateHandler:
#     """Handles all templating and HTML generation for the dashboard."""
    
#     def __init__(self, static_folder="static"):
#         """Initialize with the path to static assets."""
#         self.static_folder = static_folder
#         # Ensure the static folder exists
#         os.makedirs(static_folder, exist_ok=True)
    
#     def read_static_file(self, filename):
#         """Read a static file content."""
#         try:
#             with open(os.path.join(self.static_folder, filename), 'r', encoding='utf-8') as f:
#                 return f.read()
#         except FileNotFoundError:
#             print(f"Warning: Static file '{filename}' not found.")
#             return ""
    
#     def format_date(self, timestamp_str):
#         """Format a timestamp string to a readable date."""
#         try:
#             timestamp_str = timestamp_str.replace('Z', '+00:00')
#             dt = datetime.fromisoformat(timestamp_str)
#             if dt.tzinfo is None:
#                 dt = dt.astimezone(timezone.utc)
#             return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
#         except (ValueError, AttributeError):
#             return "Unknown time"
    
#     def generate_event_cards(self, events):
#         """Generate HTML for event cards from a list of event data."""
#         if not events:
#             return '<div class="no-events">No matching events found in the log.</div>'
        
#         def get_event_time(event):
#             try:
#                 # Check for server_time first
#                 if 'server_time' in event:
#                     time_str = event.get('server_time', '').replace('Z', '+00:00')
#                     return datetime.fromisoformat(time_str)
#                 # Fall back to client time if server_time not available
#                 else:
#                     time_str = event.get('time', '').replace('Z', '+00:00')
#                     return datetime.fromisoformat(time_str)
#             except:
#                 return datetime.min.replace(tzinfo=timezone.utc)
            
#         sorted_events = sorted(events, key=get_event_time, reverse=True)
#         event_cards = ""
        
#         for event in sorted_events:
#             # # Format client time
#             # client_time = "Unknown time"
#             # event_dt = get_event_time(event)
#             # if event_dt != datetime.min.replace(tzinfo=timezone.utc):
#             #     # Default client timezone label
#             #     client_tz = "UTC"
                
#             #     # Format server time first to check time difference
#             #     server_time = "Unknown time"
#             #     server_dt = None
#             #     if 'server_time' in event:
#             #         try:
#             #             server_time_str = event.get('server_time', '').replace('Z', '+00:00')
#             #             server_dt = datetime.fromisoformat(server_time_str)
                        
#             #             # Ensure server_dt has timezone info
#             #             if server_dt.tzinfo is None:
#             #                 server_dt = server_dt.replace(tzinfo=timezone.utc)
                        
#             #             # Ensure event_dt has timezone info too
#             #             if event_dt.tzinfo is None:
#             #                 event_dt = event_dt.replace(tzinfo=timezone.utc)
                            
#             #             # Calculate time difference in hours
#             #             time_diff = abs((event_dt - server_dt).total_seconds() / 3600)
                        
#             #             # If difference is more than 1 hour, assume client is in IST
#             #             if time_diff > 1:
#             #                 client_tz = "IST"
                            
#             #             # Format client time with appropriate timezone label
#             #             client_time = event_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + f" {client_tz}"
                        
#             #             # Format server time (always UTC)
#             #             server_time = server_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
                        
#             #         except Exception as e:
#             #             print(f"Error comparing timestamps: {e}")
#             #             # Fallback formatting if comparison fails
#             #             client_time = event_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
#             #             if server_dt:
#             #                 server_time = server_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
#             #     else:
#             #         # No server time available, just format client time
#             #         client_time = event_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"

#             for event in sorted_events:
#                 # Format client time - THIS SHOULD COME FROM event['time']
#                 client_time = "Unknown time"
#                 client_time_str = event.get('time', '').replace('Z', '+00:00')
                
#                 try:
#                     client_dt = datetime.fromisoformat(client_time_str)
#                     if client_dt.tzinfo is None:
#                         client_dt = client_dt.replace(tzinfo=timezone.utc)
#                     client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
#                 except Exception as e:
#                     print(f"Error formatting client time: {e}")
#                     client_time = "Unknown time"
                
#                 # Format server time - THIS SHOULD COME FROM event['server_time']
#                 server_time = "Unknown time"
#                 if 'server_time' in event:
#                     try:
#                         server_time_str = event.get('server_time', '').replace('Z', '+00:00')
#                         server_dt = datetime.fromisoformat(server_time_str)
                        
#                         if server_dt.tzinfo is None:
#                             server_dt = server_dt.replace(tzinfo=timezone.utc)
                            
#                         server_time = server_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
                        
#                         # Optionally add time difference detection here
#                         if client_dt and server_dt:
#                             time_diff = abs((client_dt - server_dt).total_seconds() / 3600)
#                             if time_diff > 1:
#                                 client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " IST"
#                     except Exception as e:
#                         print(f"Error formatting server time: {e}")
            
#             event_info_rows = ""
#             event_info = event.get('event_info', {})
#             event_type = event_info.get('type', 'N/A')
            
#             if isinstance(event_info, dict):
#                 details_to_show = {k: v for k, v in event_info.items() if k != 'type'}
#                 if not details_to_show:
#                     event_info_rows = '<div class="field-value">No additional details.</div>'
#                 else:
#                     for key, value in details_to_show.items():
#                         key_display = key.replace('_', ' ').capitalize()
#                         event_info_rows += f'<div class="field-name">{key_display}:</div>'
#                         event_info_rows += f'<div class="field-value">{value}</div>'
#             else:
#                 event_info_rows = f'<div class="field-value">{str(event_info)}</div>'
            
#             priority = event.get('priority', 'unknown').lower()
#             card = EVENT_CARD_TEMPLATE.format(
#                 priority=priority, 
#                 message=event.get('message', 'Unknown event message'),
#                 client_time=client_time,
#                 server_time=server_time,
#                 client_name=event.get('client_name', 'Unknown client'),
#                 client_id=event.get('client_id', 'Unknown ID'), 
#                 event_type=event_type,
#                 event_info_rows=event_info_rows
#             )
#             event_cards += card
        
#         return event_cards
    
#     def render_dashboard(self, events, show_since_dt=None):
#         """Render the complete dashboard HTML."""
#         # Read the base template
#         try:
#             template = self.read_static_file("index.html")
#         except Exception as e:
#             print(f"Error reading template: {e}")
#             template = "<html><body><h1>Error loading template</h1></body></html>"
        
#         # Generate event cards
#         event_cards = self.generate_event_cards(events)
        
#         # Generate filter info
#         if show_since_dt:
#             filter_info_html = f'<div class="filter-info">Displaying events since {show_since_dt.strftime("%Y-%m-%d %H:%M:%S %Z")}.</div>'
#         else:
#             filter_info_html = '<div class="filter-info">Displaying all events.</div>'
        
#         # Create the "from now" URL
#         current_time_iso = datetime.now(timezone.utc).isoformat()
#         from_now_url = f"/?show_since={current_time_iso}"
        
#         # Render the template
#         html_content = template.format(
#             event_count=len(events),
#             event_cards=event_cards,
#             from_now_url=from_now_url,
#             filter_info_html=filter_info_html
#         )
        
#         return html_content

# #!/usr/bin/env python
# import json
# from datetime import datetime, timezone
# # import time
# import os

# # Template for event cards
# EVENT_CARD_TEMPLATE = """
# <div class="event-card {priority}">
#     <div class="event-header">
#         <div class="event-title">{message}</div>
#         <div class="event-time">
#             <div><strong>Client Time:</strong> {client_time}</div>
#             <div><strong>Server Time:</strong> {server_time}</div>
#         </div>
#     </div>
#     <div class="event-body">
#         <div class="field-name">Client Name:</div>
#         <div class="field-value">{client_name}</div>

#         <div class="field-name">Client ID:</div>
#         <div class="field-value">{client_id}</div>

#         <div class="field-name">Priority:</div>
#         <div class="field-value" style="text-transform: capitalize;">{priority}</div>
#     </div>

#     <div class="event-info">
#         <div class="event-info-title">Event Details ({event_type}):</div>
#         <div class="info-grid">
#             {event_info_rows}
#         </div>
#     </div>
# </div>
# """

# class TemplateHandler:
#     """Handles all templating and HTML generation for the dashboard."""
    
#     def __init__(self, static_folder="static"):
#         """Initialize with the path to static assets."""
#         self.static_folder = static_folder
#         # Ensure the static folder exists
#         os.makedirs(static_folder, exist_ok=True)
    
#     def read_static_file(self, filename):
#         """Read a static file content."""
#         try:
#             with open(os.path.join(self.static_folder, filename), 'r', encoding='utf-8') as f:
#                 return f.read()
#         except FileNotFoundError:
#             print(f"Warning: Static file '{filename}' not found.")
#             return ""
    
#     def format_date(self, timestamp_str):
#         """Format a timestamp string to a readable date."""
#         try:
#             timestamp_str = timestamp_str.replace('Z', '+00:00')
#             dt = datetime.fromisoformat(timestamp_str)
#             if dt.tzinfo is None:
#                 dt = dt.astimezone(timezone.utc)
#             return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
#         except (ValueError, AttributeError):
#             return "Unknown time"
    
#     def generate_event_cards(self, events):
#         """Generate HTML for event cards from a list of event data."""
#         if not events:
#             return '<div class="no-events">No matching events found in the log.</div>'
        
#         def get_event_time(event):
#             try:
#                 # Check for server_time first
#                 if 'server_time' in event:
#                     time_str = event.get('server_time', '').replace('Z', '+00:00')
#                     return datetime.fromisoformat(time_str)
#                 # Fall back to client time if server_time not available
#                 else:
#                     time_str = event.get('time', '').replace('Z', '+00:00')
#                     return datetime.fromisoformat(time_str)
#             except:
#                 return datetime.min.replace(tzinfo=timezone.utc)
            
#         sorted_events = sorted(events, key=get_event_time, reverse=True)
#         event_cards = ""
        
#         for event in sorted_events:
#             # Format client time - THIS SHOULD COME FROM event['time']
#             client_time = "Unknown time"
#             client_time_str = event.get('time', '').replace('Z', '+00:00')
            
#             try:
#                 client_dt = datetime.fromisoformat(client_time_str)
#                 if client_dt.tzinfo is None:
#                     client_dt = client_dt.replace(tzinfo=timezone.utc)
#                 client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
#             except Exception as e:
#                 print(f"Error formatting client time: {e}")
#                 client_time = "Unknown time"
            
#             # Format server time - THIS SHOULD COME FROM event['server_time']
#             server_time = "Unknown time"
#             if 'server_time' in event:
#                 try:
#                     server_time_str = event.get('server_time', '').replace('Z', '+00:00')
#                     server_dt = datetime.fromisoformat(server_time_str)
                    
#                     if server_dt.tzinfo is None:
#                         server_dt = server_dt.replace(tzinfo=timezone.utc)
                        
#                     server_time = server_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
                    
#                     # Optionally add time difference detection here
#                     if 'client_dt' in locals() and server_dt:
#                         time_diff = abs((client_dt - server_dt).total_seconds() / 3600)
#                         if time_diff > 1:
#                             client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " IST"
#                 except Exception as e:
#                     print(f"Error formatting server time: {e}")
            
#             event_info_rows = ""
#             event_info = event.get('event_info', {})
#             event_type = event_info.get('type', 'N/A')
            
#             # Replace the existing event_info_rows logic in generate_event_cards method
#             if isinstance(event_info, dict):
#                 details_to_show = {k: v for k, v in event_info.items() if k != 'type'}
#                 if not details_to_show:
#                     event_info_rows = '<div class="field-value">No additional details.</div>'
#                 else:
#                     for key, value in details_to_show.items():
#                         key_display = key.replace('_', ' ').capitalize()
                        
#                         # Handle the Data field specifically for lists of dictionaries
#                         if key == 'data' and isinstance(value, list) and all(isinstance(item, dict) for item in value):
#                             formatted_data = '<div style="white-space: pre-line;">'
#                             for i, item in enumerate(value):
#                                 formatted_data += f"Item {i+1}:\n"
#                                 for k, v in item.items():
#                                     formatted_data += f"  {k}: {v}\n"
#                                 formatted_data += "\n"
#                             formatted_data += '</div>'
#                             event_info_rows += f'<div class="field-name">{key_display}:</div>'
#                             event_info_rows += f'<div class="field-value">{formatted_data}</div>'
#                         else:
#                             event_info_rows += f'<div class="field-name">{key_display}:</div>'
#                             event_info_rows += f'<div class="field-value">{value}</div>'
#             else:
#                 event_info_rows = f'<div class="field-value">{str(event_info)}</div>'
            
#             priority = event.get('priority', 'unknown').lower()
#             card = EVENT_CARD_TEMPLATE.format(
#                 priority=priority, 
#                 message=event.get('message', 'Unknown event message'),
#                 client_time=client_time,
#                 server_time=server_time,
#                 client_name=event.get('client_name', 'Unknown client'),
#                 client_id=event.get('client_id', 'Unknown ID'), 
#                 event_type=event_type,
#                 event_info_rows=event_info_rows
#             )
#             event_cards += card
        
#         return event_cards
    
#     def render_dashboard(self, events, show_since_dt=None):
#         """Render the complete dashboard HTML."""
#         # Read the base template
#         try:
#             template = self.read_static_file("index.html")
#         except Exception as e:
#             print(f"Error reading template: {e}")
#             template = "<html><body><h1>Error loading template</h1></body></html>"
        
#         # Generate event cards
#         event_cards = self.generate_event_cards(events)
        
#         # Generate filter info
#         if show_since_dt:
#             filter_info_html = f'<div class="filter-info">Displaying events since {show_since_dt.strftime("%Y-%m-%d %H:%M:%S %Z")}.</div>'
#         else:
#             filter_info_html = '<div class="filter-info">Displaying all events.</div>'
        
#         # Create the "from now" URL
#         current_time_iso = datetime.now(timezone.utc).isoformat()
#         from_now_url = f"/?show_since={current_time_iso}"
        
#         # Render the template
#         html_content = template.format(
#             event_count=len(events),
#             event_cards=event_cards,
#             from_now_url=from_now_url,
#             filter_info_html=filter_info_html
#         )
        
#         return html_content

#!/usr/bin/env python
import json
from datetime import datetime, timezone
# import time
import os

# Template for event cards
EVENT_CARD_TEMPLATE = """
<div class="event-card {priority}">
    <div class="event-header">
        <div class="event-title">{message}</div>
        <div class="event-time">
            <div><strong>Client Time:</strong> {client_time}</div>
            <div><strong>Server Time:</strong> {server_time}</div>
        </div>
    </div>
    <div class="event-body">
        <div class="field-name">Client Name:</div>
        <div class="field-value">{client_name}</div>

        <div class="field-name">Client ID:</div>
        <div class="field-value">{client_id}</div>

        <div class="field-name">Priority:</div>
        <div class="field-value" style="text-transform: capitalize;">{priority}</div>
    </div>

    <div class="event-info">
        <div class="event-info-title">Event Details ({event_type}):</div>
        <div class="info-grid">
            {event_info_rows}
        </div>
    </div>
</div>
"""

class TemplateHandler:
    """Handles all templating and HTML generation for the dashboard."""
    
    def __init__(self, static_folder="static"):
        """Initialize with the path to static assets."""
        self.static_folder = static_folder
        # Ensure the static folder exists
        os.makedirs(static_folder, exist_ok=True)
    
    def read_static_file(self, filename):
        """Read a static file content."""
        try:
            with open(os.path.join(self.static_folder, filename), 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Static file '{filename}' not found.")
            return ""
    
    def format_date(self, timestamp_str):
        """Format a timestamp string to a readable date."""
        try:
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        except (ValueError, AttributeError):
            return "Unknown time"
    
    def generate_event_cards(self, events):
        """Generate HTML for event cards from a list of event data."""
        if not events:
            return '<div class="no-events">No matching events found in the log.</div>'
        
        def get_event_time(event):
            try:
                # Check for server_time first
                if 'server_time' in event:
                    time_str = event.get('server_time', '').replace('Z', '+00:00')
                    return datetime.fromisoformat(time_str)
                # Fall back to client time if server_time not available
                else:
                    time_str = event.get('time', '').replace('Z', '+00:00')
                    return datetime.fromisoformat(time_str)
            except:
                return datetime.min.replace(tzinfo=timezone.utc)
            
        sorted_events = sorted(events, key=get_event_time, reverse=True)
        event_cards = ""
        
        for event in sorted_events:
            # Format client time - THIS SHOULD COME FROM event['time']
            client_time = "Unknown time"
            client_time_str = event.get('time', '').replace('Z', '+00:00')
            
            try:
                client_dt = datetime.fromisoformat(client_time_str)
                if client_dt.tzinfo is None:
                    client_dt = client_dt.replace(tzinfo=timezone.utc)
                client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
            except Exception as e:
                print(f"Error formatting client time: {e}")
                client_time = "Unknown time"
            
            # Format server time - THIS SHOULD COME FROM event['server_time']
            server_time = "Unknown time"
            if 'server_time' in event:
                try:
                    server_time_str = event.get('server_time', '').replace('Z', '+00:00')
                    server_dt = datetime.fromisoformat(server_time_str)
                    
                    if server_dt.tzinfo is None:
                        server_dt = server_dt.replace(tzinfo=timezone.utc)
                        
                    server_time = server_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " UTC"
                    
                    # Optionally add time difference detection here
                    if 'client_dt' in locals() and server_dt:
                        time_diff = abs((client_dt - server_dt).total_seconds() / 3600)
                        if time_diff > 1:
                            client_time = client_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " IST"
                except Exception as e:
                    print(f"Error formatting server time: {e}")
            
            event_info_rows = ""
            event_info = event.get('event_info', {})
            event_type = event_info.get('type', 'N/A')
            
            if isinstance(event_info, dict):
                details_to_show = {k: v for k, v in event_info.items() if k != 'type'}
                if not details_to_show:
                    event_info_rows = '<div class="field-value">No additional details.</div>'
                else:
                    for key, value in details_to_show.items():
                        key_display = key.replace('_', ' ').capitalize()
                        
                        # Handle data fields specially when they contain list of dictionaries
                        if key.lower() == 'data' and isinstance(value, list) and all(isinstance(item, dict) for item in value):
                            # Check if all dictionaries have the same keys (to create a table)
                            if value and all(item.keys() == value[0].keys() for item in value):
                                # Create table header with keys
                                keys = list(value[0].keys())
                                
                                formatted_data = '<div class="data-table-container">'
                                formatted_data += '<table class="data-table"><thead><tr>'
                                
                                # Create table headers
                                for k in keys:
                                    formatted_data += f'<th>{k}</th>'
                                formatted_data += '</tr></thead><tbody>'
                                
                                # Create table rows with values
                                for item in value:
                                    formatted_data += '<tr>'
                                    for k in keys:
                                        formatted_data += f'<td>{item.get(k, "")}</td>'
                                    formatted_data += '</tr>'
                                
                                formatted_data += '</tbody></table></div>'
                            else:
                                # Fallback for lists of dictionaries with different structures
                                formatted_data = '<div class="data-list">'
                                for i, item in enumerate(value):
                                    formatted_data += f'<div class="data-item"><strong>Item {i+1}:</strong><br>'
                                    for k, v in item.items():
                                        formatted_data += f'<span class="data-key">{k}:</span> <span class="data-value">{v}</span><br>'
                                    formatted_data += '</div>'
                                formatted_data += '</div>'
                            
                            event_info_rows += f'<div class="field-name">{key_display}:</div>'
                            event_info_rows += f'<div class="field-value">{formatted_data}</div>'
                        else:
                            event_info_rows += f'<div class="field-name">{key_display}:</div>'
                            event_info_rows += f'<div class="field-value">{value}</div>'
            else:
                event_info_rows = f'<div class="field-value">{str(event_info)}</div>'
            
            priority = event.get('priority', 'unknown').lower()
            card = EVENT_CARD_TEMPLATE.format(
                priority=priority, 
                message=event.get('message', 'Unknown event message'),
                client_time=client_time,
                server_time=server_time,
                client_name=event.get('client_name', 'Unknown client'),
                client_id=event.get('client_id', 'Unknown ID'), 
                event_type=event_type,
                event_info_rows=event_info_rows
            )
            event_cards += card
        
        return event_cards
    
    def render_dashboard(self, events, show_since_dt=None):
        """Render the complete dashboard HTML."""
        # Read the base template
        try:
            template = self.read_static_file("index.html")
        except Exception as e:
            print(f"Error reading template: {e}")
            template = "<html><body><h1>Error loading template</h1></body></html>"
        
        # Generate event cards
        event_cards = self.generate_event_cards(events)
        
        # Generate filter info
        if show_since_dt:
            filter_info_html = f'<div class="filter-info">Displaying events since {show_since_dt.strftime("%Y-%m-%d %H:%M:%S %Z")}.</div>'
        else:
            filter_info_html = '<div class="filter-info">Displaying all events.</div>'
        
        # Create the "from now" URL
        current_time_iso = datetime.now(timezone.utc).isoformat()
        from_now_url = f"/?show_since={current_time_iso}"
        
        # Render the template
        html_content = template.format(
            event_count=len(events),
            event_cards=event_cards,
            from_now_url=from_now_url,
            filter_info_html=filter_info_html
        )
        
        return html_content
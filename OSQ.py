import osquery
import time
import os
import argparse
import json
import csv

def safe_query_executor(query):
    """Execute query with error handling"""
    try:
        instance = osquery.SpawnInstance()
        instance.open()
        result = instance.client.query(query)
        
        if result.status.code != 0:
            raise RuntimeError(f"Query failed: {result.status.message}")
            
        return result.response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def format_output(data):
    """Format data with each column on a new line"""
    output = []
    for i, row in enumerate(data, 1):
        output.append(f"ROW {i}:")
        for key, value in row.items():
            output.append(f"{key}: {value}")
        output.append("")
    return "\n".join(output)

def list_tables():
    """List all available tables"""
    tables = safe_query_executor("SELECT name FROM osquery_registry WHERE registry = 'table'")
    if tables:
        print("\nAvailable Tables:\n")
        for table in tables:
            print(table['name'])
        print(f"\nTotal tables: {len(tables)}")
    else:
        print("No tables found")

def generate_filename(base, output_arg):
    """Generate filename based on command and format"""
    ext = output_arg.lower().lstrip('.') if output_arg else 'txt'
    return f"{base}.{ext}" if ext else base

def save_output(data, output_arg, command_type, table_name=None):
    """Save data to file"""
    try:
        if command_type == 'fetch':
            filename = generate_filename(table_name or 'table_output', output_arg)
        elif command_type == 'query':
            filename = generate_filename('qout', output_arg)
        else:
            filename = 'output.txt'

        with open(filename, 'w') as f:
            if filename.endswith('.json'):
                json.dump(data, f, indent=2)
            elif filename.endswith('.csv'):
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                f.write(format_output(data))
        print(f"Output saved to {filename}")
    except Exception as e:
        print(f"Error saving output: {str(e)}")

def fetch_table(table_name, limit=None, output_arg=None):
    """Fetch table contents"""
    query = f"SELECT * FROM {table_name}"
    # Only apply LIMIT if explicitly specified and positive
    if limit is not None and limit > 0:
        query += f" LIMIT {limit}"
    
    data = safe_query_executor(query)
    
    if data:
        if output_arg is not None:
            save_output(data, output_arg, 'fetch', table_name)
        else:
            print(f"\nContents of {table_name}:")
            print(format_output(data))

def execute_custom_query(query, output_arg=None):
    """Execute custom query"""
    data = safe_query_executor(query)
    if data:
        if output_arg is not None:
            save_output(data, output_arg, 'query')
        else:
            print("\nQuery Results:")
            print(format_output(data))

def loop_execution(func, interval, *args):
    """Execute function repeatedly"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            func(*args)
            print(f"\nRefreshing in {interval} seconds. Press Ctrl+C to stop.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="OSQuery custom CLI Tool")
    
    parser.add_argument("-l", "--list", action="store_true", help="List all tables")
    parser.add_argument("-f", "--fetch", metavar="TABLE", help="Fetch table contents")
    parser.add_argument("--limit", type=int, default=None, 
                       help="Max rows to display (optional, no limit if not specified)")
    parser.add_argument("--loop", type=float, metavar="SECONDS", help="Refresh interval")
    parser.add_argument("-q", "--query", help="Custom SQL query")
    parser.add_argument("-o", "--output", metavar='TYPE', help="Save output(json, csv, txt)")

    args = parser.parse_args()

    if args.list:
        list_tables()
    elif args.fetch:
        if args.loop:
            loop_execution(fetch_table, args.loop, args.fetch, args.limit, args.output)
        else:
            fetch_table(args.fetch, args.limit, args.output)
    elif args.query:
        if args.loop:
            loop_execution(execute_custom_query, args.loop, args.query, args.output)
        else:
            execute_custom_query(args.query, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


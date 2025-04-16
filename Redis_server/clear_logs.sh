#!/bin/bash

# Simple script to clear the events.log file

LOG_FILE="events.log"
BACKUP_DIR="log_backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${LOG_FILE}_${TIMESTAMP}.bak"

# Check if log file exists
if [ -f "$LOG_FILE" ]; then
    # Create backup
    echo "Creating backup of $LOG_FILE as $BACKUP_FILE"
    cp "$LOG_FILE" "$BACKUP_FILE"
    
    # Clear the log file
    echo "Clearing $LOG_FILE"
    echo "" > "$LOG_FILE"
    
    echo "Log file cleared successfully!"
    echo "A backup was saved to $BACKUP_FILE"
else
    # Create empty log file if it doesn't exist
    echo "Log file $LOG_FILE does not exist. Creating empty file."
    touch "$LOG_FILE"
fi

echo "Done!"
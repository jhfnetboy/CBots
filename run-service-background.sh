#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory - change this to your actual project path
PROJECT_DIR=~/dev/tools/jhfnetboy-CBots
LOGS_DIR=$PROJECT_DIR/logs

echo -e "${GREEN}===== Starting CBots Service in Background =====${NC}"

# Create logs directory if it doesn't exist
mkdir -p $LOGS_DIR

# Navigate to the project directory
cd $PROJECT_DIR

# Check if the service is already running
PID_FILE=$PROJECT_DIR/cbots.pid
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo -e "${RED}Service is already running with PID $PID${NC}"
        echo -e "${YELLOW}Use 'stop-service.sh' to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}Found stale PID file. Removing it.${NC}"
        rm $PID_FILE
    fi
fi

# Set up log files with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE=$LOGS_DIR/cbots_$TIMESTAMP.log
ERROR_LOG=$LOGS_DIR/cbots_error_$TIMESTAMP.log

# Activate the virtual environment and start the service in background
echo -e "${YELLOW}Starting service in background...${NC}"
(
    source venv/bin/activate
    nohup python main.py > $LOG_FILE 2> $ERROR_LOG &
    echo $! > $PID_FILE
)

# Wait a moment to check if process started correctly
sleep 2

# Check if service started successfully
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}Service started successfully with PID $PID${NC}"
        echo -e "${YELLOW}Logs are available at:${NC}"
        echo -e "  Standard output: $LOG_FILE"
        echo -e "  Error log: $ERROR_LOG"
        
        # Create symlinks to latest logs for convenience
        ln -sf $LOG_FILE $LOGS_DIR/cbots_latest.log
        ln -sf $ERROR_LOG $LOGS_DIR/cbots_error_latest.log
        echo -e "${YELLOW}Symbolic links created:${NC}"
        echo -e "  Latest log: $LOGS_DIR/cbots_latest.log"
        echo -e "  Latest error log: $LOGS_DIR/cbots_error_latest.log"
    else
        echo -e "${RED}Failed to start service${NC}"
        echo -e "${YELLOW}Check log files for details:${NC}"
        echo -e "  $LOG_FILE"
        echo -e "  $ERROR_LOG"
        exit 1
    fi
else
    echo -e "${RED}Failed to create PID file${NC}"
    exit 1
fi

echo -e "${GREEN}===== Service startup complete =====${NC}" 
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory - change this to your actual project path
PROJECT_DIR=~/dev/tools/jhfnetboy-CBots

echo -e "${GREEN}===== Stopping CBots Service =====${NC}"

# Check if the service is running
PID_FILE=$PROJECT_DIR/cbots.pid
if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}Service is not running (PID file not found)${NC}"
    
    # Check if there are any running python processes that might be our service
    RUNNING_PROCS=$(ps aux | grep python | grep main.py | grep -v grep)
    
    if [ ! -z "$RUNNING_PROCS" ]; then
        echo -e "${YELLOW}Found running processes that might be our service:${NC}"
        echo "$RUNNING_PROCS"
        
        read -p "Do you want to kill these processes? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Extract PIDs
            PIDS=$(echo "$RUNNING_PROCS" | awk '{print $2}')
            
            for PID in $PIDS; do
                echo -e "${YELLOW}Killing process $PID...${NC}"
                kill -9 $PID
            done
            echo -e "${GREEN}All matching processes killed${NC}"
        else
            echo -e "${YELLOW}No action taken${NC}"
        fi
    else
        echo -e "${YELLOW}No matching processes found${NC}"
    fi
    
    exit 1
fi

# Get PID
PID=$(cat $PID_FILE)

# Check if process is running
if ps -p $PID > /dev/null; then
    echo -e "${YELLOW}Stopping service with PID $PID...${NC}"
    kill $PID
    
    # Wait for process to stop
    for i in {1..5}; do
        if ! ps -p $PID > /dev/null; then
            echo -e "${GREEN}Service stopped successfully${NC}"
            rm $PID_FILE
            exit 0
        fi
        echo -e "${YELLOW}Waiting for service to stop (attempt $i/5)...${NC}"
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${RED}Service did not stop gracefully. Force killing...${NC}"
    kill -9 $PID
    
    # Final check
    if ! ps -p $PID > /dev/null; then
        echo -e "${GREEN}Service forcefully stopped${NC}"
        rm $PID_FILE
        exit 0
    else
        echo -e "${RED}Failed to stop service${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Process with PID $PID is not running${NC}"
    echo -e "${YELLOW}Removing stale PID file${NC}"
    rm $PID_FILE
    
    # Check if there are any other python processes that might be our service
    RUNNING_PROCS=$(ps aux | grep python | grep main.py | grep -v grep)
    
    if [ ! -z "$RUNNING_PROCS" ]; then
        echo -e "${YELLOW}Found other running processes that might be our service:${NC}"
        echo "$RUNNING_PROCS"
        
        read -p "Do you want to kill these processes? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Extract PIDs
            PIDS=$(echo "$RUNNING_PROCS" | awk '{print $2}')
            
            for PID in $PIDS; do
                echo -e "${YELLOW}Killing process $PID...${NC}"
                kill -9 $PID
            done
            echo -e "${GREEN}All matching processes killed${NC}"
        else
            echo -e "${YELLOW}No action taken${NC}"
        fi
    fi
fi

echo -e "${GREEN}===== Service shutdown complete =====${NC}" 
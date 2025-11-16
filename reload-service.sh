#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== Reloading CBots Service =====${NC}"

# Project directory - change this to your actual project path
PROJECT_DIR=~/dev/tools/jhfnetboy-CBots

# Step 1: Stop the running service
echo -e "${YELLOW}Stopping service...${NC}"
launchctl unload /Library/LaunchAgents/com.cbots.service.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Service stopped successfully${NC}"
else
    echo -e "${RED}Warning: Could not stop service properly${NC}"
    
    # Check if process is still running
    echo -e "${YELLOW}Checking for running processes...${NC}"
    RUNNING_PROCS=$(ps aux | grep python | grep main.py | grep -v grep)
    
    if [ ! -z "$RUNNING_PROCS" ]; then
        echo -e "${RED}Found running processes:${NC}"
        echo "$RUNNING_PROCS"
        
        # Extract PIDs
        PIDS=$(echo "$RUNNING_PROCS" | awk '{print $2}')
        
        echo -e "${YELLOW}Killing processes...${NC}"
        for PID in $PIDS; do
            echo "Killing process $PID"
            kill -9 $PID
        done
    else
        echo -e "${GREEN}No running processes found${NC}"
    fi
fi

# Step 2: Pull latest code (if using git)
echo -e "${YELLOW}Updating code...${NC}"
cd $PROJECT_DIR
git pull
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Code updated successfully${NC}"
else
    echo -e "${RED}Warning: Could not update code${NC}"
    echo -e "${YELLOW}Continuing with restart...${NC}"
fi

# Step 3: Restart the service
echo -e "${YELLOW}Starting service...${NC}"
launchctl load /Library/LaunchAgents/com.cbots.service.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Service started successfully${NC}"
else
    echo -e "${RED}Error: Could not start service${NC}"
    exit 1
fi

# Step 4: Verify the service is running
echo -e "${YELLOW}Verifying service status...${NC}"
SERVICE_STATUS=$(launchctl list | grep cbots)

if [ ! -z "$SERVICE_STATUS" ]; then
    echo -e "${GREEN}Service is running: ${NC}"
    echo "$SERVICE_STATUS"
else
    echo -e "${RED}Warning: Service may not be running${NC}"
    echo -e "${YELLOW}Starting manual verification...${NC}"
    
    # Wait a bit for the service to start
    sleep 3
    
    # Check processes
    RUNNING_PROCS=$(ps aux | grep python | grep main.py | grep -v grep)
    if [ ! -z "$RUNNING_PROCS" ]; then
        echo -e "${GREEN}Found running process:${NC}"
        echo "$RUNNING_PROCS"
    else
        echo -e "${RED}No running processes found${NC}"
        echo -e "${YELLOW}Try running manually: cd $PROJECT_DIR && python main.py${NC}"
    fi
    
    # Check port
    PORT_STATUS=$(lsof -i :8872 | grep LISTEN)
    if [ ! -z "$PORT_STATUS" ]; then
        echo -e "${GREEN}Service is listening on port 8872:${NC}"
        echo "$PORT_STATUS"
    else
        echo -e "${RED}No service found listening on port 8872${NC}"
    fi
fi

echo -e "${GREEN}===== Service reload complete =====${NC}" 
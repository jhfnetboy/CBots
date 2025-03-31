#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory - change this to your actual project path
PROJECT_DIR=~/dev/tools/jhfnetboy-CBots
LOGS_DIR=$PROJECT_DIR/logs

echo -e "${GREEN}===== CBots Service Logs =====${NC}"

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${RED}Logs directory not found: $LOGS_DIR${NC}"
    echo -e "${YELLOW}Make sure the service has been started with run-service-background.sh${NC}"
    exit 1
fi

# List available log files
echo -e "${YELLOW}Available log files:${NC}"
ls -lh $LOGS_DIR | grep -v "latest" | grep -v "^total"

# Check for latest logs
LATEST_LOG="$LOGS_DIR/cbots_latest.log"
LATEST_ERROR="$LOGS_DIR/cbots_error_latest.log"

if [ -f "$LATEST_LOG" ]; then
    echo
    echo -e "${GREEN}Latest standard output log available at:${NC}"
    echo -e "  $LATEST_LOG"
    echo -e "${YELLOW}Last 10 lines:${NC}"
    tail -n 10 $LATEST_LOG
    echo
    echo -e "${YELLOW}To follow this log, run:${NC}"
    echo -e "  tail -f $LATEST_LOG"
else
    echo -e "${RED}No latest standard output log found${NC}"
fi

if [ -f "$LATEST_ERROR" ]; then
    echo
    echo -e "${GREEN}Latest error log available at:${NC}"
    echo -e "  $LATEST_ERROR"
    echo -e "${YELLOW}Last 10 lines:${NC}"
    tail -n 10 $LATEST_ERROR
    echo
    echo -e "${YELLOW}To follow this log, run:${NC}"
    echo -e "  tail -f $LATEST_ERROR"
else
    echo -e "${RED}No latest error log found${NC}"
fi

# Check if service is running
PID_FILE=$PROJECT_DIR/cbots.pid
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo
        echo -e "${GREEN}Service is currently running with PID $PID${NC}"
    else
        echo
        echo -e "${RED}Service is not running, but PID file exists${NC}"
        echo -e "${YELLOW}Consider removing the stale PID file:${NC}"
        echo -e "  rm $PID_FILE"
    fi
else
    echo
    echo -e "${RED}Service is not running (PID file not found)${NC}"
fi

echo
echo -e "${GREEN}===== Log summary complete =====${NC}" 
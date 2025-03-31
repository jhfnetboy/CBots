#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory - change this to your actual project path
PROJECT_DIR=~/dev/tools/jhfnetboy-CBots

echo -e "${GREEN}===== Starting CBots Service =====${NC}"

# Navigate to the project directory
cd $PROJECT_DIR

# Activate the virtual environment
source venv/bin/activate

# Start the service in foreground
echo -e "${YELLOW}Starting service in foreground...${NC}"
python main.py

# Keep script running
wait 
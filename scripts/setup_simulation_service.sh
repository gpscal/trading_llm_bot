#!/bin/bash
# Setup script for Trading LLM Bot Simulation Service
# This script installs the simulation as a systemd service

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Trading LLM Bot Simulation Service Setup ===${NC}\n"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Project root: $PROJECT_ROOT"

# Detect virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    VENV_PATH="$PROJECT_ROOT/venv"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    VENV_PATH="$PROJECT_ROOT/.venv"
else
    echo -e "${RED}Error: Virtual environment not found. Please create one first.${NC}"
    echo "Run: python3 -m venv venv"
    exit 1
fi

VENV_BIN="$VENV_PATH/bin"
echo "Virtual environment: $VENV_PATH"

# Get current user and group
CURRENT_USER=$(whoami)
CURRENT_GROUP=$(id -gn)

echo "User: $CURRENT_USER"
echo "Group: $CURRENT_GROUP"

# Check if required files exist
if [ ! -f "$PROJECT_ROOT/simulate_wsgi.py" ]; then
    echo -e "${RED}Error: simulate_wsgi.py not found${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/simulate_gunicorn.conf.py" ]; then
    echo -e "${RED}Error: simulate_gunicorn.conf.py not found${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/trading_llm_bot_simulation.service" ]; then
    echo -e "${RED}Error: trading_llm_bot_simulation.service not found${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"
echo -e "${GREEN}?${NC} Logs directory created/verified"

# Create systemd service file with actual values
SERVICE_FILE="/tmp/trading_llm_bot_simulation.service"
sed -e "s|%USER%|$CURRENT_USER|g" \
    -e "s|%GROUP%|$CURRENT_GROUP|g" \
    -e "s|%PROJECT_ROOT%|$PROJECT_ROOT|g" \
    -e "s|%VENV_BIN%|$VENV_BIN|g" \
    "$PROJECT_ROOT/trading_llm_bot_simulation.service" > "$SERVICE_FILE"

echo -e "${GREEN}?${NC} Service file prepared"

# Install the service
echo -e "\n${YELLOW}Installing systemd service...${NC}"
echo "This requires sudo privileges."

sudo cp "$SERVICE_FILE" /etc/systemd/system/trading_llm_bot_simulation.service
sudo systemctl daemon-reload

echo -e "${GREEN}?${NC} Service installed"

# Cleanup temp file
rm "$SERVICE_FILE"

# Ask user if they want to enable and start the service
echo -e "\n${YELLOW}Would you like to enable and start the service now? [y/N]${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${YELLOW}Enabling service...${NC}"
    sudo systemctl enable trading_llm_bot_simulation.service
    
    echo -e "${YELLOW}Starting service...${NC}"
    sudo systemctl start trading_llm_bot_simulation.service
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    echo -e "\n${YELLOW}Service status:${NC}"
    sudo systemctl status trading_llm_bot_simulation.service --no-pager || true
    
    echo -e "\n${GREEN}?${NC} Service started and enabled"
    echo -e "\n${GREEN}Simulation is now running in the background!${NC}"
else
    echo -e "\n${YELLOW}Service installed but not started.${NC}"
    echo "To enable and start later, run:"
    echo "  sudo systemctl enable trading_llm_bot_simulation.service"
    echo "  sudo systemctl start trading_llm_bot_simulation.service"
fi

# Print useful commands
echo -e "\n${GREEN}=== Useful Commands ===${NC}"
echo "Check service status:"
echo "  sudo systemctl status trading_llm_bot_simulation.service"
echo ""
echo "View logs:"
echo "  sudo journalctl -u trading_llm_bot_simulation.service -f"
echo "  tail -f $PROJECT_ROOT/logs/simulation_error.log"
echo "  tail -f $PROJECT_ROOT/simulate_service.log"
echo ""
echo "Stop service:"
echo "  sudo systemctl stop trading_llm_bot_simulation.service"
echo ""
echo "Restart service:"
echo "  sudo systemctl restart trading_llm_bot_simulation.service"
echo ""
echo "Disable service:"
echo "  sudo systemctl disable trading_llm_bot_simulation.service"
echo ""
echo "Check simulation status via HTTP:"
echo "  curl http://localhost:5001/status"
echo ""
echo -e "${GREEN}Setup complete!${NC}"

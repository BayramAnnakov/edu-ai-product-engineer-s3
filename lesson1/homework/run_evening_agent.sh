#!/bin/bash
# Evening Agent Runner
# Usage: ./run_evening_agent.sh [publisher]
# Example: ./run_evening_agent.sh tagesspiegel

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default publisher
PUBLISHER="${1:-kurier}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🤖 Evening Agent Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Publisher:${NC} $PUBLISHER"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}⚠️  Warning: .env file not found in project root${NC}"
    echo -e "${YELLOW}Please create .env with:${NC}"
    echo "  ANTHROPIC_API_KEY=your-key"
    echo "  FIRECRAWL_API_KEY=your-key"
    echo ""
fi

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo -e "${YELLOW}Activating venv...${NC}"
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${RED}✗ Virtual environment not found at $PROJECT_ROOT/venv${NC}"
        echo -e "${YELLOW}Please run: python -m venv venv${NC}"
        exit 1
    fi
    echo ""
fi

# Change to project root
cd "$PROJECT_ROOT"

# Run the evening agent
echo -e "${GREEN}Starting analysis...${NC}"
echo ""

python -m homework.evening_agent --publisher "$PUBLISHER"

echo ""
echo -e "${GREEN}✓ Analysis complete!${NC}"


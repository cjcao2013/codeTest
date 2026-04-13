#!/bin/bash
# TAP Migration Skill — Demo Stop Script

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping mock-tap server...${NC}"

if pkill -f "uvicorn main:app --port 8001" 2>/dev/null; then
  echo -e "${GREEN}  ✓ mock-tap stopped${NC}"
else
  echo "  mock-tap was not running"
fi

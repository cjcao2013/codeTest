#!/bin/bash
# TAP Migration Skill — Demo Startup Script
# Starts mock-tap server and prepares the environment for demo

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MOCK_TAP_DIR="$SCRIPT_DIR/mock-tap"
MIGRATION_DIR="$SCRIPT_DIR/tap-migration"
ENV_FILE="$MIGRATION_DIR/.env"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  TAP Migration Skill — Demo Environment   ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── Check uv ─────────────────────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
  echo "❌  'uv' not found. Install it: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

# ── Install dependencies ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[1/3] Installing dependencies...${NC}"
cd "$MOCK_TAP_DIR" && uv sync --quiet
cd "$MIGRATION_DIR" && uv sync --quiet
echo -e "${GREEN}  ✓ Dependencies ready${NC}"

# ── Write .env if missing ─────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/3] Checking .env...${NC}"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
TAP_API_BASE_URL=http://localhost:8001
TAP_API_TOKEN=demo-token
TAP_PROJECT_ID=demo-project
EOF
  echo -e "${GREEN}  ✓ .env created (pointing to mock-tap on port 8001)${NC}"
else
  echo -e "${GREEN}  ✓ .env already exists${NC}"
fi

# ── Start mock-tap ────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/3] Starting mock-tap server on http://localhost:8001 ...${NC}"
cd "$MOCK_TAP_DIR"
uv run uvicorn main:app --port 8001 --log-level warning &
MOCK_TAP_PID=$!

# Wait for server to be ready
sleep 2
if curl -s http://localhost:8001/stats > /dev/null 2>&1; then
  echo -e "${GREEN}  ✓ mock-tap is running (PID $MOCK_TAP_PID)${NC}"
else
  echo "❌  mock-tap failed to start"
  kill $MOCK_TAP_PID 2>/dev/null
  exit 1
fi

# ── Ready ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅  Demo environment ready!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Mock TAP API:  http://localhost:8001"
echo "  Uploaded data: http://localhost:8001/test-data"
echo "  Uploaded cases: http://localhost:8001/test-cases"
echo "  Stats:         http://localhost:8001/stats"
echo ""
echo -e "${YELLOW}Demo commands:${NC}"
echo "  # Step 1 — Assess"
echo "  cd tap-migration && uv run python assess.py --project-dir <path-to-project>"
echo ""
echo "  # Step 2 — Migrate"
echo "  cd tap-migration && uv run python migrate.py --project-dir <path-to-project> --env .env --upload-delay 0.5"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop mock-tap"
echo ""

# Keep script alive until Ctrl+C
trap "echo ''; echo 'Stopping mock-tap...'; kill $MOCK_TAP_PID 2>/dev/null; exit 0" INT TERM
wait $MOCK_TAP_PID

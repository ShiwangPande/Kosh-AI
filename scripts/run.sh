#!/usr/bin/env bash
# ============================================================
# Kosh-AI — Quick Start Script
# ============================================================
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   ⬡  Kosh-AI  —  Quick Start         ║"
echo "  ║   Procurement Intelligence Engine     ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${RESET}"

# ── Check prerequisites ────────────────────────────────────
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${YELLOW}⚠  $1 is not installed. Please install it first.${RESET}"
        exit 1
    fi
}

check_cmd docker
check_cmd docker

echo -e "${GREEN}✓${RESET} Docker found"

# ── Create .env if missing ─────────────────────────────────
if [ ! -f .env ]; then
    echo -e "${YELLOW}→${RESET} Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓${RESET} .env created — update secrets before production use"
else
    echo -e "${GREEN}✓${RESET} .env exists"
fi

# ── Build & Start ──────────────────────────────────────────
echo ""
echo -e "${CYAN}→ Building containers...${RESET}"
docker compose build

echo ""
echo -e "${CYAN}→ Starting services...${RESET}"
docker compose up -d

echo ""
echo -e "${CYAN}→ Waiting for services to be healthy...${RESET}"
sleep 5

# ── Check health ──────────────────────────────────────────
echo ""
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${RESET} Backend API is running"
else
    echo -e "${YELLOW}⚠${RESET} Backend may still be starting..."
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${RESET} Frontend is running"
else
    echo -e "${YELLOW}⚠${RESET} Frontend may still be starting..."
fi

# ── Print info ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════${RESET}"
echo -e "${BOLD}  Kosh-AI is ready!${RESET}"
echo -e "${GREEN}═══════════════════════════════════════${RESET}"
echo ""
echo -e "  Frontend:    ${CYAN}http://localhost:3000${RESET}"
echo -e "  Backend API: ${CYAN}http://localhost:8000${RESET}"
echo -e "  API Docs:    ${CYAN}http://localhost:8000/docs${RESET}"
echo -e "  MinIO:       ${CYAN}http://localhost:9001${RESET}"
echo ""
echo -e "  ${YELLOW}Next steps:${RESET}"
echo -e "    1. Run ${BOLD}make seed${RESET} to populate sample data"
echo -e "    2. Login with admin@kosh.ai / admin123456"
echo -e "    3. Run ${BOLD}python scripts/test_requests.py${RESET} to test APIs"
echo ""

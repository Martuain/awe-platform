#!/usr/bin/env bash
set -euo pipefail

printf '\nAWE MVP v1.0 release gate\n==========================\n'

command -v pnpm >/dev/null 2>&1 || { echo 'ERROR: pnpm is required.'; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: python3 is required.'; exit 1; }

node_version=$(node --version 2>/dev/null || true)
pnpm_version=$(pnpm --version)
python_version=$(python3 --version)
printf 'Node: %s\npnpm: %s\nPython: %s\n\n' "${node_version:-unavailable}" "$pnpm_version" "$python_version"

pnpm lint
pnpm build
pnpm test

printf '\nMVP RELEASE GATE: GREEN\n'
printf 'Core repository checks passed. Start the executable stack with:\n  docker compose up --build\n\nStudio: http://localhost:3000\nAPI:    http://localhost:8000\n'

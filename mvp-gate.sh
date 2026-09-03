#!/usr/bin/env bash
set -euo pipefail

printf '\nAWE MVP v1.0 release gate\n==========================\n'

command -v pnpm >/dev/null 2>&1 || { echo 'ERROR: pnpm is required.'; exit 1; }
if [[ -x ".venv/bin/python" ]]; then
  python_bin=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_bin="$(command -v python3)"
else
  echo 'ERROR: Python 3.12+ is required.'
  exit 1
fi

python_version=$("$python_bin" --version)
python_major=$("$python_bin" -c 'import sys; print(sys.version_info.major)')
python_minor=$("$python_bin" -c 'import sys; print(sys.version_info.minor)')

if (( python_major < 3 || (python_major == 3 && python_minor < 12) )); then
  echo "ERROR: Python 3.12+ is required; found $python_version."
  exit 1
fi

export AWE_PYTHON="$python_bin"

node_version=$(node --version 2>/dev/null || true)
pnpm_version=$(pnpm --version)
printf 'Node: %s\npnpm: %s\nPython: %s\n\n' "${node_version:-unavailable}" "$pnpm_version" "$python_version"

pnpm lint
pnpm build
pnpm test

printf '\nMVP RELEASE GATE: GREEN\n'
printf 'Core repository checks passed. Start the executable stack with:\n  docker compose up --build\n\nStudio: http://localhost:3000\nAPI:    http://localhost:8000\n'

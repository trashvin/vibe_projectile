#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$ROOT_DIR/setup/bootstrap.sh"
bash "$ROOT_DIR/setup/install.sh"

VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

if [ -f "$ROOT_DIR/src/main.py" ]; then
  python -m src.main
else
  echo "No src/main.py found; app code not implemented yet"
  exit 1
fi

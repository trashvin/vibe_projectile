#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d .git ]; then
  echo "Initializing git repository in $ROOT_DIR"
  git init
else
  echo "Git repo already initialized"
fi

VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  echo "Virtual environment created. Activate with: source $VENV_DIR/bin/activate"
else
  echo "Virtual environment already exists at $VENV_DIR"
fi

echo "Bootstrap complete."
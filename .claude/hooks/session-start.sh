#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

echo "Setting up project directory: $PROJECT_DIR"

# Auto-install dependencies for each sub-project
for dir in "$PROJECT_DIR"/*/; do
  [ -d "$dir" ] || continue

  # Node.js
  if [ -f "$dir/package.json" ]; then
    echo "Installing Node dependencies in $dir..."
    (cd "$dir" && npm install)
  fi

  # Python (pip)
  if [ -f "$dir/requirements.txt" ]; then
    echo "Installing Python dependencies in $dir..."
    (cd "$dir" && pip install -r requirements.txt -q)
  fi

  # Python (pyproject.toml / poetry)
  if [ -f "$dir/pyproject.toml" ]; then
    if command -v poetry &>/dev/null; then
      echo "Installing Poetry dependencies in $dir..."
      (cd "$dir" && poetry install --no-interaction)
    else
      echo "Installing Python dependencies via pip in $dir..."
      (cd "$dir" && pip install -e . -q)
    fi
  fi

  # Go
  if [ -f "$dir/go.mod" ]; then
    echo "Downloading Go modules in $dir..."
    (cd "$dir" && go mod download)
  fi

  # Rust
  if [ -f "$dir/Cargo.toml" ]; then
    echo "Fetching Rust dependencies in $dir..."
    (cd "$dir" && cargo fetch)
  fi
done

echo "Session start setup complete."

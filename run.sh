#!/usr/bin/env bash
set -e

# Navigate to the project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check if .venv exists
if [ -d "$PROJECT_DIR/.venv" ]; then
    echo "Starting development server using virtual environment..."
    "$PROJECT_DIR/.venv/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "Virtual environment not found in $PROJECT_DIR/.venv. Falling back to system uvicorn..."
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi

#!/usr/bin/env bash
set -e

# Navigate to the project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Auto-provision virtual environment if it does not exist
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "⚙️ Virtual environment not found. Automatically setting up .venv..."
    python3 -m venv "$PROJECT_DIR/.venv"
    echo "📦 Installing required dependencies from requirements.txt..."
    "$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    echo "✅ Setup finished!"
fi

echo "🚀 Starting development server on http://0.0.0.0:8000 ..."
"$PROJECT_DIR/.venv/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

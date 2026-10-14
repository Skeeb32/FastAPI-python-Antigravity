"""
Convenience entrypoint script to launch the FastAPI server.
Usage:
    python run.py
"""

import os
import sys

# Ensure uvicorn is available or re-execute inside .venv if present
try:
    import uvicorn
except ImportError:
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print("💡 Detected virtual environment at .venv. Re-launching with .venv...")
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("\n❌ Error: 'uvicorn' is not installed in the current Python environment.")
        print(f"Current Python executable: {sys.executable}\n")
        print("👉 Run this one-liner to set up and launch automatically:")
        print("    ./run.sh\n")
        print("👉 Or set up manually:")
        print("    python3 -m venv .venv")
        print("    source .venv/bin/activate")
        print("    pip install -r requirements.txt")
        print("    python run.py\n")
        sys.exit(1)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

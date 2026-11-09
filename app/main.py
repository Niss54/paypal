"""Root-level app proxy module for deployment compatibility.

Enables both `uvicorn app.main:app` (Render default start command) and
`uvicorn backend.app.main:app` to work seamlessly.
"""
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.main import app

__all__ = ["app"]

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for layer in ("contract-share", "ui-share"):
    path = ROOT / layer
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

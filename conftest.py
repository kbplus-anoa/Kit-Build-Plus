import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAYERS = ("contract-share", "ui-share", "ingest", "extract",
          "kit", "rebuild", "score", "export")
for layer in LAYERS:
    path = ROOT / layer
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

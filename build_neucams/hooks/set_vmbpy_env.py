import os, sys
from pathlib import Path

app_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
vmbpy_dir = app_dir / "vmbpy"  # you ship this folder
prev = os.environ.get("PATH", "")
os.environ["PATH"] = str(vmbpy_dir) + (";" + prev if prev else "")
# Optionally, set a custom env var if your code expects it
# os.environ["VMBPY_DLL_PATH"] = str(vmbpy_dir) 
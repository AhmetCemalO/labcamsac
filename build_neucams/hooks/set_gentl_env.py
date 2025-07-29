import os, sys
from pathlib import Path

app_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
gentl_dir = app_dir / "gentl"          # you ship this folder
prev = os.environ.get("GENICAM_GENTL64_PATH", "")
os.environ["GENICAM_GENTL64_PATH"] = str(gentl_dir) + (";" + prev if prev else "")
os.environ["PATH"] = str(gentl_dir) + ";" + os.environ["PATH"]

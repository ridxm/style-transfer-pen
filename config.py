"""Central configuration for penDNA. Secrets come from environment variables."""
import os
from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CAPTURES_DIR = DATA_DIR / "captures"
OUTPUTS_DIR = DATA_DIR / "outputs"
for d in (DATA_DIR, CAPTURES_DIR, OUTPUTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- BLE / Pen ---
PEN_BLE_NAME = os.getenv("PEN_BLE_NAME", "penDNA")
PEN_SERVICE_UUID = os.getenv("PEN_SERVICE_UUID", "19B10000-E8F2-537E-4F6C-D104768A1214")
PEN_CHAR_UUID = os.getenv("PEN_CHAR_UUID", "19B10001-E8F2-537E-4F6C-D104768A1214")
PEN_SAMPLE_HZ = 100

# --- Camera ---
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
# Paper area in camera pixels (calibrated per setup). (x, y, w, h).
PAPER_ROI = (100, 50, 1080, 620)
# HSV range for pen tip color tracking (tune to marker color).
PEN_TIP_HSV_LOW = (0, 120, 70)
PEN_TIP_HSV_HIGH = (10, 255, 255)

# --- Paper / Plotter ---
PAPER_WIDTH_MM = 148.0   # A5
PAPER_HEIGHT_MM = 210.0
PLOTTER_PORT = os.getenv("PLOTTER_PORT", "/dev/ttyUSB0")
PLOTTER_BAUD = int(os.getenv("PLOTTER_BAUD", "115200"))
PLOTTER_FEED_DRAW = 2000    # mm/min default draw feedrate
PLOTTER_FEED_TRAVEL = 5000  # mm/min pen-up travel
PEN_DOWN_CMD = "M3 S255"
PEN_UP_CMD = "M5"

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# --- Demo server ---
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = ROOT_DIR / "datasets"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RECREACION_CSV = DATASETS_DIR / "recreacion_0.csv"
OPINIONES_CSV = DATASETS_DIR / "opiniones_google.csv"
BALNEARIOS_CSV = DATASETS_DIR / "balnearios_0.csv"

CSV_ENCODINGS = {
    "recreacion": "latin1",
    "balnearios": "latin1",
    "opiniones": "latin1",
}

CSV_SEPARATOR = ";"

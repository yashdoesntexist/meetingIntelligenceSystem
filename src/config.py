from pathlib import Path
#Configuration Settings
#Author: Meriem Lmoubariki
#Project-wide configuration and paths

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "AMI"
PROCESSED_DIR = DATA_DIR / "processed"

DEFAULT_OUTPUT_JSON = PROCESSED_DIR / "actions.json"
DEFAULT_MODEL_PATH = PROCESSED_DIR / "clf.joblib"


PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

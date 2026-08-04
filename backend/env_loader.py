"""Load backend/.env reliably regardless of process working directory."""
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)

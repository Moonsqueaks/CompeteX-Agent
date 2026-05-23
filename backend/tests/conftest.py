import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(BACKEND_ROOT / ".env.test", override=False)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DOUBAO_API_KEY", "")

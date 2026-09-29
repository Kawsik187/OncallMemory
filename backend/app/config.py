import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current working dir
env_paths = [
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path.cwd() / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break
else:
    load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
HINDSIGHT_URL: str = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
HINDSIGHT_API_KEY: str | None = os.getenv("HINDSIGHT_API_KEY") or None

# Bank ID must match across every file/tool: exactly "oncall-memory"
BANK_ID: str = "oncall-memory"

PORT: int = int(os.getenv("PORT", "8000"))
HOST: str = os.getenv("HOST", "0.0.0.0")

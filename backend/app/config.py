"""Central settings. Values come from environment variables or a .env file in backend/."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = BASE_DIR / "satark_core"      # model + analyzers (SATARK NETRA engine)
STATIC_DIR = BASE_DIR / "static"         # built React frontend is copied here


def _load_env_file():
    f = BASE_DIR / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file()


def _bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


DB_PATH = os.environ.get("SCAMSHIELD_DB", str(BASE_DIR / "scamshield.db"))
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

# Live URL intelligence (domain age via RDAP, redirects, SSL). Needs internet; turn off for offline demo.
DEEP_CHECKS = _bool("DEEP_CHECKS", True)
FETCH_WEBSITES = _bool("FETCH_WEBSITES", True)       # fetch a page when the user gives a website address

MAX_TEXT_CHARS = int(os.environ.get("MAX_TEXT_CHARS", 20000))
MAX_HTML_BYTES = int(os.environ.get("MAX_HTML_BYTES", 2_000_000))
MAX_APK_MB = int(os.environ.get("MAX_APK_MB", 60))

# An identifier (domain, phone, UPI ...) reported in at least this many Medium/High cases is treated as blacklisted.
BLACKLIST_MIN_REPORTS = int(os.environ.get("BLACKLIST_MIN_REPORTS", 2))

# Optional LLM for the investigation assistant. Without a key a built-in rule-based assistant answers from case records.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ASSISTANT_MODEL = os.environ.get("ASSISTANT_MODEL", "claude-sonnet-5-5")

"""
Server configuration — environment variables, logging, constants.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from server/ (one level up from server/src/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Persistent VRChat rate-limit state file (next to .env)
VRC_STATE_FILE = Path(__file__).resolve().parent.parent / "vrc_state.json"

# ── Logging ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("lineup-server")

# ── Config ────────────────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_KEY = os.environ.get("API_KEY", "")
VRCHAT_USERNAME = os.environ.get("VRCHAT_USERNAME", "")
VRCHAT_PASSWORD = os.environ.get("VRCHAT_PASSWORD", "")
VRCHAT_TOTP_SECRET = os.environ.get("VRCHAT_TOTP_SECRET", "").replace(" ", "")

if not BOT_TOKEN:
    log.warning("DISCORD_BOT_TOKEN not set — bot will not start.")
if not API_KEY:
    log.warning("API_KEY not set — all requests will be rejected.")
if not VRCHAT_USERNAME:
    log.warning("VRCHAT_USERNAME not set — VRChat API will not work.")

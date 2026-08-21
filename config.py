import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Parse OWNER_ID
_owner_id_raw = os.getenv("OWNER_ID", "").strip()
OWNER_ID = int(_owner_id_raw) if _owner_id_raw.isdigit() else None

# Parse TRUSTED_USER_IDS (comma-separated list of integers)
_trusted_raw = os.getenv("TRUSTED_USER_IDS", "").strip()
TRUSTED_USER_IDS = set()
if _trusted_raw:
    for item in _trusted_raw.split(","):
        item = item.strip()
        if item.isdigit():
            TRUSTED_USER_IDS.add(int(item))

# Parse MOD_LOG_CHANNEL_ID (optional)
_mod_log_raw = os.getenv("MOD_LOG_CHANNEL_ID", "").strip()
MOD_LOG_CHANNEL_ID = int(_mod_log_raw) if _mod_log_raw.isdigit() else None

def is_authorized_user(user_id: int) -> bool:
    """Check if a Discord user ID is authorized to use moderation tools."""
    if user_id is None:
        return False
    if OWNER_ID is not None and user_id == OWNER_ID:
        return True
    return user_id in TRUSTED_USER_IDS

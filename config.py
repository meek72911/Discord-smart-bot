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

# --- Model routing ---
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.6-flash").strip()
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-3.5-flash-lite").strip()

# --- OpenRouter & Groq Multi-Engine Architecture ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free").strip()
OPENROUTER_REASONING_MODEL = os.getenv("OPENROUTER_REASONING_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "groq").strip().lower()  # groq | gemini | openrouter

# --- Guild allowlist (empty = allow all guilds) ---
ALLOWED_GUILD_IDS = set()
_allow_raw = os.getenv("ALLOWED_GUILD_IDS", "").strip()
if _allow_raw:
    for item in _allow_raw.split(","):
        item = item.strip()
        if item.isdigit():
            ALLOWED_GUILD_IDS.add(int(item))

def is_guild_allowed(guild_id) -> bool:
    """Check if a guild is allowed. DMs (guild_id None) always allowed."""
    if guild_id is None:
        return True
    if not ALLOWED_GUILD_IDS:
        return True
    return int(guild_id) in ALLOWED_GUILD_IDS

# --- Watch mode (AI moderation flagging) ---
WATCH_MODE = os.getenv("WATCH_MODE", "").strip().lower() in ("1", "true", "yes", "on")
_watch_log_raw = os.getenv("WATCH_LOG_CHANNEL_ID", "").strip()
WATCH_LOG_CHANNEL_ID = int(_watch_log_raw) if _watch_log_raw.isdigit() else None
WATCH_SEVERITY_THRESHOLD = 4  # 1-10 scale; only flag at/above this

def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")

# --- Human confirmation gates for destructive tools (ban/bulk/purge/delete etc.) ---
CONFIRM_DESTRUCTIVE = _env_flag("CONFIRM_DESTRUCTIVE") if os.getenv("CONFIRM_DESTRUCTIVE") is not None else True


# --- Cooldown bypass — DEV: you are solo, so bypass is always on for 1463495220124454955 ---
_raw_bypass = os.getenv("COOLDOWN_BYPASS_IDS", "1463495220124454955").strip()
COOLDOWN_BYPASS_IDS: set[int] = set()
if _raw_bypass:
    for _b in _raw_bypass.split(","):
        _b = _b.strip()
        if _b.isdigit():
            COOLDOWN_BYPASS_IDS.add(int(_b))
# Dev note: Discord 5s gate and Gemini local RPM gate both bypassed for COOLDOWN_BYPASS_IDS.
# Google's server-side 10 RPM / 1500 RPD still applies — upgrade to paid Tier 1 (300 RPM, 1M TPM) when you go live.


def is_authorized_user(user_id: int) -> bool:
    """Check if a Discord user ID is authorized to use moderation tools."""
    if user_id is None:
        return False
    if OWNER_ID is not None and user_id == OWNER_ID:
        return True
    return user_id in TRUSTED_USER_IDS

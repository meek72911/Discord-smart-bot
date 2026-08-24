"""
Smart Bot OS — Discord OAuth2 Authentication & Role Guard Engine
Handles Discord OAuth login, admin permission verification (0x8 Administrator / 0x20 Manage Guild),
and Owner superadmin privilege enforcement.
"""

import os
import json
import time
import urllib.parse
import aiohttp
from typing import Dict, List, Optional, Any
from backend import database

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1540339098076577852")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/api/auth/callback")

# Owner Discord IDs with unrestricted global access
OWNER_DISCORD_IDS = set(
    filter(None, [x.strip() for x in os.getenv("OWNER_DISCORD_IDS", "1463495220124454955").split(",")])
)

# Discord Permission Bitflags
PERM_ADMINISTRATOR = 0x8
PERM_MANAGE_GUILD = 0x20

# Active in-memory session tokens (token -> user_dict)
_sessions: Dict[str, Dict[str, Any]] = {}


def get_discord_oauth_url(state: str = "beta") -> str:
    """Generates the official Discord OAuth2 authorization URL."""
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
        "prompt": "consent"
    }
    return f"https://discord.com/oauth2/authorize?{urllib.parse.urlencode(params)}"


def is_user_admin_of_guild(guild: Dict[str, Any]) -> bool:
    """Evaluates if the user has Administrator or Manage Guild permission in the Discord server."""
    if guild.get("owner", False):
        return True
    try:
        permissions = int(guild.get("permissions", "0"))
        if (permissions & PERM_ADMINISTRATOR) == PERM_ADMINISTRATOR:
            return True
        if (permissions & PERM_MANAGE_GUILD) == PERM_MANAGE_GUILD:
            return True
    except (ValueError, TypeError):
        pass
    return False


async def exchange_code_for_token(code: str) -> Optional[str]:
    """Exchanges authorization code for a Discord access token."""
    if not DISCORD_CLIENT_SECRET:
        return None

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers) as resp:
            if resp.status == 200:
                body = await resp.json()
                return body.get("access_token")
    return None


async def fetch_discord_user_profile(access_token: str) -> Optional[Dict[str, Any]]:
    """Fetches user identity profile from Discord API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
    return None


async def fetch_user_admin_guilds(access_token: str) -> List[Dict[str, Any]]:
    """Fetches all guilds where the authenticated user is an Administrator or Owner."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v10/users/@me/guilds", headers=headers) as resp:
            if resp.status == 200:
                guilds = await resp.json()
                return [g for g in guilds if is_user_admin_of_guild(g)]
    return []


def create_session(user_data: Dict[str, Any], guilds: List[Dict[str, Any]]) -> str:
    """Creates a local session token storing authenticated user & authorized server list."""
    discord_id = str(user_data.get("id"))
    is_owner = discord_id in OWNER_DISCORD_IDS or user_data.get("is_owner", False)

    # Upsert in database
    db_user = database.upsert_user(
        discord_id=discord_id,
        username=user_data.get("username", "DiscordUser"),
        avatar=user_data.get("avatar"),
        is_owner=is_owner
    )

    token = f"sb_session_{discord_id}_{int(time.time())}"
    _sessions[token] = {
        "user": db_user,
        "guilds": guilds,
        "is_owner": is_owner,
        "created_at": time.time()
    }
    return token


def get_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieves authenticated session by token."""
    return _sessions.get(token)


def create_mock_session(role: str = "admin", guild_id: int = 112233) -> Dict[str, Any]:
    """Generates instant local developer session for rapid verification and offline sandbox."""
    is_owner = (role.lower() == "owner")
    mock_discord_id = "1463495220124454955" if is_owner else "9988776655"
    mock_username = "Vipul (Owner)" if is_owner else "ServerAdmin_Alex"

    user = database.upsert_user(
        discord_id=mock_discord_id,
        username=mock_username,
        avatar=None,
        is_owner=is_owner
    )

    mock_guilds = [
        {
            "id": str(guild_id),
            "name": "Community Alpha Hub",
            "icon": None,
            "owner": True,
            "permissions": "8"
        }
    ]

    token = f"mock_{'owner' if is_owner else 'admin'}_{mock_discord_id}"
    _sessions[token] = {
        "user": user,
        "guilds": mock_guilds,
        "is_owner": is_owner,
        "created_at": time.time()
    }

    return {
        "token": token,
        "user": user,
        "guilds": mock_guilds,
        "is_owner": is_owner
    }

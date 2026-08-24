"""
Smart Bot Visual Embed Engine
Engineered for ultra-clean, high-contrast, modern Discord aesthetics.
"""

import discord
import datetime
from typing import Optional, List, Tuple, Any

# Modern Cyber / Luxury Discord Palette
COLORS = {
    "success": 0x57F287,       # Emerald Green
    "warn": 0xFEE75C,          # Electric Yellow
    "error": 0xED4245,         # Crimson Red
    "info": 0x5865F2,          # Blurple Core
    "mod": 0xFF7A00,           # Vivid Orange
    "intelligence": 0x818CF8,  # Indigo Intelligence
    "pink": 0xEB459E,          # Magenta Hype
}

def make_embed(
    title: str = "",
    description: str = "",
    color: int = COLORS["info"],
    fields: Optional[List[Tuple[str, str, bool]]] = None,
    thumbnail: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon: Optional[str] = None
) -> discord.Embed:
    embed = discord.Embed(
        title=title[:256] if title else None,
        description=description[:4096] if description else None,
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    if fields:
        for name, value, inline in fields[:25]:
            embed.add_field(name=name[:256], value=value[:1024] or "\u200b", inline=bool(inline))
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer[:2048], icon_url=footer_icon)
    return embed

def success_embed(title: str, desc: str = "", fields=None):
    return make_embed(title=f"✨ {title}", description=desc, color=COLORS["success"], fields=fields)

def warn_embed(title: str, desc: str = "", fields=None):
    return make_embed(title=f"⚠️ {title}", description=desc, color=COLORS["warn"], fields=fields)

def error_embed(title: str, desc: str = "", fields=None):
    return make_embed(title=f"❌ {title}", description=desc, color=COLORS["error"], fields=fields)

def mod_embed(title: str, desc: str = "", fields=None):
    return make_embed(title=f"🛡️ {title}", description=desc, color=COLORS["mod"], fields=fields)

def intelligence_embed(title: str, desc: str = "", fields=None):
    return make_embed(title=f"📊 {title}", description=desc, color=COLORS["intelligence"], fields=fields)

def level_embed(member: discord.Member, level: int, xp: int) -> discord.Embed:
    """Renders a sleek XP level-up card with visual progress bar."""
    progress_in_level = xp % 100
    bars = int(progress_in_level / 10)
    bar_str = "▰" * bars + "▱" * (10 - bars)

    embed = make_embed(
        title="🌟 Community Level Up!",
        description=(
            f">>> **Congratulations {member.display_name}!**\n"
            f"You have ascended to **Level {level}** ({xp:,} Total XP)\n\n"
            f"`Progress:` `[{bar_str}]` `{progress_in_level}/100 XP`"
        ),
        color=COLORS["intelligence"],
        thumbnail=str(member.display_avatar.url) if member.display_avatar else None,
        footer="Keep engaging with the community to unlock badges & roles!",
    )
    return embed

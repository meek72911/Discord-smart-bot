"""
Smart Bot Unified Enterprise Architecture & UI Suite
Implements:
1. Production UI Kit (Modern Palette, Status Badges, Live Streaming Card, Level-up Embeds)
2. Interactive Controls (BYOK Registration Modal, Control Center Dashboard, 30s Danger Gate)
3. Hardened Tools (purge_messages fallback for >14d Error 50034, Destructive Confirmation)
4. Context & Storage Management (Fernet Multi-Tenant BYOK, SQLite WAL auto-maintenance)
"""

import asyncio
import datetime
import os
import contextvars
from typing import Optional, List, Dict, Any, Tuple
import aiohttp
import aiosqlite
import discord
from discord import ui
from cryptography.fernet import Fernet

# =========================================================
# 1. CONTEXT VARIABLES & GLOBAL STATE
#    Note: existing tools.py defines current_user_id as int; this augments with guild_id
# =========================================================
current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_user_id", default=None)
current_reminder_channel: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_reminder_channel", default=None)
current_guild_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_guild_id", default=None)

# =========================================================
# 2. DESIGN SYSTEM & MODERN UI PALETTE
# =========================================================
class UIColors:
    BRAND_BLURPLE = 0x5865F2   # Primary Accent
    SUCCESS_EMERALD = 0x57F287  # Confirmed / Active State
    WARN_AMBER = 0xFEE75C       # Pending / High Latency
    DANGER_CORAL = 0xED4245     # Errors / Critical Destructive
    MOD_ORANGE = 0xFF7A00       # Moderation Actions
    DARK_SURFACE = 0x2B2D31     # Discord Native Canvas
    XP_GOLD = 0xF1C40F          # Leveling & Achievements

class BotUI:
    @staticmethod
    def dashboard(guild_name: str, model_name: str, quota_used: str, byok_active: bool, ping_ms: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚡ {guild_name} — Control Center",
            description="Autonomous Discord Management & LLM Gateway active.",
            color=UIColors.BRAND_BLURPLE,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        byok_badge = "🟢 `BYOK ACTIVE`" if byok_active else "🟡 `SHARED TIER`"
        embed.add_field(name="🧠 Active Model", value=f"`{model_name}`", inline=True)
        embed.add_field(name="🔑 Key Engine", value=byok_badge, inline=True)
        embed.add_field(name="📡 Latency", value=f"`{ping_ms}ms`", inline=True)
        embed.add_field(name="📊 24h Quota", value=f"`{quota_used}`", inline=True)
        embed.add_field(name="🛡️ Watch Mode", value="`ACTIVE (Sev >= 4)`", inline=True)
        embed.add_field(name="⚙️ WAL Storage", value="`SYNCHRONIZED`", inline=True)
        embed.set_footer(text="Smart Bot OS • Enterprise Ready")
        return embed

    @staticmethod
    def streaming_card(user_prompt: str) -> discord.Embed:
        prompt_snippet = (user_prompt[:90] + "...") if len(user_prompt) > 90 else user_prompt
        embed = discord.Embed(
            description="⏳ *Smart Bot is analyzing and streaming response...*",
            color=UIColors.DARK_SURFACE
        )
        embed.set_author(name=f"Prompt: \"{prompt_snippet}\"")
        return embed

    @staticmethod
    def action_confirmed(title: str, detail: str, actor: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"✅ {title}",
            description=detail,
            color=UIColors.SUCCESS_EMERALD,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text=f"Action executed by {actor}")
        return embed

    @staticmethod
    def level_up(member: discord.Member, level: int, total_xp: int) -> discord.Embed:
        # Fixed: no ping — use display_name instead of mention
        embed = discord.Embed(
            title="✨ Level Up!",
            description=f"Congratulations **{member.display_name}**!\nYou unlocked **Level {level}**.",
            color=UIColors.XP_GOLD,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="🏆 Total XP", value=f"`{total_xp:,} XP`", inline=True)
        embed.add_field(name="🎯 Next Tier", value=f"`{(level + 1) * 100:,} XP`", inline=True)
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        return embed

# =========================================================
# 3. FERNET-ENCRYPTED BYOK KEY MANAGER
# =========================================================
class GuildKeyManager:
    def __init__(self, master_fernet_key: Optional[str] = None):
        key = master_fernet_key or os.getenv("FERNET_KEY")
        if not key:
            key = Fernet.generate_key().decode()
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt_key(self, api_key: str) -> Tuple[str, str]:
        token = self.fernet.encrypt(api_key.encode()).decode()
        hint = f"...{api_key[-4:]}" if len(api_key) >= 4 else "..."
        return token, hint

    def decrypt_key(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    async def validate_gemini_key(self, api_key: str) -> bool:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, timeout=5) as resp:
                    return resp.status == 200
            except Exception:
                return False

# =========================================================
# 4. INTERACTIVE MODALS & DASHBOARD VIEWS
# =========================================================
class BYOKSetupModal(ui.Modal, title="Configure Gemini BYOK API Key"):
    api_key_input = ui.TextInput(
        label="Google AI Studio Key",
        placeholder="AIzaSy...",
        style=discord.TextStyle.short,
        min_length=30,
        max_length=60,
        required=True
    )

    def __init__(self, key_manager: GuildKeyManager, db_path: str):
        super().__init__()
        self.key_manager = key_manager
        self.db_path = db_path

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        raw_key = self.api_key_input.value.strip()

        is_valid = await self.key_manager.validate_gemini_key(raw_key)
        if not is_valid:
            err = discord.Embed(
                title="❌ Invalid Key",
                description="Failed to validate key with Google AI Studio. Check permissions at `aistudio.google.com`.",
                color=UIColors.DANGER_CORAL
            )
            await interaction.followup.send(embed=err, ephemeral=True)
            return

        encrypted_token, hint = self.key_manager.encrypt_key(raw_key)
        guild_id = str(interaction.guild_id) if interaction.guild else "DM"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO guild_keys 
                   (guild_id, provider, encrypted_key, hint, added_by, validated_at, status) 
                   VALUES (?, 'gemini', ?, ?, ?, ?, 'active')""",
                (guild_id, encrypted_token, hint, str(interaction.user.id), datetime.datetime.now(datetime.timezone.utc).isoformat())
            )
            await db.commit()

        success = discord.Embed(
            title="🔐 BYOK Locked & Active",
            description=f"Dedicated key enabled for this guild.\n\n**Hint:** `AIza...{hint}`\n**Status:** Dedicated Rate Limits Active",
            color=UIColors.SUCCESS_EMERALD
        )
        await interaction.followup.send(embed=success, ephemeral=True)

class DashboardView(ui.View):
    def __init__(self, key_manager: GuildKeyManager, db_path: str, is_admin: bool):
        super().__init__(timeout=180)
        self.key_manager = key_manager
        self.db_path = db_path
        self.is_admin = is_admin

    @ui.button(label="Set BYOK Key", style=discord.ButtonStyle.primary, emoji="🔑", row=0)
    async def set_key(self, interaction: discord.Interaction, button: ui.Button):
        if not self.is_admin:
            await interaction.response.send_message("⚠️ Admin permission required.", ephemeral=True)
            return
        await interaction.response.send_modal(BYOKSetupModal(self.key_manager, self.db_path))

class DestructiveActionView(ui.View):
    def __init__(self, initiator_id: int, on_confirm_callback):
        super().__init__(timeout=30.0)
        self.initiator_id = initiator_id
        self.on_confirm_callback = on_confirm_callback

    @ui.button(label="Confirm & Execute", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
            return
        self.stop()
        await interaction.response.defer()
        await self.on_confirm_callback(interaction)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
            return
        self.stop()
        await interaction.response.send_message("🚫 Action aborted.", ephemeral=True)

# =========================================================
# 5. HARDENED PURGE ENGINE (WITH ERROR 50034 FALLBACK)
# =========================================================
async def purge_messages_safe(channel: discord.TextChannel, limit: int) -> int:
    """Purges messages with automatic fallback to single-delete when messages exceed 14 days."""
    deleted_count = 0
    try:
        deleted = await channel.purge(limit=limit, bulk=True)
        return len(deleted)
    except discord.HTTPException as e:
        if e.code == 50034:  # Messages older than 14 days cannot be bulk deleted
            async for msg in channel.history(limit=limit):
                try:
                    await msg.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.7)  # Discord API rate-limit avoidance
                except discord.HTTPException:
                    continue
            return deleted_count
        raise e

# =========================================================
# 6. SQLITE WAL AUTOMATED MAINTENANCE WORKER
# =========================================================
async def sqlite_maintenance_worker(db_path: str, interval_hours: int = 24):
    """Periodically truncates WAL logs and prunes dead cache memory."""
    while True:
        await asyncio.sleep(interval_hours * 3600)
        try:
            async with aiosqlite.connect(db_path) as db:
                await db.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                await db.execute("VACUUM;")
                # Prune old channel memory beyond 30 days
                cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
                await db.execute("DELETE FROM channel_memory WHERE updated_at < ?", (cutoff.timestamp(),))
                await db.commit()
        except Exception:
            pass

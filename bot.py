import asyncio
import logging
import re
import sys
import time
from typing import Dict, List, Optional
import discord
from discord import app_commands
from discord.ext import commands

import config
import storage
import ai_service
import embeds
import onboarding as ob
import voice_service
import collector
import knowledge_base
import community_brain
import community_graph
import community_analyst

from logging.handlers import RotatingFileHandler

# Enterprise Multi-Handler Logger Configuration
logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Formatter
log_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s")

# 1. Console Stream Handler with UTF-8 safety
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# 2. General Rotating File Handler (5MB x 5 backups)
file_handler = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# 3. Dedicated Error Rotating File Handler (Captures ERROR & CRITICAL with full stack traces)
error_file_handler = RotatingFileHandler("bot_errors.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(log_format)
logger.addHandler(error_file_handler)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True


class SmartBot(commands.Bot):
    async def setup_hook(self) -> None:
        try:
            await self.tree.sync()
            logger.info("Slash command tree synced successfully")
        except Exception as e:
            logger.error(f"Tree sync failed: {e}", exc_info=True)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logger.error(f"Unhandled exception in Discord event '{event_method}'", exc_info=True)


# commands.Bot IS a Client subclass — every existing client.* reference stays valid.
client = SmartBot(command_prefix="!unused!", intents=intents, help_command=None)

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"Slash command '{interaction.command.name if interaction.command else 'Unknown'}' error: {error}", exc_info=True)
    try:
        if interaction.response.is_done():
            await interaction.followup.send("⚠️ An internal error occurred while processing this command. The issue has been logged.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ An internal error occurred while processing this command. The issue has been logged.", ephemeral=True)
    except Exception:
        pass

USER_COOLDOWNS: Dict[int, float] = {}
COOLDOWN_SECONDS = 5.0
COOLDOWN_EVICT_SECONDS = 3600.0
MAX_ATTACHMENTS = 5
EDIT_THROTTLE_SECONDS = 1.2
TYPING_REFRESH_SECONDS = 8.0

WATCH_USER_COOLDOWN = 60.0
WATCH_LAST_CHECK: Dict[int, float] = {}
WATCH_MAX_PER_HOUR = 120
WATCH_TIMESTAMPS: List[float] = []
_START_TS = time.time()

CATCHUP_RE = re.compile(
    r"^\s*(catch\s*me\s*up|summar(ize|ise)\s*(the\s*)?(chat|channel|recent)?|what\s*did\s*i\s*miss)\s*[?.!]*\s*$",
    re.IGNORECASE,
)
TRANSLATE_RE = re.compile(r"\btranslate\b.*?\bto\s+([a-z]{2,20})\b", re.IGNORECASE)


def clean_message_content(content: str, bot_user) -> str:
    if not bot_user or not content:
        return content
    return re.sub(rf"<@!?{bot_user.id}>", "", content).strip()


def evict_stale_cooldowns():
    now = time.time()
    if len(USER_COOLDOWNS) > 500:
        stale = [uid for uid, ts in USER_COOLDOWNS.items() if now - ts > COOLDOWN_EVICT_SECONDS]
        for uid in stale:
            del USER_COOLDOWNS[uid]


def is_user_on_cooldown(user_id: int, cooldown_seconds: float = COOLDOWN_SECONDS):
    if user_id in config.COOLDOWN_BYPASS_IDS:
        logger.info(f"cooldown bypass hit for user_id={user_id}")
        return False, 0.0
    now = time.time()
    elapsed = now - USER_COOLDOWNS.get(user_id, 0.0)
    if elapsed < cooldown_seconds:
        return True, round(cooldown_seconds - elapsed, 1)
    return False, 0.0


def update_user_cooldown(user_id: int):
    if user_id in config.COOLDOWN_BYPASS_IDS:
        logger.debug(f"skipping cooldown update for bypass user_id={user_id}")
        return
    evict_stale_cooldowns()
    USER_COOLDOWNS[user_id] = time.time()


async def send_reply_safe(message: discord.Message, text: Optional[str] = None, embed: Optional[discord.Embed] = None):
    try:
        return await message.reply(content=text, embed=embed, mention_author=False)
    except discord.NotFound:
        logger.warning("Original message deleted before reply; sending to channel instead.")
        try:
            return await message.channel.send(content=text, embed=embed)
        except Exception as e:
            logger.error(f"Failed to send fallback message: {e}")
    except (discord.Forbidden, discord.HTTPException) as e:
        logger.error(f"Failed to reply: {e}")
    return None


def split_message(text: str, limit: int = 1900) -> List[str]:
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = text.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks


async def _keep_typing(channel):
    """Refresh typing indicator periodically until cancelled."""
    try:
        while True:
            async with channel.typing():
                await asyncio.sleep(TYPING_REFRESH_SECONDS - 0.5)
    except asyncio.CancelledError:
        pass


def _is_guild_configured(guild_id: int) -> bool:
    """True if owner completed any onboarding step (log channel or trusted mods set)."""
    try:
        cfg = storage.get_guild_config(guild_id)
        return bool(cfg["log_channel_id"] or cfg["trusted_ids"])
    except Exception:
        return False


async def _post_setup_card(channel: discord.abc.Messageable, guild: discord.Guild):
    configured = _is_guild_configured(guild.id)
    try:
        await channel.send(
            embed=ob.setup_card_embed(guild, configured),
            view=ob.OnboardingView(for_user_id=guild.owner_id or 0),
        )
        logger.info(f"Setup card posted in guild {guild.id} ({guild.name}) configured={configured}")
    except discord.Forbidden:
        logger.warning(f"No permission to post setup card in guild {guild.id}")
    except Exception as e:
        logger.error(f"Failed posting setup card: {e}")


@client.event
async def on_guild_join(guild: discord.Guild):
    """AUTO-SCAN Server DNA and AUTO-POST the Setup Card the moment the bot joins a server."""
    logger.info(f"Joined new guild {guild.id} ({guild.name}) — members={guild.member_count}")
    
    # 1. Quick initial scan of public rules & announcements to seed Server DNA
    try:
        rules_text = ""
        announcements_text = ""
        for ch in guild.text_channels:
            if not getattr(ch.permissions_for(guild.me), "read_messages", False):
                continue
            name_low = ch.name.lower()
            if "rule" in name_low or "faq" in name_low or "guide" in name_low:
                async for m in ch.history(limit=5):
                    if m.content:
                        rules_text += m.content + "\n"
            elif "announcement" in name_low or "news" in name_low or "update" in name_low:
                async for m in ch.history(limit=5):
                    if m.content:
                        announcements_text += m.content + "\n"
        
        community_brain.extract_server_dna(
            guild_id=guild.id,
            guild_name=guild.name,
            rules_text=rules_text,
            announcements_text=announcements_text,
            channel_names=[c.name for c in guild.text_channels[:15]]
        )
    except Exception as e:
        logger.warning(f"Initial DNA scan on guild join skipped/failed: {e}")

    # 2. Post Setup & Server Intelligence Card
    channel = guild.system_channel
    if channel is None or not channel.permissions_for(guild.me).send_messages:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
    if channel:
        await _post_setup_card(channel, guild)


@client.event
async def on_ready():
    logger.info(f"Bot logged in as {client.user} (ID: {client.user.id})")
    logger.info(f"Owner ID: {config.OWNER_ID}")
    logger.info(f"Trusted User IDs: {config.TRUSTED_USER_IDS}")
    logger.info(f"Models: chat={config.CHAT_MODEL} fast={config.FAST_MODEL} provider={config.CHAT_PROVIDER} watch={config.WATCH_MODE}")
    if config.ALLOWED_GUILD_IDS:
        logger.info(f"Guild allowlist active: {config.ALLOWED_GUILD_IDS}")
    logger.info(f"Connected guilds: {len(client.guilds)}")
    try:
        await client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="mentions | /setup")
        )
    except Exception:
        pass
    # Start background loops
    client.loop.create_task(_reminder_loop())


@client.event
async def on_guild_join(guild: discord.Guild):
    """Post welcome setup card only when the bot first joins a new server."""
    logger.info(f"Bot joined new guild: {guild.name} (ID: {guild.id})")
    channel = guild.system_channel
    if channel is None or not channel.permissions_for(guild.me).send_messages:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
    if channel:
        try:
            await _post_setup_card(channel, guild)
        except Exception as e:
            logger.warning(f"Failed to post welcome card on join: {e}")


# =========================================================
# SLASH COMMANDS (onboarding & discovery)
# =========================================================

@client.tree.command(name="setup", description="Configure Smart Bot for this server (60-second wizard)")
async def slash_setup(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Run /setup inside your server.", ephemeral=True)
        return
    if not (config.is_authorized_user(interaction.user.id) or interaction.user.guild_permissions.manage_guild):
        await interaction.response.send_message("⛔ You need **Manage Server** permission.", ephemeral=True)
        return
    embed = ob.setup_card_embed(interaction.guild, _is_guild_configured(interaction.guild.id))
    embed.title = f"⚙️ /setup — {interaction.guild.name}"
    embed.description = "Pick options below — every choice saves instantly.\nRe-run anytime; finished steps are kept."
    await interaction.response.send_message(embed=embed, view=ob.OnboardingView(for_user_id=interaction.user.id), ephemeral=True)


@client.tree.command(name="help", description="Everything Smart Bot can do")
async def slash_help(interaction: discord.Interaction):
    pages = ob.build_help_embeds()
    await interaction.response.send_message(embeds=pages[:10], ephemeral=True)


@client.tree.command(name="status", description="Bot health, system & quota snapshot")
async def slash_status(interaction: discord.Interaction):
    from enterprise_suite import BotUI
    ping_ms = round((client.latency or 0) * 1000)
    embed = BotUI.dashboard(
        guild_name=interaction.guild.name if interaction.guild else "DM",
        model_name="Smart Bot Neural Core",
        quota_used="Active • High Performance",
        byok_active=False,
        ping_ms=ping_ms,
    )
    embed.add_field(name="⏱️ Uptime", value=f"<t:{int(_START_TS)}:R>", inline=True)
    embed.add_field(name="🏠 Guilds", value=str(len(client.guilds)), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command(name="config", description="Show current settings for this server")
@app_commands.checks.has_permissions(manage_guild=True)
async def slash_config(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Server-only command.", ephemeral=True)
        return
    cfg = storage.get_guild_config(interaction.guild.id)
    persona = storage.get_guild_persona(interaction.guild.id)
    log_ch = f"<#{cfg['log_channel_id']}>" if cfg["log_channel_id"] else "not set"
    mods = ", ".join(f"<@&{r}>" for r in cfg["trusted_ids"]) if cfg["trusted_ids"] else "none (owner only)"
    embed = discord.Embed(title="⚙️ Current configuration", color=0x5865F2)
    embed.add_field(name="Mod-log", value=log_ch, inline=True)
    embed.add_field(name="Trusted mod roles", value=mods, inline=True)
    embed.add_field(name="Watch mode", value="ON" if cfg["watch_enabled"] else "OFF", inline=True)
    embed.add_field(name="Persona", value=persona, inline=True)
    embed.add_field(name="AI Engine", value="Smart Bot Autonomous Core", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# SMART BOT OS v5.0 — COMMUNITY BRAIN SLASH COMMANDS
# =========================================================

@client.tree.command(name="brain", description="Ask the Community Brain about server history, rules, or decisions")
@app_commands.describe(query="Question to ask the Community Brain (e.g. 'Why was the tournament rescheduled?')")
async def slash_brain(interaction: discord.Interaction, query: str):
    if interaction.guild is None:
        await interaction.response.send_message("Run /brain inside your server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    res = community_brain.query_community_brain_unified(interaction.guild.id, query)
    
    embed = discord.Embed(
        title=f"🧠 Community Brain — {interaction.guild.name}",
        description=f"**Query:** *\"{query}\"*\n\n",
        color=0x5865F2
    )

    if res.get("causal_chain"):
        chain_text = ""
        for step in res["causal_chain"][:3]:
            chain_text += f"• **[{step['entity_type']}] {step['name']}**: {step['summary'][:90]}\n"
        embed.add_field(name="🔗 Causal Chain & Decisions", value=chain_text or "No direct causal path", inline=False)

    if res.get("knowledge_entries"):
        kb_text = ""
        for kb in res["knowledge_entries"][:2]:
            kb_text += f"• **[{kb['category']}] {kb['title']}**: {kb['content'][:100]}\n"
        embed.add_field(name="📚 Verified Rules & Records", value=kb_text, inline=False)

    dna = res.get("server_dna", {})
    embed.set_footer(text=f"Server Archetype: {dna.get('server_type', 'Community')} • Smart Bot")
    await interaction.followup.send(embed=embed)


@client.tree.command(name="health", description="View real-time AI Community Health Score (0-100)")
async def slash_health(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Run /health inside your server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    health = community_analyst.calculate_community_health_score(interaction.guild.id, guild=interaction.guild)
    
    desc = f"### **{health['health_score']}/100** • **{health['grade']}**\n"
    desc += f"{health.get('stage_badge', '🌱')} **Stage:** {health.get('stage', 'Community')}"
    if health.get('server_age_days') is not None:
        desc += f" *(Created {health['server_age_days']} days ago)*"
    if health.get('total_members'):
        desc += f"\n👥 **Members:** `{health.get('human_members', 0)} Humans` • `{health.get('bot_members', 0)} Bots`"

    embed = discord.Embed(
        title=f"📈 Community Health Score — {interaction.guild.name}",
        description=desc,
        color=0x57F287 if health['health_score'] >= 75 else 0xFEE75C
    )
    embed.add_field(name="📊 Engagement", value=health['metrics']['engagement'], inline=True)
    embed.add_field(name="🛡️ Staff Health", value=health['metrics']['staff_responsiveness'], inline=True)
    embed.add_field(name="⚠️ Friction Stability", value=health['metrics']['friction_stability'], inline=True)
    embed.add_field(name="📚 Knowledge Base", value=health['metrics']['knowledge_grounding'], inline=True)
    embed.add_field(name="🌟 Retention & Vibe", value=health['metrics']['vibe_retention'], inline=True)
    embed.add_field(name="🧠 Active Brain Nodes", value=str(health['total_brain_nodes']), inline=True)

    if health.get("recommendations"):
        rec_text = "\n".join(f"• {r}" for r in health['recommendations'][:3])
        embed.add_field(name="💡 AI Strategic Recommendations", value=rec_text, inline=False)

    embed.set_footer(text="Smart Bot Community Intelligence")
    await interaction.followup.send(embed=embed)


@client.tree.command(name="dna", description="View the AI Server DNA Profile and communication style")
async def slash_dna(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Run /dna inside your server.", ephemeral=True)
        return
    dna = community_brain.get_server_dna(interaction.guild.id)
    embed = discord.Embed(
        title=f"🧬 Server DNA Profile — {interaction.guild.name}",
        description=f"Autonomous culture & communication model for this community.",
        color=0x9B59B6
    )
    embed.add_field(name="🏛️ Community Archetype", value=f"**{dna['server_type']}**", inline=True)
    embed.add_field(name="💬 Communication Style", value=dna['communication_style'], inline=True)
    embed.add_field(name="🎭 Formality & Emojis", value=f"{dna['formality_level']} • {dna['emoji_style']}", inline=True)
    embed.add_field(name="🎯 Main Topics", value=", ".join(dna['main_topics']), inline=False)
    embed.add_field(name="📜 Key Grounded Rules", value="\n".join(f"• {r}" for r in dna['important_rules'][:3]), inline=False)
    embed.set_footer(text=f"Profile Confidence: {dna['confidence_pct']}% • Smart Bot")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="report", description="Generate 7-day Executive Community Intelligence Report")
async def slash_report(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Run /report inside your server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    report_text = community_analyst.generate_weekly_community_report_text(interaction.guild.id, interaction.guild.name)
    chunks = split_message(report_text, limit=1900)
    for idx, chunk in enumerate(chunks):
        if idx == 0:
            await interaction.followup.send(chunk)
        else:
            await interaction.channel.send(chunk)


def is_authorized_moderator(member: discord.Member, guild: discord.Guild = None) -> bool:
    """Checks if a user is an authorized moderator or server admin."""
    if member is None:
        return False
    if config.is_authorized_user(member.id):
        return True
    if hasattr(member, "guild_permissions"):
        return bool(
            member.guild_permissions.administrator
            or member.guild_permissions.manage_guild
            or member.guild_permissions.manage_messages
            or member.guild_permissions.moderate_members
        )
    return False


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Ingest into zero-cost Community Intelligence Buffer & Community Brain (0ms, $0.00 Cost)
    if message.guild is not None:
        author_is_staff = is_authorized_moderator(message.author, message.guild)
        channel_name = getattr(message.channel, "name", "general")
        collector.record_message(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            author_id=message.author.id,
            author_name=message.author.display_name,
            content=message.clean_content,
            channel_name=channel_name,
            author_is_staff=author_is_staff
        )
        # Background memory extraction & importance scoring (zero lag for main chat loop)
        author_is_staff = is_authorized_moderator(message.author, message.guild)
        asyncio.create_task(
            community_brain.process_incoming_message_for_memory(
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                channel_name=getattr(message.channel, "name", "channel"),
                message_id=message.id,
                author_id=message.author.id,
                author_name=message.author.display_name,
                author_is_staff=author_is_staff,
                content=message.clean_content
            )
        )

    # Passive XP award for every message in a guild (sellable staple)
    if message.guild is not None and config.is_guild_allowed(message.guild.id):
        try:
            xp = storage.add_xp(message.author.id, message.guild.id, 5)
            # Level-up announcement every 100 XP (embed, no ping)
            if xp % 100 == 0 and xp > 0:
                level = xp // 100
                try:
                    await message.channel.send(
                        embed=embeds.level_embed(message.author, level, xp),
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except Exception:
                    try:
                        await message.channel.send(
                            f"Level up! **{message.author.display_name}** reached **Level {level}** ({xp} XP)",
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    # Guild allowlist enforcement
    if message.guild is not None and not config.is_guild_allowed(message.guild.id):
        logger.warning(f"Ignoring message from non-allowlisted guild {message.guild.id}")
        return

    bot_mentioned = client.user in message.mentions if client.user else False

    is_reply_to_bot = False
    if message.reference and message.reference.resolved:
        resolved_msg = message.reference.resolved
        if getattr(resolved_msg, "author", None) == client.user:
            is_reply_to_bot = True

    is_dm = isinstance(message.channel, discord.DMChannel)
    # --- Social Media Video Auto-Embed Fixer ---
    if message.guild is not None and not message.author.bot:
        content_raw = message.content
        # Detect twitter/x, instagram reels, tiktok, reddit video links
        fixed_link = None
        if re.search(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+/status/\d+", content_raw):
            fixed_link = re.sub(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/", "https://vxtwitter.com/", content_raw)
        elif re.search(r"https?://(?:www\.)?instagram\.com/(?:reel|p)/[a-zA-Z0-9_-]+", content_raw):
            fixed_link = re.sub(r"https?://(?:www\.)?instagram\.com/", "https://ddinstagram.com/", content_raw)
        elif re.search(r"https?://(?:www\.)?(?:vm\.)?tiktok\.com/[a-zA-Z0-9_/-]+", content_raw):
            fixed_link = re.sub(r"https?://(?:www\.)?(?:vm\.)?tiktok\.com/", "https://vxtiktok.com/", content_raw)
        elif re.search(r"https?://(?:www\.)?reddit\.com/r/[a-zA-Z0-9_]+/comments/\w+", content_raw):
            fixed_link = re.sub(r"https?://(?:www\.)?reddit\.com/", "https://rxddit.com/", content_raw)

        # If fixable link detected, post clean embed with original author attribution
        if fixed_link and fixed_link != content_raw:
            try:
                await message.channel.send(f"🎬 **Video Preview** *(via {message.author.display_name})*:\n{fixed_link}")
            except Exception:
                pass

    if not (bot_mentioned or is_reply_to_bot or is_dm):
        # Watch-mode may still classify ambient messages
        if config.WATCH_MODE and message.guild is not None and config.is_guild_allowed(message.guild.id):
            await _watch_mode_check(message)
        return

    on_cooldown, remaining = is_user_on_cooldown(message.author.id)
    if on_cooldown:
        await send_reply_safe(message, f"Whoa, slow down! Please wait {remaining:.1f}s before sending another message.")
        return
    update_user_cooldown(message.author.id)

    cleaned_content = clean_message_content(message.content, client.user)
    if not cleaned_content:
        cleaned_content = "Hello!"

    attachment_urls = [att.url for att in message.attachments if att.url][:MAX_ATTACHMENTS]

    is_authorized = config.is_authorized_user(message.author.id)
    auth_status_str = "Authorized Moderator" if is_authorized else "Standard User"
    logger.info(
        f"Processing message from '{message.author}' ({message.author.id}) [{auth_status_str}] "
        f"in channel '{message.channel}' attachments={len(attachment_urls)}"
    )

    # --- Voice Channel Shortcuts ---
    cleaned_lower = cleaned_content.lower().strip()
    if message.guild is not None and ("join voice" in cleaned_lower or "join call" in cleaned_lower or "hop in voice" in cleaned_lower):
        target_vc = None
        if message.author.voice and message.author.voice.channel:
            target_vc = message.author.voice.channel
        else:
            # Check if a voice channel name was mentioned
            for vc in message.guild.voice_channels:
                if vc.name.lower() in cleaned_lower or (len(vc.members) > 0) or ("gen" in vc.name.lower()):
                    target_vc = vc
                    break
            if target_vc is None and message.guild.voice_channels:
                target_vc = message.guild.voice_channels[0]

        if target_vc:
            try:
                voice_service.ensure_opus_loaded()
                vc = message.guild.voice_client
                if vc:
                    if vc.is_connected() and vc.channel and vc.channel.id == target_vc.id:
                        await send_reply_safe(message, f"🔊 Already in **#{target_vc.name}**!")
                        return
                    elif vc.is_connected():
                        await vc.move_to(target_vc)
                    else:
                        try:
                            await vc.disconnect(force=True)
                        except Exception:
                            pass
                        vc = await target_vc.connect(timeout=20.0, reconnect=True)
                else:
                    vc = await target_vc.connect(timeout=20.0, reconnect=True)

                guild_persona = storage.get_guild_persona(message.guild.id)
                asyncio.create_task(voice_service.play_speech_in_voice(vc, f"Hey {message.author.display_name}, I've joined {target_vc.name}.", persona=guild_persona))
                await send_reply_safe(message, f"🔊 Joined voice channel **#{target_vc.name}**! I'm live and ready.")
                return
            except Exception as e:
                logger.error(f"Voice join shortcut error: {e}", exc_info=True)
                await send_reply_safe(message, f"Failed to connect to voice channel: {e}")
                return
        else:
            await send_reply_safe(message, "You need to hop into a voice channel or specify one to join (e.g. `@Smart bot join voice general`)!")
            return

    if message.guild is not None and ("leave voice" in cleaned_lower or "disconnect voice" in cleaned_lower):
        vc = message.guild.voice_client
        if vc and vc.is_connected():
            await vc.disconnect()
            await send_reply_safe(message, "👋 Disconnected from voice channel.")
            return

    # --- Landing / Setup Card Shortcut ---
    if message.guild is not None and any(kw in cleaned_lower for kw in ["resend landing", "show landing", "landing card", "welcome card", "show setup"]):
        await _post_setup_card(message.channel, message.guild)
        return

    # --- Catch-me-up shortcut ---
    if CATCHUP_RE.match(cleaned_content) and message.guild is not None:
        await _catch_me_up(message)
        return

    # --- Language preference memory ---
    lang_hint = ""
    m = TRANSLATE_RE.search(cleaned_content)
    if m:
        target_lang = m.group(1).lower()
        try:
            storage.set_user_lang(message.author.id, target_lang)
        except Exception:
            pass
        lang_hint = f"user wants responses/translations in {target_lang}"
    else:
        try:
            saved_lang = storage.get_user_lang(message.author.id)
            if saved_lang:
                lang_hint = f"user previously asked for {saved_lang}; respond in it when natural"
        except Exception:
            pass

    await _stream_ai_reply(message, cleaned_content, is_authorized, attachment_urls, lang_hint)


async def _stream_ai_reply(message, cleaned_content, is_authorized, attachment_urls, lang_hint=""):
    """Consume the AI stream and live-edit a Discord reply."""
    sent = None
    last_edit = 0.0
    final_text = ""
    typing_task = asyncio.create_task(_keep_typing(message.channel))

    # Set context variables before initializing stream generator
    guild_token = ai_service.tools.current_guild.set(message.guild)
    user_token = ai_service.tools.current_user_id.set(message.author.id)
    req_token = ai_service.tools.current_requester_id.set(message.author.id)
    src_token = ai_service.tools.current_source_message.set(message)
    rem_token = ai_service.tools.current_reminder_channel.set(message.channel.id)

    try:
        stream = ai_service.process_chat_message_stream(
            channel_id=message.channel.id,
            author_name=message.author.display_name,
            message_content=cleaned_content,
            is_authorized=is_authorized,
            attachments=attachment_urls,
            author_id=message.author.id,
            lang_hint=lang_hint,
        )
        async for prefix in stream:
            final_text = prefix
            now = time.time()
            if now - last_edit >= EDIT_THROTTLE_SECONDS:
                if sent is None:
                    sent = await send_reply_safe(message, prefix[:1990])
                elif sent is not None:
                    try:
                        await sent.edit(content=prefix[:2000])
                    except Exception:
                        pass
                last_edit = now
    except Exception as e:
        logger.error(f"Error streaming AI response: {e}", exc_info=True)
        final_text = final_text or "Oops! I ran into an error while processing that request."
    finally:
        try:
            typing_task.cancel()
        except Exception:
            pass
        ai_service.tools.current_guild.reset(guild_token)
        ai_service.tools.current_user_id.reset(user_token)
        ai_service.tools.current_requester_id.reset(req_token)
        ai_service.tools.current_source_message.reset(src_token)
        ai_service.tools.current_reminder_channel.reset(rem_token)

    # Detect if final_text contains a direct GIF / image media URL to embed cleanly
    media_url = None
    media_match = re.search(
        r'(https?://[^\s<>]+(?:giphy\.com/media/[^\s<>]+|tenor\.com/[^\s<>]+|\.(?:gif|png|jpg|jpeg|webp)(?:\?[^\s<>]*)?))',
        final_text,
        re.IGNORECASE
    )
    if media_match:
        media_url = media_match.group(1)
        final_text = final_text.replace(media_url, "").strip()

    media_embed = None
    if media_url:
        media_embed = discord.Embed(color=0x5865F2)
        media_embed.set_image(url=media_url)

    if not final_text and not media_embed:
        return
    try:
        if sent is None:
            if len(final_text) <= 2000:
                await send_reply_safe(message, text=final_text if final_text else None, embed=media_embed)
            else:
                chunks = split_message(final_text)
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await send_reply_safe(message, text=chunk, embed=media_embed)
                    else:
                        try:
                            await message.channel.send(chunk)
                        except Exception as e:
                            logger.error(f"Failed to send chunk {i}: {e}")
                    if i < len(chunks) - 1:
                        await asyncio.sleep(1.1)
        else:
            await sent.edit(content=final_text[:2000] if final_text else None, embed=media_embed)
            extra = split_message(final_text[2000:]) if len(final_text) > 2000 else []
            for i, chunk in enumerate(extra):
                try:
                    await message.channel.send(chunk)
                except Exception as e:
                    logger.error(f"Failed to send overflow chunk {i}: {e}")
                if i < len(extra) - 1:
                    await asyncio.sleep(1.1)
    except Exception as e:
        logger.error(f"Final send failed: {e}")


async def _catch_me_up(message: discord.Message):
    """Summarize recent channel messages."""
    try:
        lines = []
        async for msg in message.channel.history(limit=80, before=message):
            if msg.author.bot:
                continue
            content = msg.content.strip()
            if content:
                lines.append(f"{msg.author.display_name}: {content[:300]}")
            if len(lines) >= 60:
                break
        lines.reverse()
    except discord.Forbidden:
        await send_reply_safe(message, "I don't have permission to read this channel's history.")
        return

    async with message.channel.typing():
        summary = await ai_service.summarize_messages(lines)
    await send_reply_safe(message, summary)


async def _watch_mode_check(message: discord.Message):
    """Background AI classification of ambient messages; flags mods, never auto-punishes."""
    if not config.WATCH_LOG_CHANNEL_ID:
        return
    user_id = message.author.id
    now = time.time()
    last = WATCH_LAST_CHECK.get(user_id, 0.0)
    if now - last < WATCH_USER_COOLDOWN:
        return
    global WATCH_TIMESTAMPS
    WATCH_TIMESTAMPS = [t for t in WATCH_TIMESTAMPS if now - t < 3600]
    if len(WATCH_TIMESTAMPS) >= WATCH_MAX_PER_HOUR:
        return
    if len(message.content) < 12:
        return

    WATCH_LAST_CHECK[user_id] = now
    WATCH_TIMESTAMPS.append(now)

    verdict = await ai_service.classify_message(message.content)
    if verdict is None or not verdict.violation or verdict.severity < config.WATCH_SEVERITY_THRESHOLD:
        return

    log_channel = message.guild.get_channel(config.WATCH_LOG_CHANNEL_ID)
    if log_channel is None:
        return
    try:
        cats = ", ".join(verdict.categories[:4]) or "unknown"
        flag = (
            f"[AI Watch] Possible violation by {message.author.mention} in {message.channel.mention}\n"
            f"Category: {cats} | Severity: {verdict.severity}/10 | Confidence: {verdict.confidence:.0%}\n"
            f"Reason: {verdict.reason}\n"
            f'Message: "{message.content[:180]}"\n'
            f"Act naturally, e.g.: @mention of bot + 'timeout {message.author.display_name} 10m'"
        )
        await log_channel.send(flag[:1900])
        logger.info(f"Watch-mode flagged user {user_id}: sev={verdict.severity} {cats}")
    except Exception as e:
        logger.error(f"Failed posting watch flag: {e}")


async def _reminder_loop():
    """Background loop that delivers due reminders and prunes expired collector memory."""
    await client.wait_until_ready()
    last_collector_prune = 0.0
    while not client.is_closed():
        try:
            now = time.time()
            # 1. Deliver due reminders
            for rid, guild_id, channel_id, user_id, text in storage.due_reminders(now):
                channel = client.get_channel(channel_id)
                if channel is None:
                    try:
                        channel = await client.fetch_channel(channel_id)
                    except Exception:
                        continue
                try:
                    await channel.send(f"<@{user_id}> reminder: {text}")
                    storage.delete_reminder(rid)
                    logger.info(f"Delivered reminder {rid} to {user_id}")
                except Exception as e:
                    logger.error(f"Failed delivering reminder {rid}: {e}")

            # 2. Prune expired in-memory messages every 10 minutes (600s)
            if now - last_collector_prune > 600.0:
                pruned = collector.prune_expired_messages()
                if pruned > 0:
                    logger.info(f"Collector garbage collector pruned {pruned} expired messages from memory.")
                last_collector_prune = now

        except Exception as e:
            logger.error(f"Background worker loop error: {e}")
        await asyncio.sleep(30)


# --- Health Check HTTP Server for Render/Koyeb 24/7 Cloud Compatibility ---
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"status":"online","bot":"Smart Bot OS v5.0","cloud":"render"}')

    def log_message(self, format, *args):
        pass  # Suppress excessive health probe logs

def start_cloud_health_server():
    port = int(os.getenv("PORT", "10000"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logger.info(f"Cloud health probe HTTP server listening on 0.0.0.0:{port}")
    except Exception as e:
        logger.warning(f"Health check server startup note on port {port}: {e}")


def main():
    if not config.DISCORD_BOT_TOKEN:
        logger.error("Error: DISCORD_BOT_TOKEN is not set in environment variables.")
        sys.exit(1)
    start_cloud_health_server()
    client.run(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()

import re
import datetime
import asyncio
import logging
import contextvars
from typing import Optional, Union, Dict, List
import discord

import config

logger = logging.getLogger("tools")

# Context variables for tool execution
current_guild: contextvars.ContextVar[Optional[discord.Guild]] = contextvars.ContextVar("current_guild", default=None)
current_user_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("current_user_id", default=None)
# Confirmation-gate plumbing (set on live streaming path in bot._stream_ai_reply)
current_requester_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("current_requester_id", default=None)
current_source_message: contextvars.ContextVar[Optional[discord.Message]] = contextvars.ContextVar("current_source_message", default=None)

PERSONAS = {
    "default": "You are the default friendly, witty, chill companion.",
    "savage": "You are savage, brutally honest, roast-heavy but still playful — no filter on jokes between friends.",
    "wholesome": "You are wholesome, supportive and upbeat — the server's comfort character.",
    "professor": "You are professor mode — concise, precise, explains clearly with examples.",
    "gamer": "You are gamer mode — hype, slang-heavy, obsessed with games, uses gaming metaphors.",
}


async def _notify_and_return(res: str) -> str:
    """Helper to log successful moderation actions to MOD_LOG_CHANNEL_ID if configured."""
    if res.startswith("Successfully") and config.MOD_LOG_CHANNEL_ID:
        guild = current_guild.get()
        if guild:
            log_channel = guild.get_channel(config.MOD_LOG_CHANNEL_ID)
            if log_channel and isinstance(log_channel, discord.TextChannel):
                try:
                    await log_channel.send(f"🛡️ **[Mod Audit Log]** {res}")
                except Exception:
                    pass
    return res


async def _gate_destructive(summary: str) -> str:
    """
    Human confirmation gate for destructive tools.
    Returns "OK" to proceed, else a refusal string the model reports back truthfully.
    Fail-closed when there is no chat surface to present buttons on.
    Set config.CONFIRM_DESTRUCTIVE=false (or env) to disable globally.
    """
    if not getattr(config, "CONFIRM_DESTRUCTIVE", True):
        return "OK"
    source_msg = current_source_message.get()
    requester = current_requester_id.get()
    if source_msg is None or requester is None:
        return "Error: Destructive action requires confirmation but no chat surface is available. Nothing was executed. Ask the user to run this in a server channel."
    import embeds as _embeds
    from views.confirm import ConfirmView

    embed = _embeds.warn_embed("Confirm destructive action", summary)
    view = ConfirmView(author_id=requester, timeout=60)
    try:
        host = await source_msg.reply(embed=embed, view=view, mention_author=False)
    except Exception as e:
        return f"Error: Could not present confirmation ({str(e)[:100]}). Nothing was executed."

    await view.wait()
    if view.confirmed is True:
        try:
            await host.edit(embed=_embeds.success_embed("Confirmed — executing", summary), view=None)
        except Exception:
            pass
        # audit trail
        try:
            import storage as _storage
            guild = current_guild.get()
            _storage.record_mod_action(
                guild_id=guild.id if guild else None,
                actor_id=requester,
                target=summary[:120],
                action="confirm_gate",
                reason="approved",
            )
        except Exception:
            pass
        return "OK"
    elif view.confirmed is False:
        try:
            await host.edit(embed=_embeds.error_embed("Cancelled — nothing executed"), view=None)
        except Exception:
            pass
        return "CANCELLED: The user declined. Nothing was executed. Tell them it's cancelled."
    else:
        try:
            await host.edit(embed=_embeds.error_embed("Expired — nothing executed (60s timeout)"), view=None)
        except Exception:
            pass
        return "EXPIRED: No confirmation within 60 seconds. Nothing was executed."


def find_category(guild: discord.Guild, query: str) -> Optional[discord.CategoryChannel]:
    """Find a category channel in a guild using fuzzy lookup."""
    if not query or not guild:
        return None
    query_str = str(query).strip()
    if query_str.isdigit():
        cat = guild.get_channel(int(query_str))
        if isinstance(cat, discord.CategoryChannel):
            return cat
    for cat in guild.categories:
        if cat.name == query_str:
            return cat
    query_lower = query_str.lower()
    for cat in guild.categories:
        if query_lower in cat.name.lower():
            return cat
    return None


def find_channel(guild: discord.Guild, query: str) -> Optional[Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel]]:
    """
    Find a channel or category in a guild using fuzzy lookup order:
    1. Direct Snowflake ID
    2. Mention syntax (<#ID>)
    3. Exact name match
    4. Partial case-insensitive name match
    """
    if not query or not guild:
        return None

    query_str = str(query).strip()

    # 1. Direct ID match
    if query_str.isdigit():
        channel_id = int(query_str)
        channel = guild.get_channel(channel_id)
        if channel:
            return channel

    # 2. Mention syntax match (<#123456789012345678>)
    mention_match = re.match(r"^<#(\d+)>$", query_str)
    if mention_match:
        channel_id = int(mention_match.group(1))
        channel = guild.get_channel(channel_id)
        if channel:
            return channel

    # 3. Exact name match
    for ch in guild.channels:
        if ch.name == query_str:
            return ch

    # 4. Partial case-insensitive name match
    query_lower = query_str.lower()
    for ch in guild.channels:
        if query_lower in ch.name.lower():
            return ch

    return None


def find_member(guild: discord.Guild, query: str) -> Optional[discord.Member]:
    """
    Find a member in a guild using fuzzy lookup order:
    1. Direct Snowflake ID
    2. Mention syntax (<@ID> or <@!ID>)
    3. Exact name / display_name match
    4. Partial case-insensitive name match
    """
    if not query or not guild:
        return None

    query_str = str(query).strip()

    # 1. Direct ID match
    if query_str.isdigit():
        member_id = int(query_str)
        member = guild.get_member(member_id)
        if member:
            return member

    # 2. Mention syntax match (<@123456789012345678> or <@!123456789012345678>)
    mention_match = re.match(r"^<@!?(\d+)>$", query_str)
    if mention_match:
        member_id = int(mention_match.group(1))
        member = guild.get_member(member_id)
        if member:
            return member

    # 3. Exact name / display_name / global_name match
    for member in guild.members:
        if (member.name == query_str or
            member.display_name == query_str or
            getattr(member, 'global_name', None) == query_str):
            return member

    # 4. Partial case-insensitive name match
    query_lower = query_str.lower()
    for member in guild.members:
        names = [
            member.name.lower(),
            member.display_name.lower(),
        ]
        if getattr(member, 'global_name', None):
            names.append(member.global_name.lower())

        if any(query_lower in name for name in names):
            return member

    return None


def find_role(guild: discord.Guild, query: str) -> Optional[discord.Role]:
    """
    Find a role in a guild using fuzzy lookup order:
    1. Direct Snowflake ID
    2. Mention syntax (<@&ID>)
    3. Exact name match
    4. Partial case-insensitive name match
    """
    if not query or not guild:
        return None

    query_str = str(query).strip()

    if query_str.isdigit():
        role_id = int(query_str)
        role = guild.get_role(role_id)
        if role:
            return role

    mention_match = re.match(r"^<@&(\d+)>$", query_str)
    if mention_match:
        role_id = int(mention_match.group(1))
        role = guild.get_role(role_id)
        if role:
            return role

    for role in guild.roles:
        if role.name == query_str:
            return role

    query_lower = query_str.lower()
    for role in guild.roles:
        if query_lower in role.name.lower():
            return role

    return None


# --- Channel Controls ---

async def create_text_channel(channel_name: str, topic: str = "", category_name: str = "") -> str:
    """
    Creates a new text channel in the Discord server.

    Args:
        channel_name: The name of the text channel.
        topic: Optional topic description for the channel.
        category_name: Optional name or ID of the parent category.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        category = find_category(guild, category_name) if category_name else None
        ch = await guild.create_text_channel(name=channel_name, topic=topic or None, category=category)
        cat_str = f" in category '{category.name}'" if category else ""
        return await _notify_and_return(f"Successfully created text channel #{ch.name} (ID: {ch.id}){cat_str}.")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Channels') to create text channels."
    except Exception as e:
        return f"Error creating text channel: {str(e)}"


async def create_voice_channel(channel_name: str, user_limit: int = 0, category_name: str = "") -> str:
    """
    Creates a new voice channel in the Discord server with an optional user limit.

    Args:
        channel_name: The name of the voice channel to create.
        user_limit: Optional maximum number of users allowed in the voice channel (0 for no limit).
        category_name: Optional name or ID of the parent category.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    try:
        category = find_category(guild, category_name) if category_name else None
        limit_val = max(0, min(99, int(user_limit)))
        new_channel = await guild.create_voice_channel(name=channel_name, user_limit=limit_val, category=category)
        limit_str = f" with a limit of {limit_val} users" if limit_val > 0 else " with no user limit"
        cat_str = f" in category '{category.name}'" if category else ""
        return await _notify_and_return(f"Successfully created voice channel '{new_channel.name}' (ID: {new_channel.id}){limit_str}{cat_str}.")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Channels') to create voice channels."
    except Exception as e:
        return f"Error creating voice channel: {str(e)}"


async def create_stage_channel(channel_name: str, topic: str = "", category_name: str = "") -> str:
    """
    Creates a new Stage channel in the Discord server.

    Args:
        channel_name: The name of the Stage channel.
        topic: Optional topic description for the stage channel.
        category_name: Optional name or ID of the parent category.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        category = find_category(guild, category_name) if category_name else None
        ch = await guild.create_stage_channel(name=channel_name, topic=topic or None, category=category)
        cat_str = f" in category '{category.name}'" if category else ""
        return await _notify_and_return(f"Successfully created Stage channel '{ch.name}' (ID: {ch.id}){cat_str}.")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Channels') to create Stage channels."
    except Exception as e:
        return f"Error creating Stage channel: {str(e)}"


async def create_category(category_name: str) -> str:
    """
    Creates a new category in the Discord server.

    Args:
        category_name: The name of the category to create.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        cat = await guild.create_category(name=category_name)
        return await _notify_and_return(f"Successfully created category '{cat.name}' (ID: {cat.id}).")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Channels') to create categories."
    except Exception as e:
        return f"Error creating category: {str(e)}"


async def delete_channel(channel_name: str) -> str:
    """
    Deletes a channel or category from the Discord server.

    Args:
        channel_name: The name, ID, or mention of the channel or category to delete.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not channel:
        return f"Error: Channel or category '{channel_name}' not found."
    # SMART: disambiguate when multiple matches exist
    candidates = [c for c in guild.channels if channel_name.lower().strip() in c.name.lower()]
    if len(candidates) > 1 and not channel_name.strip().isdigit() and "<#" not in str(channel_name):
        user_id = current_user_id.get()
        user_vc = None
        if user_id:
            member = guild.get_member(user_id)
            if member and member.voice:
                user_vc = member.voice.channel
        
        # If user is in one voice channel, automatically select the other (empty) one
        empty_vc = [c for c in candidates if isinstance(c, discord.VoiceChannel) and len(c.members) == 0 and c != user_vc]
        exact_matches = [c for c in candidates if c.name.lower() == channel_name.lower().strip()]
        
        if user_vc and len(empty_vc) == 1:
            channel = empty_vc[0]
        elif len(exact_matches) == 1:
            channel = exact_matches[0]
        elif user_vc and exact_matches and any(c != user_vc for c in exact_matches):
            channel = [c for c in exact_matches if c != user_vc][0]
        elif len(empty_vc) == 1:
            channel = empty_vc[0]
        else:
            names = ", ".join(f"**{c.name}** (ID: `{c.id}`)" for c in candidates[:5])
            return f"AMBIGUOUS: '{channel_name}' matches {len(candidates)} channels — please specify which ID to delete: {names}."
    child_note = ""
    if isinstance(channel, discord.CategoryChannel):
        child_note = f" ⚠️ This is a CATEGORY containing {len(channel.channels)} channel(s)!"
    ch_disp = getattr(channel, "mention", None) or f"`{channel.name}`"
    gate = await _gate_destructive(f"**Delete** {ch_disp} `{channel.name}`{child_note}")
    if gate != "OK":
        return gate
    try:
        ch_name = channel.name
        ch_type = channel.type
        await channel.delete()
        return await _notify_and_return(f"Successfully deleted {ch_type} channel '{ch_name}'.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Channels') to delete '{channel_name}'."
    except Exception as e:
        return f"Error deleting channel: {str(e)}"


async def set_channel_read_only(channel_name: str, read_only: bool) -> str:
    """
    Toggles send-message permissions for the @everyone role on a specified text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        read_only: True to make channel read-only (disable sending messages for @everyone), False to unlock.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    channel = find_channel(guild, channel_name)
    if not channel or not isinstance(channel, discord.TextChannel):
        return f"Error: Text channel '{channel_name}' not found."

    try:
        everyone_role = guild.default_role
        overwrites = channel.overwrites_for(everyone_role)

        if read_only:
            overwrites.send_messages = False
            status = "read-only (locked send_messages for @everyone)"
        else:
            overwrites.send_messages = None  # Reset to default/neutral or True
            status = "unlocked (reset send_messages for @everyone)"

        await channel.set_permissions(everyone_role, overwrite=overwrites)
        return await _notify_and_return(f"Successfully set channel '{channel.name}' to {status}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Roles' / 'Manage Channels') to modify permissions for #{channel.name}."
    except Exception as e:
        return f"Error setting channel read-only state: {str(e)}"


async def hide_channel(channel_name: str, hide: bool) -> str:
    """
    Hides or unhides a channel for the @everyone role by toggling read_messages/view_channel permission.

    Args:
        channel_name: The name, ID, or mention of the channel.
        hide: True to hide channel from @everyone, False to make visible.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    channel = find_channel(guild, channel_name)
    if not channel:
        return f"Error: Channel '{channel_name}' not found."

    try:
        everyone_role = guild.default_role
        overwrites = channel.overwrites_for(everyone_role)

        if hide:
            overwrites.view_channel = False
            status = "hidden from @everyone"
        else:
            overwrites.view_channel = None
            status = "visible to @everyone"

        await channel.set_permissions(everyone_role, overwrite=overwrites)
        return await _notify_and_return(f"Successfully set channel '{channel.name}' to {status}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Roles' / 'Manage Channels') to modify permissions for channel '{channel.name}'."
    except Exception as e:
        return f"Error modifying channel visibility: {str(e)}"


# --- Member Moderation ---

async def ban_user(username_or_id: str, reason: str = "No reason provided", delete_message_days: int = 0) -> str:
    """
    Bans a user from the server.

    Args:
        username_or_id: The username, display name, ID, or mention of the user to ban.
        reason: Reason for the ban.
        delete_message_days: Days of recent messages to delete (0 to 7).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        # Check if username_or_id is a direct snowflake ID for banning an offline/external user
        if str(username_or_id).strip().isdigit():
            user_id = int(str(username_or_id).strip())
            # SMART GATE: verify the ID resolves to a real user before a permanent ban
            known = None
            try:
                known = await guild.fetch_member(user_id)
            except discord.NotFound:
                pass
            except Exception:
                pass
            gate = await _gate_destructive(
                f"**Ban by ID** `{user_id}`"
                + (f" (in server as **{known.name}**)" if known else " ⚠️ *not found in server — verify the ID!*")
                + f"\nReason: {reason}\nDelete message days: {delete_message_days}"
            )
            if gate != "OK":
                return gate
            try:
                user = await guild.client.fetch_user(user_id) if hasattr(guild, 'client') else discord.Object(id=user_id)
                delete_seconds = max(0, min(7, int(delete_message_days))) * 86400
                await guild.ban(user, reason=reason, delete_message_seconds=delete_seconds)
                return await _notify_and_return(f"Successfully banned user ID {user_id}. Reason: {reason}")
            except Exception as e:
                return f"Error banning user ID {user_id}: {str(e)}"
        return f"Error: User '{username_or_id}' not found in this server."

    delete_seconds = max(0, min(7, int(delete_message_days))) * 86400
    gate = await _gate_destructive(
        f"**Ban** {member.mention} ({member.name})\nReason: {reason}\nDelete message days: {delete_message_days}"
    )
    if gate != "OK":
        return gate
    try:
        await member.ban(reason=reason, delete_message_seconds=delete_seconds)
        return await _notify_and_return(f"Successfully banned {member.mention} ({member.name}). Reason: {reason}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Ban Members') or hierarchy to ban {member.name}."
    except Exception as e:
        return f"Error banning user: {str(e)}"


async def unban_user(username_or_id: str, reason: str = "No reason provided") -> str:
    """
    Unbans a user from the server.

    Args:
        username_or_id: The username or Snowflake ID of the banned user.
        reason: Reason for unbanning.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    try:
        bans = [entry async for entry in guild.bans()] if hasattr(guild, 'bans') else []
        target_user = None
        query_str = str(username_or_id).strip()

        for ban_entry in bans:
            u = ban_entry.user
            if str(u.id) == query_str or u.name == query_str or f"{u.name}#{u.discriminator}" == query_str:
                target_user = u
                break

        if not target_user and query_str.isdigit():
            target_user = discord.Object(id=int(query_str))

        if not target_user:
            return f"Error: Banned user '{username_or_id}' not found in ban list."

        await guild.unban(target_user, reason=reason)
        return await _notify_and_return(f"Successfully unbanned user '{username_or_id}'. Reason: {reason}")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Ban Members') to unban users."
    except Exception as e:
        return f"Error unbanning user: {str(e)}"


async def kick_user(username_or_id: str, reason: str = "No reason provided") -> str:
    """
    Kicks a member from the server.

    Args:
        username_or_id: The username, display name, ID, or mention of the user to kick.
        reason: Reason for kicking.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: Member '{username_or_id}' not found in this server."

    try:
        await member.kick(reason=reason)
        return await _notify_and_return(f"Successfully kicked {member.mention} ({member.name}). Reason: {reason}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Kick Members') or hierarchy to kick {member.name}."
    except Exception as e:
        return f"Error kicking member: {str(e)}"


async def timeout_user(username_or_id: str, duration_minutes: int, reason: str = "No reason provided") -> str:
    """
    Applies a temporary timeout (mute) to a server member.

    Args:
        username_or_id: The username, display name, ID, or mention of the user to timeout.
        duration_minutes: Duration of timeout in minutes (max 28 days = 40320 minutes).
        reason: Reason for applying the timeout.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    try:
        minutes = max(1, min(40320, int(duration_minutes)))
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        return await _notify_and_return(f"Successfully timed out {member.mention} ({member.name}) for {minutes} minute(s). Reason: {reason}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Moderate Members') or hierarchy to timeout {member.name}."
    except Exception as e:
        return f"Error timing out user: {str(e)}"


async def remove_timeout(username_or_id: str, reason: str = "No reason provided") -> str:
    """
    Removes an active timeout (unmutes) from a server member.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
        reason: Reason for removing the timeout.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    try:
        await member.timeout(None, reason=reason)
        return await _notify_and_return(f"Successfully removed timeout for {member.mention} ({member.name}). Reason: {reason}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Moderate Members') or hierarchy to modify timeout for {member.name}."
    except Exception as e:
        return f"Error removing timeout: {str(e)}"


async def change_nickname(username_or_id: str, nickname: str = "") -> str:
    """
    Changes or resets a member's server nickname.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
        nickname: The new nickname (empty string to reset nickname).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    try:
        new_nick = nickname.strip() if nickname else None
        await member.edit(nick=new_nick)
        action_str = f"changed to '{new_nick}'" if new_nick else "reset to default"
        return await _notify_and_return(f"Successfully {action_str} for {member.mention} ({member.name}).")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Nicknames') or hierarchy to edit nickname for {member.name}."
    except Exception as e:
        return f"Error changing nickname: {str(e)}"


async def disconnect_member_voice(username_or_id: str) -> str:
    """
    Disconnects a member from their current voice channel.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    if not member.voice or not member.voice.channel:
        return f"Error: User '{member.name}' is not currently in a voice channel."

    try:
        await member.move_to(None)
        return await _notify_and_return(f"Successfully disconnected {member.mention} ({member.name}) from voice.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Move Members') to disconnect {member.name}."
    except Exception as e:
        return f"Error disconnecting member from voice: {str(e)}"


async def move_member_voice(username_or_id: str, voice_channel_name: str) -> str:
    """
    Moves a member to a specified voice channel.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
        voice_channel_name: The name, ID, or mention of the destination voice channel.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    if not member.voice or not member.voice.channel:
        return f"Error: User '{member.name}' is not currently in a voice channel."

    channel = find_channel(guild, voice_channel_name)
    if not channel or not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
        return f"Error: Destination voice channel '{voice_channel_name}' not found."

    try:
        await member.move_to(channel)
        return await _notify_and_return(f"Successfully moved {member.mention} ({member.name}) to voice channel '{channel.name}'.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Move Members') to move {member.name}."
    except Exception as e:
        return f"Error moving member to voice channel: {str(e)}"


# --- Role Management ---

# Permissions considered too dangerous for AI-driven role assignment
_DANGEROUS_PERMISSIONS = [
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "ban_members",
    "kick_members",
    "moderate_members",
    "manage_nicknames",
    "manage_messages",
]


def _is_dangerous_role(role: discord.Role) -> bool:
    """Check if a role grants admin-level powers or sits at/above the bot's top role."""
    perms = role.permissions
    for perm_name in _DANGEROUS_PERMISSIONS:
        try:
            if getattr(perms, perm_name, False):
                return True
        except AttributeError:
            continue
    # Role at/above the bot's own top role can't be managed anyway
    guild = current_guild.get()
    try:
        if guild and guild.me and not role.is_default():
            bot_top_position = getattr(guild.me.top_role, "position", 0)
            if role.position >= bot_top_position:
                return True
    except (TypeError, AttributeError):
        pass
    return False


async def create_role(role_name: str, hex_color: str = "#000000", mentionable: bool = False) -> str:
    """
    Creates a new role in the server.

    Args:
        role_name: Name of the role to create.
        hex_color: Hex color string (e.g., '#FF0000' or '00FF00').
        mentionable: Whether the role should be mentionable by everyone.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    try:
        clean_color = hex_color.lstrip('#') if hex_color else "000000"
        color_int = int(clean_color, 16) if clean_color else 0
        role_color = discord.Color(color_int)
        role = await guild.create_role(name=role_name, color=role_color, mentionable=bool(mentionable))
        return await _notify_and_return(f"Successfully created role '{role.name}' (ID: {role.id}).")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Roles') to create roles."
    except Exception as e:
        return f"Error creating role: {str(e)}"


async def assign_role(username_or_id: str, role_name: str) -> str:
    """
    Assigns a role to a server member.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
        role_name: The name, ID, or mention of the role to assign.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    role = find_role(guild, role_name)
    if not role:
        return f"Error: Role '{role_name}' not found in this server."

    if _is_dangerous_role(role):
        return (
            f"Error: Role '{role.name}' grants admin-level powers (or is above the bot), "
            "so it can only be assigned manually by a server admin in Server Settings."
        )

    try:
        await member.add_roles(role)
        return await _notify_and_return(f"Successfully assigned role '{role.name}' to {member.mention} ({member.name}).")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Roles') or hierarchy to assign role '{role.name}'."
    except Exception as e:
        return f"Error assigning role: {str(e)}"


async def remove_role(username_or_id: str, role_name: str) -> str:
    """
    Removes a role from a server member.

    Args:
        username_or_id: The username, display name, ID, or mention of the user.
        role_name: The name, ID, or mention of the role to remove.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    role = find_role(guild, role_name)
    if not role:
        return f"Error: Role '{role_name}' not found in this server."

    if _is_dangerous_role(role):
        return (
            f"Error: Role '{role.name}' grants admin-level powers (or is above the bot), "
            "so it can only be removed manually by a server admin in Server Settings."
        )

    try:
        await member.remove_roles(role)
        return await _notify_and_return(f"Successfully removed role '{role.name}' from {member.mention} ({member.name}).")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Roles') or hierarchy to remove role '{role.name}'."
    except Exception as e:
        return f"Error removing role: {str(e)}"


# --- Message Management ---

async def purge_messages(channel_name: str, limit: int = 10) -> str:
    """
    Deletes the last N messages in a specified text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        limit: The number of messages to purge (default 10, max 100).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    channel = find_channel(guild, channel_name)
    if not channel or not isinstance(channel, discord.TextChannel):
        return f"Error: Text channel '{channel_name}' not found."

    purge_limit = max(1, min(100, int(limit)))
    # Bulk delete is destructive — always confirm (user request)
    gate = await _gate_destructive(f"**Purge** {purge_limit} message(s) in {channel.mention}")
    if gate != "OK":
        return gate

    try:
        deleted = await channel.purge(limit=purge_limit)
        return await _notify_and_return(f"Successfully purged {len(deleted)} message(s) from channel #{channel.name}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Messages') to purge messages in #{channel.name}."
    except Exception as e:
        return f"Error purging messages: {str(e)}"


async def pin_message(channel_name: str, message_id: str) -> str:
    """
    Pins a message in a text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        message_id: The Snowflake ID of the message to pin.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    channel = find_channel(guild, channel_name)
    if not channel or not isinstance(channel, discord.TextChannel):
        return f"Error: Text channel '{channel_name}' not found."

    if not str(message_id).strip().isdigit():
        return "Error: Message ID must be a numeric Snowflake ID."

    try:
        msg = await channel.fetch_message(int(message_id))
        await msg.pin()
        return await _notify_and_return(f"Successfully pinned message ID {msg.id} in channel #{channel.name}.")
    except discord.NotFound:
        return f"Error: Message ID {message_id} not found in channel #{channel.name}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Messages') to pin messages in #{channel.name}."
    except Exception as e:
        return f"Error pinning message: {str(e)}"


async def unpin_message(channel_name: str, message_id: str) -> str:
    """
    Unpins a message in a text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        message_id: The Snowflake ID of the message to unpin.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    channel = find_channel(guild, channel_name)
    if not channel or not isinstance(channel, discord.TextChannel):
        return f"Error: Text channel '{channel_name}' not found."

    if not str(message_id).strip().isdigit():
        return "Error: Message ID must be a numeric Snowflake ID."

    try:
        msg = await channel.fetch_message(int(message_id))
        await msg.unpin()
        return await _notify_and_return(f"Successfully unpinned message ID {msg.id} in channel #{channel.name}.")
    except discord.NotFound:
        return f"Error: Message ID {message_id} not found in channel #{channel.name}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Messages') to unpin messages in #{channel.name}."
    except Exception as e:
        return f"Error unpinning message: {str(e)}"


# --- Server Inspection (Read-Only) ---


async def list_channels() -> str:
    """
    Lists every channel and category in the server with its type.
    Use this to answer questions like "how many channels do we have?" or "list all channels".
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        categories = sorted(guild.categories, key=lambda c: c.position)
        if not categories and not guild.channels:
            return "This server has no channels yet."
        lines = []
        for cat in categories:
            lines.append(f"📁 Category: {cat.name}")
            for ch in sorted(cat.channels, key=lambda c: c.position):
                lines.append(f"   • #{ch.name} ({ch.type})")
        # Channels not in any category
        uncategorized = [c for c in guild.channels if c.category is None]
        if uncategorized:
            lines.append("📁 Uncategorized:")
            for ch in sorted(uncategorized, key=lambda c: c.position):
                lines.append(f"   • #{ch.name} ({ch.type})")
        lines.append(f"\nTotal channels: {len([c for c in guild.channels])} | Total categories: {len(guild.categories)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing channels: {str(e)}"


async def list_roles() -> str:
    """
    Lists every role in the server with member counts.
    Use this to answer questions like "what roles do we have?" or "how many roles?".
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        lines = []
        for role in roles:
            lines.append(f"• @{role.name} (Members: {len(role.members)})")
        lines.append(f"\nTotal roles: {len(guild.roles)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing roles: {str(e)}"


async def list_members(limit: int = 50) -> str:
    """
    Lists server members with their display names and roles.

    Args:
        limit: Maximum number of members to list (default 50, max 200).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        limit_val = max(1, min(200, int(limit)))
        members = guild.members[:limit_val]
        lines = [f"Members ({len(guild.members)} total, showing up to {limit_val}):"]
        for m in members:
            top_role = m.top_role.name if m.top_role else "None"
            lines.append(f"• {m.display_name} (@{m.name}) — Top role: {top_role}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing members: {str(e)}"


async def server_info() -> str:
    """
    Returns a summary of the server: name, member count, channel count, role count, owner.
    Use this for general "tell me about this server" questions.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        owner_name = guild.owner.display_name if guild.owner else "Unknown"
        text_ch = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_ch = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        return (
            f"Server: {guild.name}\n"
            f"Owner: {owner_name}\n"
            f"Members: {guild.member_count}\n"
            f"Text Channels: {text_ch}\n"
            f"Voice Channels: {voice_ch}\n"
            f"Categories: {len(guild.categories)}\n"
            f"Roles: {len(guild.roles)}\n"
            f"Boost Level: {guild.premium_tier}"
        )
    except Exception as e:
        return f"Error getting server info: {str(e)}"


# --- Personality & Memory & Utility (crazy-good) ---


async def remember_fact(fact: str) -> str:
    """
    Remember a personal fact about the current user for long-term memory.

    Args:
        fact: A short fact to remember, e.g. 'loves valorant', 'birthday is March 3'.
    """
    import storage

    uid = current_user_id.get()
    if not uid or not fact.strip():
        return "Error: Could not save that fact — missing context."
    storage.add_user_fact(int(uid), fact.strip())
    return f"Got it, I'll remember: {fact.strip()}"


async def recall_my_facts() -> str:
    """
    Recall the facts you remember about the current user.
    Use this when the user asks what you remember about them.
    """
    import storage

    uid = current_user_id.get()
    if not uid:
        return "Error: I don't know who you are in this context."
    facts = storage.get_user_facts(int(uid), limit=10)
    if not facts:
        return "I don't have any saved facts about you yet — tell me something to remember!"
    return "Here's what I remember about you:\n• " + "\n• ".join(facts)


async def forget_my_facts() -> str:
    """
    Forget all saved facts about the current user.
    Use when the user asks to forget/clear memory about them.
    """
    import storage

    uid = current_user_id.get()
    if not uid:
        return "Error: Missing user context."
    storage.forget_user_facts(int(uid))
    return "Done — I forgot all saved facts about you."


async def set_server_persona(persona: str) -> str:
    """
    Switch the server's AI personality.

    Args:
        persona: One of: default, savage, wholesome, professor, gamer.
    """
    import storage

    guild = current_guild.get()
    if not guild:
        return "Error: This only works inside a server."
    persona = persona.strip().lower()
    if persona not in PERSONAS:
        return f"Error: Unknown persona '{persona}'. Choose from: {', '.join(PERSONAS)}."
    storage.set_guild_persona(guild.id, persona)
    return f"Switched personality to '{persona}' — {PERSONAS[persona]}"


async def warn_user(username_or_id: str, reason: str = "No reason provided") -> str:
    """
    Give a formal warning to a user and auto-timeout on repeated warnings.
    3 warnings = 10m timeout, 4 = 1h, 5+ = 1 day.

    Args:
        username_or_id: Username, display name, ID or mention of the user.
        reason: Reason for the warning.
    """
    import storage

    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found."
    count = storage.add_warning(guild.id, member.id, reason)
    escalations = {3: 10, 4: 60, 5: 1440}
    timeout_mins = escalations.get(count, 0 if count < 3 else 1440)
    msg = await _notify_and_return(f"Warning {count} for {member.mention} ({member.name}): {reason}")
    if timeout_mins:
        try:
            await member.timeout(datetime.timedelta(minutes=timeout_mins), reason=f"auto timeout after {count} warnings: {reason}")
            msg += f" Auto-timed out for {timeout_mins}m (warning #{count})."
        except Exception as e:
            msg += f" (tried auto timeout {timeout_mins}m but failed: {e})"
    return msg


async def show_warnings(username_or_id: str) -> str:
    """
    Show the warnings a user has received.

    Args:
        username_or_id: Username, display name, ID or mention.
    """
    import storage

    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found."
    rows = storage.get_warnings(guild.id, member.id)
    if not rows:
        return f"{member.mention} has no warnings."
    lines = [f"{idx+1}. {reason} — <t:{int(ts)}>" for idx, (reason, ts) in enumerate(rows)]
    return f"Warnings for {member.display_name} ({len(rows)} total):\n" + "\n".join(lines)


async def clear_warnings(username_or_id: str) -> str:
    """
    Clear all warnings for a user.

    Args:
        username_or_id: Username, display name, ID or mention.
    """
    import storage

    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found."
    existing = storage.get_warnings(guild.id, member.id)
    if not existing:
        return f"{member.mention} has no warnings to clear."
    gate = await _gate_destructive(f"**Clear ALL warnings** for {member.mention} ({len(existing)} warning(s) will be erased)")
    if gate != "OK":
        return gate
    storage.clear_warnings(guild.id, member.id)
    return await _notify_and_return(f"Cleared all warnings for {member.mention}.")


async def set_reminder(minutes_from_now: int, reminder_text: str) -> str:
    """
    Set a reminder that will ping the user after a delay.

    Args:
        minutes_from_now: Delay in minutes (1 to 10080 = 7 days).
        reminder_text: What to remind them about.
    """
    import storage

    guild = current_guild.get()
    uid = current_user_id.get()
    if not uid:
        return "Error: Missing user context for reminder."
    # Need channel_id — store via a context var or use guild var not enough; use current_guild channel lookup
    # We'll attach via a temporary ctx: bot.py sets a var before calling
    channel_id_holder = current_reminder_channel.get()
    if not channel_id_holder:
        return "Error: Could not determine channel for reminder."

    minutes_from_now = max(1, min(10080, int(minutes_from_now)))
    remind_at = datetime.datetime.now(datetime.timezone.utc).timestamp() + minutes_from_now * 60
    rid = storage.add_reminder(
        guild.id if guild else None, int(channel_id_holder), int(uid), remind_at, reminder_text
    )
    return f"Reminder set for {minutes_from_now}m from now (ID {rid}): {reminder_text}"


async def create_poll(question: str, options: str) -> str:
    """
    Create a simple text poll listing the question and options.

    Args:
        question: Poll question, e.g. 'Best pizza?'
        options: Comma-separated options, e.g. 'pepperoni, margherita, hawaiian'
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    opts = [o.strip() for o in options.split(",") if o.strip()]
    if len(opts) < 2 or len(opts) > 10:
        return "Error: Provide 2 to 10 comma-separated options."
    if not question.strip():
        return "Error: Question cannot be empty."
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines = [f"**Poll: {question.strip()}**"]
    for idx, opt in enumerate(opts):
        lines.append(f"{emojis[idx]} {opt}")
    # Caller (bot.py) will add the numeric reactions; this tool just returns text
    return "\n".join(lines) + "\n\nReact with the number to vote!"


async def show_leaderboard() -> str:
    """
    Show the XP leaderboard for this server.
    Use when users ask about levels, rank, or who's most active.
    """
    import storage

    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    rows = storage.get_xp_leaderboard(guild.id, limit=10)
    if not rows:
        return "No XP yet — just chat a bit and you'll show up here!"
    lines = []
    for idx, (uid, xp) in enumerate(rows, 1):
        member = guild.get_member(uid)
        name = member.display_name if member else f"User {uid}"
        level = xp // 100
        lines.append(f"{idx}. {name} — Level {level} ({xp} XP)")
    return "🏆 Leaderboard:\n" + "\n".join(lines)


# --- Tickets ---


async def create_ticket(username_or_id: str, issue: str = "", category_name: str = "tickets") -> str:
    """
    Open a private ticket channel for a user. The channel is only visible to the user, mods and the bot.

    Args:
        username_or_id: The user who needs a ticket (username, display name, ID or mention).
        issue: Short description of the issue for the ticket's topic.
        category_name: Optional category to place the ticket under (default 'tickets').
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    safe_topic = (issue or f"Ticket for {member.display_name}")[:100]

    # Find or auto-create the tickets category
    category = None
    if category_name:
        category = find_category(guild, category_name)
        if not category:
            try:
                category = await guild.create_category(name=category_name)
            except Exception as e:
                return f"Error creating category '{category_name}': {str(e)}"

    # Build permission overwrites: user visible, @everyone hidden, mods/bot visible
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True),
    }
    # Give any role with Manage Messages / Moderate Members / Manage Roles visibility as staff
    try:
        for role in guild.roles:
            if role.is_default():
                continue
            perms = role.permissions
            if any(getattr(perms, p, False) for p in ("manage_messages", "moderate_members", "manage_roles", "administrator", "kick_members", "ban_members")):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    except Exception:
        pass

    channel_name = f"ticket-{member.name.lower().replace(' ', '-')}"[:90]
    existing = find_channel(guild, channel_name)
    if existing:
        return f"Error: A ticket channel for {member.mention} already exists: {existing.mention}."

    try:
        ch = await guild.create_text_channel(
            name=channel_name, topic=safe_topic, category=category, overwrites=overwrites
        )
        return await _notify_and_return(
            f"Ticket opened for {member.mention} in {ch.mention} — topic: {safe_topic}"
        )
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Channels') to create ticket for {member.display_name}."
    except Exception as e:
        return f"Error opening ticket: {str(e)}"


async def close_ticket(channel_name: str = "") -> str:
    """
    Close and delete a ticket channel.

    Args:
        channel_name: Name, ID or mention of the ticket channel to close.
                      Empty = close the current channel you're in.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    target = None
    if channel_name.strip():
        target = find_channel(guild, channel_name)
        if not target:
            return f"Error: Channel '{channel_name}' not found."
    else:
        chan_id = current_reminder_channel.get()
        if chan_id:
            target = guild.get_channel(int(chan_id))

    if not target:
        return "Error: Could not determine which ticket channel to close. Name it or run this inside the ticket itself."

    gate = await _gate_destructive(f"**Close ticket** {getattr(target, 'mention', target.name)} (`{target.name}`)\nThis permanently deletes the channel.")
    if gate != "OK":
        return gate

    try:
        name = target.name
        await target.delete(reason="ticket closed")
        return await _notify_and_return(f"Closed ticket channel '{name}'.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission to delete '{target.name}'."
    except Exception as e:
        return f"Error closing ticket: {str(e)}"


# --- Channel Editing & Extended Management ---


async def edit_channel(
    channel_name: str,
    new_name: str = "",
    topic: str = "",
    slowmode_seconds: int = -1,
    nsfw: Optional[bool] = None,
    bitrate: int = -1,
) -> str:
    """
    Edit an existing channel's properties.

    Args:
        channel_name: Name, ID or mention of the channel to edit.
        new_name: New name for the channel (empty = no change).
        topic: New topic/description (only for text/announcement channels, empty = no change).
        slowmode_seconds: Slowmode delay 0-21600 seconds (-1 = no change).
        nsfw: Whether channel is marked NSFW (None = no change).
        bitrate: Voice bitrate 8000-384000 (-1 = no change).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not channel:
        return f"Error: Channel '{channel_name}' not found."
    kwargs = {}
    if new_name.strip():
        kwargs["name"] = new_name.strip()[:100]
    if topic != "" and hasattr(channel, "topic"):
        kwargs["topic"] = topic[:1024] if topic else None
    if slowmode_seconds != -1 and hasattr(channel, "edit"):
        if 0 <= int(slowmode_seconds) <= 21600:
            kwargs["slowmode_delay"] = int(slowmode_seconds)
    if nsfw is not None and hasattr(channel, "nsfw"):
        kwargs["nsfw"] = bool(nsfw)
    if bitrate != -1 and hasattr(channel, "bitrate"):
        if 8000 <= int(bitrate) <= 384000:
            kwargs["bitrate"] = int(bitrate)
    if not kwargs:
        return "Error: No valid edit parameters provided."
    try:
        await channel.edit(**kwargs)
        return await _notify_and_return(f"Successfully edited channel '{channel.name}' with {kwargs}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Channels') to edit '{channel.name}'."
    except Exception as e:
        return f"Error editing channel: {str(e)}"


# --- Font & Bulk Rename Utilities ---

# Stylish font mappings (a-z, A-Z, 0-9) — add more as needed
_FONT_MAPS: Dict[str, Dict[str, str]] = {
    "bold": {**{chr(o+i): chr(0x1D400+i) for i in range(26) for o in [ord('a')]}, **{chr(ord('A')+i): chr(0x1D400+i) for i in range(26)}, **{chr(ord('a')+i): chr(0x1D41A+i) for i in range(26)}, **{chr(ord('0')+i): chr(0x1D7CE+i) for i in range(10)}},
    "spaced": {},  # handled specially: "general" -> "g e n e r a l ♥"
    "gothic": {chr(ord('a')+i): chr(0x1D51E+i) if i<26 else chr(0x1D51E+i) for i in range(26)},
}

# Build bold map correctly (separate upper/lower)
_BOLD_LOWER = {chr(ord('a')+i): chr(0x1D41A+i) for i in range(26)}
_BOLD_UPPER = {chr(ord('A')+i): chr(0x1D400+i) for i in range(26)}
_BOLD_DIGIT = {chr(ord('0')+i): chr(0x1D7CE+i) for i in range(10)}
_FONT_MAPS["bold"] = {**_BOLD_LOWER, **_BOLD_UPPER, **_BOLD_DIGIT}
_FONT_MAPS["italic"] = {**{chr(ord('a')+i): chr(0x1D44E+i) for i in range(26)}, **{chr(ord('A')+i): chr(0x1D434+i) for i in range(26)}}
_FONT_MAPS["monospace"] = {**{chr(ord('a')+i): chr(0x1D68A+i) for i in range(26)}, **{chr(ord('A')+i): chr(0x1D670+i) for i in range(26)}, **{chr(ord('0')+i): chr(0x1D7F6+i) for i in range(10)}}
# aesthetic spaced is special, gothic simplified
_FONT_MAPS["gothic"] = {chr(ord('a')+i): chr(0x1D56E+i) for i in range(26)}  # placeholder fallback

def _convert_to_font(text: str, font: str) -> str:
    font = font.lower().strip()
    if font in ("spaced", "aesthetic", "g e n e r a l", "heart"):
        # "general" -> "g e n e r a l ♥"  (your example style)
        base = text.strip().lower().replace(" ", "-")
        # Keep original alphanum, insert spaces between chars
        spaced = " ".join(list(base))
        return f"{spaced} ♥"
    mapping = _FONT_MAPS.get(font)
    if not mapping:
        return text  # fallback: return original
    return "".join(mapping.get(c, c) for c in text)


async def list_fonts() -> str:
    """
    List all available stylish fonts for channel/category names with examples.
    Use this when the user asks 'find different fonts' or wants font options.
    """
    examples = []
    sample = "general"
    for fname in sorted(_FONT_MAPS.keys()):
        converted = _convert_to_font(sample, fname)
        examples.append(f"• **{fname}**: {converted}")
    # Add aesthetic description
    examples.append("• **spaced/aesthetic**: g e n e r a l ♥  (spaced letters with heart — your current # g e n e r a l style)")
    return "Available fonts (use with bulk_rename):\n" + "\n".join(examples) + "\n\nTip: Ask 'rename all categories to bold font' or 'make channels in gothic'."


async def bulk_rename_channels(
    target: str = "categories",
    font: str = "spaced",
    filter_name: str = "",
) -> str:
    """
    Bulk-rename channels or categories to a stylish font in one go.

    Args:
        target: What to rename — 'categories', 'channels', 'all', or 'category_channels'. Use 'categories' for your request.
        font: Font name from list_fonts — e.g. 'spaced', 'bold', 'italic', 'monospace', 'gothic'.
        filter_name: Optional substring to filter which names to rename (empty = all).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    font = font.lower().strip() or "spaced"
    target = target.lower().strip()

    # Collect targets — NO guess fallbacks: unknown target asks the user instead of renaming everything
    targets: List[discord.abc.GuildChannel] = []
    if target in ("categories", "category", "cats"):
        targets = list(guild.categories)
    elif target in ("channels", "text", "voice", "all_channels"):
        targets = [c for c in guild.channels if not isinstance(c, discord.CategoryChannel)]
    elif target in ("all", "everything", "both"):
        targets = list(guild.categories) + [c for c in guild.channels if not isinstance(c, discord.CategoryChannel)]
    else:
        # Try to interpret target as a specific category name to rename its children
        cat = find_category(guild, target)
        if cat:
            targets = list(cat.channels)
        else:
            return (
                f"AMBIGUOUS TARGET: '{target}' is not a recognized scope.\n"
                f"Valid scopes: `categories`, `channels`, `all`, or an exact category name.\n"
                f"Ask the user which they meant instead of guessing."
            )

    if filter_name.strip():
        filt = filter_name.strip().lower()
        targets = [t for t in targets if filt in t.name.lower()]

    if not targets:
        return f"Error: No {target} found matching '{filter_name}'."

    # Build rename plan (skip already styled / avoid double conversion)
    plan = []
    for ch in targets:
        new_name = _convert_to_font(ch.name, font)
        # Channel names have strict rules: lowercase, no spaces in actual Discord name? But category names allow spaces/symbols more freely.
        # Discord will auto-lowercase channel names; categories keep case. We'll try as-is.
        if new_name != ch.name:
            plan.append((ch, new_name))

    if not plan:
        return f"No channels needed renaming for font '{font}' — already in that style."

    # Bulk layout change — confirm before mass-editing
    preview = ", ".join(f"{ch.name} → {new_name}" for ch, new_name in plan[:6])
    gate = await _gate_destructive(
        f"**Bulk rename {len(plan)} item(s)** to `{font}` font\nPreview: {preview}" + (" ..." if len(plan) > 6 else "")
    )
    if gate != "OK":
        return gate

    successes, failures = [], []
    for channel, new_name in plan:
        try:
            await channel.edit(name=new_name[:100])
            successes.append(f"• {channel.id} → {new_name}")
            await asyncio.sleep(1.0)  # rate-limit pacing for bulk edits (Discord 5/5s per guild)
        except discord.Forbidden:
            failures.append(f"• {channel.name}: missing Manage Channels")
        except discord.HTTPException as e:
            if "50035" in str(e) or "name" in str(e).lower():
                failures.append(f"• {channel.name}: invalid name for Discord (try simpler font)")
            else:
                failures.append(f"• {channel.name}: {str(e)[:80]}")
        except Exception as e:
            failures.append(f"• {channel.name}: {str(e)[:80]}")

    summary = f"Bulk rename ({font}) — {len(successes)}/{len(plan)} succeeded for target '{target}':\n" + "\n".join(successes[:20])
    if failures:
        summary += "\n\nFailures:\n" + "\n".join(failures[:10])
    if len(plan) > 20:
        summary += f"\n...and {len(plan)-20} more"
    return await _notify_and_return(summary)


async def bulk_ban(username_or_ids: str, reason: str = "Bulk ban", delete_message_days: int = 1) -> str:
    """
    Bulk-ban up to 200 users at once.

    Args:
        username_or_ids: Comma-separated list of usernames, IDs or mentions.
        reason: Reason for the bulk ban.
        delete_message_days: Days of messages to delete (0-7).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    raw = [x.strip() for x in username_or_ids.split(",") if x.strip()]
    if not raw:
        return "Error: No users provided for bulk ban."
    if len(raw) > 200:
        return "Error: Bulk ban supports up to 200 users at once."
    # Resolve to IDs
    ids = []
    for entry in raw:
        member = find_member(guild, entry)
        if member:
            ids.append(member.id)
        elif entry.isdigit():
            ids.append(int(entry))
        else:
            m = re.match(r"^<@!?(\d+)>$", entry)
            if m:
                ids.append(int(m.group(1)))
    if not ids:
        return "Error: None of the provided users could be resolved."
    # HARD GATE — bulk ban always confirms, even for owner
    gate = await _gate_destructive(
        f"**BULK BAN {len(ids)} user(s)**\nReason: {reason}\nDelete message days: {delete_message_days}\nIDs: " + ", ".join(f"<@{i}>" for i in ids[:15]) + (" ..." if len(ids) > 15 else "")
    )
    if gate != "OK":
        return gate
    try:
        # Use guild.bulk_ban if available (discord.py 2.4+), else loop
        if hasattr(guild, "bulk_ban"):
            snowflakes = [discord.Object(id=i) for i in ids]
            try:
                await guild.bulk_ban(snowflakes, reason=reason, delete_message_days=max(0, min(7, int(delete_message_days))))
            except TypeError:
                # older signature
                await guild.bulk_ban(snowflakes, reason=reason)
        else:
            for uid in ids:
                await guild.ban(discord.Object(id=uid), reason=reason)
        return await _notify_and_return(f"Bulk-banned {len(ids)} users. Reason: {reason}")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Ban Members') for bulk ban."
    except Exception as e:
        return f"Error during bulk ban: {str(e)}"


# --- Native Discord Polls ---


async def create_native_poll(question: str, options: str, duration_hours: int = 24, allow_multiselect: bool = False) -> str:
    """
    Create a native Discord Poll widget (not a text poll).

    Args:
        question: Poll question (max 300 characters).
        options: Comma-separated answers (2-10, each max 55 characters).
        duration_hours: How long the poll runs (1-768 hours, default 24).
        allow_multiselect: Whether users can select multiple answers.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel_id = current_reminder_channel.get()
    if not channel_id:
        return "Error: Could not determine channel for poll."
    channel = guild.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return "Error: Polls can only be created in text channels."
    opts = [o.strip() for o in options.split(",") if o.strip()]
    if len(opts) < 2 or len(opts) > 10:
        return "Error: Provide 2 to 10 comma-separated options."
    try:
        poll = discord.Poll(
            question=discord.PollQuestion(text=question[:300]),
            duration=datetime.timedelta(hours=max(1, min(768, int(duration_hours)))),
            allow_multiselect=bool(allow_multiselect),
        )
        for opt in opts:
            poll.add_answer(text=opt[:55])
        msg = await channel.send(poll=poll)
        return await _notify_and_return(f"Created native poll '{question[:300]}' with {len(opts)} options in {channel.mention} (ID: {msg.id}).")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Send Messages' + 'Send Polls') in {channel.name}."
    except Exception as e:
        return f"Error creating native poll: {str(e)}"


async def expire_poll(message_id: str) -> str:
    """
    End a native polling early.

    Args:
        message_id: The Snowflake ID of the poll message to end.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel_id = current_reminder_channel.get()
    if not channel_id:
        return "Error: Could not determine channel for poll."
    channel = guild.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return "Error: Polls exist only in text channels."
    if not str(message_id).strip().isdigit():
        return "Error: Message ID must be numeric."
    try:
        msg = await channel.fetch_message(int(message_id))
        if not msg.poll:
            return f"Error: Message {message_id} is not a poll."
        await msg.poll.end()
        return await _notify_and_return(f"Ended poll {message_id} early in {channel.mention}.")
    except discord.NotFound:
        return f"Error: Message {message_id} not found."
    except discord.Forbidden:
        return "Error: Bot lacks permission to end this poll (must be the poll author)."
    except Exception as e:
        return f"Error ending poll: {str(e)}"


# --- Invites ---


async def create_invite(channel_name: str = "", max_age: int = 86400, max_uses: int = 0) -> str:
    """
    Create an invite link for a channel.

    Args:
        channel_name: Channel name/ID/mention (empty = current channel).
        max_age: Seconds until expiry (0 = never expires).
        max_uses: Max uses (0 = unlimited).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    target = None
    if channel_name.strip():
        target = find_channel(guild, channel_name)
    else:
        cid = current_reminder_channel.get()
        if cid:
            target = guild.get_channel(int(cid))
    if not target or not hasattr(target, "create_invite"):
        return f"Error: Channel '{channel_name or 'current'}' not found or not invitable."
    try:
        invite = await target.create_invite(max_age=int(max_age), max_uses=int(max_uses))
        return f"Invite for {target.name}: {invite.url} (expires in {max_age}s, max uses {max_uses})"
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Create Instant Invite') for {target.name}."
    except Exception as e:
        return f"Error creating invite: {str(e)}"


async def list_invites() -> str:
    """
    List all invites for this server.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        invites = await guild.invites()
        if not invites:
            return "No active invites in this server."
        lines = [f"• {inv.url} — channel #{inv.channel.name} by {inv.inviter} (uses {inv.uses}/{inv.max_uses or '∞'})" for inv in invites[:20]]
        return "\n".join(lines) + f"\nTotal invites: {len(invites)}"
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Server') to list invites."
    except Exception as e:
        return f"Error listing invites: {str(e)}"


async def delete_invite(invite_code_or_url: str) -> str:
    """
    Delete an invite by code or full URL.

    Args:
        invite_code_or_url: Invite code (e.g. 'abc123') or full discord.gg URL.
    """
    invite_code_or_url = invite_code_or_url.strip()
    # Extract code from full URL
    if "discord.gg/" in invite_code_or_url:
        invite_code_or_url = invite_code_or_url.split("discord.gg/")[-1].split("?")[0].split("/")[0]
    if "/" in invite_code_or_url:
        invite_code_or_url = invite_code_or_url.split("/")[-1]
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        invites = await guild.invites()
        for inv in invites:
            if inv.code == invite_code_or_url or inv.url == invite_code_or_url:
                await inv.delete()
                return await _notify_and_return(f"Deleted invite {inv.code} ({inv.url}).")
        return f"Error: Invite '{invite_code_or_url}' not found among {len(invites)} active invites."
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Server') to delete invites."
    except Exception as e:
        return f"Error deleting invite '{invite_code_or_url}': {str(e)}"


# --- Reactions ---


async def add_reaction(channel_name: str, message_id: str, emoji: str) -> str:
    """
    Add a reaction emoji to a message.

    Args:
        channel_name: Channel name/ID/mention.
        message_id: The message Snowflake ID.
        emoji: Emoji to add (unicode like '👍' or custom like '<:name:id>').
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return f"Error: Channel '{channel_name}' not found."
    if not str(message_id).strip().isdigit():
        return "Error: Message ID must be numeric."
    try:
        msg = await channel.fetch_message(int(message_id))
        await msg.add_reaction(emoji)
        return f"Added reaction {emoji} to message {message_id} in #{channel.name}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission to add reactions in #{channel.name}."
    except Exception as e:
        return f"Error adding reaction: {str(e)}"


async def clear_reactions(channel_name: str, message_id: str, emoji: str = "") -> str:
    """
    Clear reactions from a message.

    Args:
        channel_name: Channel name/ID/mention.
        message_id: The message Snowflake ID.
        emoji: Specific emoji to clear (empty = clear all reactions).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return f"Error: Channel '{channel_name}' not found."
    try:
        msg = await channel.fetch_message(int(message_id))
        if emoji.strip():
            await msg.clear_reaction(emoji.strip())
            return f"Cleared reactions {emoji} from message {message_id}."
        else:
            await msg.clear_reactions()
            return f"Cleared all reactions from message {message_id}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Messages') to clear reactions."
    except Exception as e:
        return f"Error clearing reactions: {str(e)}"


# --- Webhooks ---


async def create_webhook(channel_name: str, webhook_name: str) -> str:
    """
    Create a webhook in a text channel.

    Args:
        channel_name: Channel name/ID/mention.
        webhook_name: Name for the webhook (1-80 characters).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return f"Error: Channel '{channel_name}' not found."
    try:
        hook = await channel.create_webhook(name=webhook_name[:80])
        return await _notify_and_return(f"Created webhook '{hook.name}' in #{channel.name}: {hook.url}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Webhooks') in #{channel.name}."
    except Exception as e:
        return f"Error creating webhook: {str(e)}"


async def list_webhooks(channel_name: str = "") -> str:
    """
    List webhooks in a channel (or all channels if no channel specified).

    Args:
        channel_name: Channel name/ID/mention (empty = all channels in server).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        if channel_name.strip():
            channel = find_channel(guild, channel_name)
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Channel '{channel_name}' not found."
            hooks = await channel.webhooks()
        else:
            hooks = await guild.webhooks()
        if not hooks:
            return "No webhooks found."
        lines = [f"• {h.name} in #{h.channel.name if h.channel else '?'} — {h.url}" for h in hooks[:20]]
        return "\n".join(lines)
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Webhooks') to list webhooks."
    except Exception as e:
        return f"Error listing webhooks: {str(e)}"


async def delete_webhook(webhook_url_or_name: str) -> str:
    """
    Delete a webhook by its URL or name.

    Args:
        webhook_url_or_name: Full webhook URL or the webhook name.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        hooks = await guild.webhooks()
        target = None
        for h in hooks:
            if h.url == webhook_url_or_name.strip() or h.name == webhook_url_or_name.strip():
                target = h
                break
        if not target:
            return f"Error: Webhook '{webhook_url_or_name}' not found."
        gate = await _gate_destructive(f"**Delete webhook** `{target.name}` in {getattr(target.channel, 'mention', 'unknown channel')}")
        if gate != "OK":
            return gate
        await target.delete()
        return await _notify_and_return(f"Deleted webhook '{target.name}'.")
    except discord.Forbidden:
        return "Error: Bot lacks permission to delete webhooks."
    except Exception as e:
        return f"Error deleting webhook: {str(e)}"


# --- Emojis / Stickers / Soundboard ---


async def list_emojis() -> str:
    """
    List all custom emojis in this server.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        emojis = guild.emojis
        if not emojis:
            return "No custom emojis in this server."
        lines = [f"• {e.name} <:{e.name}:{e.id}> — {e.url}" for e in emojis[:30]]
        return "\n".join(lines) + f"\nTotal emojis: {len(emojis)}"
    except Exception as e:
        return f"Error listing emojis: {str(e)}"


async def create_emoji(emoji_name: str, image_url: str) -> str:
    """
    Create a custom emoji from an image URL.

    Args:
        emoji_name: Name for the emoji (2-32 characters, alphanumeric + underscore).
        image_url: Direct URL to the image (PNG/JPG/GIF, max 256 KiB, 128x128).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    if not emoji_name.strip():
        return "Error: Emoji name cannot be empty."
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    return f"Error: Could not download image from {image_url} (status {resp.status})."
                if int(resp.headers.get("Content-Length", "0") or 0) > 256 * 1024:
                    return "Error: Image too large for emoji (max 256 KiB)."
                data = await resp.content.read(256 * 1024 + 1)
                if len(data) > 256 * 1024:
                    return "Error: Image too large for emoji (max 256 KiB)."
                img_bytes = data
        emoji = await guild.create_custom_emoji(name=emoji_name.strip()[:32], image=img_bytes)
        return await _notify_and_return(f"Created emoji :{emoji.name}: <:{emoji.name}:{emoji.id}>")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Create Guild Expressions') to create emojis."
    except Exception as e:
        return f"Error creating emoji: {str(e)}"


# --- Scheduled Events ---


async def create_scheduled_event(
    event_name: str, description: str = "", start_in_minutes: int = 60, event_type: str = "external", location: str = ""
) -> str:
    """
    Create a scheduled event.

    Args:
        event_name: Name of the event.
        description: Description of the event.
        start_in_minutes: Minutes from now until start (1 to 10080).
        event_type: One of external, voice, stage (external = no channel, voice = voice channel, stage = stage channel).
        location: Channel name or location text (for external events this is the location string).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=max(1, min(10080, int(start_in_minutes))))
        kwargs = {"name": event_name[:100], "description": description[:1000], "start_time": start_time}
        if event_type.lower() == "external":
            kwargs["location"] = location or "TBD"
            kwargs["entity_type"] = discord.EntityType.external
            kwargs["end_time"] = start_time + datetime.timedelta(hours=1)
        else:
            ch = find_channel(guild, location) if location else None
            if not ch:
                return f"Error: Channel '{location}' not found for {event_type} event."
            kwargs["channel"] = ch
            kwargs["entity_type"] = discord.EntityType.voice if event_type.lower() == "voice" else discord.EntityType.stage_instance
        event = await guild.create_scheduled_event(**kwargs)
        return await _notify_and_return(f"Created scheduled event '{event.name}' for <t:{int(start_time.timestamp())}:F> (ID: {event.id}).")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Events') to create events."
    except Exception as e:
        return f"Error creating scheduled event: {str(e)}"


async def list_scheduled_events() -> str:
    """
    List all scheduled events in this server.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        events = guild.scheduled_events
        if not events:
            return "No scheduled events in this server."
        lines = []
        for ev in events[:20]:
            status = str(ev.status).split(".")[-1] if ev.status else "unknown"
            lines.append(f"• {ev.name} — <t:{int(ev.start_time.timestamp())}:F> ({status})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing events: {str(e)}"


# --- Stage Instance ---


async def create_stage_instance(channel_name: str, topic: str) -> str:
    """
    Create a Stage instance (go live) in a stage channel.

    Args:
        channel_name: Stage channel name/ID/mention.
        topic: Topic for the Stage (1-120 characters).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.StageChannel):
        return f"Error: Stage channel '{channel_name}' not found."
    try:
        inst = await channel.create_instance(topic=topic[:120])
        return await _notify_and_return(f"Stage live in {channel.mention}: {inst.topic}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission to create Stage instance in {channel.name}."
    except Exception as e:
        return f"Error creating Stage instance: {str(e)}"


# --- AutoMod ---


async def list_automod_rules() -> str:
    """
    List all AutoMod rules in this server.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        rules = await guild.fetch_automod_rules()
        if not rules:
            return "No AutoMod rules in this server."
        lines = [f"• {r.name} — trigger {r.trigger.type} enabled={r.enabled} (ID: {r.id})" for r in rules[:20]]
        return "\n".join(lines)
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Server') to list AutoMod rules."
    except Exception as e:
        return f"Error listing AutoMod rules: {str(e)}"


async def create_automod_rule(rule_name: str, trigger_words: str, block_message: bool = True) -> str:
    """
    Create an AutoMod keyword filter rule.

    Args:
        rule_name: Name for the rule.
        trigger_words: Comma-separated keywords to block (e.g. 'spam, scam, badword').
        block_message: Whether to block the message (True) or just send an alert.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    keywords = [w.strip() for w in trigger_words.split(",") if w.strip()]
    if not keywords:
        return "Error: No keywords provided."
    try:
        trigger = discord.AutoModTrigger(type=discord.AutoModTriggerType.keyword, keyword_filter=keywords)
        actions = []
        if block_message:
            actions.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message))
        else:
            # Need a mod-log channel for alert
            log_ch = None
            try:
                log_ch = guild.get_channel(config.MOD_LOG_CHANNEL_ID) if config.MOD_LOG_CHANNEL_ID else None
            except Exception:
                pass
            if log_ch:
                actions.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.send_alert_message, channel=log_ch))
        rule = await guild.create_automod_rule(
            name=rule_name[:100],
            event_type=discord.AutoModEventType.message_send,
            trigger=trigger,
            actions=actions,
            enabled=True,
        )
        return await _notify_and_return(f"Created AutoMod rule '{rule.name}' with {len(keywords)} keywords (ID: {rule.id}).")
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Server') to create AutoMod rules."
    except Exception as e:
        return f"Error creating AutoMod rule: {str(e)}"


# --- Audit Log ---


async def read_audit_log(limit: int = 10, action_type: str = "") -> str:
    """
    Read recent audit log entries.

    Args:
        limit: Number of entries to read (1-20).
        action_type: Optional filter (e.g. 'ban', 'kick', 'channel_create', 'role_create' or empty for all).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    try:
        entries = []
        async for entry in guild.audit_logs(limit=max(1, min(20, int(limit)))):
            # Simple substring filter on action name
            action_name = str(entry.action).split(".")[-1].lower()
            if action_type.strip() and action_type.strip().lower() not in action_name:
                continue
            entries.append(f"• {entry.user} {action_name} → {entry.target} — <t:{int(entry.created_at.timestamp())}:R> {entry.reason or ''}")
            if len(entries) >= int(limit):
                break
        if not entries:
            return "No matching audit log entries found."
        return "\n".join(entries)
    except discord.Forbidden:
        return "Error: Bot lacks permission ('View Audit Log') to read audit logs."
    except Exception as e:
        return f"Error reading audit log: {str(e)}"


# --- Threads & Forums ---


async def create_thread(channel_name: str, thread_name: str, is_private: bool = False) -> str:
    """
    Create a thread in a text channel.

    Args:
        channel_name: Parent text channel name/ID/mention.
        thread_name: Name for the thread.
        is_private: Whether to create a private thread (requires Manage Threads).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return f"Error: Text channel '{channel_name}' not found."
    try:
        if is_private:
            thread = await channel.create_thread(name=thread_name[:100], auto_archive_duration=1440, type=discord.ChannelType.private_thread)
        else:
            thread = await channel.create_thread(name=thread_name[:100], auto_archive_duration=1440)
        return await _notify_and_return(f"Created {'private ' if is_private else ''}thread {thread.mention} in #{channel.name}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission to create threads in #{channel.name}."
    except Exception as e:
        return f"Error creating thread: {str(e)}"


async def archive_thread(channel_name: str, locked: bool = False) -> str:
    """
    Archive (or lock) a thread.

    Args:
        channel_name: Thread name/ID/mention.
        locked: Whether to lock the thread as well (only mods can unlock).
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."
    thread = find_channel(guild, channel_name)
    if not thread or not isinstance(thread, discord.Thread):
        return f"Error: Thread '{channel_name}' not found."
    try:
        await thread.edit(archived=True, locked=bool(locked))
        return await _notify_and_return(f"Archived thread '{thread.name}'{' and locked' if locked else ''}.")
    except discord.Forbidden:
        return f"Error: Bot lacks permission to archive thread '{thread.name}'."
    except Exception as e:
        return f"Error archiving thread: {str(e)}"


current_reminder_channel: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "current_reminder_channel", default=None
)


# --- Web Research & GIFs ---


async def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for information. Use for research, news, definitions, or any factual lookup.

    Args:
        query: Search query (e.g. 'valorant new agent 2025', 'python decorators').
        num_results: Number of results to return (1-10, default 5).
    """
    import aiohttp
    from bs4 import BeautifulSoup
    import urllib.parse

    query = query.strip()
    if not query:
        return "Error: Query cannot be empty."
    num_results = max(1, min(10, int(num_results)))

    q_enc = urllib.parse.quote_plus(query)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/",
    }

    async def _try_fetch(url: str):
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    # DuckDuckGo returns 202 for anti-bot; still has HTML, treat 200/202 as success
                    if resp.status not in (200, 202):
                        return None, f"status {resp.status}"
                    html = await resp.text()
                    return html, None
        except Exception as e:
            return None, str(e)[:150]

    # Try lite first (less bot detection), then html, then Bing fallback
    urls_to_try = [
        f"https://lite.duckduckgo.com/lite/?q={q_enc}",
        f"https://html.duckduckgo.com/html/?q={q_enc}",
        f"https://www.bing.com/search?q={q_enc}",
    ]

    for url in urls_to_try:
        html, err = await _try_fetch(url)
        if html is None:
            continue
        soup = BeautifulSoup(html, "html.parser")
        results = []
        # DuckDuckGo selectors (both lite and html variants)
        for sel in [".result", ".result__body", ".b_algo", "#links .result", "a.result__a"]:
            for res in soup.select(sel)[:num_results]:
                title_el = res.select_one("a") or res.select_one(".result__a")
                if not title_el:
                    continue
                title_raw = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                # DuckDuckGo wraps links via /l/?uddg=
                if "uddg=" in href:
                    try:
                        href = urllib.parse.unquote(href.split("uddg=")[-1].split("&")[0])
                    except Exception:
                        pass
                # Bing wraps via /ck/a?u= base64
                if "bing.com/ck/a" in href and "u=" in href:
                    try:
                        import base64
                        u_param = href.split("u=")[-1].split("&")[0]
                        if u_param.startswith("a1"):
                            u_param = u_param[2:]
                        padded = u_param + "=" * (-len(u_param) % 4)
                        href = base64.b64decode(padded).decode()
                    except Exception:
                        pass
                # Clean title: remove embedded URL artifacts (Bing sometimes duplicates)
                title = title_raw
                if "http" in title_raw:
                    title = title_raw.split("http")[0].strip()
                if not title:
                    title = title_raw[:60]
                snippet_el = res.select_one(".result__snippet") or res.select_one(".b_caption p")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                if title and href and "duckduckgo.com" not in href:
                    results.append(f"{len(results)+1}. **{title}**\n   {href}\n   {snippet[:180]}")
                if len(results) >= num_results:
                    break
            if len(results) >= num_results:
                break
        # Fallback: generic link extraction if no results via selectors
        if not results:
            for a in soup.find_all("a", href=True)[: num_results * 3]:
                href = a.get("href", "")
                # Decode Bing redirects in fallback too
                if "bing.com/ck/a" in href and "u=" in href:
                    try:
                        import base64
                        u_param = href.split("u=")[-1].split("&")[0]
                        if u_param.startswith("a1"):
                            u_param = u_param[2:]
                        padded = u_param + "=" * (-len(u_param) % 4)
                        href = base64.b64decode(padded).decode()
                    except Exception:
                        pass
                elif "uddg=" in href:
                    try:
                        href = urllib.parse.unquote(href.split("uddg=")[-1].split("&")[0])
                    except Exception:
                        pass
                title = a.get_text(strip=True)
                if href.startswith("http") and len(title) > 10 and "duckduckgo.com" not in href:
                    # Filter out Bing's own links
                    if "bing.com" in href and "/ck/a" in href:
                        continue
                    results.append(f"{len(results)+1}. **{title[:80]}**\n   {href}\n")
                    if len(results) >= num_results:
                        break
        if results:
            return f"Web search for '{query}':\n" + "\n\n".join(results[:num_results])

    return f"Web search for '{query}' — no results from primary engines. Try a more specific query or use web_fetch with a direct URL."


async def web_fetch(url: str) -> str:
    """
    Fetch and extract readable text from a URL for research. Use after web_search.
    Uses an intelligent Jina Reader bypass for Cloudflare, paywalls, and JavaScript pages.

    Args:
        url: Full URL to fetch (must start with https://).
    """
    import aiohttp
    from bs4 import BeautifulSoup

    url = url.strip()
    if not url.startswith("http"):
        return "Error: URL must start with http:// or https://."

    # 1. Primary extractor: r.jina.ai proxy (bypasses Cloudflare & renders JS cleanly to markdown)
    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            async with session.get(jina_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if text and len(text.strip()) > 50:
                        return f"Content of {url} (Clean Markdown):\n\n" + text.strip()[:4500]
    except Exception:
        pass

    # 2. Fallback: Direct HTML parser
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return f"Error: Fetch failed with status {resp.status}."
                ctype = resp.headers.get("Content-Type", "")
                if "text/html" not in ctype and "text/" not in ctype:
                    return f"Error: Not a text page (Content-Type: {ctype})."
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()
                text = soup.get_text(separator="\n")
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                cleaned = "\n".join(lines)[:4000]
                if not cleaned:
                    return "Error: No readable text found on the page."
                return f"Content of {url}:\n\n{cleaned}"
    except Exception as e:
        return f"Error fetching URL: {str(e)[:200]}"


async def gif_search(query: str, limit: int = 5) -> str:
    """
    Search for GIFs to send in chat. Returns direct GIF URLs.

    Args:
        query: Search query for the GIF (e.g. 'cat dance', 'valorant ace').
        limit: Number of GIFs to return (1-5, default 3).
    """
    import aiohttp

    query = query.strip()
    if not query:
        return "Error: Query cannot be empty."
    limit = max(1, min(5, int(limit)))

    # Prefer Tenor v2 if key is set, otherwise use public Giphy beta key
    tenor_key = (__import__("os").getenv("TENOR_API_KEY", "") or __import__("os").getenv("GIPHY_API_KEY", "")).strip()
    # Try Tenor first if key available
    if tenor_key and "TENOR" in __import__("os").environ.get("TENOR_API_KEY", "") or tenor_key:
        # Check if it's a Tenor key (starts with AIza)
        is_tenor = tenor_key.startswith("AIza")
        if is_tenor:
            url = f"https://tenor.googleapis.com/v2/search?q={query}&key={tenor_key}&limit={limit}&media_filter=gif"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results = [r["media_formats"]["gif"]["url"] for r in data.get("results", []) if "media_formats" in r]
                            if results:
                                return "GIF results for '" + query + "':\n" + "\n".join(results[:limit]) + "\n\nSend the URL you like in chat — Discord will embed it."
            except Exception:
                pass

    # Fallback: Giphy search (works with public demo key, rate-limited)
    # Try env GIPHY_API_KEY or use a placeholder that hints to add one
    giphy_key = __import__("os").getenv("GIPHY_API_KEY", "").strip() or "GlVGYHkr3WSBnllca54iNt0yFbjz7L65"  # Giphy public beta key
    url = f"https://api.giphy.com/v1/gifs/search?api_key={giphy_key}&q={query}&limit={limit}&rating=g"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = [item["images"]["original"]["url"] for item in data.get("data", [])]
                    if results:
                        return "GIF results for '" + query + "':\n" + "\n".join(results[:limit])
                # If Giphy fails, return a Tenor search link as fallback
                return f"No direct GIF API key configured. Browse GIFs for '{query}': https://tenor.com/search/{query.replace(' ', '-')}-gifs\nTip: Add TENOR_API_KEY or GIPHY_API_KEY to .env for direct URLs."
    except Exception as e:
        return f"Error searching GIFs: {str(e)[:150]} — try https://tenor.com/search/{query.replace(' ', '-')}-gifs"


async def summarize_channel_history(hours: float = 24.0, channel_name_or_id: Optional[str] = None) -> str:
    """
    Fetch and summarize conversation history from a channel over a specific time window (e.g. past 2 hours or past 24 hours).

    Args:
        hours: How many hours of past history to look back (default 24.0, min 0.5, max 72.0).
        channel_name_or_id: Optional channel name, #mention, or ID (defaults to current channel).
    """
    import datetime
    guild = current_guild.get()
    if guild is None:
        return "Error: Channel history can only be summarized inside a server (guild)."

    # Resolve target channel
    target_channel = None
    if channel_name_or_id:
        target_channel = find_channel(guild, channel_name_or_id)
        if target_channel is None:
            return f"Error: Channel '{channel_name_or_id}' could not be found."
    else:
        rem_ch = current_reminder_channel.get()
        if rem_ch:
            target_channel = find_channel(guild, str(rem_ch))
        if target_channel is None and guild.text_channels:
            target_channel = guild.text_channels[0]

    if not isinstance(target_channel, discord.TextChannel):
        return "Error: Target channel is not a readable text channel."

    # Privacy / Permissions check
    user_id = current_user_id.get()
    if user_id:
        member = guild.get_member(user_id)
        if member and not target_channel.permissions_for(member).read_messages:
            return f"Error: You do not have permission to view history in #{target_channel.name}."

    hours = max(0.5, min(72.0, float(hours)))
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)

    messages = []
    try:
        async for msg in target_channel.history(after=cutoff, limit=350, oldest_first=True):
            if msg.author.bot:
                continue
            content = msg.clean_content.strip()
            if content:
                time_str = msg.created_at.strftime("%H:%M")
                messages.append(f"[{time_str}] {msg.author.display_name}: {content[:300]}")
    except discord.Forbidden:
        return f"Error: Bot lacks permission to read message history in #{target_channel.name}."
    except Exception as e:
        return f"Error reading channel history: {str(e)[:150]}"

    if not messages:
        return f"No messages were found in #{target_channel.name} over the past {hours:.1f} hours."

    formatted_transcript = "\n".join(messages[:150])
    return f"Channel #{target_channel.name} transcript for the past {hours:.1f} hours ({len(messages)} messages found):\n\n{formatted_transcript}\n\n[End of Transcript — Summarize the key topics, decisions, and active participants above]."


async def analyze_dispute_timeline(target_users: Optional[str] = None, hours: float = 6.0, channel_name_or_id: Optional[str] = None) -> str:
    """
    Analyze conversation history to diagnose why an argument or dispute started, tracing the timeline and key turning points objectively.

    Args:
        target_users: Optional comma-separated usernames or mentions involved in the dispute.
        hours: How many hours back to scan (default 6.0, max 24.0).
        channel_name_or_id: Optional channel name, #mention, or ID.
    """
    import datetime
    guild = current_guild.get()
    if guild is None:
        return "Error: Dispute analysis can only be performed inside a server (guild)."

    target_channel = None
    if channel_name_or_id:
        target_channel = find_channel(guild, channel_name_or_id)
        if target_channel is None:
            return f"Error: Channel '{channel_name_or_id}' could not be found."
    else:
        rem_ch = current_reminder_channel.get()
        if rem_ch:
            target_channel = find_channel(guild, str(rem_ch))
        if target_channel is None and guild.text_channels:
            target_channel = guild.text_channels[0]

    if not isinstance(target_channel, discord.TextChannel):
        return "Error: Target channel is not a readable text channel."

    # Permissions check
    user_id = current_user_id.get()
    if user_id:
        member = guild.get_member(user_id)
        if member and not target_channel.permissions_for(member).read_messages:
            return f"Error: You do not have permission to view messages in #{target_channel.name}."

    hours = max(0.5, min(24.0, float(hours)))
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)

    messages = []
    try:
        async for msg in target_channel.history(after=cutoff, limit=300, oldest_first=True):
            if msg.author.bot:
                continue
            content = msg.clean_content.strip()
            if content:
                time_str = msg.created_at.strftime("%H:%M:%S")
                messages.append(f"[{time_str}] {msg.author.display_name}: {content[:300]}")
    except Exception as e:
        return f"Error reading channel dispute logs: {str(e)[:150]}"

    if not messages:
        return f"No recent messages found in #{target_channel.name} within the last {hours:.1f} hours to analyze."

    transcript = "\n".join(messages[:180])
    target_filter_note = f" (Focus on users: {target_users})" if target_users else ""
    return (
        f"Chronological chat transcript from #{target_channel.name} ({len(messages)} messages){target_filter_note}:\n\n"
        f"{transcript}\n\n"
        f"[DISPUTE DIAGNOSIS INSTRUCTION: Analyze the transcript above with strict neutrality. Identify:\n"
        f"1. THE CATALYST: The exact first message/topic that caused disagreement.\n"
        f"2. CORE STANCES: What each participant was arguing for, using brief direct quotes.\n"
        f"3. ESCALATION TURNING POINT: Where the conversation shifted from debate to hostility.\n"
        f"4. CURRENT STATUS: Whether it calmed down or is unresolved.]"
    )


# --- Community Intelligence Platform Suite ---

async def generate_community_report(timeframe_days: int = 7) -> str:
    """
    Generate an executive AI Community Intelligence Report for server admins.
    Summarizes server engagement, top 3 trending topics, community friction/confusion points,
    and actionable recommendations for server leadership.

    Args:
        timeframe_days: Number of days to analyze (default 7, max 14).
    """
    import collector
    guild = current_guild.get()
    if guild is None:
        return "Error: Community reports can only be generated inside a server."

    days = max(1, min(14, int(timeframe_days)))
    hours = days * 24.0
    stats = collector.get_guild_activity_stats(guild.id, hours=hours)
    compressed_context = collector.get_compressed_community_context(guild.id, hours=hours, max_messages=120)

    # Fallback to channel history if in-memory buffer is fresh
    if stats["total_messages"] < 10 and guild.text_channels:
        messages = []
        for ch in guild.text_channels[:3]:
            try:
                async for msg in ch.history(limit=50):
                    if not msg.author.bot and msg.clean_content:
                        messages.append(f"[#{ch.name}] {msg.author.display_name}: {msg.clean_content[:200]}")
            except Exception:
                pass
        if messages:
            compressed_context = "Recent Channel Sample:\n" + "\n".join(messages[:100])

    return (
        f"=== SERVER COMMUNITY INTELLIGENCE AUDIT ({guild.name} — Past {days} Days) ===\n"
        f"Active Members Sampled: {max(stats['active_chatters'], len(guild.members) // 20)}\n"
        f"Context Sample:\n{compressed_context}\n\n"
        f"[COMMUNITY ANALYST DIRECTIVE: Format as an Executive Community Intelligence Report:\n"
        f"1. 📊 ENGAGEMENT & VIBE: Overall sentiment score (e.g. 85% positive) & active discussion tone.\n"
        f"2. 🔥 TOP 3 TRENDING TOPICS: Key discussions driving community activity.\n"
        f"3. ⚠️ PAIN POINTS & CONFUSION: Unanswered user questions or community friction.\n"
        f"4. 💡 ACTIONABLE RECOMMENDATIONS: 2-3 concrete steps admins should take (e.g. FAQ updates, AMAs).]"
    )


async def get_trending_topics(hours: float = 6.0) -> str:
    """
    Inspect real-time trending discussion topics and community buzz in the server.

    Args:
        hours: Lookback window in hours (default 6.0, max 24.0).
    """
    import collector
    guild = current_guild.get()
    if guild is None:
        return "Error: Trending topics can only be checked inside a server."

    hours = max(1.0, min(24.0, float(hours)))
    stats = collector.get_guild_activity_stats(guild.id, hours=hours)

    if not stats["top_keywords"]:
        # Fallback inspection
        if guild.text_channels:
            msgs = []
            try:
                async for msg in guild.text_channels[0].history(limit=60):
                    if not msg.author.bot and msg.clean_content:
                        msgs.append(f"{msg.author.display_name}: {msg.clean_content[:150]}")
                if msgs:
                    return f"Recent discussion pulse in #{guild.text_channels[0].name} (Past {hours:.1f}h):\n" + "\n".join(msgs[:30]) + "\n\nSynthesize the top 3 trending topics from above."
            except Exception:
                pass
        return f"No significant message volume detected in the past {hours:.1f} hours to compute trends."

    keywords_formatted = ", ".join([f"**{kw}** ({cnt}x)" for kw, cnt in stats["top_keywords"][:8]])
    return (
        f"🔥 **Trending Server Pulse (Past {hours:.1f}h)**:\n"
        f"• Active Chatters: {stats['active_chatters']}\n"
        f"• Top Discussion Keywords: {keywords_formatted}\n"
        f"• Recent Questions Logged: {len(stats['sample_questions'])}\n\n"
        f"Synthesize a 3-bullet summary of what the community is focusing on right now."
    )


async def get_repeating_questions() -> str:
    """
    Scan recent server conversations to identify recurring questions members are asking,
    helping staff pinpoint missing documentation and create FAQs.
    """
    import collector
    guild = current_guild.get()
    if guild is None:
        return "Error: Can only check repeating questions inside a server."

    stats = collector.get_guild_activity_stats(guild.id, hours=48.0)
    questions = stats.get("sample_questions", [])

    if not questions:
        return "No recurring questions detected in the active buffer. (Ask members to chat or check back as activity logs)."

    q_list = "\n".join([f"- {q}" for q in questions[:12]])
    return (
        f"Recent Community Inquiries:\n{q_list}\n\n"
        f"[DIRECTIVE: Identify the top 3 recurring themes/questions from the inquiries above and provide a draft official FAQ answer for each to help server moderators.]"
    )


async def index_community_knowledge(category: str, title: str, content: str) -> str:
    """
    Store an official server rule, announcement, tournament detail, or FAQ in the Living Community Knowledge Base.

    Args:
        category: Category type: 'RULE', 'ANNOUNCEMENT', 'FAQ', 'DECISION', or 'EVENT'.
        title: Short title or subject of the knowledge entry.
        content: The full verified details, rules, or answers.
    """
    import knowledge_base
    guild = current_guild.get()
    if guild is None:
        return "Error: Knowledge base can only be updated inside a server."

    user_id = current_user_id.get()
    author_name = "Admin"
    if user_id:
        member = guild.get_member(user_id)
        if member:
            author_name = member.display_name

    entry_id = knowledge_base.add_knowledge_entry(
        guild_id=guild.id,
        category=category,
        title=title,
        content=content,
        author_name=author_name
    )
    return f"✅ Indexed into Community Knowledge Base (ID #{entry_id}) [{category.upper()}]: **{title}**"


async def query_community_knowledge(question: str) -> str:
    """
    Search the server's Living Knowledge Base (rules, announcements, decisions, FAQs) to provide grounded, factual answers.

    Args:
        question: The question or keyword to look up (e.g. 'tournament prize', 'server rules', 'giveaway deadline').
    """
    import knowledge_base
    guild = current_guild.get()
    if guild is None:
        return "Error: Knowledge lookup can only be performed inside a server."

    results = knowledge_base.search_knowledge_entries(guild.id, question, limit=4)
    if not results:
        return f"No direct entry found in the Community Knowledge Base for '{question}'. (Admins can index rules with index_community_knowledge)."

    formatted = []
    for r in results:
        formatted.append(f"📌 **[{r['category']}] {r['title']}** (via {r['author_name']}):\n{r['content']}")

    return f"Knowledge Base entries for '{question}':\n\n" + "\n\n".join(formatted) + "\n\nAnswer the user query accurately citing the grounded facts above."


# --- Voice Channel Controls & Neural Speech Tools ---

async def join_voice_channel(channel_name_or_id: Optional[str] = None) -> str:
    """
    Connect the bot to a voice channel to speak, listen, and hang out with the community.

    Args:
        channel_name_or_id: Optional name or ID of the voice channel to join (e.g. 'general', 'Lounge', '12345'). If omitted, joins the channel where the user is currently connected.
    """
    import voice_service
    import storage
    guild = current_guild.get()
    if guild is None:
        return "Error: Voice channels only exist inside a server (guild)."

    target_vc = None
    if channel_name_or_id:
        target_vc = find_channel(guild, channel_name_or_id)
    else:
        user_id = current_user_id.get()
        if user_id:
            member = guild.get_member(user_id)
            if member and member.voice and member.voice.channel:
                target_vc = member.voice.channel

    if target_vc is None:
        # Fallback: if server has voice channels, pick the first one with active users or general
        for vc in guild.voice_channels:
            if "gen" in vc.name.lower() or len(vc.members) > 0:
                target_vc = vc
                break
        if target_vc is None and guild.voice_channels:
            target_vc = guild.voice_channels[0]

    # Permissions check
    perms = target_vc.permissions_for(guild.me)
    if not perms.connect:
        return f"Error: Bot lacks permission to connect to voice channel #{target_vc.name}."

    try:
        voice_service.ensure_opus_loaded()
        vc = guild.voice_client
        if vc:
            if vc.is_connected() and vc.channel and vc.channel.id == target_vc.id:
                return f"🔊 Already connected to voice channel **#{target_vc.name}**!"
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

        persona = storage.get_guild_persona(guild.id)
        asyncio.create_task(voice_service.play_speech_in_voice(vc, f"Hey everyone! I've joined {target_vc.name}.", persona=persona))
        return f"🔊 Successfully connected to voice channel **#{target_vc.name}**! I am live and ready."
    except Exception as e:
        logger.error(f"Voice join error: {e}", exc_info=True)
        return f"Error connecting to voice channel: {str(e)[:150]}"


async def leave_voice_channel() -> str:
    """
    Disconnect the bot from the current voice channel.
    """
    guild = current_guild.get()
    if guild is None:
        return "Error: Voice operations only work inside a server."

    vc = guild.voice_client
    if vc and vc.is_connected():
        await vc.disconnect()
        return "👋 Disconnected from the voice channel."
    return "The bot is not currently connected to any voice channel."


async def speak_in_voice(text: str, persona: Optional[str] = None) -> str:
    """
    Speak a message out loud in the currently connected voice channel using studio-grade female neural voice.

    Args:
        text: The text/message to synthesize and speak out loud.
        persona: Optional persona tone (default, savage, wholesome, professor, gamer).
    """
    import voice_service
    import storage
    guild = current_guild.get()
    if guild is None:
        return "Error: Voice speech is only supported inside a server."

    vc = guild.voice_client
    if not vc or not vc.is_connected():
        return "The bot is not in a voice channel yet. Use join_voice_channel first."

    active_persona = persona or storage.get_guild_persona(guild.id)
    success = await voice_service.play_speech_in_voice(vc, text, persona=active_persona)
    if success:
        return f"🎙️ Spoke in voice channel **#{vc.channel.name}** [{active_persona.upper()}]: \"{text[:120]}\""
    return "Failed to synthesize or play speech in the voice channel."


# ==============================================================================
# SMART BOT OS v5.0 — COMMUNITY BRAIN & ANALYST TOOLS
# ==============================================================================

async def ask_community_brain(query: str) -> str:
    """
    Query the unified Community Brain graph, vector knowledge, and temporal history
    to answer complex questions about server history, rules, decisions, tournaments, and problems.

    Args:
        query: The question to ask the Community Brain (e.g. 'Why was the tournament moved?', 'What are our key rules?').
    """
    import community_brain
    guild = current_guild.get()
    if guild is None:
        return "Error: Community Brain operations only work inside a server."

    res = community_brain.query_community_brain_unified(guild.id, query)
    
    out = [f"🧠 **COMMUNITY BRAIN SYNTHESIS FOR:** *\"{query}\"*\n"]
    
    # Causal path if found
    if res.get("causal_chain"):
        out.append("🔗 **Causal Chain & Relationships:**")
        for step in res["causal_chain"][:4]:
            out.append(f"• [{step['entity_type']}] **{step['name']}** ({step['status']}) — {step['summary'][:100]}")
        out.append("")

    # Temporal history if found
    if res.get("temporal_history") and len(res["temporal_history"]) > 1:
        out.append("⏳ **Temporal Evolution:**")
        for th in res["temporal_history"]:
            status_tag = "🟢 ACTIVE" if th["status"] == "active" else f"⚪ {th['status'].upper()}"
            out.append(f"• {status_tag} **{th['name']}** — {th['summary'][:80]}")
        out.append("")

    # Knowledge entries if found
    if res.get("knowledge_entries"):
        out.append("📚 **Verified Knowledge Base Records:**")
        for kb in res["knowledge_entries"][:3]:
            out.append(f"• **[{kb['category']}] {kb['title']}**: {kb['content'][:120]}")
        out.append("")

    # Server DNA summary
    dna = res.get("server_dna", {})
    if dna:
        out.append(f"🧬 **Server Context:** {dna.get('server_type', 'Community')} • Tone: {dna.get('communication_style', 'Casual')}")

    return "\n".join(out)


async def query_memory_graph(entity_type: Optional[str] = None, query: Optional[str] = None) -> str:
    """
    Inspect the Community Brain graph nodes, causal connections, and relationships.

    Args:
        entity_type: Optional entity type filter (USER, EVENT, TOPIC, DECISION, PROBLEM, SOLUTION, RULE, ANNOUNCEMENT).
        query: Optional keyword or node name to trace causal pathways.
    """
    import community_graph
    guild = current_guild.get()
    if guild is None:
        return "Error: Memory graph operations only work inside a server."

    if query:
        causal = community_graph.trace_causal_path(guild.id, query)
        if causal:
            out = [f"🕸️ **Memory Graph Causal Trace for:** *\"{query}\"*\n"]
            for step in causal:
                rel = f"[{step['relation'].upper()}]" if step.get("relation") else ""
                out.append(f"• {rel} **{step['entity_type']}**: **{step['name']}** ({step['status']})\n  ↳ {step['summary'][:120]}")
            return "\n".join(out)

    subgraph = community_graph.query_subgraph(guild.id, entity_type=entity_type, limit=12)
    nodes = subgraph.get("nodes", [])
    if not nodes:
        return f"No memory graph nodes found for guild (entity_type={entity_type or 'all'})."

    out = [f"🕸️ **Community Brain Graph** ({len(nodes)} active nodes, {len(subgraph.get('edges', []))} edges):\n"]
    for n in nodes[:10]:
        out.append(f"• **[{n['entity_type']}] {n['name']}** (Score: {n['importance_score']}/10) — {n['summary'][:90]}")
    
    return "\n".join(out)


async def get_community_health_score() -> str:
    """
    Calculate and display the real-time AI Community Health Score (0-100),
    including engagement metrics, staff health, friction points, and recommendations.
    """
    import community_analyst
    guild = current_guild.get()
    if guild is None:
        return "Error: Community Health metrics only work inside a server."

    health = community_analyst.calculate_community_health_score(guild.id, guild=guild)
    
    stage_header = f"{health.get('stage_badge', '🌱')} **Lifecycle Stage:** {health.get('stage', 'Community')}"
    if health.get('server_age_days') is not None:
        stage_header += f" *(Created {health['server_age_days']} days ago)*"

    demo_header = ""
    if health.get('total_members'):
        demo_header = f"👥 **Demographics:** `{health.get('human_members', 0)} Humans` • `{health.get('bot_members', 0)} Bots`\n"

    out = [
        f"📈 **COMMUNITY HEALTH EVALUATION — {guild.name.upper()}**",
        stage_header,
        demo_header if demo_header else "",
        f"🏆 **Overall Score: {health['health_score']}/100 — {health['grade']}**\n",
        "**Score Breakdown:**",
        f"• Engagement & Activity: `{health['metrics']['engagement']}`",
        f"• Staff Responsiveness: `{health['metrics']['staff_responsiveness']}`",
        f"• Friction & Stability: `{health['metrics']['friction_stability']}`",
        f"• Knowledge Grounding: `{health['metrics']['knowledge_grounding']}`",
        f"• Vibe & Retention: `{health['metrics']['vibe_retention']}`\n",
        "**⚠️ Friction Radar:**"
    ]
    # Filter empty lines
    out = [line for line in out if line != ""]
    for f in health["frictions"][:3]:
        out.append(f"• {f}")
    
    out.append("\n**💡 Strategic AI Recommendations:**")
    for r in health["recommendations"][:3]:
        out.append(f"• {r}")

    return "\n".join(out)


async def generate_weekly_report() -> str:
    """
    Generate a full 7-day Executive Community Intelligence Report featuring Server DNA,
    Health Score, Trending Topics, Friction Points, and AI Action Items.
    """
    import community_analyst
    guild = current_guild.get()
    if guild is None:
        return "Error: Community reports only work inside a server."

    return community_analyst.generate_weekly_community_report_text(guild.id, guild.name)


async def scan_server_dna(force_rescan: bool = False) -> str:
    """
    Scans public channels, rules, and announcements to generate or update the Server DNA Profile.

    Args:
        force_rescan: Set to True to re-read public channels and rebuild the profile.
    """
    import community_brain
    guild = current_guild.get()
    if guild is None:
        return "Error: Server DNA profiling only works inside a server."

    if not force_rescan:
        dna = community_brain.get_server_dna(guild.id)
        if dna.get("confidence_pct", 0) > 0 and len(dna.get("scanned_channels", [])) > 0:
            return (
                f"🧬 **SERVER DNA PROFILE — {guild.name}**\n"
                f"• **Archetype:** {dna['server_type']}\n"
                f"• **Communication Style:** {dna['communication_style']}\n"
                f"• **Formality:** {dna['formality_level']} • **Emoji Style:** {dna['emoji_style']}\n"
                f"• **Main Topics:** {', '.join(dna['main_topics'])}\n"
                f"• **Confidence:** {dna['confidence_pct']}%\n"
                f"• **Key Rules:**\n" + "\n".join(f"  - {r}" for r in dna['important_rules'][:3])
            )

    # Collect rules and announcements
    rules_text = ""
    announcements_text = ""
    scanned_channels = []
    
    text_channels = getattr(guild, "text_channels", [])
    for ch in text_channels:
        perms_fn = getattr(ch, "permissions_for", None)
        if perms_fn and hasattr(guild, "me"):
            perms = perms_fn(guild.me)
            if not getattr(perms, "read_messages", True):
                continue
        ch_name_lower = ch.name.lower()
        if "rule" in ch_name_lower or "guideline" in ch_name_lower:
            scanned_channels.append(ch.name)
            if hasattr(ch, "history"):
                try:
                    async for msg in ch.history(limit=10):
                        if msg.content:
                            rules_text += msg.content + "\n"
                except Exception:
                    pass
        elif "announcement" in ch_name_lower or "news" in ch_name_lower or "update" in ch_name_lower:
            scanned_channels.append(ch.name)
            if hasattr(ch, "history"):
                try:
                    async for msg in ch.history(limit=10):
                        if msg.content:
                            announcements_text += msg.content + "\n"
                except Exception:
                    pass
        elif len(scanned_channels) < 8:
            scanned_channels.append(ch.name)

    dna = community_brain.extract_server_dna(
        guild_id=guild.id,
        guild_name=guild.name,
        rules_text=rules_text,
        announcements_text=announcements_text,
        channel_names=[c.name for c in text_channels[:20]]
    )

    return (
        f"🧬 **SERVER DNA PROFILED SUCCESSFULLY!**\n"
        f"• **Server Archetype:** {dna['server_type']}\n"
        f"• **Communication Style:** {dna['communication_style']}\n"
        f"• **Tone / Formality:** {dna['formality_level']} ({dna['emoji_style']})\n"
        f"• **Main Community Topics:** {', '.join(dna['main_topics'])}\n"
        f"• **Confidence Level:** {dna['confidence_pct']}%\n"
        f"• **Scanned Sources:** {', '.join(dna['scanned_channels'][:5]) or 'Server channels'}"
    )


async def manage_memory_privacy(action: str, target: Optional[str] = None) -> str:
    """
    Manage Enterprise Privacy & Memory controls for the community brain.

    Args:
        action: 'view' to inspect stored memories, 'export' to download JSON summary, or 'clear' to wipe server graph.
        target: Optional specific entity type or channel to filter.
    """
    import community_graph
    import json
    guild = current_guild.get()
    if guild is None:
        return "Error: Memory privacy controls only work inside a server."

    action_clean = action.lower().strip()
    if action_clean == "view":
        subgraph = community_graph.query_subgraph(guild.id, entity_type=target, limit=15)
        return (
            f"🛡️ **COMMUNITY MEMORY AUDIT:**\n"
            f"• Total Active Nodes: {len(subgraph['nodes'])}\n"
            f"• Total Causal Edges: {len(subgraph['edges'])}\n"
            f"• Privacy Shield: Enabled (Private channels & DMs strictly excluded)"
        )
    elif action_clean == "export":
        subgraph = community_graph.query_subgraph(guild.id, limit=50)
        return f"📁 **Export Summary:** {len(subgraph['nodes'])} memory nodes and {len(subgraph['edges'])} edges ready for export in Web Dashboard."
    elif action_clean == "clear":
        with community_graph._lock:
            conn = community_graph._get_conn()
            conn.execute("DELETE FROM graph_edges WHERE guild_id = ?", (guild.id,))
            conn.execute("DELETE FROM graph_nodes WHERE guild_id = ?", (guild.id,))
            conn.commit()
        return f"🧹 **Privacy Action Complete:** Cleared all memory graph nodes and relationships for **{guild.name}**."
    else:
        return "Unknown privacy action. Valid actions: 'view', 'export', 'clear'."


# ==============================================================================
# FEATURE SUGGESTIONS & PRODUCT FEEDBACK LOOP
# ==============================================================================

async def suggest_feature(suggestion: str, category: str = "general") -> str:
    """
    Submit a product feature request or capability suggestion for Smart Bot OS.

    Args:
        suggestion: Description of the feature you want added.
        category: Category of feature (e.g. 'voice', 'integrations', 'moderation', 'analytics', 'general').
    """
    import storage
    guild = current_guild.get()
    user_id = current_user_id.get() or current_requester_id.get() or 0
    src_msg = current_source_message.get()
    author_name = src_msg.author.display_name if src_msg and hasattr(src_msg, "author") and hasattr(src_msg.author, "display_name") else f"User {user_id}" if user_id else "Member"
    guild_id = guild.id if guild else 0

    s_id = storage.submit_feature_suggestion(
        guild_id=guild_id,
        user_id=user_id,
        author_name=author_name,
        suggestion=suggestion,
        category=category
    )
    return (
        f"💡 **FEATURE SUGGESTION RECORDED (ID: #{s_id})**\n"
        f"• **Idea:** *\"{suggestion.strip()}\"*\n"
        f"• **Category:** {category.capitalize()}\n"
        f"• **Author:** {author_name}\n"
        f"• **Status:** Added to Product Roadmap Backlog (1 Vote). Other members can upvote this feature!"
    )


async def list_feature_suggestions(limit: int = 5) -> str:
    """
    List top voted community feature suggestions and product feedback.

    Args:
        limit: Number of suggestions to return (default 5).
    """
    import storage
    guild = current_guild.get()
    guild_id = guild.id if guild else None
    suggestions = storage.get_feature_suggestions(guild_id=guild_id, limit=limit)

    if not suggestions:
        return "💡 No feature suggestions logged yet! Use `@Smart bot suggest feature [your idea]` to submit one."

    lines = ["💡 **TOP COMMUNITY FEATURE REQUESTS:**"]
    for s in suggestions:
        lines.append(f"• **[#{s['id']}] {s['suggestion']}** — 🔥 {s['votes']} votes (by {s['author_name']} in {s['category']})")
    return "\n".join(lines)





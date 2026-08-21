import re
import datetime
import contextvars
from typing import Optional, Union
import discord

import config

# Context variable to hold the active guild context for tool execution
current_guild: contextvars.ContextVar[Optional[discord.Guild]] = contextvars.ContextVar("current_guild", default=None)


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
            try:
                user = await guild.client.fetch_user(user_id) if hasattr(guild, 'client') else discord.Object(id=user_id)
                delete_seconds = max(0, min(7, int(delete_message_days))) * 86400
                await guild.ban(user, reason=reason, delete_message_seconds=delete_seconds)
                return await _notify_and_return(f"Successfully banned user ID {user_id}. Reason: {reason}")
            except Exception as e:
                return f"Error banning user ID {user_id}: {str(e)}"
        return f"Error: User '{username_or_id}' not found in this server."

    try:
        delete_seconds = max(0, min(7, int(delete_message_days))) * 86400
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

    try:
        purge_limit = max(1, min(100, int(limit)))
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

import re
import datetime
import contextvars
from typing import Optional, Union
import discord

# Context variable to hold the active guild context for tool execution
current_guild: contextvars.ContextVar[Optional[discord.Guild]] = contextvars.ContextVar("current_guild", default=None)


def find_channel(guild: discord.Guild, query: str) -> Optional[Union[discord.TextChannel, discord.VoiceChannel]]:
    """
    Find a text or voice channel in a guild using fuzzy lookup order:
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


async def create_voice_channel(channel_name: str, user_limit: int = 0) -> str:
    """
    Creates a new voice channel in the Discord server with an optional user limit.

    Args:
        channel_name: The name of the voice channel to create.
        user_limit: Optional maximum number of users allowed in the voice channel (0 for no limit).

    Returns:
        A string describing the result of the operation.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    try:
        user_limit_val = max(0, min(99, int(user_limit)))
        new_channel = await guild.create_voice_channel(name=channel_name, user_limit=user_limit_val)
        limit_str = f" with a limit of {user_limit_val} users" if user_limit_val > 0 else " with no user limit"
        return f"Successfully created voice channel '{new_channel.name}' (ID: {new_channel.id}){limit_str}."
    except discord.Forbidden:
        return "Error: Bot lacks permission ('Manage Channels') to create voice channels."
    except discord.HTTPException as e:
        return f"Error creating voice channel: {e.text if hasattr(e, 'text') else str(e)}"
    except Exception as e:
        return f"Error creating voice channel: {str(e)}"


async def set_channel_read_only(channel_name: str, read_only: bool) -> str:
    """
    Toggles send-message permissions for the @everyone role on a specified text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        read_only: True to make channel read-only (disable sending messages for @everyone), False to unlock.

    Returns:
        A string describing the result of the operation.
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
        return f"Successfully set channel '{channel.name}' to {status}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Roles' / 'Manage Channels') to modify permissions for #{channel.name}."
    except discord.HTTPException as e:
        return f"Error setting channel read-only state: {e.text if hasattr(e, 'text') else str(e)}"
    except Exception as e:
        return f"Error setting channel read-only state: {str(e)}"


async def timeout_user(username_or_id: str, duration_minutes: int, reason: str = "No reason provided") -> str:
    """
    Applies a temporary timeout (mute) to a server member.

    Args:
        username_or_id: The username, display name, ID, or mention of the user to timeout.
        duration_minutes: Duration of timeout in minutes.
        reason: Reason for applying the timeout.

    Returns:
        A string describing the result of the operation.
    """
    guild = current_guild.get()
    if not guild:
        return "Error: Guild context is missing."

    member = find_member(guild, username_or_id)
    if not member:
        return f"Error: User '{username_or_id}' not found in this server."

    try:
        minutes = max(1, int(duration_minutes))
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        return f"Successfully timed out {member.mention} ({member.name}) for {minutes} minute(s). Reason: {reason}"
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Moderate Members') or hierarchy to timeout {member.name}."
    except discord.HTTPException as e:
        return f"Error timing out user: {e.text if hasattr(e, 'text') else str(e)}"
    except Exception as e:
        return f"Error timing out user: {str(e)}"


async def purge_messages(channel_name: str, limit: int = 10) -> str:
    """
    Deletes the last N messages in a specified text channel.

    Args:
        channel_name: The name, ID, or mention of the text channel.
        limit: The number of messages to purge (default 10, max 100).

    Returns:
        A string describing the result of the operation.
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
        return f"Successfully purged {len(deleted)} message(s) from channel #{channel.name}."
    except discord.Forbidden:
        return f"Error: Bot lacks permission ('Manage Messages') to purge messages in #{channel.name}."
    except discord.HTTPException as e:
        return f"Error purging messages: {e.text if hasattr(e, 'text') else str(e)}"
    except Exception as e:
        return f"Error purging messages: {str(e)}"

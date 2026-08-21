import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
import discord

import tools


@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)

    # Setup mock default role
    default_role = MagicMock()
    guild.default_role = default_role

    # Setup mock channels
    text_ch1 = MagicMock(spec=discord.TextChannel)
    text_ch1.id = 1001
    text_ch1.name = "general"
    text_ch1.overwrites_for.return_value = MagicMock()
    text_ch1.set_permissions = AsyncMock()
    text_ch1.purge = AsyncMock(return_value=[MagicMock(), MagicMock()])

    voice_ch1 = MagicMock(spec=discord.VoiceChannel)
    voice_ch1.id = 1002
    voice_ch1.name = "Lounge"

    guild.channels = [text_ch1, voice_ch1]

    def get_channel(ch_id):
        for c in guild.channels:
            if c.id == ch_id:
                return c
        return None

    guild.get_channel.side_effect = get_channel
    guild.create_voice_channel = AsyncMock()

    # Setup mock members
    member1 = MagicMock(spec=discord.Member)
    member1.id = 2001
    member1.name = "alice_dev"
    member1.display_name = "Alice"
    member1.global_name = "Alice Global"
    member1.mention = "<@2001>"
    member1.timeout = AsyncMock()

    member2 = MagicMock(spec=discord.Member)
    member2.id = 2002
    member2.name = "bob_tester"
    member2.display_name = "Bob"
    member2.global_name = "Bob Global"
    member2.mention = "<@2002>"
    member2.timeout = AsyncMock()

    guild.members = [member1, member2]

    def get_member(m_id):
        for m in guild.members:
            if m.id == m_id:
                return m
        return None

    guild.get_member.side_effect = get_member

    token = tools.current_guild.set(guild)
    yield guild
    tools.current_guild.reset(token)


def test_find_channel_by_id(mock_guild):
    channel = tools.find_channel(mock_guild, "1001")
    assert channel is not None
    assert channel.id == 1001
    assert channel.name == "general"


def test_find_channel_by_mention(mock_guild):
    channel = tools.find_channel(mock_guild, "<#1001>")
    assert channel is not None
    assert channel.id == 1001


def test_find_channel_by_exact_name(mock_guild):
    channel = tools.find_channel(mock_guild, "Lounge")
    assert channel is not None
    assert channel.id == 1002


def test_find_channel_by_fuzzy_name(mock_guild):
    channel = tools.find_channel(mock_guild, "gen")
    assert channel is not None
    assert channel.id == 1001


def test_find_member_by_id(mock_guild):
    member = tools.find_member(mock_guild, "2001")
    assert member is not None
    assert member.id == 2001


def test_find_member_by_mention(mock_guild):
    member = tools.find_member(mock_guild, "<@!2001>")
    assert member is not None
    assert member.id == 2001


def test_find_member_by_exact_name(mock_guild):
    member = tools.find_member(mock_guild, "Alice")
    assert member is not None
    assert member.id == 2001


def test_find_member_by_fuzzy_name(mock_guild):
    member = tools.find_member(mock_guild, "bob")
    assert member is not None
    assert member.id == 2002


@pytest.mark.asyncio
async def test_create_voice_channel_success(mock_guild):
    created_ch = MagicMock()
    created_ch.name = "Gaming Room"
    created_ch.id = 1003
    mock_guild.create_voice_channel.return_value = created_ch

    res = await tools.create_voice_channel("Gaming Room", user_limit=5)
    assert "Successfully created voice channel 'Gaming Room'" in res
    mock_guild.create_voice_channel.assert_called_once_with(name="Gaming Room", user_limit=5)


@pytest.mark.asyncio
async def test_create_voice_channel_forbidden(mock_guild):
    mock_guild.create_voice_channel.side_effect = discord.Forbidden(MagicMock(), "Forbidden")
    res = await tools.create_voice_channel("Secret Room")
    assert "lacks permission" in res


@pytest.mark.asyncio
async def test_set_channel_read_only(mock_guild):
    res = await tools.set_channel_read_only("general", read_only=True)
    assert "Successfully set channel 'general' to read-only" in res

    res_unlock = await tools.set_channel_read_only("general", read_only=False)
    assert "Successfully set channel 'general' to unlocked" in res_unlock


@pytest.mark.asyncio
async def test_timeout_user(mock_guild):
    res = await tools.timeout_user("alice_dev", duration_minutes=10, reason="Spamming")
    assert "Successfully timed out" in res
    assert "alice_dev" in res or "Alice" in res or "<@2001>" in res


@pytest.mark.asyncio
async def test_purge_messages(mock_guild):
    res = await tools.purge_messages("general", limit=5)
    assert "Successfully purged 2 message(s)" in res

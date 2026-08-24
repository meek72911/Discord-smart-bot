import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import discord

import tools
import config


@pytest.fixture(autouse=True)
def _disable_confirm_gates():
    """Unit tests call tools directly without a chat surface — disable gates."""
    with patch.object(config, "CONFIRM_DESTRUCTIVE", False):
        yield


@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)

    default_role = MagicMock()
    default_role.name = "@everyone"
    guild.default_role = default_role

    mock_log_channel = MagicMock(spec=discord.TextChannel)
    mock_log_channel.send = AsyncMock()

    text_ch1 = MagicMock(spec=discord.TextChannel)
    text_ch1.id = 1001
    text_ch1.name = "general"
    text_ch1.type = discord.ChannelType.text
    text_ch1.overwrites_for.return_value = MagicMock()
    text_ch1.set_permissions = AsyncMock()
    text_ch1.purge = AsyncMock(return_value=[MagicMock(), MagicMock()])
    text_ch1.delete = AsyncMock()

    mock_msg = MagicMock()
    mock_msg.id = 5555
    mock_msg.pin = AsyncMock()
    mock_msg.unpin = AsyncMock()
    text_ch1.fetch_message = AsyncMock(return_value=mock_msg)

    voice_ch1 = MagicMock(spec=discord.VoiceChannel)
    voice_ch1.id = 1002
    voice_ch1.name = "Lounge"
    voice_ch1.type = discord.ChannelType.voice
    voice_ch1.delete = AsyncMock()

    category1 = MagicMock(spec=discord.CategoryChannel)
    category1.id = 1000
    category1.name = "Community"

    guild.channels = [text_ch1, voice_ch1, mock_log_channel]
    guild.categories = [category1]

    def get_channel(ch_id):
        if ch_id == 1000:
            return category1
        if ch_id == 9999:
            return mock_log_channel
        for c in guild.channels:
            if c.id == ch_id:
                return c
        return None

    guild.get_channel.side_effect = get_channel
    guild.create_text_channel = AsyncMock()
    guild.create_voice_channel = AsyncMock()
    guild.create_stage_channel = AsyncMock()
    guild.create_category = AsyncMock()

    # Setup mock members
    member1 = MagicMock(spec=discord.Member)
    member1.id = 2001
    member1.name = "alice_dev"
    member1.display_name = "Alice"
    member1.global_name = "Alice Global"
    member1.mention = "<@2001>"
    member1.timeout = AsyncMock()
    member1.ban = AsyncMock()
    member1.kick = AsyncMock()
    member1.edit = AsyncMock()
    member1.move_to = AsyncMock()
    member1.add_roles = AsyncMock()
    member1.remove_roles = AsyncMock()
    member1.voice = MagicMock(channel=voice_ch1)

    member2 = MagicMock(spec=discord.Member)
    member2.id = 2002
    member2.name = "bob_tester"
    member2.display_name = "Bob"
    member2.global_name = "Bob Global"
    member2.mention = "<@2002>"
    member2.timeout = AsyncMock()
    member2.voice = None

    guild.members = [member1, member2]

    def get_member(m_id):
        for m in guild.members:
            if m.id == m_id:
                return m
        return None

    guild.get_member.side_effect = get_member
    guild.ban = AsyncMock()
    guild.unban = AsyncMock()

    # Roles
    role1 = MagicMock(spec=discord.Role)
    role1.id = 3001
    role1.name = "Moderator"
    # Safe permissions: nothing dangerous enabled
    safe_perms = MagicMock(spec=discord.Permissions)
    for perm_name in tools._DANGEROUS_PERMISSIONS:
        setattr(safe_perms, perm_name, False)
    role1.permissions = safe_perms
    role1.is_default.return_value = False
    role1.position = 5  # below the bot's top role (10)
    guild.me = MagicMock(spec=discord.Member)
    guild.me.top_role.position = 10
    guild.roles = [role1]
    guild.get_role = lambda r_id: role1 if r_id == 3001 else None
    guild.create_role = AsyncMock(return_value=role1)

    token = tools.current_guild.set(guild)
    yield guild
    tools.current_guild.reset(token)


# --- Channel Tests ---

def test_find_channel_and_member(mock_guild):
    assert tools.find_channel(mock_guild, "1001").id == 1001
    assert tools.find_member(mock_guild, "2001").id == 2001
    assert tools.find_role(mock_guild, "3001").id == 3001


@pytest.mark.asyncio
async def test_create_text_channel(mock_guild):
    mock_ch = MagicMock()
    mock_ch.name = "announcements"
    mock_ch.id = 1004
    mock_guild.create_text_channel.return_value = mock_ch

    res = await tools.create_text_channel("announcements", topic="Server news")
    assert "Successfully created text channel #announcements" in res


@pytest.mark.asyncio
async def test_create_voice_channel(mock_guild):
    mock_ch = MagicMock()
    mock_ch.name = "Gaming Room"
    mock_ch.id = 1003
    mock_guild.create_voice_channel.return_value = mock_ch

    res = await tools.create_voice_channel("Gaming Room", user_limit=5)
    assert "Successfully created voice channel 'Gaming Room'" in res


@pytest.mark.asyncio
async def test_delete_channel(mock_guild):
    res = await tools.delete_channel("general")
    assert "Successfully deleted" in res


@pytest.mark.asyncio
async def test_hide_channel(mock_guild):
    res = await tools.hide_channel("general", hide=True)
    assert "hidden from @everyone" in res


# --- Member Tests ---

@pytest.mark.asyncio
async def test_ban_user(mock_guild):
    res = await tools.ban_user("alice_dev", reason="Rules violation")
    assert "Successfully banned" in res


@pytest.mark.asyncio
async def test_kick_user(mock_guild):
    res = await tools.kick_user("alice_dev", reason="Spam")
    assert "Successfully kicked" in res


@pytest.mark.asyncio
async def test_timeout_user_and_clamping(mock_guild):
    res = await tools.timeout_user("alice_dev", duration_minutes=100000)
    assert "Successfully timed out" in res
    assert "40320 minute(s)" in res


@pytest.mark.asyncio
async def test_audit_log_channel_notification(mock_guild):
    with patch.object(config, "MOD_LOG_CHANNEL_ID", 9999):
        res = await tools.kick_user("alice_dev", reason="Test audit log")
        assert "Successfully kicked" in res
        log_channel = mock_guild.get_channel(9999)
        log_channel.send.assert_called_once()
        call_arg = log_channel.send.call_args[0][0]
        assert "Mod Audit Log" in call_arg


@pytest.mark.asyncio
async def test_change_nickname(mock_guild):
    res = await tools.change_nickname("alice_dev", nickname="AliceTheAdmin")
    assert "changed to 'AliceTheAdmin'" in res


@pytest.mark.asyncio
async def test_disconnect_and_move_voice(mock_guild):
    res = await tools.disconnect_member_voice("alice_dev")
    assert "Successfully disconnected" in res


# --- Role & Message Tests ---

@pytest.mark.asyncio
async def test_create_assign_remove_role(mock_guild):
    res_create = await tools.create_role("VIP", hex_color="#FF0000")
    assert "Successfully created role" in res_create

    res_assign = await tools.assign_role("alice_dev", "Moderator")
    assert "Successfully assigned role 'Moderator'" in res_assign

    res_remove = await tools.remove_role("alice_dev", "Moderator")
    assert "Successfully removed role 'Moderator'" in res_remove


@pytest.mark.asyncio
async def test_dangerous_role_guard_blocks_assignment(mock_guild):
    # Give the mock role dangerous permissions; guard must refuse assignment
    admin_perms = MagicMock(spec=discord.Permissions)
    for perm_name in tools._DANGEROUS_PERMISSIONS:
        setattr(admin_perms, perm_name, False)
    admin_perms.administrator = True

    role1 = mock_guild.roles[0]
    original_perms = role1.permissions
    role1.permissions = admin_perms
    try:
        res_assign = await tools.assign_role("alice_dev", "Moderator")
        assert "admin-level powers" in res_assign
        member = tools.find_member(mock_guild, "alice_dev")
        member.add_roles.assert_not_called()
    finally:
        role1.permissions = original_perms


@pytest.mark.asyncio
async def test_purge_and_pin_message(mock_guild):
    res_purge = await tools.purge_messages("general", limit=5)
    assert "Successfully purged 2 message(s)" in res_purge

    res_pin = await tools.pin_message("general", "5555")
    assert "Successfully pinned message ID 5555" in res_pin

    res_unpin = await tools.unpin_message("general", "5555")
    assert "Successfully unpinned message ID 5555" in res_unpin


@pytest.mark.asyncio
async def test_ban_requires_human_confirmation(mock_guild):
    """Gate ON + no chat surface -> ban must NOT execute (fail-closed)."""
    member = mock_guild.get_member(2001)
    with patch.object(config, "CONFIRM_DESTRUCTIVE", True):
        res = await tools.ban_user("alice_dev", reason="gate test")
        assert "Nothing was executed" in res or "confirmation" in res.lower()
        member.ban.assert_not_called()


@pytest.mark.asyncio
async def test_ban_executes_after_confirmation(mock_guild):
    """Gate ON + confirmed via ConfirmView -> ban executes."""
    import views.confirm as vc
    from unittest.mock import patch as _p

    member = mock_guild.get_member(2001)

    class _FakeHost:
        async def edit(self, **kw):
            pass

    class _FakeMessage:
        async def reply(self, **kw):
            return _FakeHost()

    fake_msg = _FakeMessage()
    token_req = tools.current_requester_id.set(1463495220124454955)
    token_src = tools.current_source_message.set(fake_msg)
    try:
        with patch.object(config, "CONFIRM_DESTRUCTIVE", True):
            with _p.object(vc.ConfirmView, "wait", AsyncMock(return_value=None)):
                # Simulate user pressing Confirm before wait() resolves
                orig_wait = vc.ConfirmView.wait

                async def confirmed_wait(self_view):
                    self_view.confirmed = True
                    return None

                with _p.object(vc.ConfirmView, "wait", confirmed_wait):
                    res = await tools.ban_user("alice_dev", reason="confirmed test")
        assert "Successfully banned" in res
        member.ban.assert_called_once()
    finally:
        tools.current_requester_id.reset(token_req)
        tools.current_source_message.reset(token_src)


@pytest.mark.asyncio
async def test_suggest_feature_and_list(mock_guild):
    token_g = tools.current_guild.set(mock_guild)
    token_u = tools.current_user_id.set(9999)
    try:
        # Submit suggestion
        res = await tools.suggest_feature("Add Discord event Google Calendar sync", category="integrations")
        assert "FEATURE SUGGESTION RECORDED" in res
        assert "Calendar sync" in res

        # List suggestions
        list_res = await tools.list_feature_suggestions(limit=5)
        assert "TOP COMMUNITY FEATURE REQUESTS" in list_res
        assert "Calendar sync" in list_res
    finally:
        tools.current_guild.reset(token_g)
        tools.current_user_id.reset(token_u)

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord

import bot


def test_clean_message_content():
    bot_user = MagicMock(spec=discord.User)
    bot_user.id = 123456789

    content = "<@123456789> create voice channel test"
    cleaned = bot.clean_message_content(content, bot_user)
    assert cleaned == "create voice channel test"

    content_nick = "<@!123456789> hello bot"
    cleaned_nick = bot.clean_message_content(content_nick, bot_user)
    assert cleaned_nick == "hello bot"


def test_cooldown_tracking():
    bot.USER_COOLDOWNS.clear()

    # First time: not on cooldown
    on_cd, _ = bot.is_user_on_cooldown(111, cooldown_seconds=3.0)
    assert on_cd is False

    # Update cooldown
    bot.update_user_cooldown(111)

    # Immediately after: on cooldown
    on_cd2, remaining = bot.is_user_on_cooldown(111, cooldown_seconds=3.0)
    assert on_cd2 is True
    assert remaining > 0


@pytest.mark.asyncio
async def test_on_message_ignores_bot():
    message = MagicMock(spec=discord.Message)
    message.author.bot = True

    with patch("ai_service.process_chat_message", new_callable=AsyncMock) as mock_process:
        await bot.on_message(message)
        mock_process.assert_not_called()

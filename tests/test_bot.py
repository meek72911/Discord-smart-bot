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


@pytest.mark.asyncio
async def test_on_message_ignores_bot():
    message = MagicMock(spec=discord.Message)
    message.author.bot = True

    with patch("ai_service.process_chat_message", new_callable=AsyncMock) as mock_process:
        await bot.on_message(message)
        mock_process.assert_not_called()

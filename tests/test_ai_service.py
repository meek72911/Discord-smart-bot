import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

import ai_service
import storage


class _FakeChunk:
    def __init__(self, text=None, function_calls=None):
        self.text = text
        self.function_calls = function_calls


class _StreamAwaitable:
    """Mimics google-genai AwaitableGenerator: awaited to get an async generator."""

    def __init__(self, chunks):
        self.chunks = chunks

    def __await__(self):
        async def _coro():
            async def _gen():
                for c in self.chunks:
                    yield c
            return _gen()
        return _coro().__await__()


class _FakeChat:
    def __init__(self, turns):
        self.turns = [list(t) for t in turns]
        self.sent = []

    def get_history(self):
        return []  # empty history => compaction never triggers

    def send_message_stream(self, message):
        self.sent.append(message)
        return _StreamAwaitable(self.turns.pop(0) if self.turns else [])


def _patch_storage():
    return patch.multiple(
        storage,
        load_channel_history=MagicMock(return_value=[]),
        save_channel_history=MagicMock(),
        delete_channel_memory=MagicMock(),
    )


@pytest.mark.asyncio
async def test_process_chat_message_unauthorized():
    reply = "Hello! How can I help you today?"
    fake_chat = _FakeChat([[_FakeChunk(text=reply)]])
    mock_client = MagicMock()
    mock_client.aio.chats.create.return_value = fake_chat

    with patch.object(ai_service, "CHAT_PROVIDER", "gemini"), patch("ai_service.get_client", return_value=mock_client), _patch_storage():
        res = await ai_service.process_chat_message(
            guild=None,
            channel_id=999,
            author_name="StandardUser",
            message_content="Hi bot!",
            is_authorized=False,
        )

        assert res == reply
        kwargs = mock_client.aio.chats.create.call_args.kwargs
        assert kwargs["model"] == ai_service.CHAT_MODEL
        assert kwargs["config"].tools == ai_service.ALL_TOOLS
        assert fake_chat.sent, "message should have been sent to the session"


@pytest.mark.asyncio
async def test_process_chat_message_authorized_with_tool_call():
    fc = MagicMock()
    fc.name = "create_voice_channel"
    fc.args = {"channel_name": "Game Lounge", "user_limit": 4}

    final_reply = "I created the voice channel 'Game Lounge' for you!"
    fake_chat = _FakeChat([
        [_FakeChunk(function_calls=[fc])],
        [_FakeChunk(text=final_reply)],
    ])
    mock_client = MagicMock()
    mock_client.aio.chats.create.return_value = fake_chat
    mock_tool = AsyncMock(return_value="Successfully created voice channel 'Game Lounge'")

    guild = MagicMock(spec=discord.Guild)
    guild.id = 1234

    with patch.object(ai_service, "CHAT_PROVIDER", "gemini"), patch("ai_service.get_client", return_value=mock_client), _patch_storage():
        with patch.dict(ai_service.TOOL_MAP, {"create_voice_channel": mock_tool}):
            res = await ai_service.process_chat_message(
                guild=guild,
                channel_id=888,
                author_name="AdminUser",
                message_content="Create a voice channel named Game Lounge for 4 people",
                is_authorized=True,
            )

            assert res == final_reply
            mock_tool.assert_called_once()


@pytest.mark.asyncio
async def test_unauthorized_tool_execution_is_blocked():
    fc = MagicMock()
    fc.name = "ban_user"
    fc.args = {"username_or_id": "someone"}

    fake_chat = _FakeChat([
        [_FakeChunk(function_calls=[fc])],
        [_FakeChunk(text="Sorry, only trusted moderators can do that.")],
    ])
    mock_client = MagicMock()
    mock_client.aio.chats.create.return_value = fake_chat
    mock_tool = AsyncMock(return_value="Successfully banned someone")

    guild = MagicMock(spec=discord.Guild)
    guild.id = 1234

    with patch.object(ai_service, "CHAT_PROVIDER", "gemini"), patch("ai_service.get_client", return_value=mock_client), _patch_storage():
        with patch.dict(ai_service.TOOL_MAP, {"ban_user": mock_tool}):
            res = await ai_service.process_chat_message(
                guild=guild,
                channel_id=777,
                author_name="RandomUser",
                message_content="ban someone",
                is_authorized=False,
            )

            assert res == "Sorry, only trusted moderators can do that."
            mock_tool.assert_not_called()

            # The function response fed back to the model must be the auth error
            second_call = fake_chat.sent[1]
            fr_part = second_call[0] if isinstance(second_call, list) else second_call.parts[0]
            assert "Authorization required" in str(fr_part.function_response.response)

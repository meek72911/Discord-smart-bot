import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

import ai_service


@pytest.mark.asyncio
async def test_process_chat_message_unauthorized():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = [
        MagicMock(content=MagicMock())
    ]
    mock_response.function_calls = None
    mock_response.text = "Hello! How can I help you today?"
    mock_client.models.generate_content.return_value = mock_response

    with patch("ai_service.get_client", return_value=mock_client):
        ai_service.CHANNEL_HISTORIES.clear()
        res = await ai_service.process_chat_message(
            guild=None,
            channel_id=999,
            author_name="StandardUser",
            message_content="Hi bot!",
            is_authorized=False,
        )

        assert res == "Hello! How can I help you today?"

        # Verify call config had tools=None
        call_args = mock_client.models.generate_content.call_args
        gen_config = call_args.kwargs.get("config")
        assert gen_config is not None
        assert gen_config.tools is None


@pytest.mark.asyncio
async def test_process_chat_message_authorized_with_tool_call():
    mock_client = MagicMock()

    # First turn returns a function call
    func_call = MagicMock()
    func_call.name = "create_voice_channel"
    func_call.args = {"channel_name": "Game Lounge", "user_limit": 4}

    response1 = MagicMock()
    response1.candidates = [MagicMock(content=MagicMock())]
    response1.function_calls = [func_call]

    # Second turn returns final natural response
    response2 = MagicMock()
    response2.candidates = [MagicMock(content=MagicMock())]
    response2.function_calls = None
    response2.text = "I created the voice channel 'Game Lounge' for you!"

    mock_client.models.generate_content.side_effect = [response1, response2]

    mock_tool = AsyncMock(return_value="Successfully created voice channel 'Game Lounge'")

    with patch("ai_service.get_client", return_value=mock_client):
        with patch.dict(ai_service.TOOL_MAP, {"create_voice_channel": mock_tool}):
            ai_service.CHANNEL_HISTORIES.clear()
            res = await ai_service.process_chat_message(
                guild=MagicMock(spec=discord.Guild),
                channel_id=888,
                author_name="AdminUser",
                message_content="Create a voice channel named Game Lounge for 4 people",
                is_authorized=True,
            )

            assert res == "I created the voice channel 'Game Lounge' for you!"
            mock_tool.assert_called_once()

            # Verify call config had tools set
            call_args = mock_client.models.generate_content.call_args_list[0]
            gen_config = call_args.kwargs.get("config")
            assert gen_config is not None
            assert gen_config.tools == ai_service.MODERATION_TOOLS

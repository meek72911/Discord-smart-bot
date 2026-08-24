"""
Unit tests for Smart Bot Voice Service & Voice Tools
"""

import pytest
import os
import voice_service
import tools
from unittest.mock import AsyncMock, MagicMock, patch
import discord

def test_persona_voices_configuration():
    assert "default" in voice_service.FEMALE_PERSONA_VOICES
    assert "savage" in voice_service.FEMALE_PERSONA_VOICES
    assert "wholesome" in voice_service.FEMALE_PERSONA_VOICES
    assert "professor" in voice_service.FEMALE_PERSONA_VOICES
    assert "gamer" in voice_service.FEMALE_PERSONA_VOICES
    for p, cfg in voice_service.FEMALE_PERSONA_VOICES.items():
        assert "voice" in cfg
        assert "rate" in cfg
        assert "pitch" in cfg
        assert "Neural" in cfg["voice"]

def test_ensure_opus_loaded():
    voice_service.ensure_opus_loaded()
    assert discord.opus.is_loaded()

@pytest.mark.asyncio
async def test_leave_voice_channel_not_connected():
    mock_guild = MagicMock(spec=discord.Guild)
    mock_guild.voice_client = None
    tools.current_guild.set(mock_guild)
    
    res = await tools.leave_voice_channel()
    assert "not currently connected" in res

@pytest.mark.asyncio
async def test_speak_in_voice_not_in_channel():
    mock_guild = MagicMock(spec=discord.Guild)
    mock_guild.voice_client = None
    mock_guild.id = 1234
    tools.current_guild.set(mock_guild)
    
    res = await tools.speak_in_voice("Hello world")
    assert "not in a voice channel" in res

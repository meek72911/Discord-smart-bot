"""
Smart Bot Voice Service
Provides studio-grade female neural TTS playback in Discord Voice channels via Edge-TTS.
"""

import os
import asyncio
import logging
from typing import Optional, Dict
import discord
import discord.opus
import edge_tts

logger = logging.getLogger("voice_service")

# Auto-load Discord Opus library for Windows voice connections
def ensure_opus_loaded():
    if not discord.opus.is_loaded():
        try:
            discord.opus._load_default()
            logger.info("Discord Opus encoder loaded successfully")
        except Exception as e:
            logger.warning(f"Opus load warning: {e}")

ensure_opus_loaded()

# Map personas to realistic female neural voices with natural rate & pitch tuning
FEMALE_PERSONA_VOICES: Dict[str, Dict[str, str]] = {
    "default": {
        "voice": "en-US-AvaMultilingualNeural",  # Ultra-natural conversational American girl
        "rate": "+2%",
        "pitch": "+0Hz"
    },
    "savage": {
        "voice": "en-GB-SoniaNeural",           # Sharp, witty British female roastmaster
        "rate": "+15%",
        "pitch": "+2Hz"
    },
    "wholesome": {
        "voice": "en-US-EmmaMultilingualNeural", # Sweet, cheerful, warm girl voice
        "rate": "+0%",
        "pitch": "+1Hz"
    },
    "professor": {
        "voice": "en-US-AriaNeural",            # Articulate, clear precision
        "rate": "-6%",
        "pitch": "-2Hz"
    },
    "gamer": {
        "voice": "en-US-AnaNeural",             # High-energy, gaming hype voice
        "rate": "+18%",
        "pitch": "+4Hz"
    }
}

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "voice")
os.makedirs(CACHE_DIR, exist_ok=True)

# Guild Voice Playback Queues
_VOICE_QUEUES: Dict[int, asyncio.Queue] = {}
_QUEUE_WORKERS: Dict[int, asyncio.Task] = {}

async def synthesize_speech(text: str, persona: str = "default", output_filename: Optional[str] = None) -> str:
    """
    Synthesize text into a high-quality, human-sounding female neural speech MP3.
    """
    config = FEMALE_PERSONA_VOICES.get(persona.lower(), FEMALE_PERSONA_VOICES["default"])
    if not output_filename:
        safe_hash = abs(hash(f"{text}_{persona}_{config['voice']}")) % 10000000
        output_path = os.path.join(CACHE_DIR, f"speech_{safe_hash}.mp3")
    else:
        output_path = os.path.join(CACHE_DIR, output_filename)

    # If cached file exists and has content, reuse it for instant 0ms playback
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
        return output_path

    comm = edge_tts.Communicate(
        text=text,
        voice=config["voice"],
        rate=config["rate"],
        pitch=config["pitch"]
    )
    await comm.save(output_path)
    return output_path

async def _voice_queue_worker(guild_id: int, voice_client: discord.VoiceClient):
    """
    Background worker that plays queued voice clips sequentially with studio mastering.
    """
    q = _VOICE_QUEUES[guild_id]
    try:
        while True:
            audio_path = await q.get()
            try:
                if voice_client and voice_client.is_connected():
                    # Studio mastering: loudnorm (-16 LUFS) + volume boost for broadcast mic clarity
                    ffmpeg_options = {
                        'options': '-filter:a "loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.15"'
                    }
                    try:
                        audio_source = discord.FFmpegPCMAudio(audio_path, **ffmpeg_options)
                    except Exception:
                        audio_source = discord.FFmpegPCMAudio(audio_path)

                    done = asyncio.Event()

                    def after_playing(error):
                        if error:
                            logger.warning(f"Voice playback warning: {error}")
                        done.set()

                    voice_client.play(audio_source, after=after_playing)
                    await done.wait()
                    await asyncio.sleep(0.3)  # natural human pause between sentences
            except Exception as e:
                logger.error(f"Error in voice playback queue: {e}")
            finally:
                q.task_done()
    except asyncio.CancelledError:
        pass
    finally:
        _QUEUE_WORKERS.pop(guild_id, None)

async def play_speech_in_voice(voice_client: discord.VoiceClient, text: str, persona: str = "default") -> bool:
    """
    Plays synthesized neural speech directly in an active Discord VoiceClient via queue.
    """
    if not voice_client or not voice_client.is_connected():
        logger.warning("Voice client is not connected to a voice channel.")
        return False

    try:
        audio_path = await synthesize_speech(text, persona=persona)
        guild_id = voice_client.guild.id

        if guild_id not in _VOICE_QUEUES:
            _VOICE_QUEUES[guild_id] = asyncio.Queue()

        if guild_id not in _QUEUE_WORKERS or _QUEUE_WORKERS[guild_id].done():
            _QUEUE_WORKERS[guild_id] = asyncio.create_task(_voice_queue_worker(guild_id, voice_client))

        await _VOICE_QUEUES[guild_id].put(audio_path)
        return True
    except Exception as e:
        logger.error(f"Failed to queue audio in voice channel: {e}")
        return False



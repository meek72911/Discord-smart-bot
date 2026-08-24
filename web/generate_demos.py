import asyncio
import os
import edge_tts

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

FEMALE_DEMOS = {
    "default": {
        "text": "Hey everyone! I'm Smart Bot, your autonomous Discord operating system. I can run 63 server tools, manage tickets, and chat with your community naturally.",
        "voice": "en-US-JennyNeural",
        "rate": "+0%",
        "pitch": "+0Hz"
    },
    "savage": {
        "text": "Oh, look who finally decided to show up. Try not to break the server rules today, or I'll put you on timeout faster than you can blame lag.",
        "voice": "en-GB-SoniaNeural",
        "rate": "+15%",
        "pitch": "+2Hz"
    },
    "wholesome": {
        "text": "Welcome to the server! Remember to take breaks, stay hydrated, and have an amazing time with everyone here today.",
        "voice": "en-US-MichelleNeural",
        "rate": "+0%",
        "pitch": "+0Hz"
    },
    "professor": {
        "text": "Welcome to today's briefing. We will examine distributed architecture, asynchronous concurrency, and cryptographic security protocols.",
        "voice": "en-US-AriaNeural",
        "rate": "-8%",
        "pitch": "-2Hz"
    },
    "gamer": {
        "text": "Let's go chat! We are totally locked in. Drop your gamer tag and let's queue up for the next tournament match right now!",
        "voice": "en-US-AnaNeural",
        "rate": "+18%",
        "pitch": "+4Hz"
    }
}

async def generate_all():
    print("Generating female voice demo audio files with Edge-TTS...")
    for key, data in FEMALE_DEMOS.items():
        out_path = os.path.join(AUDIO_DIR, f"{key}.mp3")
        comm = edge_tts.Communicate(text=data["text"], voice=data["voice"], rate=data["rate"], pitch=data["pitch"])
        await comm.save(out_path)
        print(f"[OK] Generated: {key}.mp3 ({data['voice']})")
    print("\nAll female audio demos ready in web/audio/!")

if __name__ == "__main__":
    asyncio.run(generate_all())

import logging
import re
import sys
import time
from typing import Dict
import discord

import config
import ai_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("discord_bot")

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

# Per-user cooldown tracking (in seconds)
USER_COOLDOWNS: Dict[int, float] = {}
COOLDOWN_SECONDS = 3.0


def clean_message_content(content: str, bot_user: discord.User) -> str:
    """Removes bot mention tags from message content."""
    if not bot_user or not content:
        return content
    # Remove <@bot_id> or <@!bot_id>
    cleaned = re.sub(rf"<@!?{bot_user.id}>", "", content).strip()
    return cleaned


def is_user_on_cooldown(user_id: int, cooldown_seconds: float = COOLDOWN_SECONDS) -> tuple[bool, float]:
    """Checks if a user is on cooldown. Returns (is_on_cooldown, remaining_seconds)."""
    now = time.time()
    last_time = USER_COOLDOWNS.get(user_id, 0.0)
    elapsed = now - last_time
    if elapsed < cooldown_seconds:
        return True, round(cooldown_seconds - elapsed, 1)
    return False, 0.0


def update_user_cooldown(user_id: int):
    """Updates the last interaction timestamp for a user."""
    USER_COOLDOWNS[user_id] = time.time()


@client.event
async def on_ready():
    logger.info(f"Bot logged in as {client.user} (ID: {client.user.id})")
    logger.info(f"Owner ID: {config.OWNER_ID}")
    logger.info(f"Trusted User IDs: {config.TRUSTED_USER_IDS}")
    if config.MOD_LOG_CHANNEL_ID:
        logger.info(f"Mod Audit Log Channel ID: {config.MOD_LOG_CHANNEL_ID}")


@client.event
async def on_message(message: discord.Message):
    # Ignore messages sent by bots (including ourselves)
    if message.author.bot:
        return

    # Check if bot was mentioned
    bot_mentioned = client.user in message.mentions if client.user else False

    # Check if message is a reply to the bot
    is_reply_to_bot = False
    if message.reference and message.reference.resolved:
        resolved_msg = message.reference.resolved
        if isinstance(resolved_msg, discord.Message) and resolved_msg.author == client.user:
            is_reply_to_bot = True

    # Check if message is in Direct Messages
    is_dm = isinstance(message.channel, discord.DMChannel)

    # Bot should only respond if mentioned, replied to, or in DM
    if not (bot_mentioned or is_reply_to_bot or is_dm):
        return

    # Check per-user cooldown
    on_cooldown, remaining = is_user_on_cooldown(message.author.id)
    if on_cooldown:
        await message.reply(
            f"Whoa, slow down! Please wait {remaining:.1f}s before sending another message.",
            mention_author=False,
        )
        return

    # Update user cooldown
    update_user_cooldown(message.author.id)

    # Clean message content
    cleaned_content = clean_message_content(message.content, client.user)
    if not cleaned_content:
        cleaned_content = "Hello!"

    is_authorized = config.is_authorized_user(message.author.id)
    auth_status_str = "Authorized Moderator" if is_authorized else "Standard User"
    logger.info(f"Processing message from '{message.author}' ({message.author.id}) [{auth_status_str}] in channel '{message.channel}'")

    async with message.channel.typing():
        try:
            response_text = await ai_service.process_chat_message(
                guild=message.guild,
                channel_id=message.channel.id,
                author_name=message.author.display_name,
                message_content=cleaned_content,
                is_authorized=is_authorized,
            )
        except Exception as e:
            logger.error(f"Error processing AI chat response: {e}", exc_info=True)
            response_text = "Oops! I ran into an error while processing that request."

    # Handle Discord's 2000 character limit by splitting long messages
    if len(response_text) <= 2000:
        await message.reply(response_text, mention_author=False)
    else:
        # Chunk messages
        chunks = [response_text[i : i + 1900] for i in range(0, len(response_text), 1900)]
        for chunk in chunks:
            await message.channel.send(chunk)


def main():
    if not config.DISCORD_BOT_TOKEN:
        logger.error("Error: DISCORD_BOT_TOKEN is not set in environment variables.")
        sys.exit(1)

    client.run(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()

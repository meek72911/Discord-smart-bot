# AI-Powered Moderation & Companion Discord Bot

An intelligent, production-ready Discord bot built with Python (`discord.py`) and Google Gemini API (`google-genai` SDK) using model `gemini-2.5-flash`. It acts as a witty, grounded, chill companion for standard users while executing full server moderation tasks via Gemini Function Calling for authorized moderators.

---

## Features

- **Companion Persona**: Witty, grounded, and chill companion persona that chats naturally in Discord servers and direct messages.
- **Strict Execution Guard**: Moderation tool definitions are completely omitted from request payloads for standard users, ensuring Gemini can only execute moderation tasks for authorized user IDs (`OWNER_ID` or `TRUSTED_USER_IDS`).
- **Context Resolution**: Retains recent multi-turn conversation context (10-15 messages) per Discord channel so natural references ("mute him", "lock this channel", "clear these") resolve accurately.
- **Fuzzy Target Lookup**: Robust lookup for channels, categories, members, and roles supporting:
  1. Direct Snowflake ID
  2. Mention syntax (`<#123...>`, `<@!123...>`, `<@&123...>`)
  3. Exact name / display name match
  4. Case-insensitive partial name match
- **Comprehensive Moderation Tool Engine**:
  - **Channel Controls**: `create_text_channel`, `create_voice_channel`, `create_stage_channel`, `create_category`, `delete_channel`, `set_channel_read_only`, `hide_channel`
  - **Member Moderation**: `ban_user`, `unban_user`, `kick_user`, `timeout_user`, `remove_timeout`, `change_nickname`, `disconnect_member_voice`, `move_member_voice`
  - **Role Management**: `create_role`, `assign_role`, `remove_role`
  - **Message Management**: `purge_messages`, `pin_message`, `unpin_message`
- **Multi-Tool Execution Loop**: Gemini can return and execute multiple tool calls in a single turn for complex multi-step instructions before delivering the final natural response.

---

## Project Structure

```
├── bot.py                # Main entry point and Discord client event loop
├── config.py             # Environment variable loader and auth check
├── ai_service.py         # Gemini API setup, persona prompt, and tool execution loop
├── tools.py              # Discord API actions exposed as Gemini functions
├── tests/                # Automated pytest unit test suite
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
└── README.md             # Documentation
```

---

## Discord Bot Configuration

### 1. Enable Privileged Gateway Intents
In the [Discord Developer Portal](https://discord.com/developers/applications):
1. Navigate to **Bot** section.
2. Enable **Message Content Intent**.
3. Enable **Server Members Intent**.

### 2. Bot OAuth2 Permissions Required
When inviting the bot to your server, grant the following permissions:
- `Manage Channels`
- `Manage Roles`
- `Moderate Members`
- `Ban Members`
- `Kick Members`
- `Manage Nicknames`
- `Move Members`
- `Manage Messages`
- `Send Messages`
- `Read Message History` / `View Channels`

---

## Setup & Installation

### 1. Clone & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OWNER_ID=123456789012345678
TRUSTED_USER_IDS=234567890123456789,345678901234567890
```

- **`OWNER_ID`**: Your primary Discord User ID (integer).
- **`TRUSTED_USER_IDS`**: Comma-separated list of additional authorized Discord User IDs (integers).

---

## Running the Bot

Start the Discord bot:

```bash
python bot.py
```

---

## Running Automated Tests

Run the test suite using `pytest`:

```bash
PYTHONPATH=. pytest
```

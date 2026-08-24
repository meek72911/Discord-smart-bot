# 🤖 Smart Bot — Full Report

```markdown
╔══════════════════════════════════════════════════════════════════╗
║  Smart bot#4771 — ID 1540339098076577852 — PID 17112 (live)     ║
║  Owner: 1463495220124454955 | Trusted: {1463495220124454955}    ║
║  Guild: Sophie ♡'s Cave (1 guild) — Models: 3.6-flash / 3.5-lite ║
║  Bypass: COOLDOWN_BYPASS_IDS=1463495220124454955 (5s gate skipped)║
║  Tests: 26 passed | DB: botdata.db 65KB WAL                     ║
╚══════════════════════════════════════════════════════════════════╝
```

## Live Status
- Gateway: Shard 279102b4... connected 03:24:12
- Prefix: mention / reply-to-bot / DM trigger only
- Cooldown: 5.0s (bypassed for owner), eviction >500 after 1h
- Logs: bot.out.log / bot.err.log (PyNaCl/davey voice disabled warnings expected)
- Invite: https://discord.com/oauth2/authorize?client_id=1540339098076577852&permissions=8&scope=bot%20applications.commands

---

## Features (63 tools + passives)

### Trigger
- @Smart bot + reply-to-bot + DM

### AI Brain
- Sessions per channel (SQLite persisted, auto-compaction at 24k est tokens), streaming live-edit 1.2s + typing 8s refresh
- Dual routing: gemini-3.6-flash (chat) / gemini-3.5-flash-lite (fast: summarize/classify)
- Safety: BLOCK_ONLY_HIGH x4, code_execution + url_context + YouTube ingest (first link), 8MB attachment cap

### Passives
- XP +5/msg, level = XP//100, embed level-up, leaderboard
- Reminder loop 30s, watch-mode classifier (ModerationVerdict), catch-me-up (limits handled)

### Tools Categories
- Channels (9): create_text/voice/stage, create_category, delete_channel, set_channel_read_only, hide_channel, edit_channel, bulk_ban helper
- Threads/Forum (2): create_thread, archive_thread
- Invites (3): create_invite, list_invites, delete_invite
- Webhooks (3): create_webhook, list_webhooks, delete_webhook
- Expressions (2): list_emojis, create_emoji
- Events/Stage (3): create_scheduled_event, list_scheduled_events, create_stage_instance
- AutoMod/Audit (3): list_automod_rules, create_automod_rule, read_audit_log
- Members (8+1): ban/unban/kick/timeout/remove_timeout/change_nickname/disconnect/move + bulk_ban
- Roles (3): create/assign/remove (dangerous guard blocks admin perms or >= bot top role)
- Messages (5): purge, pin/unpin, add_reaction, clear_reactions
- Polls (3): create_poll (text), create_native_poll (Discord Poll widget), expire_poll
- Inspection (4): list_channels, list_roles, list_members, server_info
- Warnings (3): warn_user (3=10m/4=1h/5+=1d), show_warnings, clear_warnings
- Tickets (2): create_ticket (private overwrites, auto category), close_ticket
- Memory/Persona (7): remember_fact, recall_my_facts, forget_my_facts, set_server_persona (5 personas), set_reminder, create_poll, show_leaderboard
- Native (2): code_execution, url_context

---

## Project Structure
```
C:\Users\vipul\Desktop\Discord-smart-bot\
├── bot.py              — Client, streaming, allowlist, catch-up, watch, reminders (381→~380 lines, now embeds)
├── ai_service.py       — Sessions, dual-model, streaming, safety, native tools (595→~600 lines)
├── tools.py            — 37→60+ Discord wrappers (1252→~1900 lines)
├── config.py           — Env loader + allowlist + bypass + model vars (63→~90 lines)
├── storage.py          — SQLite WAL: guild_config/mod_actions/user_lang/channel_memory/user_memory/guild_persona/user_xp/warnings/reminders/guild_extra (+ guild_keys ready)
├── embeds.py           — Palette (success/warn/error/mod/blurple) + confirm/paginator views
├── views/confirm.py, paginator.py
├── requirements.txt    — discord.py>=2.3.0, google-genai>=0.1.0, python-dotenv, pytest
├── .env.example        — token + owner + models + allowlist + bypass + watch
├── FULL_REPORT.md      — this file
└── tests/              — 26 tests (ai_service 3, tools 14, storage 5, bot 4)
```

---

## Code: config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_owner_id_raw = os.getenv("OWNER_ID", "").strip()
OWNER_ID = int(_owner_id_raw) if _owner_id_raw.isdigit() else None

_trusted_raw = os.getenv("TRUSTED_USER_IDS", "").strip()
TRUSTED_USER_IDS = set()
if _trusted_raw:
    for item in _trusted_raw.split(","):
        item = item.strip()
        if item.isdigit():
            TRUSTED_USER_IDS.add(int(item))

_mod_log_raw = os.getenv("MOD_LOG_CHANNEL_ID", "").strip()
MOD_LOG_CHANNEL_ID = int(_mod_log_raw) if _mod_log_raw.isdigit() else None

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.6-flash").strip()
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-3.5-flash-lite").strip()

ALLOWED_GUILD_IDS = set()
_allow_raw = os.getenv("ALLOWED_GUILD_IDS", "").strip()
if _allow_raw:
    for item in _allow_raw.split(","):
        item = item.strip()
        if item.isdigit():
            ALLOWED_GUILD_IDS.add(int(item))

def is_guild_allowed(guild_id) -> bool:
    if guild_id is None: return True
    if not ALLOWED_GUILD_IDS: return True
    return int(guild_id) in ALLOWED_GUILD_IDS

WATCH_MODE = os.getenv("WATCH_MODE", "").strip().lower() in ("1", "true", "yes", "on")
_watch_log_raw = os.getenv("WATCH_LOG_CHANNEL_ID", "").strip()
WATCH_LOG_CHANNEL_ID = int(_watch_log_raw) if _watch_log_raw.isdigit() else None
WATCH_SEVERITY_THRESHOLD = 4

def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")

_raw_bypass = os.getenv("COOLDOWN_BYPASS_IDS", "1463495220124454955").strip()
COOLDOWN_BYPASS_IDS: set[int] = set()
if _raw_bypass:
    for _b in _raw_bypass.split(","):
        _b = _b.strip()
        if _b.isdigit():
            COOLDOWN_BYPASS_IDS.add(int(_b))

def is_authorized_user(user_id: int) -> bool:
    if user_id is None: return False
    if OWNER_ID is not None and user_id == OWNER_ID: return True
    return user_id in TRUSTED_USER_IDS
```

## Code: requirements.txt
```
discord.py>=2.3.0
google-genai>=0.1.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## Code: .env.example
```
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OWNER_ID=123456789012345678
TRUSTED_USER_IDS=234567890123456789,345678901234567890
MOD_LOG_CHANNEL_ID=987654321098765432
CHAT_MODEL=gemini-3.6-flash
FAST_MODEL=gemini-3.5-flash-lite
ALLOWED_GUILD_IDS=
COOLDOWN_BYPASS_IDS=1463495220124454955
WATCH_MODE=false
WATCH_LOG_CHANNEL_ID=
```

## Code: storage.py (schema excerpt)
```python
DB_PATH = os.getenv("BOT_DATA_DB", "botdata.db")
# Tables: guild_config, mod_actions, user_lang, channel_memory,
#         user_memory, guild_persona, guild_extra, user_xp, reminders, warnings
#         + guild_keys (BYOK ready: guild_id PK, provider, encrypted_key, hint, validated_at)
# Helpers: get/set guild_config, record_mod_action, get/set user_lang,
#          load/save channel_memory (cap 40), add/get/forget user facts,
#          get/set persona, add_xp/get leaderboard, warnings CRUD, reminders queue
```

## Code: embeds.py
```python
import discord, datetime
COLORS = {"success":0x57F287, "warn":0xFEE75C, "error":0xED4245, "info":0x5865F2, "mod":0xFF7A00}
def make_embed(title="", description="", color=COLORS["info"], fields=None, thumbnail=None, footer=None): ...
def level_embed(member, level, xp): # gold embed with avatar thumbnail
```

## Code: ai_service.py (key excerpt)
```python
CHAT_MODEL = config.CHAT_MODEL  # gemini-3.6-flash
FAST_MODEL = config.FAST_MODEL  # gemini-3.5-flash-lite
SYSTEM_INSTRUCTION = "witty chill companion + mod tools + code/link/yt + security rules + persona injection"
SAFETY_SETTINGS = [BLOCK_ONLY_HIGH x4]
MODERATION_TOOLS = [30+ funcs: channels/members/roles/messages/tickets/warnings + 22 new: edit/bulk_ban/polls/invites/webhooks/emojis/events/stage/automod/audit/threads]
UNIVERSAL_TOOLS = [memory/persona/reminder/poll/leaderboard 7]
NATIVE = [Tool(code_execution), Tool(url_context)]  # + YouTube via FileData
ALL_TOOLS = MODERATION + UNIVERSAL + NATIVE

CHANNEL_CHATS: Dict[int, AsyncChat]  # per-channel persistent sessions via client.aio.chats.create(history=restored)
# streaming: async for chunk in await chat.send_message_stream(parts) → yield prefixes, handle function_calls
# dual routing: summarize/classify → FAST_MODEL, chat → CHAT_MODEL
# compaction: estimate tokens //4 >24k → FAST_MODEL summarize oldest half → reseed [summary, ack] + recent
# classify_message(text) → ModerationVerdict (response_schema JSON)
# Storage: save_channel_history after each exchange, user facts hint injection, guild persona in _base_gen_config
```

## Code: bot.py (key excerpt)
```python
intents = Intents.default() + message_content + members + guilds
USER_COOLDOWNS: Dict[int,float]; COOLDOWN_SECONDS=5.0
COOLDOWN_BYPASS_IDS hits → bypass check in is_user_on_cooldown / update_user_cooldown
MAX_ATTACHMENTS=5, EDIT_THROTTLE 1.2s, TYPING_REFRESH 8s
on_message:
  if author.bot: return
  storage.add_xp(+5) + level-up embed if xp%100==0
  if not (mentioned or reply_to_bot or DM): watch_mode_check(maybe) → return
  if is_user_on_cooldown and not bypass: send slow-down
  cleaned = clean_message_content; attachments capped; is_authorized = is_authorized_user
  CATCHUP_RE → _catch_me_up (history 80 → summarize_messages), TRANSLATE_RE → storage language hint
  → _stream_ai_reply → process_chat_message_stream(author_id, lang_hint, attachments) with guild/user/reminder contextvars + streaming edits
_stream_ai_reply: sent None → reply else edit, split_message with word-boundary + 1.1s pacing
_reminder_loop: every 30s deliver due_reminders
```

## Code: tools.py (sample — 60+ funcs, pattern)
```python
current_guild: ContextVar[Guild|None]; current_user_id; current_reminder_channel
PERSONAS = {default/savage/wholesome/professor/gamer}
_DANGEROUS_PERMISSIONS = [administrator, manage_guild/roles/channels/webhooks, ban/kick/moderate/manage_*]
def _is_dangerous_role(role): checks perms + position >= bot top role → block
async def create_ticket(username_or_id, issue, category_name="tickets"): private overwrites (@everyone deny, user+staff allow), auto-create category
async def edit_channel(channel_name, new_name, topic, slowmode, nsfw, bitrate): channel.edit(**kwargs)
async def bulk_ban(csv ids, reason): guild.bulk_ban 200 or loop
async def create_native_poll(question, options csv, duration 1-768h, multiselect): channel.send(poll=Poll(...))
# + create_invite/list_invites/delete_invite, add_reaction/clear_reactions, create_webhook/list/delete_webhook,
#   list_emojis/create_emoji (aiohttp download 256KiB), create_scheduled_event/list, create_stage_instance,
#   list/create_automod_rule, read_audit_log, create_thread/archive_thread, warn/show/clear_warnings, memory, etc.
```

## Tests
```bash
PYTHONPATH=. pytest → 26 passed (1 warning audioop deprecated)
tests/test_ai_service.py — 3 (unauthorized, tool_call, blocked_auth)
tests/test_tools.py — 14 inc. dangerous guard test
tests/test_storage.py — 5 (guild_config, mod_actions, user_lang, channel_memory, verdict)
tests/test_config.py — 2, tests/test_bot.py — 2
```

## Invocation (natural language, no slash)
```
@Smart bot ban @mencia spamming
@Smart bot bulk ban user1, user2 reason raiding
@Smart bot edit #general slowmode to 10
@Smart bot create native poll "Best game?" valorant, lol, cs2 duration 24
@Smart bot create invite for #welcome
@Smart bot add reaction thumbsup to message 123 in #general
@Smart bot create webhook logger in #general
@Smart bot create emoji hype from https://...
@Smart bot create scheduled event Gaming Night in 60m external at Discord
@Smart bot list automod rules
@Smart bot read audit log for ban
@Smart bot open ticket for @user payment issue / close this ticket
@Smart bot remember I love cats / what do you remember about me?
@Smart bot set persona to savage
@Smart bot catch me up / leaderboard
```

Report generated: 2026-08-23 — run `python bot.py` or `start.bat` to launch.

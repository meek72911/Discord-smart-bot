import json
import os
import time
import sqlite3
import threading
from typing import Dict, List, Optional, Tuple, Any

DB_PATH = os.getenv("BOT_DATA_DB", "botdata.db")
_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout = 5000")
        _init_tables(_conn)
    return _conn


def _init_tables(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            trusted_ids TEXT NOT NULL DEFAULT '',
            log_channel_id INTEGER,
            watch_enabled INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS mod_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            guild_id INTEGER,
            actor_id INTEGER,
            target TEXT,
            action TEXT,
            reason TEXT
        );
        CREATE TABLE IF NOT EXISTS user_lang (
            user_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS channel_memory (
            channel_id INTEGER PRIMARY KEY,
            history_json TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fact TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feature_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            votes INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'open',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS guild_persona (
            guild_id INTEGER PRIMARY KEY,
            persona TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS guild_extra (
            guild_id INTEGER PRIMARY KEY,
            xp_enabled INTEGER NOT NULL DEFAULT 1,
            welcome_channel_id INTEGER,
            starboard_channel_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS user_xp (
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            remind_at REAL NOT NULL,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS guild_keys (
            guild_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL DEFAULT 'gemini',
            encrypted_key TEXT NOT NULL,
            hint TEXT NOT NULL DEFAULT '',
            added_by TEXT,
            validated_at TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        );
        """
    )
    conn.commit()


# --- guild_config ---


def get_guild_config(guild_id: int) -> Dict:
    with _lock:
        row = _get_conn().execute(
            "SELECT trusted_ids, log_channel_id, watch_enabled FROM guild_config WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
    if not row:
        return {"trusted_ids": [], "log_channel_id": None, "watch_enabled": False}
    return {
        "trusted_ids": [int(x) for x in row[0].split(",") if x.strip().isdigit()],
        "log_channel_id": row[1],
        "watch_enabled": bool(row[2]),
    }


def set_guild_config(guild_id: int, **kwargs) -> None:
    current = get_guild_config(guild_id)
    trusted = kwargs.get("trusted_ids", current["trusted_ids"])
    log_ch = kwargs.get("log_channel_id", current["log_channel_id"])
    watch = int(kwargs.get("watch_enabled", current["watch_enabled"]))
    with _lock:
        _get_conn().execute(
            """INSERT INTO guild_config (guild_id, trusted_ids, log_channel_id, watch_enabled)
               VALUES (?,?,?,?)
               ON CONFLICT(guild_id) DO UPDATE SET trusted_ids=excluded.trusted_ids,
                 log_channel_id=excluded.log_channel_id, watch_enabled=excluded.watch_enabled""",
            (guild_id, ",".join(str(t) for t in trusted), log_ch, watch),
        )
        _get_conn().commit()


# --- mod_actions ---


def record_mod_action(guild_id: Optional[int], actor_id: Optional[int], target: str, action: str, reason: str = "") -> None:
    import time

    with _lock:
        _get_conn().execute(
            "INSERT INTO mod_actions (ts, guild_id, actor_id, target, action, reason) VALUES (?,?,?,?,?,?)",
            (time.time(), guild_id, actor_id, target, action, reason),
        )
        _get_conn().commit()


def recent_mod_actions(guild_id: int, limit: int = 10) -> List[Tuple]:
    with _lock:
        rows = _get_conn().execute(
            "SELECT ts, actor_id, target, action, reason FROM mod_actions WHERE guild_id=? ORDER BY id DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
    return rows


# --- user_lang ---


def get_user_lang(user_id: int) -> Optional[str]:
    with _lock:
        row = _get_conn().execute("SELECT lang FROM user_lang WHERE user_id=?", (user_id,)).fetchone()
    return row[0] if row else None


def set_user_lang(user_id: int, lang: str) -> None:
    with _lock:
        _get_conn().execute(
            "INSERT INTO user_lang (user_id, lang) VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
            (user_id, lang[:32]),
        )
        _get_conn().commit()


# --- channel_memory (serialized chat history) ---


def load_channel_history(channel_id: int) -> List[Dict]:
    """Return stored history as list of {role, parts:[{text}|{function_call}|{function_response}]} dicts."""
    with _lock:
        row = _get_conn().execute(
            "SELECT history_json FROM channel_memory WHERE channel_id=?", (channel_id,)
        ).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row[0])
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_channel_history(channel_id: int, history_dicts: List[Dict]) -> None:
    import time

    try:
        payload = json.dumps(history_dicts[-40:])  # cap stored size
    except (TypeError, ValueError):
        return
    with _lock:
        _get_conn().execute(
            """INSERT INTO channel_memory (channel_id, history_json, updated_at)
               VALUES (?,?,?)
               ON CONFLICT(channel_id) DO UPDATE SET history_json=excluded.history_json,
                 updated_at=excluded.updated_at""",
            (channel_id, payload, time.time()),
        )
        _get_conn().commit()


def delete_channel_memory(channel_id: int) -> None:
    with _lock:
        _get_conn().execute("DELETE FROM channel_memory WHERE channel_id=?", (channel_id,))
        _get_conn().commit()


# --- user memory / personas / XP / reminders / warnings ---


def add_user_fact(user_id: int, fact: str) -> None:
    import time

    with _lock:
        _get_conn().execute(
            "INSERT INTO user_memory (user_id, fact, created_at) VALUES (?,?,?)",
            (user_id, fact[:500], time.time()),
        )
        _get_conn().commit()


def get_user_facts(user_id: int, limit: int = 10) -> List[str]:
    with _lock:
        rows = _get_conn().execute(
            "SELECT fact FROM user_memory WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return [r[0] for r in rows]


def forget_user_facts(user_id: int) -> None:
    with _lock:
        _get_conn().execute("DELETE FROM user_memory WHERE user_id=?", (user_id,))
        _get_conn().commit()


def scrub_user_from_logs(user_id: int) -> int:
    """Scrub a user's ID and occurrences from local bot.log and rotated log files."""
    scrubbed_count = 0
    uid_str = str(user_id)
    log_files = ["bot.log", "bot.log.1", "bot.log.2", "bot.log.3", "bot.log.4", "bot.log.5"]
    for log_path in log_files:
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                modified = False
                new_lines = []
                for line in lines:
                    if uid_str in line:
                        new_lines.append(line.replace(uid_str, "[PURGED_USER_ID]"))
                        scrubbed_count += 1
                        modified = True
                    else:
                        new_lines.append(line)
                if modified:
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
            except Exception:
                pass
    return scrubbed_count


def purge_user_data(user_id: int) -> Dict[str, int]:
    """
    Comprehensively purges all stored personal data for a user across all tables and logs:
    - user_memory (saved facts & context)
    - user_lang (language preference)
    - reminders (pending user reminders)
    - user_xp (gamification record)
    - bot.log (active & rotated disk logs)
    """
    counts = {}
    with _lock:
        conn = _get_conn()
        c1 = conn.execute("DELETE FROM user_memory WHERE user_id=?", (user_id,)).rowcount
        c2 = conn.execute("DELETE FROM user_lang WHERE user_id=?", (user_id,)).rowcount
        c3 = conn.execute("DELETE FROM reminders WHERE user_id=?", (user_id,)).rowcount
        c4 = conn.execute("DELETE FROM user_xp WHERE user_id=?", (user_id,)).rowcount
        conn.commit()
        c5 = scrub_user_from_logs(user_id)
        counts = {"user_memory": c1, "user_lang": c2, "reminders": c3, "user_xp": c4, "logs_scrubbed": c5}
    return counts


def get_guild_persona(guild_id: int) -> str:
    with _lock:
        row = _get_conn().execute("SELECT persona FROM guild_persona WHERE guild_id=?", (guild_id,)).fetchone()
    return row[0] if row else "default"


def set_guild_persona(guild_id: int, persona: str) -> None:
    import time

    with _lock:
        _get_conn().execute(
            """INSERT INTO guild_persona (guild_id, persona, updated_at) VALUES (?,?,?)
               ON CONFLICT(guild_id) DO UPDATE SET persona=excluded.persona, updated_at=excluded.updated_at""",
            (guild_id, persona[:32], time.time()),
        )
        _get_conn().commit()


def add_xp(user_id: int, guild_id: int, amount: int = 5) -> int:
    with _lock:
        _get_conn().execute(
            """INSERT INTO user_xp (user_id, guild_id, xp) VALUES (?,?,?)
               ON CONFLICT(user_id, guild_id) DO UPDATE SET xp=xp+excluded.xp""",
            (user_id, guild_id, amount),
        )
        row = _get_conn().execute("SELECT xp FROM user_xp WHERE user_id=? AND guild_id=?", (user_id, guild_id)).fetchone()
        _get_conn().commit()
    return row[0] if row else amount


def get_xp_leaderboard(guild_id: int, limit: int = 10) -> List[Tuple]:
    with _lock:
        return _get_conn().execute(
            "SELECT user_id, xp FROM user_xp WHERE guild_id=? ORDER BY xp DESC LIMIT ?", (guild_id, limit)
        ).fetchall()


def add_warning(guild_id: int, user_id: int, reason: str) -> int:
    import time

    with _lock:
        _get_conn().execute("INSERT INTO warnings (guild_id, user_id, reason, ts) VALUES (?,?,?,?)", (guild_id, user_id, reason[:300], time.time()))
        count = _get_conn().execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id)
        ).fetchone()[0]
        _get_conn().commit()
    return count


def get_warnings(guild_id: int, user_id: int) -> List[Tuple]:
    with _lock:
        return _get_conn().execute(
            "SELECT reason, ts FROM warnings WHERE guild_id=? AND user_id=? ORDER BY ts DESC", (guild_id, user_id)
        ).fetchall()


def clear_warnings(guild_id: int, user_id: int) -> None:
    with _lock:
        _get_conn().execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        _get_conn().commit()


def add_reminder(guild_id, channel_id: int, user_id: int, remind_at: float, text: str) -> int:
    with _lock:
        cur = _get_conn().execute(
            "INSERT INTO reminders (guild_id, channel_id, user_id, remind_at, text) VALUES (?,?,?,?,?)",
            (guild_id, channel_id, user_id, remind_at, text[:500]),
        )
        _get_conn().commit()
        return cur.lastrowid


def due_reminders(now: float) -> List[Tuple]:
    with _lock:
        return _get_conn().execute(
            "SELECT id, guild_id, channel_id, user_id, text FROM reminders WHERE remind_at<=? ORDER BY remind_at", (now,)
        ).fetchall()


def delete_reminder(rid: int) -> None:
    with _lock:
        _get_conn().execute("DELETE FROM reminders WHERE id=?", (rid,))
        _get_conn().commit()


# ==============================================================================
# FEATURE SUGGESTIONS & FEEDBACK LOOP
# ==============================================================================

def submit_feature_suggestion(guild_id: int, user_id: int, author_name: str, suggestion: str, category: str = "general") -> int:
    """Submits a member product feature suggestion with 1 starting vote."""
    now = time.time()
    g_id = int(guild_id) if isinstance(guild_id, int) else 0
    u_id = int(user_id) if isinstance(user_id, int) else 0
    with _lock:
        cur = _get_conn().execute(
            """
            INSERT INTO feature_suggestions (guild_id, user_id, author_name, suggestion, category, votes, status, created_at)
            VALUES (?, ?, ?, ?, ?, 1, 'open', ?)
            """,
            (g_id, u_id, str(author_name), suggestion.strip(), str(category), now)
        )
        _get_conn().commit()
        return cur.lastrowid


def get_feature_suggestions(guild_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves top feature suggestions ranked by votes."""
    g_id = int(guild_id) if isinstance(guild_id, int) else None
    with _lock:
        if g_id is not None:
            rows = _get_conn().execute(
                """
                SELECT id, guild_id, user_id, author_name, suggestion, category, votes, status, created_at
                FROM feature_suggestions
                WHERE guild_id = ?
                ORDER BY votes DESC, created_at DESC LIMIT ?
                """,
                (g_id, limit)
            ).fetchall()
        else:
            rows = _get_conn().execute(
                """
                SELECT id, guild_id, user_id, author_name, suggestion, category, votes, status, created_at
                FROM feature_suggestions
                ORDER BY votes DESC, created_at DESC LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [
            {
                "id": r[0],
                "guild_id": r[1],
                "user_id": r[2],
                "author_name": r[3],
                "suggestion": r[4],
                "category": r[5],
                "votes": r[6],
                "status": r[7],
                "created_at": r[8]
            }
            for r in rows
        ]


def upvote_feature_suggestion(suggestion_id: int) -> int:
    """Increments vote count for a feature suggestion."""
    with _lock:
        _get_conn().execute(
            "UPDATE feature_suggestions SET votes = votes + 1 WHERE id = ?",
            (suggestion_id,)
        )
        _get_conn().commit()
        row = _get_conn().execute("SELECT votes FROM feature_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
        return row[0] if row else 0


def close() -> None:
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None

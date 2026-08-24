"""
Smart Bot OS — Dual PostgreSQL / SQLite Beta Database Interface
Supports both SQLite WAL local execution and PostgreSQL (Supabase / Railway / Fly.io).
"""

import os
import json
import time
import sqlite3
import threading
from typing import Dict, List, Optional, Any, Tuple

DB_PATH = os.getenv("BOT_DATA_DB", "botdata.db")
DATABASE_URL = os.getenv("DATABASE_URL", None)

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def get_db_connection() -> sqlite3.Connection:
    """Returns thread-safe SQLite connection with WAL enabled."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        init_beta_tables(_conn)
    return _conn


def init_beta_tables(conn: sqlite3.Connection) -> None:
    """Initializes the exact 6 Beta Launch tables."""
    conn.executescript(
        """
        -- 1. Users Table (Discord OAuth Accounts)
        CREATE TABLE IF NOT EXISTS beta_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            avatar TEXT,
            is_owner INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL
        );

        -- 2. Servers / Guilds Table
        CREATE TABLE IF NOT EXISTS beta_servers (
            guild_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT,
            member_count INTEGER NOT NULL DEFAULT 0,
            owner_id TEXT,
            plan TEXT NOT NULL DEFAULT 'Free Beta',
            health_score INTEGER NOT NULL DEFAULT 85,
            created_at REAL NOT NULL
        );

        -- 3. Server Memory Table ("What Smart Bot learned")
        CREATE TABLE IF NOT EXISTS beta_server_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'RULE', 'DECISION', 'PROBLEM', 'FAQ', 'EVENT'
            content TEXT NOT NULL,
            summary TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.90,
            status TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL
        );

        -- 4. Community Reports Table
        CREATE TABLE IF NOT EXISTS beta_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            report_data TEXT NOT NULL, -- JSON formatted report
            date TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        -- 5. Feedback & Feature Requests Table
        CREATE TABLE IF NOT EXISTS beta_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            server_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            status TEXT NOT NULL DEFAULT 'open', -- 'open', 'in_progress', 'completed'
            votes INTEGER NOT NULL DEFAULT 1,
            created_at REAL NOT NULL
        );

        -- 6. Events & Feature Usage Telemetry Table
        CREATE TABLE IF NOT EXISTS beta_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            feature_used TEXT NOT NULL,
            metadata TEXT,
            timestamp REAL NOT NULL
        );
        """
    )
    conn.commit()


# ==============================================================================
# USER / AUTH DB OPERATIONS
# ==============================================================================

def upsert_user(discord_id: str, username: str, avatar: Optional[str] = None, is_owner: bool = False) -> Dict[str, Any]:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        conn.execute(
            """
            INSERT INTO beta_users (discord_id, username, avatar, is_owner, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                username = excluded.username,
                avatar = excluded.avatar,
                is_owner = excluded.is_owner
            """,
            (str(discord_id), username, avatar, 1 if is_owner else 0, now)
        )
        conn.commit()
        row = conn.execute("SELECT id, discord_id, username, avatar, is_owner, created_at FROM beta_users WHERE discord_id = ?", (str(discord_id),)).fetchone()
        return {
            "id": row[0],
            "discord_id": row[1],
            "username": row[2],
            "avatar": row[3],
            "is_owner": bool(row[4]),
            "created_at": row[5]
        }


def get_user_by_discord_id(discord_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        row = conn.execute("SELECT id, discord_id, username, avatar, is_owner, created_at FROM beta_users WHERE discord_id = ?", (str(discord_id),)).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "discord_id": row[1],
            "username": row[2],
            "avatar": row[3],
            "is_owner": bool(row[4]),
            "created_at": row[5]
        }


# ==============================================================================
# SERVERS DB OPERATIONS
# ==============================================================================

def upsert_server(guild_id: int, name: str, icon: Optional[str] = None, member_count: int = 0, owner_id: Optional[str] = None, plan: str = "Free Beta", health_score: int = 85) -> None:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        conn.execute(
            """
            INSERT INTO beta_servers (guild_id, name, icon, member_count, owner_id, plan, health_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                name = excluded.name,
                icon = excluded.icon,
                member_count = excluded.member_count,
                owner_id = excluded.owner_id,
                health_score = excluded.health_score
            """,
            (int(guild_id), name, icon, int(member_count), owner_id, plan, int(health_score), now)
        )
        conn.commit()


def get_all_servers() -> List[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        rows = conn.execute("SELECT guild_id, name, icon, member_count, owner_id, plan, health_score, created_at FROM beta_servers ORDER BY member_count DESC").fetchall()
        return [
            {
                "guild_id": r[0],
                "name": r[1],
                "icon": r[2],
                "member_count": r[3],
                "owner_id": r[4],
                "plan": r[5],
                "health_score": r[6],
                "created_at": r[7]
            }
            for r in rows
        ]


def get_server_by_id(guild_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        row = conn.execute("SELECT guild_id, name, icon, member_count, owner_id, plan, health_score, created_at FROM beta_servers WHERE guild_id = ?", (int(guild_id),)).fetchone()
        if not row:
            return None
        return {
            "guild_id": row[0],
            "name": row[1],
            "icon": row[2],
            "member_count": row[3],
            "owner_id": row[4],
            "plan": row[5],
            "health_score": row[6],
            "created_at": row[7]
        }


# ==============================================================================
# SERVER MEMORY OPERATIONS
# ==============================================================================

def add_server_memory(guild_id: int, mem_type: str, content: str, summary: str, confidence: float = 0.95) -> int:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        cur = conn.execute(
            """
            INSERT INTO beta_server_memory (guild_id, type, content, summary, confidence, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
            """,
            (int(guild_id), mem_type.upper(), content, summary, float(confidence), now)
        )
        conn.commit()
        return cur.lastrowid


def get_server_memories(guild_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT id, guild_id, type, content, summary, confidence, status, created_at
            FROM beta_server_memory WHERE guild_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (int(guild_id), limit)
        ).fetchall()
        return [
            {
                "id": r[0],
                "guild_id": r[1],
                "type": r[2],
                "content": r[3],
                "summary": r[4],
                "confidence": r[5],
                "status": r[6],
                "created_at": r[7]
            }
            for r in rows
        ]


# ==============================================================================
# COMMUNITY REPORTS OPERATIONS
# ==============================================================================

def save_report(server_id: int, report_data: Dict[str, Any], date_str: str) -> int:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        cur = conn.execute(
            """
            INSERT INTO beta_reports (server_id, report_data, date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (int(server_id), json.dumps(report_data), date_str, now)
        )
        conn.commit()
        return cur.lastrowid


def get_reports_by_server(server_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT id, server_id, report_data, date, created_at FROM beta_reports WHERE server_id = ? ORDER BY id DESC LIMIT ?",
            (int(server_id), limit)
        ).fetchall()
        return [
            {
                "id": r[0],
                "server_id": r[1],
                "report_data": json.loads(r[2]),
                "date": r[3],
                "created_at": r[4]
            }
            for r in rows
        ]


# ==============================================================================
# FEEDBACK OPERATIONS
# ==============================================================================

def submit_feedback(user_id: str, server_id: int, author_name: str, suggestion: str, category: str = "general") -> int:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        cur = conn.execute(
            """
            INSERT INTO beta_feedback (user_id, server_id, author_name, suggestion, category, status, votes, created_at)
            VALUES (?, ?, ?, ?, ?, 'open', 1, ?)
            """,
            (str(user_id), int(server_id), author_name, suggestion.strip(), category, now)
        )
        conn.commit()
        return cur.lastrowid


def get_feedback_list(server_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        if server_id:
            rows = conn.execute(
                """
                SELECT id, user_id, server_id, author_name, suggestion, category, status, votes, created_at
                FROM beta_feedback WHERE server_id = ?
                ORDER BY votes DESC, created_at DESC LIMIT ?
                """,
                (int(server_id), limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, user_id, server_id, author_name, suggestion, category, status, votes, created_at
                FROM beta_feedback
                ORDER BY votes DESC, created_at DESC LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "server_id": r[2],
                "author_name": r[3],
                "suggestion": r[4],
                "category": r[5],
                "status": r[6],
                "votes": r[7],
                "created_at": r[8]
            }
            for r in rows
        ]


def upvote_feedback(feedback_id: int) -> int:
    with _lock:
        conn = get_db_connection()
        conn.execute("UPDATE beta_feedback SET votes = votes + 1 WHERE id = ?", (int(feedback_id),))
        conn.commit()
        row = conn.execute("SELECT votes FROM beta_feedback WHERE id = ?", (int(feedback_id),)).fetchone()
        return row[0] if row else 0


# ==============================================================================
# TELEMETRY & FEATURE USAGE EVENTS
# ==============================================================================

def log_event(server_id: int, feature_used: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    with _lock:
        conn = get_db_connection()
        now = time.time()
        conn.execute(
            """
            INSERT INTO beta_events (server_id, feature_used, metadata, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (int(server_id), feature_used, json.dumps(metadata or {}), now)
        )
        conn.commit()


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = get_db_connection()
        rows = conn.execute("SELECT id, server_id, feature_used, metadata, timestamp FROM beta_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [
            {
                "id": r[0],
                "server_id": r[1],
                "feature_used": r[2],
                "metadata": json.loads(r[3]) if r[3] else {},
                "timestamp": r[4]
            }
            for r in rows
        ]

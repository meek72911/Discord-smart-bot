"""
Smart Bot Living Community Knowledge Base
Allows server administrators and community managers to store, search, and recall
grounded server rules, official announcements, tournament guidelines, and FAQs.
"""

import sqlite3
import time
import os
import re
from typing import Dict, List, Optional, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "botdata.db")

def init_kb_table():
    """Initializes the community knowledge base table in SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS community_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                category TEXT NOT NULL, -- RULE, ANNOUNCEMENT, FAQ, DECISION, EVENT
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_channel TEXT,
                author_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kb_guild ON community_knowledge(guild_id)")
        conn.commit()

init_kb_table()

def add_knowledge_entry(
    guild_id: int,
    category: str,
    title: str,
    content: str,
    source_channel: str = "general",
    author_name: str = "Admin"
) -> int:
    """
    Adds a verified piece of community knowledge into the database.
    """
    category_clean = category.upper().strip()
    if category_clean not in {"RULE", "ANNOUNCEMENT", "FAQ", "DECISION", "EVENT"}:
        category_clean = "FAQ"

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO community_knowledge (guild_id, category, title, content, source_channel, author_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, category_clean, title.strip(), content.strip(), source_channel, author_name))
        conn.commit()
        return cursor.lastrowid

def search_knowledge_entries(guild_id: int, query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Performs keyword & semantic relevance lookup across community knowledge.
    """
    query_clean = query.strip().lower()
    keywords = [w for w in re.findall(r"\w+", query_clean) if len(w) > 2]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, category, title, content, source_channel, author_name, created_at
            FROM community_knowledge
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT 50
        """, (guild_id,)).fetchall()

    if not rows:
        return []

    scored_entries = []
    for r in rows:
        text_corpus = f"{r['title']} {r['content']} {r['category']}".lower()
        score = 0
        if query_clean in text_corpus:
            score += 10
        for kw in keywords:
            if kw in text_corpus:
                score += 2
        scored_entries.append((score, dict(r)))

    # Sort by relevance score descending
    scored_entries.sort(key=lambda x: x[0], reverse=True)
    results = [entry for score, entry in scored_entries if score > 0]
    if not results and rows:
        # Fallback to recent entries if no exact keywords match
        results = [dict(r) for r in rows[:limit]]
    return results[:limit]

def list_knowledge_categories(guild_id: int) -> List[Dict[str, Any]]:
    """
    Lists all indexed community knowledge entries for a guild.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, category, title, source_channel, created_at
            FROM community_knowledge
            WHERE guild_id = ?
            ORDER BY category, id DESC
        """, (guild_id,)).fetchall()
    return [dict(r) for r in rows]

def delete_knowledge_entry(guild_id: int, entry_id: int) -> bool:
    """
    Deletes an entry from the knowledge base by ID.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            DELETE FROM community_knowledge
            WHERE guild_id = ? AND id = ?
        """, (guild_id, entry_id))
        conn.commit()
        return cursor.rowcount > 0

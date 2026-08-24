"""
Smart Bot OS v5.0 — Community Memory Graph Engine
Provides an ultra-fast, zero-cost SQLite-backed property graph layer for Discord communities.
Stores entities (USER, EVENT, TOPIC, DECISION, PROBLEM, SOLUTION, RULE, ANNOUNCEMENT, CHANNEL, ROLE)
and their causal relationships (caused_by, created_by, fixed, discussed_in, superseded_by, participated_in).
"""

import json
import sqlite3
import time
import os
import threading
from typing import Dict, List, Optional, Any, Tuple, Set

DB_PATH = os.getenv("BOT_DATA_DB", "botdata.db")
_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None

# Entity and Relationship Vocabulary
VALID_ENTITY_TYPES = {
    "USER", "EVENT", "TOPIC", "DECISION", "PROBLEM",
    "SOLUTION", "RULE", "ANNOUNCEMENT", "CHANNEL", "ROLE"
}

VALID_RELATION_TYPES = {
    "participated_in", "caused_by", "created_by", "fixed",
    "discussed_in", "superseded_by", "impacted_by", "requested_by",
    "related_to", "assigned_to", "resolved_by"
}

def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        init_graph_tables(_conn)
    return _conn

def init_graph_tables(conn: Optional[sqlite3.Connection] = None):
    """Initializes graph nodes, edges, and temporal state tables."""
    target_conn = conn or _get_conn()
    with _lock:
        target_conn.executescript("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                attributes_json TEXT NOT NULL DEFAULT '{}',
                source_channel_id INTEGER,
                source_message_id INTEGER,
                author_id INTEGER,
                importance_score INTEGER NOT NULL DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'active', -- active, expired, superseded, archived
                valid_from REAL NOT NULL,
                valid_until REAL,
                superseded_by_id INTEGER,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS graph_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                source_node_id INTEGER NOT NULL,
                target_node_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL NOT NULL DEFAULT 1.0,
                evidence TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (source_node_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (target_node_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS server_dna (
                guild_id INTEGER PRIMARY KEY,
                server_type TEXT NOT NULL DEFAULT 'General Community',
                communication_style TEXT NOT NULL DEFAULT 'Casual & Friendly',
                main_topics_json TEXT NOT NULL DEFAULT '[]',
                important_rules_json TEXT NOT NULL DEFAULT '[]',
                emoji_style TEXT NOT NULL DEFAULT 'Moderate',
                slang_vocabulary_json TEXT NOT NULL DEFAULT '[]',
                formality_level TEXT NOT NULL DEFAULT 'Casual',
                confidence_pct INTEGER NOT NULL DEFAULT 85,
                scanned_channels_json TEXT NOT NULL DEFAULT '[]',
                last_scanned_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS member_intelligence (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                contribution_type TEXT NOT NULL, -- helper, knowledge_holder, event_organizer, active_contributor
                helpful_actions_count INTEGER NOT NULL DEFAULT 0,
                key_skills_json TEXT NOT NULL DEFAULT '[]',
                last_active_at REAL NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_nodes_guild_type ON graph_nodes(guild_id, entity_type, status);
            CREATE INDEX IF NOT EXISTS idx_nodes_name ON graph_nodes(guild_id, name);
            CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(guild_id, source_node_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(guild_id, target_node_id);
        """)
        target_conn.commit()

init_graph_tables()

# ==============================================================================
# GRAPH NODE OPERATIONS
# ==============================================================================

def add_or_update_node(
    guild_id: int,
    entity_type: str,
    name: str,
    summary: str,
    attributes: Optional[Dict[str, Any]] = None,
    source_channel_id: Optional[int] = None,
    source_message_id: Optional[int] = None,
    author_id: Optional[int] = None,
    importance_score: int = 5,
    valid_from: Optional[float] = None,
    valid_until: Optional[float] = None,
    status: str = "active"
) -> int:
    """
    Creates or updates a memory node in the community graph.
    """
    entity_type_clean = entity_type.upper().strip()
    if entity_type_clean not in VALID_ENTITY_TYPES:
        entity_type_clean = "TOPIC"

    now = time.time()
    v_from = valid_from if valid_from is not None else now
    attr_json = json.dumps(attributes or {})

    with _lock:
        conn = _get_conn()
        # Check if an active node with the same name and entity type already exists
        cursor = conn.execute("""
            SELECT id, attributes_json, status FROM graph_nodes
            WHERE guild_id = ? AND entity_type = ? AND LOWER(name) = LOWER(?) AND status = 'active'
            ORDER BY id DESC LIMIT 1
        """, (guild_id, entity_type_clean, name.strip()))
        row = cursor.fetchone()

        if row:
            node_id = row[0]
            existing_attr = json.loads(row[1]) if row[1] else {}
            if isinstance(attributes, dict):
                existing_attr.update(attributes)
            conn.execute("""
                UPDATE graph_nodes
                SET summary = ?, attributes_json = ?, importance_score = ?, valid_until = ?, updated_at = ?
                WHERE id = ?
            """, (summary.strip(), json.dumps(existing_attr), max(1, min(10, importance_score)), valid_until, now, node_id))
            conn.commit()
            return node_id
        else:
            cursor = conn.execute("""
                INSERT INTO graph_nodes (
                    guild_id, entity_type, name, summary, attributes_json,
                    source_channel_id, source_message_id, author_id,
                    importance_score, status, valid_from, valid_until,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild_id, entity_type_clean, name.strip(), summary.strip(), attr_json,
                source_channel_id, source_message_id, author_id,
                max(1, min(10, importance_score)), status, v_from, valid_until,
                now, now
            ))
            conn.commit()
            return cursor.lastrowid

def supersede_node(guild_id: int, old_node_id: int, new_node_id: int, reason: str = "") -> bool:
    """
    Marks an old memory node as superseded by a newer node (e.g. rescheduled event or updated rule).
    """
    now = time.time()
    with _lock:
        conn = _get_conn()
        conn.execute("""
            UPDATE graph_nodes
            SET status = 'superseded', superseded_by_id = ?, valid_until = ?, updated_at = ?
            WHERE guild_id = ? AND id = ?
        """, (new_node_id, now, now, guild_id, old_node_id))
        
        # Link the two nodes with a superseded_by edge
        conn.execute("""
            INSERT INTO graph_edges (guild_id, source_node_id, target_node_id, relation_type, evidence, created_at)
            VALUES (?, ?, ?, 'superseded_by', ?, ?)
        """, (guild_id, old_node_id, new_node_id, reason, now))
        conn.commit()
        return True

def get_node(guild_id: int, node_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single node by ID with parsed attributes."""
    with _lock:
        row = _get_conn().execute("""
            SELECT id, guild_id, entity_type, name, summary, attributes_json,
                   source_channel_id, source_message_id, author_id, importance_score,
                   status, valid_from, valid_until, superseded_by_id, created_at, updated_at
            FROM graph_nodes WHERE guild_id = ? AND id = ?
        """, (guild_id, node_id)).fetchone()
    
    if not row:
        return None
    return {
        "id": row[0],
        "guild_id": row[1],
        "entity_type": row[2],
        "name": row[3],
        "summary": row[4],
        "attributes": json.loads(row[5]),
        "source_channel_id": row[6],
        "source_message_id": row[7],
        "author_id": row[8],
        "importance_score": row[9],
        "status": row[10],
        "valid_from": row[11],
        "valid_until": row[12],
        "superseded_by_id": row[13],
        "created_at": row[14],
        "updated_at": row[15]
    }

# ==============================================================================
# GRAPH EDGE OPERATIONS & RELATIONSHIPS
# ==============================================================================

def add_edge(
    guild_id: int,
    source_node_id: int,
    target_node_id: int,
    relation_type: str,
    evidence: str = "",
    weight: float = 1.0
) -> int:
    """
    Creates a directed edge between two memory nodes.
    """
    rel_clean = relation_type.lower().strip()
    if rel_clean not in VALID_RELATION_TYPES:
        rel_clean = "related_to"

    now = time.time()
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("""
            SELECT id FROM graph_edges
            WHERE guild_id = ? AND source_node_id = ? AND target_node_id = ? AND relation_type = ?
        """, (guild_id, source_node_id, target_node_id, rel_clean))
        row = cursor.fetchone()
        if row:
            conn.execute("""
                UPDATE graph_edges SET weight = ?, evidence = ? WHERE id = ?
            """, (weight, evidence, row[0]))
            conn.commit()
            return row[0]
        else:
            cursor = conn.execute("""
                INSERT INTO graph_edges (guild_id, source_node_id, target_node_id, relation_type, weight, evidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, source_node_id, target_node_id, rel_clean, weight, evidence, now))
            conn.commit()
            return cursor.lastrowid

# ==============================================================================
# GRAPH REASONING & CAUSAL CHAIN QUERIES
# ==============================================================================

def query_subgraph(guild_id: int, entity_type: Optional[str] = None, status: str = "active", limit: int = 50) -> Dict[str, Any]:
    """
    Fetches nodes and edges for visualizing or reasoning over the community brain graph.
    """
    with _lock:
        conn = _get_conn()
        if entity_type:
            cursor = conn.execute("""
                SELECT id, entity_type, name, summary, attributes_json, status, importance_score, created_at
                FROM graph_nodes
                WHERE guild_id = ? AND entity_type = ? AND (status = ? OR ? = 'all')
                ORDER BY importance_score DESC, updated_at DESC LIMIT ?
            """, (guild_id, entity_type.upper().strip(), status, status, limit))
        else:
            cursor = conn.execute("""
                SELECT id, entity_type, name, summary, attributes_json, status, importance_score, created_at
                FROM graph_nodes
                WHERE guild_id = ? AND (status = ? OR ? = 'all')
                ORDER BY importance_score DESC, updated_at DESC LIMIT ?
            """, (guild_id, status, status, limit))
        
        nodes = []
        node_ids = set()
        for r in cursor.fetchall():
            node_ids.add(r[0])
            nodes.append({
                "id": r[0],
                "entity_type": r[1],
                "name": r[2],
                "summary": r[3],
                "attributes": json.loads(r[4]),
                "status": r[5],
                "importance_score": r[6],
                "created_at": r[7]
            })

        if not node_ids:
            return {"nodes": [], "edges": []}

        # Fetch connected edges
        placeholders = ",".join("?" for _ in node_ids)
        edge_cursor = conn.execute(f"""
            SELECT id, source_node_id, target_node_id, relation_type, weight, evidence
            FROM graph_edges
            WHERE guild_id = ? AND (source_node_id IN ({placeholders}) OR target_node_id IN ({placeholders}))
        """, [guild_id] + list(node_ids) + list(node_ids))
        
        edges = []
        for er in edge_cursor.fetchall():
            edges.append({
                "id": er[0],
                "source": er[1],
                "target": er[2],
                "relation": er[3],
                "weight": er[4],
                "evidence": er[5]
            })

        return {"nodes": nodes, "edges": edges}

def trace_causal_path(guild_id: int, node_name: str) -> List[Dict[str, Any]]:
    """
    Traces the causal and explanatory chain for a node ("Why did this happen?").
    Returns the connected upstream decisions, causes, problems, and solutions.
    """
    with _lock:
        conn = _get_conn()
        # Find matching node
        cursor = conn.execute("""
            SELECT id, entity_type, name, summary, status FROM graph_nodes
            WHERE guild_id = ? AND LOWER(name) LIKE LOWER(?)
            ORDER BY importance_score DESC LIMIT 1
        """, (guild_id, f"%{node_name.strip()}%"))
        root = cursor.fetchone()
        if not root:
            return []

        root_id = root[0]
        results = [{
            "step": 0,
            "node_id": root_id,
            "entity_type": root[1],
            "name": root[2],
            "summary": root[3],
            "status": root[4],
            "relation": "TARGET"
        }]

        # Find incoming and outgoing edges
        edge_cursor = conn.execute("""
            SELECT e.relation_type, e.evidence, n.id, n.entity_type, n.name, n.summary, n.status, 'incoming' as dir
            FROM graph_edges e
            JOIN graph_nodes n ON e.source_node_id = n.id
            WHERE e.guild_id = ? AND e.target_node_id = ?
            UNION ALL
            SELECT e.relation_type, e.evidence, n.id, n.entity_type, n.name, n.summary, n.status, 'outgoing' as dir
            FROM graph_edges e
            JOIN graph_nodes n ON e.target_node_id = n.id
            WHERE e.guild_id = ? AND e.source_node_id = ?
        """, (guild_id, root_id, guild_id, root_id))

        for idx, er in enumerate(edge_cursor.fetchall(), 1):
            results.append({
                "step": idx,
                "node_id": er[2],
                "entity_type": er[3],
                "name": er[4],
                "summary": er[5],
                "status": er[6],
                "relation": er[0],
                "evidence": er[1],
                "direction": er[7]
            })

        return results

def get_temporal_history(guild_id: int, entity_name: str) -> List[Dict[str, Any]]:
    """
    Returns the full temporal timeline for an evolving entity (e.g. tournament dates or rule changes),
    including active, expired, and superseded versions.
    """
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("""
            SELECT id, entity_type, name, summary, status, valid_from, valid_until, superseded_by_id, created_at
            FROM graph_nodes
            WHERE guild_id = ? AND LOWER(name) LIKE LOWER(?)
            ORDER BY created_at ASC
        """, (guild_id, f"%{entity_name.strip()}%"))
        
        history = []
        for r in cursor.fetchall():
            history.append({
                "id": r[0],
                "entity_type": r[1],
                "name": r[2],
                "summary": r[3],
                "status": r[4],
                "valid_from": r[5],
                "valid_until": r[6],
                "superseded_by_id": r[7],
                "created_at": r[8]
            })
        return history

"""
Smart Bot OS v5.0 — Community Brain Engine
The central intelligence coordinator uniting:
1. Smart Onboarding & Server DNA Scanner
2. Importance Scoring & Memory Extraction Pipeline (0-10)
3. Temporal Memory Resolver (Active vs Expired vs Superseded)
4. Privacy-Safe Member Intelligence
5. Hybrid Brain Retrieval (Graph + Vector + Activity Context)
"""

import re
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
import sqlite3

import community_graph
import knowledge_base
import collector

logger = logging.getLogger("community_brain")

# ==============================================================================
# 1. IMPORTANCE SCORING ENGINE (0-10)
# ==============================================================================

# High-signal keywords indicating server decisions, rules, problems, or events
DECISION_PATTERNS = [
    r"\b(admin|staff|mod|mods|owner)\s+(decided|announced|changed|updated|voted|approved|banned|removed)\b",
    r"\bnew\s+(rule|policy|requirement|update|system|role)\b",
    r"\b(rule\s+\d+|rules\s+updated|guidelines)\b"
]

EVENT_PATTERNS = [
    r"\b(tournament|scrim|scrims|match|bracket|giveaway|stream|meetup|movie\s+night)\b",
    r"\b(registration\s+open|prize\s+pool|starts\s+at|rescheduled|date\s+changed|postponed)\b"
]

PROBLEM_PATTERNS = [
    r"\b(issue|bug|glitch|error|broken|not\s+working|can't|cant|down|lag|crash|failing)\b",
    r"\b(complaining|everyone\s+asking|confusion|confused|problem|frustrated)\b"
]

SOLUTION_PATTERNS = [
    r"\b(fixed|resolved|solution|fix\s+is|patched|solved|workaround|guide\s+posted)\b",
    r"\b(how\s+to\s+fix|step\s+by\s+step|follow\s+these\s+steps)\b"
]

def score_message_importance(content: str, author_is_staff: bool = False, channel_name: str = "") -> Tuple[int, str]:
    """
    Evaluates message importance from 0 to 10 and identifies the primary entity category.
    0-4: Casual banter / greetings (bypass storage)
    5-7: Moderate community topics / questions / feedback
    8-10: Critical announcements, rule changes, staff decisions, major events
    """
    if not content:
        return 0, "CASUAL"

    clean = content.lower().strip()
    words = clean.split()
    word_count = len(words)

    # Fast bypass for tiny greetings and reactions
    if word_count <= 2 and clean in {"hi", "hello", "hey", "yo", "sup", "lol", "lmao", "gg", "nice", "ok", "cool", "ty", "thanks", "bye"}:
        return 0, "CASUAL"

    score = 1
    category = "TOPIC"

    # Channel-based priors
    ch_lower = channel_name.lower()
    if any(k in ch_lower for k in ["rule", "announcement", "faq", "update", "news", "official"]):
        score += 4
        category = "ANNOUNCEMENT"
    elif any(k in ch_lower for k in ["staff", "mod", "admin", "leadership"]):
        score += 3
        category = "DECISION"
    elif any(k in ch_lower for k in ["feedback", "bug", "report", "help", "support"]):
        score += 2
        category = "PROBLEM"

    # Staff author prior
    if author_is_staff:
        score += 2

    # Pattern matching (Problems & Solutions prioritized over general event mentions if conflict)
    if any(re.search(pat, clean) for pat in DECISION_PATTERNS):
        score += 4
        category = "DECISION"
    elif any(re.search(pat, clean) for pat in PROBLEM_PATTERNS):
        score += 3
        category = "PROBLEM"
    elif any(re.search(pat, clean) for pat in SOLUTION_PATTERNS):
        score += 3
        category = "SOLUTION"
    elif any(re.search(pat, clean) for pat in EVENT_PATTERNS):
        score += 3
        category = "EVENT"

    # Check for dates or times (temporal signals)
    if re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}(?:st|nd|rd|th)?\s+(?:am|pm|est|pst|gmt|utc))\b", clean):
        score += 1

    final_score = max(0, min(10, score))
    return final_score, category

# ==============================================================================
# 2. SERVER DNA SCANNER (FIRST 5 MINUTES & AUTOMATED PROFILING)
# ==============================================================================

def extract_server_dna(
    guild_id: int,
    guild_name: str,
    rules_text: str = "",
    announcements_text: str = "",
    channel_names: Optional[List[str]] = None,
    recent_sample_messages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyzes public server metadata, rules, announcements, and channel structures
    to generate the comprehensive SERVER DNA PROFILE.
    """
    ch_list = channel_names or []
    all_text = f"{rules_text}\n{announcements_text}\n" + "\n".join(ch_list) + "\n" + "\n".join(recent_sample_messages or [])
    clean_text = all_text.lower()

    # Detect Server Archetype
    gaming_kw = {"tournament", "scrim", "roster", "clan", "valorant", "minecraft", "roblox", "csgo", "apex", "fortnite", "gaming", "esports", "ranked"}
    tech_kw = {"github", "python", "code", "dev", "developer", "api", "programming", "docker", "ai", "machine learning", "linux", "backend"}
    anime_kw = {"anime", "manga", "genshin", "art", "fanart", "cosplay", "waifu", "chill", "lounge", "hangout"}
    community_kw = {"general", "chat", "memes", "media", "voice", "music", "events", "introductions"}

    gaming_matches = sum(1 for kw in gaming_kw if kw in clean_text)
    tech_matches = sum(1 for kw in tech_kw if kw in clean_text)
    anime_matches = sum(1 for kw in anime_kw if kw in clean_text)

    if gaming_matches >= 3:
        server_type = "Gaming & Esports Community"
        comm_style = "Casual, Competitive & Meme-Friendly"
        emoji_style = "High (Gaming & Hype Emojis)"
        formality = "Casual"
    elif tech_matches >= 3:
        server_type = "Developer & Tech Community"
        comm_style = "Technical, Collaborative & Concise"
        emoji_style = "Moderate (Tech & Status Icons)"
        formality = "Balanced"
    elif anime_matches >= 3:
        server_type = "Anime & Creative Hangout"
        comm_style = "Warm, Expressive & Wholesome"
        emoji_style = "Expressive (Kaomoji & Cute Emojis)"
        formality = "Chill"
    else:
        server_type = "General Social Community"
        comm_style = "Friendly, Casual & Welcoming"
        emoji_style = "Standard"
        formality = "Casual"

    # Extract Key Topics
    detected_topics = []
    if "tournament" in clean_text: detected_topics.append("Tournaments & Matches")
    if "giveaway" in clean_text: detected_topics.append("Community Giveaways")
    if "update" in clean_text or "patch" in clean_text: detected_topics.append("Game & Server Updates")
    if "scrim" in clean_text or "clan" in clean_text: detected_topics.append("Clans & Scrimmages")
    if "event" in clean_text: detected_topics.append("Community Events")
    if "art" in clean_text or "music" in clean_text: detected_topics.append("Creative Showcases")
    if not detected_topics:
        detected_topics = ["General Discussions", "Community Hangouts", "Voice Activities"]

    # Extract Important Rules
    extracted_rules = []
    if rules_text:
        lines = [l.strip() for l in rules_text.split("\n") if len(l.strip()) > 5]
        for line in lines[:5]:
            clean_rule = re.sub(r"^[\d\.\-\*\#\s]+", "", line).strip()
            if clean_rule:
                extracted_rules.append(clean_rule[:100])
    if not extracted_rules:
        extracted_rules = [
            "Be respectful and constructive with all community members.",
            "No spamming, advertising, or unsolicited direct messages.",
            "Keep discussions relevant to channel topics."
        ]

    confidence = min(98, max(75, 75 + len(detected_topics) * 4 + (5 if rules_text else 0)))

    dna = {
        "guild_id": guild_id,
        "guild_name": guild_name,
        "server_type": server_type,
        "communication_style": comm_style,
        "main_topics": detected_topics,
        "important_rules": extracted_rules,
        "emoji_style": emoji_style,
        "slang_vocabulary": ["gg", "clutch", "hype", "w", "vibe", "fr"] if "Gaming" in server_type else ["cool", "solid", "nice", "looks good"],
        "formality_level": formality,
        "confidence_pct": confidence,
        "scanned_channels": ch_list[:15],
        "last_scanned_at": time.time()
    }

    # Save to SQLite database
    save_server_dna(dna)
    return dna

def save_server_dna(dna: Dict[str, Any]):
    """Persists the Server DNA profile into SQLite."""
    with community_graph._lock:
        conn = community_graph._get_conn()
        conn.execute("""
            INSERT INTO server_dna (
                guild_id, server_type, communication_style, main_topics_json,
                important_rules_json, emoji_style, slang_vocabulary_json,
                formality_level, confidence_pct, scanned_channels_json, last_scanned_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                server_type = excluded.server_type,
                communication_style = excluded.communication_style,
                main_topics_json = excluded.main_topics_json,
                important_rules_json = excluded.important_rules_json,
                emoji_style = excluded.emoji_style,
                slang_vocabulary_json = excluded.slang_vocabulary_json,
                formality_level = excluded.formality_level,
                confidence_pct = excluded.confidence_pct,
                scanned_channels_json = excluded.scanned_channels_json,
                last_scanned_at = excluded.last_scanned_at
        """, (
            dna["guild_id"], dna["server_type"], dna["communication_style"],
            json.dumps(dna["main_topics"]), json.dumps(dna["important_rules"]),
            dna["emoji_style"], json.dumps(dna["slang_vocabulary"]),
            dna["formality_level"], dna["confidence_pct"],
            json.dumps(dna["scanned_channels"]), dna["last_scanned_at"]
        ))
        conn.commit()

def get_server_dna(guild_id: int) -> Dict[str, Any]:
    """Fetches the stored Server DNA profile or returns sensible default."""
    with community_graph._lock:
        row = community_graph._get_conn().execute("""
            SELECT server_type, communication_style, main_topics_json, important_rules_json,
                   emoji_style, slang_vocabulary_json, formality_level, confidence_pct,
                   scanned_channels_json, last_scanned_at
            FROM server_dna WHERE guild_id = ?
        """, (guild_id,)).fetchone()

    if not row:
        return {
            "guild_id": guild_id,
            "server_type": "General Community",
            "communication_style": "Casual & Friendly",
            "main_topics": ["General Discussions", "Events", "Gaming"],
            "important_rules": ["Be respectful", "No spam", "Keep topics relevant"],
            "emoji_style": "Moderate",
            "slang_vocabulary": ["gg", "hype", "w", "vibe"],
            "formality_level": "Casual",
            "confidence_pct": 80,
            "scanned_channels": [],
            "last_scanned_at": time.time()
        }

    return {
        "guild_id": guild_id,
        "server_type": row[0],
        "communication_style": row[1],
        "main_topics": json.loads(row[2]),
        "important_rules": json.loads(row[3]),
        "emoji_style": row[4],
        "slang_vocabulary": json.loads(row[5]),
        "formality_level": row[6],
        "confidence_pct": row[7],
        "scanned_channels": json.loads(row[8]),
        "last_scanned_at": row[9]
    }

# ==============================================================================
# 3. ASYNCHRONOUS MEMORY EXTRACTION PIPELINE
# ==============================================================================

async def process_incoming_message_for_memory(
    guild_id: int,
    channel_id: int,
    channel_name: str,
    message_id: int,
    author_id: int,
    author_name: str,
    author_is_staff: bool,
    content: str
):
    """
    Evaluates ambient messages in real-time, extracts high-importance entities (score >= 5),
    resolves temporal links, and updates the community memory graph.
    """
    if not content or len(content.strip()) < 8:
        return

    score, category = score_message_importance(content, author_is_staff=author_is_staff, channel_name=channel_name)
    if score < 5:
        return  # Filter out trivial banter

    # Extract clean title/name for the entity
    words = content.strip().split()
    name_snippet = " ".join(words[:6])
    if len(name_snippet) > 50:
        name_snippet = name_snippet[:50] + "..."

    # Check for temporal updates (e.g. rescheduled event or modified rule)
    if category in {"EVENT", "RULE", "DECISION"}:
        # Check if an existing node shares keywords
        subgraph = community_graph.query_subgraph(guild_id, entity_type=category, status="active", limit=10)
        for existing in subgraph["nodes"]:
            # If significant keyword overlap exists, mark previous node as superseded
            ex_words = set(existing["name"].lower().split())
            new_words = set(name_snippet.lower().split())
            overlap = ex_words.intersection(new_words)
            if len(overlap) >= 2 and existing["id"]:
                new_node_id = community_graph.add_or_update_node(
                    guild_id=guild_id,
                    entity_type=category,
                    name=name_snippet,
                    summary=content.strip(),
                    source_channel_id=channel_id,
                    source_message_id=message_id,
                    author_id=author_id,
                    importance_score=score
                )
                community_graph.supersede_node(
                    guild_id=guild_id,
                    old_node_id=existing["id"],
                    new_node_id=new_node_id,
                    reason=f"Updated via message from {author_name}"
                )
                logger.info(f"🧠 [COMMUNITY BRAIN] Superseded {existing['name']} with new {category} #{new_node_id}")
                return

    # Add standard active node
    node_id = community_graph.add_or_update_node(
        guild_id=guild_id,
        entity_type=category,
        name=name_snippet,
        summary=content.strip(),
        source_channel_id=channel_id,
        source_message_id=message_id,
        author_id=author_id,
        importance_score=score
    )

    # If it's a staff decision or solution, link author
    if author_is_staff or category in {"DECISION", "SOLUTION"}:
        record_member_contribution(guild_id, author_id, author_name, "helper" if category == "SOLUTION" else "active_contributor")

    logger.debug(f"🧠 [COMMUNITY BRAIN] Indexed {category} node #{node_id} (Score: {score}/10): '{name_snippet}'")

# ==============================================================================
# 4. PRIVACY-SAFE MEMBER INTELLIGENCE
# ==============================================================================

def record_member_contribution(guild_id: int, user_id: int, username: str, contribution_type: str = "helper"):
    """
    Safely records member helpfulness and community leadership metrics without logging private chats.
    """
    now = time.time()
    with community_graph._lock:
        conn = community_graph._get_conn()
        conn.execute("""
            INSERT INTO member_intelligence (guild_id, user_id, username, contribution_type, helpful_actions_count, last_active_at)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                username = excluded.username,
                helpful_actions_count = member_intelligence.helpful_actions_count + 1,
                last_active_at = excluded.last_active_at
        """, (guild_id, user_id, username, contribution_type, now))
        conn.commit()

def get_top_community_contributors(guild_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches top helpful community members and knowledge anchors."""
    with community_graph._lock:
        cursor = community_graph._get_conn().execute("""
            SELECT user_id, username, contribution_type, helpful_actions_count, last_active_at
            FROM member_intelligence
            WHERE guild_id = ?
            ORDER BY helpful_actions_count DESC LIMIT ?
        """, (guild_id, limit))
        
        results = []
        for r in cursor.fetchall():
            results.append({
                "user_id": r[0],
                "username": r[1],
                "contribution_type": r[2],
                "helpful_actions": r[3],
                "last_active_at": r[4]
            })
        return results

# ==============================================================================
# 5. HYBRID BRAIN REASONING ENGINE (GRAPH + VECTOR + CONTEXT)
# ==============================================================================

def query_community_brain_unified(guild_id: int, query: str) -> Dict[str, Any]:
    """
    Executes a comprehensive multi-layered brain search:
    1. Graph memory & causal connections
    2. Vector / Keyword knowledge base entries
    3. Server DNA profile
    4. Recent community discussion context
    """
    # 1. Graph lookup & causal path
    causal_chain = community_graph.trace_causal_path(guild_id, query)
    temporal_history = community_graph.get_temporal_history(guild_id, query)
    subgraph = community_graph.query_subgraph(guild_id, limit=15)

    # 2. Knowledge base RAG lookup
    kb_results = knowledge_base.search_knowledge_entries(guild_id, query, limit=3)

    # 3. Server DNA profile
    dna = get_server_dna(guild_id)

    # 4. Activity stats & recent topics
    stats = collector.get_guild_activity_stats(guild_id, hours=48.0)

    return {
        "query": query,
        "server_dna": dna,
        "causal_chain": causal_chain,
        "temporal_history": temporal_history,
        "knowledge_entries": kb_results,
        "graph_summary": {
            "total_nodes": len(subgraph["nodes"]),
            "total_edges": len(subgraph["edges"])
        },
        "community_stats": {
            "messages_48h": stats.get("total_messages", 0),
            "active_chatters": stats.get("active_chatters", 0),
            "top_keywords": stats.get("top_keywords", [])
        }
    }

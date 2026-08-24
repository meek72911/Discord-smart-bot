"""
Unit tests for Smart Bot OS v5.0 — Community Brain Evolution Platform
Tests Community Graph, Importance Scoring, Temporal Memory, Server DNA,
Community Analyst Health Scoring, and Community Brain Tools.
"""

import pytest
import time
import community_graph
import community_brain
import community_analyst
import tools

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Isolate DB for testing."""
    pass

def test_graph_nodes_and_edges():
    guild_id = 112233
    
    # 1. Create Problem Node
    prob_id = community_graph.add_or_update_node(
        guild_id=guild_id,
        entity_type="PROBLEM",
        name="Game Server Outage",
        summary="Riot scheduled server maintenance on August 20.",
        importance_score=8
    )
    assert prob_id > 0

    # 2. Create Decision Node
    dec_id = community_graph.add_or_update_node(
        guild_id=guild_id,
        entity_type="DECISION",
        name="Move Tournament Date",
        summary="Staff voted to move tournament to August 25 to avoid outage.",
        importance_score=9
    )
    assert dec_id > 0

    # 3. Link them with causal edge
    edge_id = community_graph.add_edge(
        guild_id=guild_id,
        source_node_id=prob_id,
        target_node_id=dec_id,
        relation_type="caused_by",
        evidence="Discussion in #staff-room"
    )
    assert edge_id > 0

    # 4. Trace Causal Path
    causal = community_graph.trace_causal_path(guild_id, "Move Tournament Date")
    assert len(causal) >= 2
    assert causal[0]["name"] == "Move Tournament Date"

def test_temporal_memory_superseding():
    guild_id = int(time.time() * 1000) % 10000000 + 400000

    # 1. Old Announcement
    old_id = community_graph.add_or_update_node(
        guild_id=guild_id,
        entity_type="EVENT",
        name="Valorant Tournament Aug 20",
        summary="Tournament begins August 20 at 5pm.",
        importance_score=8
    )

    # 2. New Announcement
    new_id = community_graph.add_or_update_node(
        guild_id=guild_id,
        entity_type="EVENT",
        name="Valorant Tournament Aug 25",
        summary="Tournament rescheduled to August 25 at 6pm.",
        importance_score=9
    )

    # 3. Supersede old event
    success = community_graph.supersede_node(
        guild_id=guild_id,
        old_node_id=old_id,
        new_node_id=new_id,
        reason="Postponed due to game patch"
    )
    assert success is True

    # 4. Verify old node status
    old_node = community_graph.get_node(guild_id, old_id)
    assert old_node["status"] == "superseded"
    assert old_node["superseded_by_id"] == new_id

    # 5. Check Temporal History
    timeline = community_graph.get_temporal_history(guild_id, "Valorant Tournament")
    assert len(timeline) == 2
    assert timeline[0]["status"] == "superseded"
    assert timeline[1]["status"] == "active"

def test_importance_scoring():
    # Casual greeting -> score 0
    score1, cat1 = community_brain.score_message_importance("hi everyone")
    assert score1 <= 2

    # High-signal staff announcement -> score 8-10
    score2, cat2 = community_brain.score_message_importance(
        "Staff decided to change tournament rules and prize pool to $500",
        author_is_staff=True,
        channel_name="announcements"
    )
    assert score2 >= 8
    assert cat2 in {"DECISION", "ANNOUNCEMENT"}

    # Bug report -> score 5-7
    score3, cat3 = community_brain.score_message_importance(
        "Members complaining about registration broken not working",
        channel_name="bug-reports"
    )
    assert score3 >= 5
    assert cat3 == "PROBLEM"

def test_server_dna_extraction():
    guild_id = int(time.time() * 1000) % 10000000 + 700000
    dna = community_brain.extract_server_dna(
        guild_id=guild_id,
        guild_name="Valorant Champions Elite",
        rules_text="1. Respect everyone - no toxicity\n2. English only in chat\n3. No spam",
        announcements_text="Tournament matches start this Saturday! Register with your clan.",
        channel_names=["general", "tournaments", "scrims", "clips", "rules", "announcements"]
    )

    assert "Gaming" in dna["server_type"] or "Esports" in dna["server_type"]
    assert "Tournaments & Matches" in dna["main_topics"]
    assert len(dna["important_rules"]) >= 2
    assert dna["confidence_pct"] >= 80

def test_community_health_score():
    guild_id = int(time.time() * 1000) % 10000000 + 100000
    health = community_analyst.calculate_community_health_score(guild_id)
    
    assert 0 <= health["health_score"] <= 100
    assert "metrics" in health
    assert "engagement" in health["metrics"]
    assert len(health["recommendations"]) >= 1

def test_member_intelligence():
    guild_id = int(time.time() * 1000) % 10000000 + 900000
    community_brain.record_member_contribution(guild_id, 101, "HelperHero", "helper")
    community_brain.record_member_contribution(guild_id, 101, "HelperHero", "helper")
    
    contributors = community_brain.get_top_community_contributors(guild_id, limit=3)
    assert len(contributors) >= 1
    assert contributors[0]["username"] == "HelperHero"
    assert contributors[0]["helpful_actions"] >= 2

@pytest.mark.asyncio
async def test_tools_community_brain(monkeypatch):
    guild_id = int(time.time() * 1000) % 10000000 + 500000
    
    class DummyChannel:
        id = 111
        name = "general"
    
    class DummyGuild:
        id = guild_id
        name = "Test Community Server"
        text_channels = [DummyChannel()]
    
    token = tools.current_guild.set(DummyGuild())
    try:
        # Index a problem & decision
        p_id = community_graph.add_or_update_node(guild_id, "PROBLEM", "Bot Delay", "Audio packets were lagging", importance_score=7)
        d_id = community_graph.add_or_update_node(guild_id, "DECISION", "Fast Route", "Switched to local CPU inference", importance_score=8)
        community_graph.add_edge(guild_id, p_id, d_id, "fixed", "Resolved in patch")

        # Test ask_community_brain
        brain_out = await tools.ask_community_brain("Bot Delay")
        assert "COMMUNITY BRAIN" in brain_out
        assert "Bot Delay" in brain_out

        # Test query_memory_graph
        graph_out = await tools.query_memory_graph(query="Bot Delay")
        assert "Memory Graph Causal Trace" in graph_out

        # Test get_community_health_score
        health_out = await tools.get_community_health_score()
        assert "COMMUNITY HEALTH EVALUATION" in health_out
        assert "/100" in health_out

        # Test scan_server_dna
        dna_out = await tools.scan_server_dna()
        assert "SERVER DNA" in dna_out

        # Test manage_memory_privacy
        audit_out = await tools.manage_memory_privacy(action="view")
        assert "COMMUNITY MEMORY AUDIT" in audit_out

    finally:
        tools.current_guild.reset(token)

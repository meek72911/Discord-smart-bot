"""
Unit & Integration Tests for Collector v2.1 Community Intelligence Engine
Tests Observation Layer, Topic Surge Promotion, Confidence Scoring,
Canonical Topic Clustering, Culture Extraction, Expiration & Thread Safety.
"""

import time
import asyncio
import pytest
import collector

def setup_function():
    """Reset collector state before each test."""
    with collector._LOCK:
        collector._GUILD_STAGES.clear()
        collector._TOPIC_PULSE.clear()
        collector._CULTURE_TRACKER.clear()
        collector._DEDUP_CACHE.clear()
        collector._STATS["messages_scanned"] = 0
        collector._STATS["messages_filtered"] = 0
        collector._STATS["messages_stored"] = 0
        collector._STATS["important_detected"] = 0
        collector._STATS["memories_created"] = 0
        collector._STATS["surges_promoted"] = 0
        collector._STATS["duplicates_blocked"] = 0

def test_noise_filter():
    # 1. Single word reactions should be dropped
    assert collector.is_noise_message("lol")[0] is True
    assert collector.is_noise_message("gg")[0] is True
    assert collector.is_noise_message("ok")[0] is True
    assert collector.is_noise_message("hello")[0] is True

    # 2. Bot command prefixes should be dropped
    assert collector.is_noise_message("!rank")[0] is True
    assert collector.is_noise_message("?help")[0] is True
    assert collector.is_noise_message("-play")[0] is True

    # 3. Repeated character/syllable spam should be dropped
    assert collector.is_noise_message("aaaaaaaaaa")[0] is True
    assert collector.is_noise_message("lololololol")[0] is True
    assert collector.is_noise_message("hahahahahaha")[0] is True

    # 4. Valid discussion messages should pass
    is_noise, reason = collector.is_noise_message("Why did tournament rules change?")
    assert is_noise is False

def test_topic_clustering_normalization():
    # Morphological variations should resolve to canonical cluster
    assert collector.identify_topic_cluster("Game is crashing on startup") == "game_crash_stability"
    assert collector.identify_topic_cluster("I experienced a fatal freeze and crash") == "game_crash_stability"
    assert collector.identify_topic_cluster("Cannot log in to my account 2fa issue") == "auth_login_issues"
    assert collector.identify_topic_cluster("When is the 5v5 tournament bracket announced?") == "tournament_esports"
    assert collector.identify_topic_cluster("Why is my ping lagging with packet loss?") == "network_latency_lag"

def test_context_aware_scoring_and_confidence():
    # Case A: False-Positive Meta Question -> Low score, dampened confidence
    score_a, conf_a, stage_a, cluster_a, _ = collector.calculate_importance_and_confidence(
        content="Anyone know what tournament means?",
        author_is_staff=False,
        channel_name="general"
    )
    assert score_a <= 3
    assert conf_a <= 50
    assert stage_a == "TEMPORARY"

    # Case B: Staff Declarative Announcement -> High score, >= 90% confidence, PERMANENT stage
    score_b, conf_b, stage_b, cluster_b, _ = collector.calculate_importance_and_confidence(
        content="Official tournament date rescheduled to August 25 with $1000 prize pool",
        author_is_staff=True,
        channel_name="announcements",
        reaction_count=8
    )
    assert score_b >= 8
    assert conf_b >= 90
    assert stage_b == "PERMANENT"

def test_observation_layer_and_surge_promotion():
    guild_id = 999333

    # User 1 reports login problem (initially enters TEMPORARY observation layer)
    msg1 = collector.record_message(guild_id, 1, 101, "User1", "Anyone else having login issues?", channel_name="general")
    assert msg1["stage"] == "TEMPORARY"

    with collector._LOCK:
        assert len(collector._GUILD_STAGES[guild_id]["TEMPORARY"]) == 1
        assert len(collector._GUILD_STAGES[guild_id]["ACTIVE"]) == 0

    # 3 more users report same login issue within 30 minutes -> triggers SURGE PROMOTION!
    collector.record_message(guild_id, 1, 102, "User2", "Cannot log in, 2fa verification failing", channel_name="general")
    collector.record_message(guild_id, 1, 103, "User3", "Yeah login is completely broken for me too", channel_name="general")
    collector.record_message(guild_id, 1, 104, "User4", "Auth server down, cant login", channel_name="general")

    # Verify that all 4 messages were promoted to ACTIVE memory!
    with collector._LOCK:
        assert len(collector._GUILD_STAGES[guild_id]["ACTIVE"]) >= 3
        # Check health stats
        health = collector.get_collector_health()
        assert health["surges_promoted"] >= 1

def test_server_culture_extraction():
    guild_id = 555666

    # Server A: Meme & Slang heavy
    collector.record_message(guild_id, 1, 1, "Gamer", "fr no cap that was a hype clutch bro ez", channel_name="general")
    collector.record_message(guild_id, 1, 2, "Gamer2", "ong based gameplay w play", channel_name="general")

    profile = collector.get_server_culture_profile(guild_id)
    assert "High-Energy" in profile["communication_style"] or "Casual" in profile["communication_style"]
    assert profile["formality_score"] <= 50

def test_expiration_garbage_collector():
    guild_id = 888222
    now = time.time()

    # Ingest a TEMPORARY observation message from 60 minutes ago (> 45m threshold)
    collector.record_message(guild_id, 1, 10, "Casual", "anyone playing casual?", channel_name="general")
    with collector._LOCK:
        collector._GUILD_STAGES[guild_id]["TEMPORARY"][0]["timestamp"] = now - (60 * 60)

    # Ingest a PERMANENT announcement from 20 hours ago (< 72h threshold)
    collector.record_message(
        guild_id, 2, 1, "Admin",
        "Official policy updated for tournament verification",
        channel_name="rules",
        author_is_staff=True
    )
    with collector._LOCK:
        collector._GUILD_STAGES[guild_id]["PERMANENT"][0]["timestamp"] = now - (20 * 3600)

    # Run Pruning
    pruned = collector.prune_expired_messages(guild_id)
    assert pruned == 1  # 60m TEMPORARY message pruned, 20h PERMANENT retained

    with collector._LOCK:
        assert len(collector._GUILD_STAGES[guild_id]["TEMPORARY"]) == 0
        assert len(collector._GUILD_STAGES[guild_id]["PERMANENT"]) == 1

@pytest.mark.asyncio
async def test_non_blocking_async_analytics():
    guild_id = 777333
    for i in range(10):
        collector.record_message(
            guild_id=guild_id,
            channel_id=1,
            author_id=100 + i,
            author_name=f"User{i}",
            content=f"Question {i}: Why is the audio quality buffering?",
            channel_name="support"
        )

    stats = await collector.get_guild_activity_stats_async(guild_id)
    assert stats["total_messages"] == 10
    assert stats["active_chatters"] == 10

    context = await collector.get_compressed_community_context_async(guild_id, max_messages=5)
    assert "GUILD ACTIVITY OVER PAST" in context
    assert "User0" in context

"""
Unit tests for Smart Bot v4.2 Community Intelligence Platform
Tests collector buffer aggregation and knowledge base RAG lookup.
"""

import pytest
import collector
import knowledge_base

def test_collector_buffering():
    guild_id = 999999
    ch_id = 111111

    # Record sample messages
    collector.record_message(guild_id, ch_id, 101, "Alice", "When does the tournament start?")
    collector.record_message(guild_id, ch_id, 102, "Bob", "I think the tournament is on Saturday at 5pm.")
    collector.record_message(guild_id, ch_id, 103, "Charlie", "Are there any prizes for the tournament?")

    stats = collector.get_guild_activity_stats(guild_id, hours=1.0)
    assert stats["total_messages"] == 3
    assert stats["active_chatters"] == 3
    assert len(stats["sample_questions"]) >= 2

    # Check keyword extraction
    keywords = [kw for kw, _ in stats["top_keywords"]]
    assert "tournament" in keywords

    # Check compressed context output
    context = collector.get_compressed_community_context(guild_id, hours=1.0)
    assert "Alice" in context
    assert "tournament" in context

def test_knowledge_base_indexing_and_search():
    guild_id = 888888
    
    # Add rules and announcement
    id1 = knowledge_base.add_knowledge_entry(
        guild_id=guild_id,
        category="RULE",
        title="Rule 1: Be Respectful",
        content="No harassment, hate speech, or toxicity allowed in any channel.",
        author_name="Owner"
    )
    assert id1 > 0

    id2 = knowledge_base.add_knowledge_entry(
        guild_id=guild_id,
        category="ANNOUNCEMENT",
        title="Grand Valorant Tournament",
        content="The tournament takes place on Saturday with a $500 prize pool.",
        author_name="TournamentHost"
    )
    assert id2 > 0

    # Search knowledge
    results = knowledge_base.search_knowledge_entries(guild_id, "tournament prize")
    assert len(results) >= 1
    assert "Grand Valorant Tournament" in results[0]["title"]
    assert "$500" in results[0]["content"]

    # Delete entry
    deleted = knowledge_base.delete_knowledge_entry(guild_id, id2)
    assert deleted is True

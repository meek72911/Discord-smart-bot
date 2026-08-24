"""
Unit and Integration Tests for Smart Bot OS Beta Launch Backend Architecture.
"""

import pytest
from backend import database
from backend.api import auth, dashboard, owner
from backend import main as backend_router


def test_database_beta_tables():
    """Verify all 6 Beta Launch tables can be created, written to, and queried."""
    # 1. Users
    user = database.upsert_user(
        discord_id="1234567890",
        username="BetaTester",
        avatar="avatar_hash",
        is_owner=False
    )
    assert user["discord_id"] == "1234567890"
    assert user["username"] == "BetaTester"
    assert not user["is_owner"]

    # 2. Servers
    database.upsert_server(
        guild_id=99901,
        name="Beta Test Server",
        member_count=5400,
        plan="Free Beta",
        health_score=91
    )
    server = database.get_server_by_id(99901)
    assert server is not None
    assert server["name"] == "Beta Test Server"
    assert server["health_score"] == 91

    # 3. Server Memory
    m_id = database.add_server_memory(
        guild_id=99901,
        mem_type="RULE",
        content="No spoilers in main chat",
        summary="Community spoiler prevention policy",
        confidence=0.96
    )
    assert m_id > 0
    memories = database.get_server_memories(99901)
    assert len(memories) >= 1
    assert memories[0]["type"] == "RULE"

    # 4. Reports
    r_id = database.save_report(
        server_id=99901,
        report_data={"health": 91, "summary": "Healthy test community"},
        date_str="2026-08-24"
    )
    assert r_id > 0
    reports = database.get_reports_by_server(99901)
    assert len(reports) >= 1
    assert reports[0]["report_data"]["health"] == 91

    # 5. Feedback & Voting
    f_id = database.submit_feedback(
        user_id="1234567890",
        server_id=99901,
        author_name="BetaTester",
        suggestion="Add custom reaction roles",
        category="roles"
    )
    assert f_id > 0
    new_votes = database.upvote_feedback(f_id)
    assert new_votes == 2

    # 6. Telemetry Events
    database.log_event(
        server_id=99901,
        feature_used="ask_community_brain",
        metadata={"query": "when is tournament"}
    )
    events = database.get_recent_events(limit=5)
    assert len(events) >= 1
    assert events[0]["feature_used"] == "ask_community_brain"


def test_auth_permission_evaluation():
    """Verify Discord Administrator (0x8) and Manage Guild (0x20) permission evaluations."""
    # Admin guild
    admin_guild = {"id": "1001", "name": "Admin Guild", "owner": False, "permissions": "8"}
    assert auth.is_user_admin_of_guild(admin_guild) is True

    # Manage Guild
    manage_guild = {"id": "1002", "name": "Manage Guild", "owner": False, "permissions": "32"}
    assert auth.is_user_admin_of_guild(manage_guild) is True

    # Owner guild
    owner_guild = {"id": "1003", "name": "Owned Guild", "owner": True, "permissions": "0"}
    assert auth.is_user_admin_of_guild(owner_guild) is True

    # Non-admin regular member
    regular_guild = {"id": "1004", "name": "General Guild", "owner": False, "permissions": "1049600"}
    assert auth.is_user_admin_of_guild(regular_guild) is False


def test_auth_mock_and_session_flow():
    """Verify session creation, token retrieval, and role isolation."""
    # Server admin mock session
    admin_session = auth.create_mock_session(role="admin", guild_id=99901)
    assert "token" in admin_session
    assert not admin_session["is_owner"]
    assert len(admin_session["guilds"]) == 1

    # Verify session lookup
    stored = auth.get_session(admin_session["token"])
    assert stored is not None
    assert stored["user"]["username"] == "ServerAdmin_Alex"

    # Owner mock session
    owner_session = auth.create_mock_session(role="owner")
    assert owner_session["is_owner"] is True


def test_customer_dashboard_apis():
    """Verify Overview, Memory, Reports, and Feedback dashboard APIs."""
    # Overview
    overview = dashboard.get_dashboard_overview(99901)
    assert "community_score" in overview
    assert "messages_analyzed" in overview
    assert "important_memories_count" in overview

    # Memories
    memories = dashboard.get_dashboard_memories(99901)
    assert len(memories) >= 1

    # Reports
    reports = dashboard.get_dashboard_reports(99901)
    assert len(reports) >= 1
    assert "summary" in reports[0]["report_data"]

    # Feedback
    feedback = dashboard.list_dashboard_feedback(99901)
    assert len(feedback) >= 1


def test_owner_panel_apis():
    """Verify Owner fleet overview, server drilldown, and AI product improvement telemetry."""
    # Fleet overview
    fleet = owner.get_owner_fleet_overview()
    assert "global_kpis" in fleet
    assert "fleet" in fleet
    assert len(fleet["fleet"]) >= 1

    # Server intelligence drilldown
    drilldown = owner.get_owner_server_intelligence(99901)
    assert "health_score" in drilldown
    assert "top_user_questions" in drilldown
    assert "feature_usage" in drilldown

    # AI product improvements
    improvements = owner.get_ai_product_improvements()
    assert len(improvements) >= 1
    assert "demand_signal" in improvements[0]


def test_backend_router_dispatch():
    """Verify unified REST router dispatches GET and POST requests accurately."""
    # 1. GET /api/auth/url
    code, data = backend_router.handle_api_request("GET", "/api/auth/url", {})
    assert code == 200
    assert "url" in data
    assert "discord.com" in data["url"]

    # 2. GET /api/dashboard/overview
    code, data = backend_router.handle_api_request("GET", "/api/dashboard/overview", {"guild_id": ["99901"]})
    assert code == 200
    assert data["guild_id"] == 99901

    # 3. POST /api/dashboard/feedback
    payload = {
        "user_id": "tester_1",
        "server_id": 99901,
        "author_name": "API_Tester",
        "suggestion": "Add dark mode toggle for reports",
        "category": "ui"
    }
    code, data = backend_router.handle_api_request("POST", "/api/dashboard/feedback", {}, body_json=payload)
    assert code == 200
    assert data["success"] is True

    # 4. GET /api/owner/fleet
    code, data = backend_router.handle_api_request("GET", "/api/owner/fleet", {})
    assert code == 200
    assert "global_kpis" in data

    # 5. GET 404 handler
    code, data = backend_router.handle_api_request("GET", "/api/invalid/path", {})
    assert code == 404

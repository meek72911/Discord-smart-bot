"""
Smart Bot OS — Backend Router & Gateway
Dispatches incoming REST API requests to auth, dashboard, and owner modules.
"""

import json
import urllib.parse
from typing import Dict, Any, Tuple, Optional, List
from backend.api import auth, dashboard, owner
from backend import database


def handle_api_request(method: str, path: str, query: Dict[str, list], body_json: Optional[Dict[str, Any]] = None, auth_header: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
    """
    Unified router handling both standard HTTP requests and FastAPI endpoints.
    """
    # --------------------------------------------------------------------------
    # 1. AUTH ROUTES
    # --------------------------------------------------------------------------
    if path == "/api/auth/url":
        return 200, {"url": auth.get_discord_oauth_url()}

    elif path == "/api/auth/mock-login":
        role = query.get("role", ["admin"])[0]
        gid_str = query.get("guild_id", ["112233"])[0]
        gid = int(gid_str) if gid_str.isdigit() else 112233
        session = auth.create_mock_session(role=role, guild_id=gid)
        return 200, session

    elif path == "/api/auth/me":
        token = auth_header or query.get("token", [None])[0]
        if token:
            session = auth.get_session(token)
            if session:
                return 200, session
        return 401, {"error": "Unauthorized. Please login with Discord."}

    # --------------------------------------------------------------------------
    # 2. CUSTOMER DASHBOARD ROUTES
    # --------------------------------------------------------------------------
    elif path == "/api/dashboard/overview":
        gid_str = query.get("guild_id", ["112233"])[0]
        gid = int(gid_str) if gid_str.isdigit() else 112233
        return 200, dashboard.get_dashboard_overview(gid)

    elif path == "/api/dashboard/memory":
        gid_str = query.get("guild_id", ["112233"])[0]
        gid = int(gid_str) if gid_str.isdigit() else 112233
        mem_type = query.get("type", [None])[0]
        return 200, {"memories": dashboard.get_dashboard_memories(gid, mem_type)}

    elif path == "/api/dashboard/reports":
        gid_str = query.get("guild_id", ["112233"])[0]
        gid = int(gid_str) if gid_str.isdigit() else 112233
        return 200, {"reports": dashboard.get_dashboard_reports(gid)}

    elif path == "/api/dashboard/feedback":
        if method == "POST" and body_json:
            user_id = body_json.get("user_id", "guest")
            server_id = int(body_json.get("server_id", 112233))
            author_name = body_json.get("author_name", "Member")
            suggestion = body_json.get("suggestion", "")
            category = body_json.get("category", "general")
            res = dashboard.submit_dashboard_feedback(user_id, server_id, author_name, suggestion, category)
            return 200, res
        else:
            gid_str = query.get("server_id", [None])[0]
            gid = int(gid_str) if gid_str and gid_str.isdigit() else None
            return 200, {"feedback": dashboard.list_dashboard_feedback(gid)}

    elif path == "/api/dashboard/feedback/upvote":
        fid_str = query.get("id", [None])[0]
        if fid_str and fid_str.isdigit():
            new_votes = database.upvote_feedback(int(fid_str))
            return 200, {"success": True, "votes": new_votes}
        return 400, {"error": "Missing or invalid feedback id"}

    # --------------------------------------------------------------------------
    # 3. OWNER / SUPERADMIN ROUTES
    # --------------------------------------------------------------------------
    elif path == "/api/owner/fleet":
        return 200, owner.get_owner_fleet_overview()

    elif path.startswith("/api/owner/server/"):
        parts = path.strip("/").split("/")
        if len(parts) >= 4 and parts[3].isdigit():
            gid = int(parts[3])
            return 200, owner.get_owner_server_intelligence(gid)
        return 400, {"error": "Invalid server guild_id in path"}

    elif path == "/api/owner/improvements":
        return 200, {"improvements": owner.get_ai_product_improvements()}

    return 404, {"error": f"Endpoint '{path}' not found."}

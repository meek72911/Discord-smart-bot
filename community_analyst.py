"""
Smart Bot OS v5.0 — Community Analyst & Health Score Engine
Calculates the AI Community Health Score (0-100), detects recurring friction points,
tracks engagement trends, and generates executive community intelligence reports.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import collector
import community_graph
import community_brain
import knowledge_base

logger = logging.getLogger("community_analyst")

def calculate_community_health_score(guild_id: int, guild: Optional[Any] = None) -> Dict[str, Any]:
    """
    Computes the 0-100 AI Community Health Score using weighted multi-dimensional metrics
    calibrated to server lifecycle stage (Seed/Incubation vs Scaling vs Mega Server):
    - Engagement & Activity (25%)
    - Staff Presence & Response Health (20%)
    - Confusion & Friction Radar (20%)
    - Knowledge Base & Rule Grounding (15%)
    - Member Growth & Retention Signals (20%)
    """
    # 0. Extract Server Lifecycle & Demographic Metadata
    human_members = 0
    bot_members = 0
    total_members = 0
    server_age_days = None
    stage = "Established Community"
    stage_badge = "🌳"

    if guild is not None:
        try:
            members = getattr(guild, "members", [])
            total_members = getattr(guild, "member_count", len(members)) or len(members)
            if members:
                human_members = len([m for m in members if not getattr(m, "bot", False)])
                bot_members = len([m for m in members if getattr(m, "bot", False)])
            else:
                human_members = total_members

            created_at = getattr(guild, "created_at", None)
            if created_at is not None:
                # Handle offset-aware or naive datetimes
                ts = created_at.timestamp() if hasattr(created_at, "timestamp") else time.time()
                server_age_days = max(0, round((time.time() - ts) / 86400, 1))
        except Exception as e:
            logger.warning(f"Failed extracting guild demographics: {e}")

    # Determine Lifecycle Stage
    is_seed_stage = False
    if (server_age_days is not None and server_age_days <= 14) or (0 < human_members <= 10):
        is_seed_stage = True
        stage = "Incubation / Seed Phase"
        stage_badge = "🌱"
    elif 10 < human_members <= 50:
        stage = "Emerging Community"
        stage_badge = "🌿"
    elif human_members > 500:
        stage = "Mega Community"
        stage_badge = "🏰"

    # 1. Gather ambient activity metrics (last 48 hours)
    stats = collector.get_guild_activity_stats(guild_id, hours=48.0)
    total_msgs = stats.get("total_messages", 0)
    active_chatters = stats.get("active_chatters", 0)
    questions = stats.get("sample_questions", [])
    
    # 2. Gather brain graph & knowledge coverage
    subgraph = community_graph.query_subgraph(guild_id, status="all", limit=50)
    active_nodes = [n for n in subgraph["nodes"] if n["status"] == "active"]
    problems = [n for n in subgraph["nodes"] if n["entity_type"] == "PROBLEM"]
    solutions = [n for n in subgraph["nodes"] if n["entity_type"] == "SOLUTION"]
    decisions = [n for n in subgraph["nodes"] if n["entity_type"] == "DECISION"]
    
    dna = community_brain.get_server_dna(guild_id)
    top_contributors = community_brain.get_top_community_contributors(guild_id, limit=3)

    # 3. Component Scoring (Normalized for Server Stage)

    # A. Engagement Score (0-25)
    if is_seed_stage:
        # Seed servers are evaluated on founding conversation activation
        if active_chatters >= 2 or total_msgs >= 5:
            engagement_score = 22
        elif total_msgs >= 1:
            engagement_score = 18
        else:
            engagement_score = 15
    else:
        if active_chatters >= 20 or total_msgs >= 200:
            engagement_score = 25
        elif active_chatters >= 5 or total_msgs >= 50:
            engagement_score = 20
        elif total_msgs > 5:
            engagement_score = 15
        else:
            engagement_score = 10

    # B. Staff & Decision Health (0-20)
    if len(decisions) >= 3 or len(solutions) >= 2:
        staff_score = 20
    elif len(decisions) >= 1 or len(top_contributors) >= 1 or is_seed_stage:
        staff_score = 18 if is_seed_stage else 16
    else:
        staff_score = 12

    # C. Friction / Confusion Radar (0-20)
    friction_penalty = min(10, len(problems) * 2)
    friction_score = max(5, 20 - friction_penalty)

    # D. Knowledge & Rule Coverage (0-15)
    kb_entries = len(dna.get("important_rules", [])) + len(active_nodes)
    if kb_entries >= 10:
        knowledge_score = 15
    elif kb_entries >= 4 or (is_seed_stage and kb_entries >= 1):
        knowledge_score = 13 if is_seed_stage else 12
    else:
        knowledge_score = 9 if is_seed_stage else 8

    # E. Community Growth & Vibe (0-20)
    growth_score = 19 if (dna.get("confidence_pct", 80) >= 85 or is_seed_stage) else 14

    total_score = engagement_score + staff_score + friction_score + knowledge_score + growth_score
    total_score = max(10, min(100, total_score))

    # Grade determination
    if is_seed_stage:
        if total_score >= 80: grade = "A (Healthy Incubation Setup)"
        elif total_score >= 65: grade = "B (Clean Early Foundation)"
        else: grade = "C (Needs Founding Structure)"
    else:
        if total_score >= 90: grade = "A+ (Thriving & Healthy)"
        elif total_score >= 80: grade = "A (Strong & Active)"
        elif total_score >= 70: grade = "B (Good with Minor Friction)"
        elif total_score >= 50: grade = "C (Needs Moderation Attention)"
        else: grade = "D (High Friction & Inactive)"

    # Identify Key Strengths
    strengths = []
    if is_seed_stage:
        strengths.append(f"Clean zero-friction founding stage ({human_members or 'Founding'} human members)")
        if total_msgs > 0: strengths.append("Early founder dialogues actively initializing")
    else:
        if engagement_score >= 20: strengths.append("High active chatter participation")
        if staff_score >= 15: strengths.append("Active staff leadership & problem resolution")
    if knowledge_score >= 12: strengths.append("Clear rule indexing & Server DNA profile")
    if not strengths: strengths.append("Welcoming baseline social foundation")

    # Identify Friction Points & Problems
    frictions = []
    if len(questions) >= 5: frictions.append(f"Recurring questions detected ({len(questions)} in past 48h)")
    if len(problems) > len(solutions): frictions.append("Unresolved community complaints logged in Brain")
    if not is_seed_stage and active_chatters < 3 and total_msgs > 0:
        frictions.append("Low multi-user dialogue diversity")
    elif is_seed_stage:
        frictions.append("Early incubation phase: member circle currently forming")
    if not frictions: frictions.append("No critical friction points detected")

    # AI Actionable Recommendations (Tailored to Stage)
    recommendations = []
    if is_seed_stage:
        recommendations.append("Set up `#welcome` & `#introductions` channels with a pinned server overview.")
        recommendations.append("Invite your first circle of 10-15 core members/friends to spark daily conversations.")
        recommendations.append("Use `@Smart bot index rule [Rule Text]` to establish the server's core principles.")
    else:
        if len(questions) >= 3:
            recommendations.append("Publish a pinned FAQ or onboarding guide addressing repeat questions.")
        if len(active_nodes) < 5:
            recommendations.append("Index server guidelines or rules via `@Smart bot index rule`.")
        if len(top_contributors) == 0:
            recommendations.append("Recognize active community helpers with contributor roles.")
        if not recommendations:
            recommendations.append("Host a community event or game night to maintain momentum.")

    return {
        "guild_id": guild_id,
        "health_score": total_score,
        "grade": grade,
        "stage": stage,
        "stage_badge": stage_badge,
        "server_age_days": server_age_days,
        "human_members": human_members,
        "bot_members": bot_members,
        "total_members": total_members,
        "is_seed_stage": is_seed_stage,
        "metrics": {
            "engagement": f"{engagement_score}/25",
            "staff_responsiveness": f"{staff_score}/20",
            "friction_stability": f"{friction_score}/20",
            "knowledge_grounding": f"{knowledge_score}/15",
            "vibe_retention": f"{growth_score}/20"
        },
        "strengths": strengths,
        "frictions": frictions,
        "recommendations": recommendations,
        "active_problems_count": len(problems),
        "total_brain_nodes": len(active_nodes),
        "evaluated_at": time.time()
    }

def generate_weekly_community_report_text(guild_id: int, guild_name: str = "Discord Server") -> str:
    """
    Renders the comprehensive Executive Weekly Community Health Report in clean Markdown.
    """
    health = calculate_community_health_score(guild_id)
    dna = community_brain.get_server_dna(guild_id)
    stats = collector.get_guild_activity_stats(guild_id, hours=168.0)  # 7 days
    contributors = community_brain.get_top_community_contributors(guild_id, limit=3)
    
    top_topics = ", ".join(dna.get("main_topics", ["General Discussions"]))
    keywords_list = [f"#{kw}" for kw, _ in stats.get("top_keywords", [])[:5]]
    keywords_str = " ".join(keywords_list) if keywords_list else "#general #community #events"

    report = (
        f"📊 **COMMUNITY INTELLIGENCE REPORT — {guild_name.upper()}**\n"
        f"*Generated by Smart Bot Community Intelligence*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 **SERVER DNA PROFILE**\n"
        f"• **Archetype:** {dna.get('server_type', 'General Community')}\n"
        f"• **Tone & Style:** {dna.get('communication_style', 'Casual & Friendly')}\n"
        f"• **Main Topics:** {top_topics}\n"
        f"• **DNA Confidence:** {dna.get('confidence_pct', 85)}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 **COMMUNITY HEALTH: {health['health_score']}/100 — {health['grade']}**\n"
        f"• **Engagement:** {health['metrics']['engagement']}\n"
        f"• **Staff & Moderation:** {health['metrics']['staff_responsiveness']}\n"
        f"• **Friction Stability:** {health['metrics']['friction_stability']}\n"
        f"• **Knowledge Grounding:** {health['metrics']['knowledge_grounding']}\n\n"
        f"🔥 **ACTIVITY & TRENDING RADAR**\n"
        f"• **7-Day Total Messages:** {stats.get('total_messages', 0):,}\n"
        f"• **Active Chatters:** {stats.get('active_chatters', 0):,}\n"
        f"• **Trending Keywords:** {keywords_str}\n\n"
        f"⚠️ **FRICTION & REPEATING INQUIRIES**\n"
    )

    for f in health["frictions"][:3]:
        report += f"• {f}\n"

    report += "\n💡 **AI STRATEGIC RECOMMENDATIONS**\n"
    for r in health["recommendations"][:3]:
        report += f"• {r}\n"

    if contributors:
        report += "\n🏆 **TOP COMMUNITY ANCHORS**\n"
        for c in contributors:
            report += f"• **{c['username']}** — {c['helpful_actions']} helpful community actions\n"

    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return report

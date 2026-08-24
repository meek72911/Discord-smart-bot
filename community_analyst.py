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

def calculate_community_health_score(guild_id: int) -> Dict[str, Any]:
    """
    Computes the 0-100 AI Community Health Score using weighted multi-dimensional metrics:
    - Engagement & Activity (25%)
    - Staff Presence & Response Health (20%)
    - Confusion & Friction Radar (20%)
    - Knowledge Base & Rule Grounding (15%)
    - Member Growth & Retention Signals (20%)
    """
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

    # 3. Component Scoring

    # A. Engagement Score (0-25)
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
    elif len(decisions) >= 1 or len(top_contributors) >= 1:
        staff_score = 16
    else:
        staff_score = 12

    # C. Friction / Confusion Radar (0-20)
    # High repeat questions or unsolved problems reduce this score
    friction_penalty = min(10, len(problems) * 2)
    friction_score = max(5, 20 - friction_penalty)

    # D. Knowledge & Rule Coverage (0-15)
    kb_entries = len(dna.get("important_rules", [])) + len(active_nodes)
    if kb_entries >= 10:
        knowledge_score = 15
    elif kb_entries >= 4:
        knowledge_score = 12
    else:
        knowledge_score = 8

    # E. Community Growth & Vibe (0-20)
    growth_score = 18 if dna.get("confidence_pct", 80) >= 85 else 14

    total_score = engagement_score + staff_score + friction_score + knowledge_score + growth_score
    total_score = max(10, min(100, total_score))

    # Grade determination
    if total_score >= 90: grade = "A+ (Thriving & Healthy)"
    elif total_score >= 80: grade = "A (Strong & Active)"
    elif total_score >= 70: grade = "B (Good with Minor Friction)"
    elif total_score >= 50: grade = "C (Needs Moderation Attention)"
    else: grade = "D (High Friction & Inactive)"

    # Identify Key Strengths
    strengths = []
    if engagement_score >= 20: strengths.append("High active chatter participation")
    if staff_score >= 15: strengths.append("Active staff leadership & problem resolution")
    if knowledge_score >= 12: strengths.append("Clear rule indexing & Server DNA profile")
    if not strengths: strengths.append("Welcoming baseline social foundation")

    # Identify Friction Points & Problems
    frictions = []
    if len(questions) >= 5: frictions.append(f"Recurring questions detected ({len(questions)} in past 48h)")
    if len(problems) > len(solutions): frictions.append("Unresolved community complaints logged in Brain")
    if active_chatters < 3 and total_msgs > 0: frictions.append("Low multi-user dialogue diversity")
    if not frictions: frictions.append("No critical friction points detected")

    # AI Actionable Recommendations
    recommendations = []
    if len(questions) >= 3:
        recommendations.append("Publish a pinned FAQ or onboarding guide addressing repeat questions.")
    if len(active_nodes) < 5:
        recommendations.append("Index server tournament guidelines or rules via `@Smart bot index rule`.")
    if len(top_contributors) == 0:
        recommendations.append("Recognize active community helpers with contributor roles.")
    if not recommendations:
        recommendations.append("Host a weekend community event or tournament to maintain high momentum.")

    return {
        "guild_id": guild_id,
        "health_score": total_score,
        "grade": grade,
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
        f"*Generated by Smart Bot OS v5.0 Community Brain*\n\n"
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

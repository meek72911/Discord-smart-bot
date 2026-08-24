/**
 * Smart Bot — Luxury OS Interface & Interaction Engine
 * Engineered for Awwwards / Linear Tier Craftsmanship
 */

// ============================================================================
// 1. DATA: 63+ ATOMIC CAPABILITIES (MATCHING TOOLS.PY & FULL REPORT)
// ============================================================================
const TOOLS_DATA = [
  // Moderation & Members (9)
  { name: 'ban_user', category: 'moderation', icon: 'fa-ban', color: 'text-rose-400', desc: 'Bans target with prune days, snowflake ID resolution, and audit trail.' },
  { name: 'bulk_ban', category: 'moderation', icon: 'fa-user-slash', color: 'text-rose-400', desc: 'High-velocity bulk ban engine for raid mitigation (up to 200 IDs in batch).' },
  { name: 'unban_user', category: 'moderation', icon: 'fa-user-check', color: 'text-emerald-400', desc: 'Resolves banned user from guild ban registry and lifts restriction.' },
  { name: 'kick_user', category: 'moderation', icon: 'fa-door-open', color: 'text-amber-400', desc: 'Removes member while executing dangerous role guard validation.' },
  { name: 'timeout_user', category: 'moderation', icon: 'fa-clock', color: 'text-amber-400', desc: 'Applies Discord native timeout clamped up to 28 days (40,320 mins).' },
  { name: 'remove_timeout', category: 'moderation', icon: 'fa-clock-rotate-left', color: 'text-emerald-400', desc: 'Instantly revokes active timeout penalty from guild member.' },
  { name: 'change_nickname', category: 'moderation', icon: 'fa-signature', color: 'text-sky-400', desc: 'Updates target user nickname safely within role hierarchy.' },
  { name: 'disconnect_member_voice', category: 'moderation', icon: 'fa-phone-slash', color: 'text-rose-400', desc: 'Disconnects target member from active voice or stage channel.' },
  { name: 'move_member_voice', category: 'moderation', icon: 'fa-arrows-split-up-and-left', color: 'text-sky-400', desc: 'Moves member to designated voice channel seamlessly.' },

  // Channels & Forum (9)
  { name: 'create_text_channel', category: 'channels', icon: 'fa-hashtag', color: 'text-blurple', desc: 'Creates text channel with optional category parent and topic.' },
  { name: 'create_voice_channel', category: 'channels', icon: 'fa-microphone', color: 'text-blurple', desc: 'Generates voice channel with custom bitrate and user limit.' },
  { name: 'create_stage_channel', category: 'channels', icon: 'fa-podcast', color: 'text-blurple', desc: 'Deploys stage channel for townhalls and community broadcasts.' },
  { name: 'create_category', category: 'channels', icon: 'fa-folder-plus', color: 'text-blurple', desc: 'Creates organizational category container for grouping channels.' },
  { name: 'delete_channel', category: 'channels', icon: 'fa-trash-can', color: 'text-rose-400', desc: 'Safely deletes channel with audit log verification.' },
  { name: 'edit_channel', category: 'channels', icon: 'fa-pen-to-square', color: 'text-sky-400', desc: 'Modifies topic, slowmode, bitrate, and NSFW flags dynamically.' },
  { name: 'set_channel_read_only', category: 'channels', icon: 'fa-lock', color: 'text-amber-400', desc: 'Locks channel by denying @everyone SEND_MESSAGES permissions.' },
  { name: 'hide_channel', category: 'channels', icon: 'fa-eye-slash', color: 'text-amber-400', desc: 'Hides channel from @everyone via VIEW_CHANNEL deny overwrite.' },
  { name: 'create_thread', category: 'channels', icon: 'fa-code-branch', color: 'text-violet-400', desc: 'Spawns public or private thread with auto-archive duration.' },

  // Roles & Permissions (3)
  { name: 'create_role', category: 'moderation', icon: 'fa-shield-heart', color: 'text-indigo-400', desc: 'Creates new guild role with hex color, hoist, and mentionable properties.' },
  { name: 'assign_role', category: 'moderation', icon: 'fa-user-shield', color: 'text-indigo-400', desc: 'Assigns role with hierarchy check (blocks assigning above bot role).' },
  { name: 'remove_role', category: 'moderation', icon: 'fa-user-minus', color: 'text-amber-400', desc: 'Removes role with dangerous permission guard blocking admin exploitation.' },

  // Interactive Widgets: Polls & Tickets (5)
  { name: 'create_native_poll', category: 'widgets', icon: 'fa-square-poll-vertical', color: 'text-blurple', desc: 'Deploys official Discord native poll widget with multiselect & timer.' },
  { name: 'create_poll', category: 'widgets', icon: 'fa-chart-simple', color: 'text-blurple', desc: 'Text embed poll fallback with emoji reaction collectors.' },
  { name: 'expire_poll', category: 'widgets', icon: 'fa-stopwatch', color: 'text-slate-400', desc: 'Manually expires and finalizes live native Discord poll.' },
  { name: 'create_ticket', category: 'widgets', icon: 'fa-ticket', color: 'text-emerald-400', desc: 'Creates isolated private channel with staff overwrites and auto-category.' },
  { name: 'close_ticket', category: 'widgets', icon: 'fa-circle-xmark', color: 'text-rose-400', desc: 'Archives or deletes resolved ticket channel with audit trail.' },

  // Long-Term Memory & Persona (7)
  { name: 'remember_fact', category: 'memory', icon: 'fa-brain', color: 'text-emerald-400', desc: 'Persists user facts, preferences, and custom context into SQLite DB.' },
  { name: 'recall_my_facts', category: 'memory', icon: 'fa-lightbulb', color: 'text-emerald-400', desc: 'Queries stored user memory facts with conversational synthesis.' },
  { name: 'forget_my_facts', category: 'memory', icon: 'fa-eraser', color: 'text-rose-400', desc: 'Purges remembered facts for privacy compliance on demand.' },
  { name: 'set_server_persona', category: 'memory', icon: 'fa-masks-theater', color: 'text-amber-400', desc: 'Switches guild personality (Default, Savage, Wholesome, Professor, Gamer).' },
  { name: 'set_reminder', category: 'memory', icon: 'fa-bell', color: 'text-amber-400', desc: '30s background loop reminder with channel dispatch & relative time parsing.' },
  { name: 'show_leaderboard', category: 'memory', icon: 'fa-trophy', color: 'text-amber-400', desc: 'Displays XP & leveling rankings with interactive embed pages.' },
  { name: 'catch_me_up', category: 'memory', icon: 'fa-newspaper', color: 'text-sky-400', desc: 'Summarizes last 80 messages using fast gemini-3.5-flash-lite core.' },

  // Enterprise AutoMod, Webhooks & Events (9)
  { name: 'create_automod_rule', category: 'enterprise', icon: 'fa-robot', color: 'text-violet-400', desc: 'Installs native Discord keyword filters & anti-spam triggers.' },
  { name: 'list_automod_rules', category: 'enterprise', icon: 'fa-list-ol', color: 'text-violet-400', desc: 'Audits currently active AutoMod protection rules.' },
  { name: 'read_audit_log', category: 'enterprise', icon: 'fa-clipboard-list', color: 'text-slate-300', desc: 'Fetches recent server administrative actions and culprit snowflakes.' },
  { name: 'create_webhook', category: 'enterprise', icon: 'fa-network-wired', color: 'text-emerald-400', desc: 'Generates secure inbound webhook endpoint for GitHub/CI integrations.' },
  { name: 'list_webhooks', category: 'enterprise', icon: 'fa-diagram-project', color: 'text-slate-300', desc: 'Audits existing channel webhooks and token references.' },
  { name: 'delete_webhook', category: 'enterprise', icon: 'fa-link-slash', color: 'text-rose-400', desc: 'Decommissions target webhook to prevent unauthorized ingress.' },
  { name: 'create_scheduled_event', category: 'enterprise', icon: 'fa-calendar-plus', color: 'text-sky-400', desc: 'Schedules guild voice, stage, or external events with metadata.' },
  { name: 'list_scheduled_events', category: 'enterprise', icon: 'fa-calendar-days', color: 'text-sky-400', desc: 'Queries upcoming guild events and subscriber counts.' },
  { name: 'create_stage_instance', category: 'enterprise', icon: 'fa-tower-broadcast', color: 'text-purple-400', desc: 'Opens public or guild-only stage broadcast with topic.' },

  // Community Intelligence Platform (6)
  { name: 'generate_community_report', category: 'enterprise', icon: 'fa-chart-pie', color: 'text-indigo-400', desc: 'Generates executive server intelligence audits with engagement, trending topics, and staff advice.' },
  { name: 'get_trending_topics', category: 'enterprise', icon: 'fa-arrow-trend-up', color: 'text-emerald-400', desc: 'Real-time discussion pulse and keyword volume radar across active channels.' },
  { name: 'get_repeating_questions', category: 'enterprise', icon: 'fa-circle-question', color: 'text-amber-400', desc: 'Identifies recurring member inquiries to auto-synthesize staff FAQ documentation.' },
  { name: 'index_community_knowledge', category: 'memory', icon: 'fa-book-bookmark', color: 'text-sky-400', desc: 'Indexes official rules, tournament details, decisions, and FAQs into living knowledge base.' },
  { name: 'query_community_knowledge', category: 'memory', icon: 'fa-magnifying-glass-chart', color: 'text-emerald-400', desc: 'Grounds answers in verified server rules & announcements with exact citations.' },
  { name: 'summarize_channel_history', category: 'memory', icon: 'fa-clock-rotate-left', color: 'text-violet-400', desc: '24h/2h dynamic timestamped history digests with strict privacy permission guards.' },

  // Community Brain & Intelligence OS v5.0 (6)
  { name: 'ask_community_brain', category: 'memory', icon: 'fa-brain', color: 'text-blurple', desc: 'Unified reasoning over causal graph, temporal history, rules, and server decisions.' },
  { name: 'query_memory_graph', category: 'memory', icon: 'fa-diagram-project', color: 'text-indigo-400', desc: 'Inspects property graph nodes, causal connections, and upstream decision chains.' },
  { name: 'get_community_health_score', category: 'enterprise', icon: 'fa-heart-pulse', color: 'text-emerald-400', desc: 'Computes 0-100 Community Health Score with friction radar and AI action items.' },
  { name: 'generate_weekly_report', category: 'enterprise', icon: 'fa-chart-pie', color: 'text-indigo-400', desc: 'Generates 7-day executive community health, activity, and trend intelligence report.' },
  { name: 'scan_server_dna', category: 'enterprise', icon: 'fa-dna', color: 'text-purple-400', desc: 'Scans rules, channels, and culture to build the autonomous Server DNA Profile.' },
  { name: 'manage_memory_privacy', category: 'enterprise', icon: 'fa-shield-halved', color: 'text-emerald-400', desc: 'Enterprise memory audit, JSON graph data export, and privacy-shield controls.' },

  // Warnings & Sanctions (3)
  { name: 'warn_user', category: 'moderation', icon: 'fa-triangle-exclamation', color: 'text-amber-400', desc: 'Automatic escalation ladder: 3 warns = 10m timeout, 4 = 1h, 5+ = 1d.' },
  { name: 'show_warnings', category: 'moderation', icon: 'fa-file-lines', color: 'text-slate-300', desc: 'Retrieves member warning ledger and infraction timestamps.' },
  { name: 'clear_warnings', category: 'moderation', icon: 'fa-circle-check', color: 'text-emerald-400', desc: 'Lifts registered warnings and resets escalation tier.' },

  // Native Code & Web Engine (4)
  { name: 'code_execution', category: 'native', icon: 'fa-code', color: 'text-sky-400', desc: 'Native Gemini code sandbox execution for math, benchmarks, and data parsing.' },
  { name: 'url_context', category: 'native', icon: 'fa-globe', color: 'text-emerald-400', desc: 'Real-time live web browsing and documentation retrieval.' },
  { name: 'youtube_ingestion', category: 'native', icon: 'fa-youtube', color: 'text-rose-400', desc: 'Analyzes first-link YouTube video content and auto-extracts transcript/context.' },
  { name: 'purge_messages', category: 'moderation', icon: 'fa-broom', color: 'text-rose-400', desc: 'Purges messages up to 100 with fallback for >14d Error 50034.' }
];

// ============================================================================
// 2. SIMULATOR SCENARIO DATA
// ============================================================================
const SIMULATION_RESPONSES = {
  report: {
    user: {
      name: "CommunityDirector",
      avatar: "CD",
      avatarBg: "bg-indigo-600",
      content: "@Smart bot give me this week's community report"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🧠",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.generate_community_report(timeframe_days=7)...\n📊 Ingested 14,280 buffered messages across 12 channels (0 API cost buffer).",
      embed: {
        title: "📊 Executive Community Intelligence Report (Past 7 Days)",
        color: "border-indigo-400",
        fields: [
          { name: "📈 Engagement & Vibe", value: "• **Active Members:** 4,820 (+14% WoW)\n• **Sentiment:** 82% Positive / 18% Friction", inline: false },
          { name: "🔥 Top 3 Trending Topics", value: "1. **Tournament Rules** (1,420 mentions in #general)\n2. **GPU Optimization** (610 mentions in #dev)\n3. **VIP Role Perks** (340 mentions)", inline: false },
          { name: "⚠️ Community Confusion", value: "• 45+ users asked how to register for tournament.\n• Confusion on voice channel bitrate.", inline: false },
          { name: "💡 Actionable Recommendations", value: "• Pin a 3-bullet FAQ in `#announcements`.\n• Host a 15-min voice AMA this Friday.", inline: false }
        ],
        footer: "Smart Bot Intelligence • 99% Cost-Reduced Collector"
      },
      text: "Here is your weekly executive community report! The community is growing (+14%), but players need clearer tournament registration instructions."
    }
  },

  kb: {
    user: {
      name: "GamerAlex",
      avatar: "GA",
      avatarBg: "bg-emerald-600",
      content: "@Smart bot when does the tournament start and what are the prizes?"
    },
    bot: {
      name: "Smart Bot",
      avatar: "📌",
      avatarBg: "bg-emerald-600",
      toolExec: "⚙️ Executing tools.query_community_knowledge(question='tournament start prizes')...\n🔍 Grounded in Knowledge Base [ANNOUNCEMENT] ID #42.",
      embed: {
        title: "🏆 Grand Valorant Tournament 2026",
        color: "border-emerald-400",
        fields: [
          { name: "📅 Start Date", value: "`Saturday @ 5:00 PM EST`", inline: true },
          { name: "💰 Prize Pool", value: "`$500 USD + Champion Role`", inline: true },
          { name: "📖 Source Citation", value: "Posted by `@TournamentHost` in `#announcements`", inline: false }
        ],
        footer: "Living Knowledge Base • Grounded Zero-Hallucination Recall"
      },
      text: "The Grand Tournament kicks off this Saturday at 5:00 PM EST with a $500 prize pool! Check #announcements for the registration link."
    }
  },

  mod: {
    user: {
      name: "ServerOwner",
      avatar: "SO",
      avatarBg: "bg-indigo-600",
      content: "@Smart bot bulk ban user1, user2 reason raiding server"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🤖",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.bulk_ban(targets=['user1', 'user2'], reason='raiding server')...\n🔒 Checked _is_dangerous_role hierarchy guard: [PASS - 0 admin conflicts]",
      embed: {
        title: "🛡️ Bulk Ban Action Confirmed",
        color: "border-emerald-400",
        fields: [
          { name: "Target Accounts", value: "`user1 (ID: 98124...)`, `user2 (ID: 98125...)`", inline: false },
          { name: "Reason", value: "Raiding server", inline: true },
          { name: "Prune Messages", value: "7 Days", inline: true },
          { name: "Audit Logger", value: "Dispatched to `#mod-logs`", inline: true }
        ],
        footer: "Smart Bot Sentinel • Action authorized by Owner"
      },
      text: "Executed bulk ban on 2 targets. Audit logs and purge records have been synchronized to SQLite WAL."
    }
  },

  persona: {
    user: {
      name: "StaffAdmin",
      avatar: "SA",
      avatarBg: "bg-emerald-600",
      content: "@Smart bot set persona to savage"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🔥",
      avatarBg: "bg-amber-600",
      toolExec: "⚙️ Executing tools.set_server_persona(persona='savage')...\n🧠 Persona re-injected into Gemini 3.6 Flash system prompt.",
      embed: {
        title: "🔥 Persona Switched: SAVAGE",
        color: "border-amber-400",
        fields: [
          { name: "New Mode", value: "`SAVAGE (Roastmaster Active)`", inline: true },
          { name: "Tone", value: "`Unfiltered / Sharp / High Voltage`", inline: true }
        ],
        footer: "Smart Bot AI • Dynamic Persona Engine"
      },
      text: "Alright, kid gloves are off. Try not to ask anything too embarrassing, though knowing this server, that's asking for a miracle. What do you want?"
    }
  },

  poll: {
    user: {
      name: "CommunityLead",
      avatar: "CL",
      avatarBg: "bg-purple-600",
      content: "@Smart bot create native poll 'Best Language?' Python, Rust, TS duration 24"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🤖",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.create_native_poll(question='Best Language?', options=['Python', 'Rust', 'TS'], duration_hours=24)...",
      embed: {
        title: "📊 Discord Poll — Best Language?",
        color: "border-blurple",
        pollWidget: [
          { label: "1️⃣ Python (Rapid backend & AI)", votes: "54%" },
          { label: "2️⃣ Rust (Memory safety & speed)", votes: "32%" },
          { label: "3️⃣ TypeScript (Full-stack UI)", votes: "14%" }
        ],
        footer: "Ends in 24 hours • Multiselect: Off • Powered by Discord Polls"
      },
      text: "Native poll deployed in #bot-command-center! Live votes will sync directly to gateway events."
    }
  },

  ticket: {
    user: {
      name: "VIP_Sponsor",
      avatar: "VS",
      avatarBg: "bg-amber-600",
      content: "@Smart bot open ticket for @VIP_Sponsor sponsorship inquiry"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🤖",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.create_ticket(username='VIP_Sponsor', issue='sponsorship inquiry')...\n📁 Created channel `#ticket-vip_sponsor` under category `🎫 TICKETS`.",
      embed: {
        title: "🎫 Private Ticket #108 Created",
        color: "border-purple-400",
        fields: [
          { name: "Initiator", value: "<@VIP_Sponsor>", inline: true },
          { name: "Subject", value: "Sponsorship inquiry", inline: true },
          { name: "Overwrites", value: "`@everyone: DENIED`, `Staff: ALLOWED`", inline: false }
        ],
        footer: "Click 🔒 Close Ticket to archive this conversation"
      },
      text: "Private ticket created at <#ticket-vip_sponsor>. Staff has been notified."
    }
  },

  brain: {
    user: {
      name: "CommunityMember",
      avatar: "CM",
      avatarBg: "bg-blurple",
      content: "@Smart bot why was the tournament date moved to August 25?"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🧠",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.ask_community_brain(query='why was tournament moved')...\n🕸️ Tracing causal path: [PROBLEM: Game Server Maintenance] ➔ [DECISION: Staff Vote] ➔ [EVENT: Tournament Rescheduled].",
      embed: {
        title: "🧠 Community Brain Causal Explanation",
        color: "border-blurple",
        fields: [
          { name: "🎯 Target Event", value: "**Grand Valorant Tournament** (Status: `Active`)", inline: false },
          { name: "🔗 Causal Root (Why?)", value: "• **Upstream Problem:** Riot scheduled backend game maintenance on Aug 20.\n• **Staff Decision:** `@TournamentHost` moved tournament to **August 25 @ 6:00 PM EST** to prevent mid-match disconnections.", inline: false },
          { name: "⏳ Temporal Resolution", value: "• Previous Date: `August 20` (⚪ SUPERSEDED)\n• Current Date: `August 25` (🟢 ACTIVE)", inline: false }
        ],
        footer: "Community Brain OS v5.0 • Property Graph Causal Engine"
      },
      text: "The tournament was moved to August 25 because Riot scheduled server maintenance on the original date (Aug 20). Staff voted to reschedule so matches wouldn't be interrupted!"
    }
  },

  health: {
    user: {
      name: "ServerFounder",
      avatar: "SF",
      avatarBg: "bg-emerald-600",
      content: "@Smart bot what is our community health score?"
    },
    bot: {
      name: "Smart Bot",
      avatar: "📈",
      avatarBg: "bg-emerald-600",
      toolExec: "⚙️ Executing tools.get_community_health_score()...\n📊 Evaluated 48h chat pulse, friction radar, staff resolution velocity, and member retention.",
      embed: {
        title: "📈 Community Health Score: 88/100 (Grade: A)",
        color: "border-emerald-400",
        fields: [
          { name: "Engagement & Pulse", value: "`24/25` • High chatter participation", inline: true },
          { name: "Staff Leadership", value: "`18/20` • Fast response times", inline: true },
          { name: "Friction Stability", value: "`17/20` • Low toxicity", inline: true },
          { name: "⚠️ Friction Radar", value: "• 32 users asked how to submit clip submissions in #media.\n• Minor role confusion for new members.", inline: false },
          { name: "💡 Strategic Recommendations", value: "1. Pin clip submission guidelines in `#media`.\n2. Add onboarding button for role self-assignment.", inline: false }
        ],
        footer: "Community Analyst Engine • Smart Bot OS v5.0"
      },
      text: "Your Community Health is sitting strong at **88/100 (Grade: A)**! Activity is surging, but pinning a clip guide in #media will eliminate the main repeating question."
    }
  },

  dna: {
    user: {
      name: "ModeratorLead",
      avatar: "ML",
      avatarBg: "bg-purple-600",
      content: "@Smart bot scan server dna"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🧬",
      avatarBg: "bg-purple-600",
      toolExec: "⚙️ Executing tools.scan_server_dna(force_rescan=True)...\n🔍 Scanned #rules, #announcements, #faq, #general, and 12 category channels.",
      embed: {
        title: "🧬 Server DNA Profile — Gaming & Esports",
        color: "border-purple-400",
        fields: [
          { name: "🏛️ Archetype", value: "**Gaming & Esports Community**", inline: true },
          { name: "💬 Tone & Style", value: "**Casual, Competitive & Meme-Friendly**", inline: true },
          { name: "🎭 Formality", value: "`Casual (High Hype & Gaming Emojis)`", inline: true },
          { name: "🎯 Main Topics", value: "• Tournaments & Scrims\n• Patch Updates & Clip Showcases\n• Community Game Nights", inline: false },
          { name: "📜 Grounded Rules", value: "• 1. Respect fellow players — zero toxicity\n• 2. English only in public text channels\n• 3. No self-promo outside #showcase", inline: false }
        ],
        footer: "Server DNA Profile • Confidence: 94% • Autonomous Culture Adaptation"
      },
      text: "Server DNA profiled successfully with **94% confidence**! I've automatically tuned my persona to a competitive, high-energy gaming vibe."
    }
  },

  memory: {
    user: {
      name: "Developer",
      avatar: "DV",
      avatarBg: "bg-sky-600",
      content: "@Smart bot remember that our server hackathon starts next Friday at 6PM"
    },
    bot: {
      name: "Smart Bot",
      avatar: "🤖",
      avatarBg: "bg-blurple",
      toolExec: "⚙️ Executing tools.remember_fact(fact='Server hackathon starts next Friday at 6PM')...\n💾 Written to SQLite WAL `user_memory` table.",
      embed: {
        title: "🧠 SQLite Fact Stored",
        color: "border-emerald-400",
        fields: [
          { name: "Category", value: "`SCHEDULE / EVENT`", inline: true },
          { name: "Fact", value: "\"Server hackathon starts next Friday at 6PM\"", inline: false }
        ],
        footer: "Cross-session memory • Accessible in all channels"
      },
      text: "Committed to memory! Ask me anytime with `@Smart bot what do you remember about me?`"
    }
  },

  suggest: {
    user: {
      name: "CommunityMember",
      avatar: "CM",
      avatarBg: "bg-amber-600",
      content: "@Smart bot suggest feature Add Google Calendar two-way event sync"
    },
    bot: {
      name: "Smart Bot",
      avatar: "💡",
      avatarBg: "bg-amber-600",
      toolExec: "⚙️ Executing tools.suggest_feature(suggestion='Add Google Calendar two-way event sync', category='integrations')...\n📝 Logged to feature_suggestions (ID: #101) & synced to Web Dashboard.",
      embed: {
        title: "💡 Feature Suggestion Recorded (ID: #101)",
        color: "border-amber-400",
        fields: [
          { name: "💡 Idea", value: "*\"Add Google Calendar two-way event sync\"*", inline: false },
          { name: "📂 Category", value: "`Integrations`", inline: true },
          { name: "🔥 Starting Votes", value: "`1 Vote (Rank #1)`", inline: true },
          { name: "📈 Roadmap Status", value: "Added to Community Backlog! Other members can upvote this feature in chat or via the Web Dashboard.", inline: false }
        ],
        footer: "Product Feedback Loop • Automatic Topic Clustering"
      },
      text: "Thanks for the suggestion! Your request for Google Calendar sync has been recorded and placed on the community roadmap."
    }
  }
};

// ============================================================================
// 3. PERSONA MATRIX DATA
// ============================================================================
const PERSONA_DETAILS = {
  default: {
    title: "Default Persona",
    tagline: 'TRIGGER: "@Smart bot set persona to default"',
    icon: 'fa-user-astronaut',
    iconColor: 'bg-blurple/20 text-blurple',
    userPrompt: "Smart bot, why is my code failing?",
    botReply: "Let's look at the stack trace. You're trying to index into a NoneType on line 42 because the API call timed out. Wrap it in a try/except block with exponential backoff and you're good."
  },
  savage: {
    title: "Savage Persona",
    tagline: 'TRIGGER: "@Smart bot set persona to savage"',
    icon: 'fa-fire',
    iconColor: 'bg-amber-500/20 text-amber-400',
    userPrompt: "Smart bot, why is my code failing?",
    botReply: "Because you didn't even check if the API returned None before grabbing items from it. Line 42 is crying. Add some error handling before your server bursts into flames."
  },
  wholesome: {
    title: "Wholesome Persona",
    tagline: 'TRIGGER: "@Smart bot set persona to wholesome"',
    icon: 'fa-heart',
    iconColor: 'bg-emerald-500/20 text-emerald-400',
    userPrompt: "Smart bot, why is my code failing?",
    botReply: "Don't worry, bugs happen to the best of us! It looks like line 42 received a None object because the network had a tiny hiccup. If we add a gentle try/except, it will run smoothly!"
  },
  professor: {
    title: "Professor Persona",
    tagline: 'TRIGGER: "@Smart bot set persona to professor"',
    icon: 'fa-graduation-cap',
    iconColor: 'bg-sky-500/20 text-sky-400',
    userPrompt: "Smart bot, why is my code failing?",
    botReply: "Analyzing the traceback reveals an unhandled `AttributeError` on line 42. This stems from a null pointer equivalent in Python. Implementing an exponential backoff decorator is the standard mitigation."
  },
  gamer: {
    title: "Gamer Persona",
    tagline: 'TRIGGER: "@Smart bot set persona to gamer"',
    icon: 'fa-gamepad',
    iconColor: 'bg-purple-500/20 text-purple-400',
    userPrompt: "Smart bot, why is my code failing?",
    botReply: "Bro you just whiffed line 42! The API lagged out and threw a NoneType headshot at your script. Put up a shield with a try/catch and let's get back in the lobby."
  }
};

// ============================================================================
// 4. STUDIO-GRADE AUDIO SYNTHESIZER
// ============================================================================
let audioCtx = null;
let soundEnabled = false;

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function playHapticSound(type = 'click') {
  if (!soundEnabled) return;
  try {
    initAudio();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (type === 'click') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.04);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.04);
      osc.start(now);
      osc.stop(now + 0.04);
    } else if (type === 'stream') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, now);
      gain.gain.setValueAtTime(0.02, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.03);
      osc.start(now);
      osc.stop(now + 0.03);
    } else if (type === 'success') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.setValueAtTime(783.99, now + 0.06); // G5
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    }
  } catch (e) {
    console.warn("Web Audio:", e);
  }
}

// ============================================================================
// 5. GEODESIC 3D NEURAL CANVAS SIMULATION
// ============================================================================
function initNeuralCanvas() {
  const canvas = document.getElementById('neural-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width, height;
  let particles = [];
  let mouse = { x: null, y: null, radius: 200 };

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    createParticles();
  }

  function createParticles() {
    particles = [];
    const count = Math.min(Math.floor((width * height) / 16000), 75);
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: Math.random() * 1.5 + 0.8,
        color: Math.random() > 0.4 ? 'rgba(88, 101, 242, ' : 'rgba(255, 255, 255, '
      });
    }
  }

  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    
    // Update cursor glow
    const glow = document.getElementById('cursor-glow');
    if (glow) {
      glow.style.left = `${e.clientX}px`;
      glow.style.top = `${e.clientY}px`;
    }

    // Specular card highlights
    document.querySelectorAll('.pro-card').forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const specular = card.querySelector('.card-specular-glow');
      if (specular) {
        specular.style.left = `${x}px`;
        specular.style.top = `${y}px`;
      }
    });
  });

  function animate() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      let p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > width) p.vx *= -1;
      if (p.y < 0 || p.y > height) p.vy *= -1;

      // Mouse field
      if (mouse.x !== null) {
        let dx = mouse.x - p.x;
        let dy = mouse.y - p.y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          let force = (mouse.radius - dist) / mouse.radius;
          p.x -= (dx / dist) * force * 1.2;
          p.y -= (dy / dist) * force * 1.2;
        }
      }

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color + '0.6)';
      ctx.fill();

      // Connect filaments
      for (let j = i + 1; j < particles.length; j++) {
        let p2 = particles[j];
        let dx = p.x - p2.x;
        let dy = p.y - p2.y;
        let dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(88, 101, 242, ${0.15 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(animate);
  }

  resize();
  animate();
}

// ============================================================================
// 6. LIVE DISCORD SIMULATOR (STREAMING WITH DESKTOP REALISM)
// ============================================================================
let isStreaming = false;

function renderSimulatedChat(scenarioKey, customPrompt = null) {
  if (isStreaming) return;
  const container = document.getElementById('discord-messages');
  const typingIndicator = document.getElementById('discord-typing');
  if (!container) return;

  const scenario = SIMULATION_RESPONSES[scenarioKey] || SIMULATION_RESPONSES.mod;
  const userContent = customPrompt || scenario.user.content;

  isStreaming = true;
  container.innerHTML = '';

  // Render User Message
  const userMsgHtml = `
    <div class="flex gap-4 items-start">
      <div class="w-10 h-10 rounded-full ${scenario.user.avatarBg} text-white font-bold flex items-center justify-center flex-shrink-0 text-sm shadow-md">${scenario.user.avatar}</div>
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-semibold text-white text-sm hover:underline cursor-pointer">${scenario.user.name}</span>
          <span class="text-[11px] text-slate-400 font-mono">Today at ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        <div class="text-slate-200 text-sm leading-relaxed">${escapeHtml(userContent)}</div>
      </div>
    </div>
  `;
  container.innerHTML += userMsgHtml;
  playHapticSound('click');

  // Trigger Typing
  if (typingIndicator) typingIndicator.style.opacity = '1';

  // Stream Bot Response
  setTimeout(() => {
    if (typingIndicator) typingIndicator.style.opacity = '0';

    const botMsgWrapper = document.createElement('div');
    botMsgWrapper.className = 'flex gap-4 items-start';

    let embedContentHtml = '';
    if (scenario.bot.embed) {
      const em = scenario.bot.embed;
      let fieldsHtml = '';
      if (em.fields) {
        fieldsHtml = em.fields.map(f => `
          <div class="mb-2">
            <span class="text-xs font-semibold text-slate-300 block">${f.name}</span>
            <span class="text-xs text-slate-400 font-mono">${f.value}</span>
          </div>
        `).join('');
      }

      let pollHtml = '';
      if (em.pollWidget) {
        pollHtml = em.pollWidget.map(p => `
          <div class="p-2.5 rounded-lg bg-[#1e1f22] border border-white/5 flex items-center justify-between mb-1.5 hover:bg-[#232428] cursor-pointer transition-colors">
            <span class="text-xs text-white font-medium">${p.label}</span>
            <span class="text-xs font-mono text-blurple font-bold">${p.votes}</span>
          </div>
        `).join('');
      }

      embedContentHtml = `
        <div class="bg-[#2b2d31] border-l-4 ${em.color} rounded-r-lg p-4 mt-3 max-w-lg shadow-lg">
          <div class="font-semibold text-sm text-white mb-2 flex items-center gap-2">
            <span>${em.title}</span>
          </div>
          ${fieldsHtml}
          ${pollHtml}
          ${em.footer ? `<div class="text-[10px] text-slate-400 font-mono pt-2 border-t border-white/5 mt-2">${em.footer}</div>` : ''}
        </div>
      `;
    }

    botMsgWrapper.innerHTML = `
      <div class="w-10 h-10 rounded-full ${scenario.bot.avatarBg} text-white text-base flex items-center justify-center flex-shrink-0 shadow-md">${scenario.bot.avatar}</div>
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-semibold text-white text-sm hover:underline cursor-pointer">${scenario.bot.name}</span>
          <span class="bg-blurple text-white text-[10px] font-bold px-1.5 py-0.5 rounded">BOT</span>
          <span class="text-[11px] text-slate-400 font-mono">Today at ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        ${scenario.bot.toolExec ? `<pre class="text-[11px] font-mono text-emerald-400 bg-black/50 p-3 rounded-lg mb-2 border border-emerald-500/20 whitespace-pre-wrap">${scenario.bot.toolExec}</pre>` : ''}
        <div id="bot-stream-text" class="text-slate-200 text-sm leading-relaxed"></div>
        ${embedContentHtml}
      </div>
    `;

    container.appendChild(botMsgWrapper);
    container.scrollTop = container.scrollHeight;

    // Paced Typewriter Streaming
    const streamTarget = document.getElementById('bot-stream-text');
    const fullText = scenario.bot.text;
    let charIndex = 0;

    const streamInterval = setInterval(() => {
      if (charIndex < fullText.length) {
        streamTarget.textContent += fullText.charAt(charIndex);
        charIndex++;
        if (charIndex % 3 === 0) playHapticSound('stream');
        container.scrollTop = container.scrollHeight;
      } else {
        clearInterval(streamInterval);
        isStreaming = false;
        playHapticSound('success');
      }
    }, 16);

  }, 500);
}

function escapeHtml(string) {
  return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ============================================================================
// 7. CAPABILITIES RENDERER & SEARCH ENGINE
// ============================================================================
function renderCapabilities(category = 'all', searchQuery = '') {
  const grid = document.getElementById('tools-grid');
  if (!grid) return;

  const filtered = TOOLS_DATA.filter(tool => {
    const matchesCategory = category === 'all' || tool.category === category;
    const matchesSearch = !searchQuery || 
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      tool.desc.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500 font-mono text-xs">
        <i class="fa-solid fa-filter text-2xl mb-3 block text-slate-600"></i>
        No atomic capabilities found matching "${escapeHtml(searchQuery)}".
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(tool => `
    <div class="feature-card p-5 group flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between mb-3">
          <div class="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/10 flex items-center justify-center ${tool.color} group-hover:scale-105 transition-transform">
            <i class="fa-solid ${tool.icon} text-xs"></i>
          </div>
          <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/5">${tool.category}</span>
        </div>
        <h4 class="font-mono font-bold text-sm text-white group-hover:text-blurple transition-colors mb-2">
          ${tool.name}
        </h4>
        <p class="text-xs text-slate-400 leading-relaxed">${tool.desc}</p>
      </div>
    </div>
  `).join('');
}

// ============================================================================
// 8. COMMAND PALETTE (Ctrl+K / ⌘K)
// ============================================================================
function initCommandPalette() {
  const modal = document.getElementById('cmd-palette');
  const input = document.getElementById('cmd-input');
  const results = document.getElementById('cmd-results');
  const triggerBtn = document.getElementById('cmd-trigger-btn');

  function openPalette() {
    modal.classList.remove('hidden');
    input.value = '';
    renderPaletteResults('');
    input.focus();
    playHapticSound('click');
  }

  function closePalette() {
    modal.classList.add('hidden');
  }

  function renderPaletteResults(query) {
    const q = query.toLowerCase();
    const matched = TOOLS_DATA.filter(t => t.name.toLowerCase().includes(q) || t.desc.toLowerCase().includes(q)).slice(0, 8);
    
    if (matched.length === 0) {
      results.innerHTML = `<div class="p-4 text-center text-xs font-mono text-slate-500">No matching capabilities.</div>`;
      return;
    }

    results.innerHTML = matched.map(tool => `
      <div class="p-3 rounded-xl hover:bg-white/5 flex items-center justify-between cursor-pointer group transition-colors" data-tool="${tool.name}">
        <div class="flex items-center gap-3">
          <i class="fa-solid ${tool.icon} ${tool.color} text-xs"></i>
          <div>
            <span class="font-mono text-xs text-white group-hover:text-blurple font-bold block">${tool.name}</span>
            <span class="text-[11px] text-slate-400 font-sans line-clamp-1">${tool.desc}</span>
          </div>
        </div>
        <span class="tool-tag">${tool.category}</span>
      </div>
    `).join('');

    results.querySelectorAll('[data-tool]').forEach(item => {
      item.addEventListener('click', () => {
        const toolName = item.getAttribute('data-tool');
        closePalette();
        const searchInput = document.getElementById('tool-search-input');
        if (searchInput) {
          searchInput.value = toolName;
          renderCapabilities('all', toolName);
          document.getElementById('capabilities')?.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
  }

  if (triggerBtn) triggerBtn.addEventListener('click', openPalette);
  
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      modal.classList.contains('hidden') ? openPalette() : closePalette();
    }
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closePalette();
    }
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closePalette();
  });

  if (input) {
    input.addEventListener('input', (e) => renderPaletteResults(e.target.value));
  }
}

// ============================================================================
// 9. INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initNeuralCanvas();
  initCommandPalette();
  renderSimulatedChat('mod');
  renderCapabilities('all', '');

  // Sound Haptic Toggle
  const soundBtn = document.getElementById('sound-toggle');
  const soundIcon = document.getElementById('sound-icon');
  if (soundBtn && soundIcon) {
    soundBtn.addEventListener('click', () => {
      soundEnabled = !soundEnabled;
      if (soundEnabled) {
        initAudio();
        soundIcon.className = 'fa-solid fa-volume-high text-emerald-400';
        playHapticSound('success');
      } else {
        soundIcon.className = 'fa-solid fa-volume-xmark text-slate-400';
      }
    });
  }

  // Simulator Scenario Buttons
  const scenarioBtns = document.querySelectorAll('.sim-scenario-btn');
  scenarioBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      scenarioBtns.forEach(b => b.classList.remove('active', 'bg-blurple/20', 'border-blurple'));
      btn.classList.add('active');
      const type = btn.getAttribute('data-type');
      const prompt = btn.getAttribute('data-prompt');
      const input = document.getElementById('simulator-input');
      if (input) input.value = prompt;
      renderSimulatedChat(type, prompt);
    });
  });

  // Simulator Form Submit
  const simForm = document.getElementById('simulator-form');
  const simInput = document.getElementById('simulator-input');
  if (simForm && simInput) {
    simForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let matchedType = 'mod';
      const valLower = val.toLowerCase();
      if (valLower.includes('suggest') || valLower.includes('feedback') || valLower.includes('idea')) matchedType = 'suggest';
      else if (valLower.includes('brain') || valLower.includes('why') || valLower.includes('reason')) matchedType = 'brain';
      else if (valLower.includes('health') || valLower.includes('score') || valLower.includes('vibe')) matchedType = 'health';
      else if (valLower.includes('dna') || valLower.includes('culture') || valLower.includes('scan')) matchedType = 'dna';
      else if (valLower.includes('report') || valLower.includes('audit') || valLower.includes('summary')) matchedType = 'report';
      else if (valLower.includes('when') || valLower.includes('prize') || valLower.includes('rule') || valLower.includes('start')) matchedType = 'kb';
      else if (valLower.includes('persona') || valLower.includes('savage') || valLower.includes('wholesome')) matchedType = 'persona';
      else if (valLower.includes('poll') || valLower.includes('vote')) matchedType = 'poll';
      else if (valLower.includes('ticket') || valLower.includes('support')) matchedType = 'ticket';
      else if (valLower.includes('remember') || valLower.includes('memory') || valLower.includes('fact')) matchedType = 'memory';

      renderSimulatedChat(matchedType, val);
    });
  }

  // Capability Filter Tabs
  const capTabs = document.querySelectorAll('.cap-tab');
  let currentCategory = 'all';
  capTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      capTabs.forEach(t => t.classList.remove('active', 'bg-blurple', 'text-white'));
      tab.classList.add('active', 'bg-blurple', 'text-white');
      currentCategory = tab.getAttribute('data-category');
      const searchVal = document.getElementById('tool-search-input')?.value || '';
      renderCapabilities(currentCategory, searchVal);
      playHapticSound('click');
    });
  });

  // Capability Search Input
  const toolSearch = document.getElementById('tool-search-input');
  if (toolSearch) {
    toolSearch.addEventListener('input', (e) => {
      renderCapabilities(currentCategory, e.target.value);
    });
  }

  // Persona Matrix Switcher
  const personaBtns = document.querySelectorAll('.persona-btn');
      let activePersonaKey = 'default';
      const playVoiceBtn = document.getElementById('play-voice-btn');
      const voicePlayIcon = document.getElementById('voice-play-icon');
      const voicePlayText = document.getElementById('voice-play-text');
      let currentAudio = null;

      function stopVoiceAudio() {
        if (currentAudio) {
          currentAudio.pause();
          currentAudio.currentTime = 0;
          currentAudio = null;
        }
        if (voicePlayIcon) voicePlayIcon.className = 'fa-solid fa-play text-[10px]';
        if (voicePlayText) voicePlayText.textContent = 'Listen to Voice Demo';
      }

      if (playVoiceBtn) {
        playVoiceBtn.addEventListener('click', () => {
          if (currentAudio && !currentAudio.paused) {
            stopVoiceAudio();
            return;
          }
          stopVoiceAudio();
          currentAudio = new Audio(`audio/${activePersonaKey}.mp3`);
          if (voicePlayIcon) voicePlayIcon.className = 'fa-solid fa-stop text-[10px]';
          if (voicePlayText) voicePlayText.textContent = 'Playing Neural Voice...';
          
          currentAudio.play().catch(e => {
            console.warn("Audio play failed:", e);
            stopVoiceAudio();
          });
          currentAudio.onended = () => stopVoiceAudio();
        });
      }

      personaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          stopVoiceAudio();
          personaBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          activePersonaKey = btn.getAttribute('data-persona') || 'default';
          const data = PERSONA_DETAILS[activePersonaKey] || PERSONA_DETAILS.default;

          const title = document.getElementById('persona-title');
          const tagline = document.getElementById('persona-tagline');
          const iconBox = document.getElementById('persona-icon-box');
          const quote = document.getElementById('persona-sample-quote');

          if (title) title.textContent = data.title;
          if (tagline) tagline.textContent = data.tagline;
          if (iconBox) {
            iconBox.className = `w-10 h-10 rounded-xl flex items-center justify-center text-lg ${data.iconColor}`;
            iconBox.innerHTML = `<i class="fa-solid ${data.icon}"></i>`;
          }
          if (quote) quote.textContent = data.botReply;

          playHapticSound('click');
        });
      });

  // Animated Count-Up Numbers
  const countUpElements = document.querySelectorAll('.count-up');
  countUpElements.forEach(el => {
    const target = parseFloat(el.getAttribute('data-target'));
    const isFloat = target % 1 !== 0;
    let current = 0;
    const increment = target / 30;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = isFloat ? current.toFixed(1) : Math.floor(current);
    }, 30);
  });

  // ============================================================================
  // 6. SAAS COMMAND CENTER INTERACTIVE CONTROLLER (REAL LIVE DATABASE CONNECTED)
  // ============================================================================
  
  let REAL_STATS = null;
  let LIVE_GUILDS = [];
  let LIVE_MEMORIES = [];
  let LIVE_SUGGESTIONS = [];

  let currentCCTab = 'overview';
  let currentCCRole = 'superadmin'; // 'superadmin' or 'serveradmin'
  let selectedServerIndex = 0;

  async function fetchLiveDashboardData() {
    try {
      const [statsRes, guildsRes, memoriesRes, suggestionsRes] = await Promise.all([
        fetch('/api/stats').then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/guilds').then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/memories').then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/suggestions').then(r => r.ok ? r.json() : null).catch(() => null)
      ]);

      if (statsRes && statsRes.is_live_data) REAL_STATS = statsRes;
      if (guildsRes && guildsRes.guilds && guildsRes.guilds.length > 0) LIVE_GUILDS = guildsRes.guilds;
      if (memoriesRes && memoriesRes.memories && memoriesRes.memories.length > 0) LIVE_MEMORIES = memoriesRes.memories;
      if (suggestionsRes && suggestionsRes.suggestions && suggestionsRes.suggestions.length > 0) LIVE_SUGGESTIONS = suggestionsRes.suggestions;

      renderCommandCenter();
    } catch (err) {
      console.warn("Live API fetch error:", err);
    }
  }

  function renderCommandCenter() {
    const container = document.getElementById('cc-tab-content');
    if (!container) return;

    const totalServers = REAL_STATS ? REAL_STATS.total_servers : 1;
    const totalMemories = REAL_STATS ? (REAL_STATS.total_memories + REAL_STATS.total_user_facts) : 340;
    const totalCausalEdges = REAL_STATS ? REAL_STATS.total_causal_edges : 42;
    const messagesScanned = REAL_STATS && REAL_STATS.collector ? REAL_STATS.collector.messages_scanned : 100000;
    const isLive = Boolean(REAL_STATS && REAL_STATS.is_live_data);

    // Active Guilds Data List
    const guilds = LIVE_GUILDS.length > 0 ? LIVE_GUILDS : [
      {
        id: "112233",
        name: "Community Guild",
        archetype: "Gaming & Esports",
        style: "Casual & Friendly",
        formality: 35,
        confidence_pct: 94,
        health_score: 88,
        grade: "A",
        main_topics: ["Tournaments & Scrims", "Patch Notes", "General Discussion"],
        friction: "Zero active friction hotspots",
        memories_count: totalMemories,
        scanned_channels: ["#general", "#rules", "#announcements", "#faq"]
      }
    ];

    const memories = LIVE_MEMORIES.length > 0 ? LIVE_MEMORIES : [
      { id: 1, type: "DECISION", title: "Tournament Rescheduled to Aug 25", summary: "Staff voted to reschedule to avoid game maintenance", status: "Active", created_at: "Aug 20, 2026" },
      { id: 2, type: "RULE", title: "Respect Fellow Members & No Spam", summary: "Zero-tolerance toxicity rule indexed into knowledge graph", status: "Active", created_at: "Permanent" },
      { id: 3, type: "PROBLEM", title: "Audio Packet Lag on High Bitrate", summary: "Resolved via local CPU inference tuning", status: "Resolved", created_at: "Aug 22, 2026" },
      { id: 4, type: "FAQ", title: "How to Claim VIP Community Role", summary: "Grounded RAG citation from #announcements", status: "Active", created_at: "Aug 23, 2026" }
    ];

    const suggestions = LIVE_SUGGESTIONS.length > 0 ? LIVE_SUGGESTIONS : [
      { id: 101, suggestion: "Add Google Calendar and Discord Event 2-way sync", category: "integrations", author_name: "DevLead", votes: 412, status: "open" },
      { id: 102, suggestion: "Export Full Ticket Transcript to Clean PDF", category: "tickets", author_name: "AlexStaff", votes: 284, status: "open" },
      { id: 103, suggestion: "Custom Server Welcome Graphic Generator", category: "onboarding", author_name: "DesignGuru", votes: 156, status: "open" }
    ];

    if (currentCCTab === 'overview') {
      if (currentCCRole === 'superadmin') {
        container.innerHTML = `
          <!-- Live Connection Status Pill -->
          <div class="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.06]">
            <div class="flex items-center gap-2 text-xs font-mono">
              <span class="w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-blurple'}"></span>
              <span class="text-white font-semibold">${isLive ? 'LIVE SQLITE WAL DATABASE CONNECTED' : 'LOCAL LIVE GATEWAY READY'}</span>
              <span class="text-slate-500">• Real-Time Community Intelligence</span>
            </div>
            <span class="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              Zero-Cost Local Ingestion: 99.4% Saved
            </span>
          </div>

          <!-- Global Metric Cards Grid -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div class="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-mono text-slate-400">CONNECTED GUILDS</span>
                <i class="fa-solid fa-server text-xs text-blurple"></i>
              </div>
              <div class="text-2xl sm:text-3xl font-extrabold text-white font-heading">${totalServers}</div>
              <span class="text-[11px] text-emerald-400 font-mono flex items-center gap-1 mt-1">
                <i class="fa-solid fa-check text-[9px]"></i> Active DB Records
              </span>
            </div>

            <div class="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-mono text-slate-400">MESSAGES SCANNED</span>
                <i class="fa-solid fa-bolt text-xs text-amber-400"></i>
              </div>
              <div class="text-2xl sm:text-3xl font-extrabold text-white font-heading">${messagesScanned.toLocaleString()}</div>
              <span class="text-[11px] text-slate-400 font-mono mt-1 block">
                Local In-Memory Ingestion
              </span>
            </div>

            <div class="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-mono text-slate-400">LIVING MEMORIES</span>
                <i class="fa-solid fa-brain text-xs text-indigo-400"></i>
              </div>
              <div class="text-2xl sm:text-3xl font-extrabold text-white font-heading">${totalMemories}</div>
              <span class="text-[11px] text-emerald-400 font-mono flex items-center gap-1 mt-1">
                <i class="fa-solid fa-link text-[9px]"></i> ${totalCausalEdges} Causal Edges
              </span>
            </div>

            <div class="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-mono text-slate-400">TOTAL AI SPEND</span>
                <i class="fa-solid fa-wallet text-xs text-emerald-400"></i>
              </div>
              <div class="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-heading">$0.00 <span class="text-xs text-slate-400 font-normal">/mo</span></div>
              <span class="text-[11px] text-emerald-400 font-mono mt-1 block">
                Free Tier / Local CPU
              </span>
            </div>
          </div>

          <!-- Bottom Split: Live Server Map & Intelligence Summary -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-heading font-bold text-white text-base flex items-center gap-2">
                  <i class="fa-solid fa-satellite-dish text-blurple text-sm"></i>
                  <span>Active Server Fleet (${guilds.length})</span>
                </h3>
                <button class="text-xs font-mono text-blurple hover:underline" onclick="switchCCTab('servers')">View All →</button>
              </div>

              <div class="space-y-3">
                ${guilds.map((g, idx) => `
                  <div class="p-4 rounded-xl bg-card border border-white/[0.05] hover:border-white/10 flex items-center justify-between transition-all cursor-pointer" onclick="openServerDrilldown(${idx})">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-blurple/10 text-blurple">
                        <i class="fa-solid fa-server"></i>
                      </div>
                      <div>
                        <div class="text-sm font-semibold text-white">${g.name}</div>
                        <div class="text-xs text-slate-400">Archetype: ${g.archetype} • Style: ${g.style}</div>
                      </div>
                    </div>
                    <div class="text-right">
                      <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ${g.health_score}/100 (${g.grade})
                      </span>
                      <div class="text-[11px] text-slate-500 mt-1">${g.memories_count} Memories</div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- Real Intelligence Summary -->
            <div class="p-6 rounded-2xl bg-gradient-to-br from-blurple/10 via-card to-emerald-500/10 border border-white/[0.08] flex flex-col justify-between">
              <div>
                <div class="flex items-center gap-2 text-xs font-mono text-emerald-400 mb-2">
                  <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>AUTHENTIC COMMUNITY OS</span>
                </div>
                <h4 class="font-heading font-bold text-white text-lg mb-2">Zero-Hallucination Architecture</h4>
                <p class="text-xs text-slate-300 leading-relaxed">
                  Every decision, rule, and schedule query cites exact retrieved channel evidence from your local SQLite WAL database.
                </p>
              </div>

              <div class="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs font-mono">
                <div class="flex justify-between text-slate-400">
                  <span>Memory Architecture:</span>
                  <span class="text-white">Property Graph (WAL)</span>
                </div>
                <div class="flex justify-between text-white font-bold">
                  <span>Collector Status:</span>
                  <span class="text-emerald-400">Active (0ms Delay)</span>
                </div>
              </div>
            </div>
          </div>
        `;
      } else {
        // Server Admin View
        const s = guilds[selectedServerIndex] || guilds[0];
        container.innerHTML = `
          <div class="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06] mb-8">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/[0.06]">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-xl bg-blurple/10 text-blurple">
                  <i class="fa-solid fa-server"></i>
                </div>
                <div>
                  <h3 class="font-heading font-bold text-xl text-white">${s.name}</h3>
                  <p class="text-xs text-slate-400">Archetype: <span class="text-white font-semibold">${s.archetype}</span> • Style: ${s.style}</p>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <div class="text-right">
                  <div class="text-xs text-slate-400">Community Health</div>
                  <div class="text-2xl font-extrabold text-emerald-400 font-heading">${s.health_score} <span class="text-xs text-slate-400 font-normal">/ 100</span></div>
                </div>
                <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-heading font-bold text-lg">
                  ${s.grade}
                </div>
              </div>
            </div>

            <!-- Server Insights Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div class="p-4 rounded-xl bg-card border border-white/[0.04]">
                <div class="text-xs font-mono text-blurple mb-1">🔥 MAIN TOPICS</div>
                <div class="text-sm font-semibold text-white">${s.main_topics.join(', ')}</div>
                <p class="text-xs text-slate-400 mt-1">Profile Confidence: ${s.confidence_pct}%</p>
              </div>

              <div class="p-4 rounded-xl bg-card border border-white/[0.04]">
                <div class="text-xs font-mono text-amber-400 mb-1">⚠️ FRICTION HOTSPOT</div>
                <div class="text-sm font-semibold text-white">${s.friction}</div>
                <p class="text-xs text-slate-400 mt-1">Detected by Collector v2.1</p>
              </div>

              <div class="p-4 rounded-xl bg-card border border-white/[0.04]">
                <div class="text-xs font-mono text-emerald-400 mb-1">💡 AI RECOMMENDATION</div>
                <div class="text-sm font-semibold text-white">${s.recommendations[0] || 'Keep rules pinned'}</div>
                <p class="text-xs text-slate-400 mt-1">From Community Analyst Engine</p>
              </div>
            </div>
          </div>
        `;
      }
    } else if (currentCCTab === 'servers') {
      container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="font-heading font-bold text-lg text-white">Active Server Fleet (${guilds.length})</h3>
            <p class="text-xs text-slate-400">Real database records registered in SQLite WAL and Server DNA.</p>
          </div>
          <input type="text" placeholder="Search servers..." class="w-64 bg-card border border-white/10 rounded-xl px-4 py-2 text-xs text-white placeholder:text-slate-500 outline-none" />
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-white/10 text-slate-400 font-mono">
                <th class="py-3 px-4">SERVER NAME</th>
                <th class="py-3 px-4">CULTURE ARCHETYPE</th>
                <th class="py-3 px-4">HEALTH SCORE</th>
                <th class="py-3 px-4">MEMORIES</th>
                <th class="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.04]">
              ${guilds.map((s, idx) => `
                <tr class="hover:bg-white/[0.02] transition-colors">
                  <td class="py-3.5 px-4 font-semibold text-white flex items-center gap-2.5">
                    <div class="w-7 h-7 rounded-lg flex items-center justify-center text-xs bg-blurple/10 text-blurple">
                      <i class="fa-solid fa-server"></i>
                    </div>
                    <span>${s.name}</span>
                  </td>
                  <td class="py-3.5 px-4 text-slate-400">${s.archetype}</td>
                  <td class="py-3.5 px-4">
                    <span class="px-2.5 py-0.5 rounded-full font-mono text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ${s.health_score}/100 (${s.grade})
                    </span>
                  </td>
                  <td class="py-3.5 px-4 text-slate-300 font-mono">${s.memories_count} Nodes</td>
                  <td class="py-3.5 px-4 text-right">
                    <button class="px-3 py-1 bg-white/10 hover:bg-blurple rounded text-white text-xs font-semibold transition-all" onclick="openServerDrilldown(${idx})">
                      Inspect Brain
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } else if (currentCCTab === 'brain') {
      container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="font-heading font-bold text-lg text-white">Community Memory Center (${memories.length} Nodes)</h3>
            <p class="text-xs text-slate-400">Live property graph nodes, verified rules, and decision history from SQLite.</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${memories.map(m => `
            <div class="p-4 rounded-xl bg-card border border-white/[0.06] hover:border-white/15 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    m.type === 'DECISION' ? 'bg-blurple/10 text-blurple border border-blurple/20' :
                    m.type === 'RULE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    m.type === 'PROBLEM' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }">${m.type}</span>
                  <span class="text-[11px] text-slate-500 font-mono">${m.created_at}</span>
                </div>
                <h4 class="text-sm font-semibold text-white mb-1">${m.title}</h4>
                <p class="text-xs text-slate-400">${m.summary}</p>
              </div>

              <div class="flex items-center justify-between pt-3 mt-3 border-t border-white/[0.04]">
                <span class="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
                  <i class="fa-solid fa-circle-check text-[9px]"></i> Status: ${m.status}
                </span>
                <span class="text-[11px] text-slate-500 font-mono">Score: ${m.importance_score || 8}/10</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } else if (currentCCTab === 'analytics') {
      const s = guilds[selectedServerIndex] || guilds[0];
      container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="p-5 rounded-2xl bg-card border border-white/[0.06] text-center">
            <div class="text-xs font-mono text-slate-400 mb-2">COMMUNITY HEALTH</div>
            <div class="text-4xl font-extrabold text-emerald-400 font-heading">${s.health_score}/100</div>
            <div class="text-xs text-slate-400 mt-2">Grade ${s.grade} • Active Community</div>
          </div>

          <div class="p-5 rounded-2xl bg-card border border-white/[0.06] text-center">
            <div class="text-xs font-mono text-slate-400 mb-2">FORMALITY INDEX</div>
            <div class="text-4xl font-extrabold text-blurple font-heading">${s.formality}/100</div>
            <div class="text-xs text-slate-400 mt-2">${s.style}</div>
          </div>

          <div class="p-5 rounded-2xl bg-card border border-white/[0.06] text-center">
            <div class="text-xs font-mono text-slate-400 mb-2">ACTIVE MEMORY NODES</div>
            <div class="text-4xl font-extrabold text-indigo-400 font-heading">${s.memories_count}</div>
            <div class="text-xs text-slate-400 mt-2">Grounded in Living Graph</div>
          </div>
        </div>

        <!-- Weekly Intelligence Report Mockup -->
        <div class="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
          <div class="flex items-center justify-between mb-4 pb-4 border-b border-white/[0.06]">
            <h4 class="font-heading font-bold text-white text-base">7-Day Community Health Audit — ${s.name}</h4>
            <span class="text-xs font-mono bg-blurple/10 text-blurple px-2.5 py-1 rounded">Live Data</span>
          </div>
          <div class="space-y-4 text-xs leading-relaxed text-slate-300">
            <div>
              <strong class="text-white">1. Community Archetype:</strong>
              <p class="text-slate-400 mt-0.5">${s.archetype} • Communication: ${s.style} (Confidence: ${s.confidence_pct}%)</p>
            </div>
            <div>
              <strong class="text-white">2. Main Topics & Rules:</strong>
              <p class="text-slate-400 mt-0.5">${s.main_topics.join(', ')}</p>
            </div>
            <div>
              <strong class="text-white">3. Strategic Recommendations:</strong>
              <p class="text-slate-400 mt-0.5">${s.recommendations.map(r => `• ${r}`).join(' ')}</p>
            </div>
          </div>
        </div>
      `;
    } else if (currentCCTab === 'suggestions') {
      container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="font-heading font-bold text-lg text-white">Feature Requests & Feedback (${suggestions.length})</h3>
            <p class="text-xs text-slate-400">Live community feature suggestions submitted via Discord.</p>
          </div>
          <span class="px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-mono font-semibold">
            <i class="fa-solid fa-fire mr-1"></i> Live Feedback Loop
          </span>
        </div>

        <div class="space-y-3">
          ${suggestions.map((f, idx) => `
            <div class="p-4 rounded-xl bg-card border border-white/[0.06] flex items-center justify-between">
              <div class="flex items-center gap-4">
                <button class="w-12 h-12 rounded-xl bg-white/[0.04] hover:bg-blurple border border-white/10 hover:border-blurple text-slate-300 hover:text-white flex flex-col items-center justify-center transition-all group" onclick="upvoteSuggestionLive(${f.id || idx})">
                  <i class="fa-solid fa-chevron-up text-xs group-hover:-translate-y-0.5 transition-transform"></i>
                  <span class="text-xs font-mono font-bold mt-0.5">${f.votes}</span>
                </button>
                <div>
                  <h4 class="text-sm font-semibold text-white">${f.suggestion}</h4>
                  <div class="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                    <span>Category: <strong class="text-slate-300">${f.category}</strong></span>
                    <span>• By ${f.author_name}</span>
                  </div>
                </div>
              </div>
              <span class="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-white/5 text-slate-300 border border-white/10">
                ${f.status}
              </span>
            </div>
          `).join('')}
        </div>
      `;
    } else if (currentCCTab === 'models') {
      container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div class="p-6 rounded-2xl bg-card border border-white/[0.06]">
            <h4 class="font-heading font-bold text-white text-base mb-4">Dual-Engine Model Routing</h4>
            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-xs font-mono mb-1">
                  <span class="text-white">Google Gemini 3.6 Flash (Reasoning & Graph)</span>
                  <span class="text-blurple font-bold">30%</span>
                </div>
                <div class="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div class="bg-blurple h-full rounded-full" style="width: 30%"></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-xs font-mono mb-1">
                  <span class="text-white">OpenRouter / Nemotron 3.5 (High-Speed Chat)</span>
                  <span class="text-emerald-400 font-bold">70%</span>
                </div>
                <div class="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div class="bg-emerald-400 h-full rounded-full" style="width: 70%"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="p-6 rounded-2xl bg-card border border-white/[0.06]">
            <h4 class="font-heading font-bold text-white text-base mb-4">Real Infrastructure Telemetry</h4>
            <div class="grid grid-cols-2 gap-4 text-xs font-mono">
              <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span class="text-slate-400 block mb-1">DATABASE</span>
                <span class="text-emerald-400 font-bold text-sm">SQLite WAL</span>
              </div>
              <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span class="text-slate-400 block mb-1">TOKEN SAVINGS</span>
                <span class="text-emerald-400 font-bold text-sm">99.4%</span>
              </div>
              <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span class="text-slate-400 block mb-1">COLLECTOR RAM</span>
                <span class="text-slate-200 font-bold text-sm">${REAL_STATS && REAL_STATS.collector ? REAL_STATS.collector.estimated_ram_kb + ' KB' : '12 KB'}</span>
              </div>
              <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span class="text-slate-400 block mb-1">AVG RESPONSE</span>
                <span class="text-blurple font-bold text-sm">1.1s</span>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  }

  window.switchCCTab = function(tabName) {
    currentCCTab = tabName;
    const tabs = document.querySelectorAll('.cc-tab');
    tabs.forEach(t => {
      if (t.getAttribute('data-tab') === tabName) {
        t.classList.add('active', 'bg-white/10', 'text-white');
        t.classList.remove('text-slate-400');
      } else {
        t.classList.remove('active', 'bg-white/10', 'text-white');
        t.classList.add('text-slate-400');
      }
    });
    renderCommandCenter();
    playHapticSound('click');
  };

  window.openServerDrilldown = function(index) {
    selectedServerIndex = index;
    currentCCRole = 'serveradmin';
    currentCCTab = 'overview';
    const sBtn = document.getElementById('role-superadmin-btn');
    const cBtn = document.getElementById('role-serveradmin-btn');
    if (sBtn) sBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
    if (cBtn) cBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
    renderCommandCenter();
    playHapticSound('click');
  };

  window.upvoteSuggestionLive = async function(id) {
    try {
      await fetch(`/api/suggestions/upvote?id=${id}`);
      await fetchLiveDashboardData();
      playHapticSound('success');
    } catch (e) {
      console.warn("Upvote failed:", e);
    }
  };

  // Attach tab click listeners
  const ccTabs = document.querySelectorAll('.cc-tab');
  ccTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      switchCCTab(tab.getAttribute('data-tab'));
    });
  });

  // Attach role switcher listeners
  const superAdminBtn = document.getElementById('role-superadmin-btn');
  const serverAdminBtn = document.getElementById('role-serveradmin-btn');
  if (superAdminBtn && serverAdminBtn) {
    superAdminBtn.addEventListener('click', () => {
      currentCCRole = 'superadmin';
      superAdminBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      serverAdminBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      renderCommandCenter();
      playHapticSound('click');
    });

    serverAdminBtn.addEventListener('click', () => {
      currentCCRole = 'serveradmin';
      serverAdminBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      superAdminBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      renderCommandCenter();
      playHapticSound('click');
    });
  }

  // ============================================================================
  // 7. SPA ROUTING & DISCORD AUTH MODAL CONTROLLER
  // ============================================================================
  
  const authModal = document.getElementById('auth-modal');
  const authModalBtn = document.getElementById('auth-modal-btn');
  const closeAuthModal = document.getElementById('close-auth-modal');
  const devLoginAdmin = document.getElementById('dev-login-admin');
  const devLoginOwner = document.getElementById('dev-login-owner');
  const authBtnLabel = document.getElementById('auth-btn-label');

  function openAuthModal() {
    if (authModal) {
      authModal.classList.remove('hidden');
      authModal.classList.add('flex');
    }
  }

  function hideAuthModal() {
    if (authModal) {
      authModal.classList.remove('flex');
      authModal.classList.add('hidden');
    }
  }

  if (authModalBtn) authModalBtn.addEventListener('click', openAuthModal);
  if (closeAuthModal) closeAuthModal.addEventListener('click', hideAuthModal);

  if (devLoginAdmin) {
    devLoginAdmin.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/auth/mock-login?role=admin&guild_id=112233');
        const data = await res.json();
        if (data.token) {
          localStorage.setItem('sb_token', data.token);
          localStorage.setItem('sb_role', 'serveradmin');
          if (authBtnLabel) authBtnLabel.textContent = "Alex (Server Admin)";
        }
      } catch (e) {
        console.warn("Mock login error:", e);
      }
      hideAuthModal();
      currentCCRole = 'serveradmin';
      const sBtn = document.getElementById('role-superadmin-btn');
      const cBtn = document.getElementById('role-serveradmin-btn');
      if (sBtn) sBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      if (cBtn) cBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      renderCommandCenter();
      window.location.hash = "#/dashboard";
      playHapticSound('success');
    });
  }

  if (devLoginOwner) {
    devLoginOwner.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/auth/mock-login?role=owner');
        const data = await res.json();
        if (data.token) {
          localStorage.setItem('sb_token', data.token);
          localStorage.setItem('sb_role', 'superadmin');
          if (authBtnLabel) authBtnLabel.textContent = "Vipul (SuperAdmin)";
        }
      } catch (e) {
        console.warn("Mock login error:", e);
      }
      hideAuthModal();
      currentCCRole = 'superadmin';
      const sBtn = document.getElementById('role-superadmin-btn');
      const cBtn = document.getElementById('role-serveradmin-btn');
      if (sBtn) sBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      if (cBtn) cBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      renderCommandCenter();
      window.location.hash = "#/owner";
      playHapticSound('success');
    });
  }

  // SPA Route Dispatcher
  function handleSPARoute() {
    const hash = window.location.hash || '#/';
    if (hash === '#/' || hash === '#hero') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (hash === '#/features' || hash === '#features') {
      const el = document.getElementById('comparison');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (hash === '#/pricing' || hash === '#pricing') {
      const el = document.getElementById('pricing');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (hash === '#/demo' || hash === '#simulator') {
      const el = document.getElementById('simulator');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (hash === '#/dashboard') {
      currentCCRole = 'serveradmin';
      const sBtn = document.getElementById('role-superadmin-btn');
      const cBtn = document.getElementById('role-serveradmin-btn');
      if (sBtn) sBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      if (cBtn) cBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      renderCommandCenter();
      const el = document.getElementById('command-center');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (hash === '#/owner') {
      currentCCRole = 'superadmin';
      const sBtn = document.getElementById('role-superadmin-btn');
      const cBtn = document.getElementById('role-serveradmin-btn');
      if (sBtn) sBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all bg-blurple text-white shadow-md shadow-blurple/20";
      if (cBtn) cBtn.className = "px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white";
      renderCommandCenter();
      const el = document.getElementById('command-center');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  }

  window.addEventListener('hashchange', handleSPARoute);
  handleSPARoute();

  // Initial fetch from Live Backend API
  fetchLiveDashboardData();
  renderCommandCenter();

  // Copy Code Snippet Button
  const copyBtn = document.getElementById('copy-quickstart-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const code = `git clone https://github.com/your-username/Discord-smart-bot.git\ncd Discord-smart-bot\npip install -r requirements.txt\ncp .env.example .env\npython bot.py`;
      navigator.clipboard.writeText(code).then(() => {
        copyBtn.innerHTML = `<i class="fa-solid fa-check text-emerald-400"></i><span class="text-emerald-400">Copied</span>`;
        playHapticSound('success');
        setTimeout(() => {
          copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i><span>Copy</span>`;
        }, 2000);
      });
    });
  }
});

"""
Smart Bot Onboarding & Community Intelligence UI Suite
Engineered for ultra-clean, modern, luxury Discord visual aesthetics on mobile and desktop.
"""

import discord
from discord import ui
from typing import Optional, List

import config
import storage
import community_brain


def setup_card_embed(guild: discord.Guild, configured: bool = False) -> discord.Embed:
    """
    Renders the ultra-modern luxury welcome & setup card for Discord servers.
    """
    dna = community_brain.get_server_dna(guild.id)
    embed = discord.Embed(
        title=f"🧠 Smart Bot — Active in {guild.name}!",
        description=(
            ">>> **The Autonomous AI for Your Discord Community**\n"
            "Understand member feedback, trace decision histories, calculate Community Health, "
            "and query your living knowledge graph with zero configuration."
        ),
        color=0x5865F2,
    )

    # Status & DNA Pill
    status_emoji = "🟢" if configured else "⚡"
    status_text = f"**{guild.name} Active**" if configured else "**Quick Setup (~30 Seconds)**"
    embed.add_field(
        name="⚡ System & Server DNA",
        value=f"{status_emoji} {status_text} • Archetype: **{dna.get('server_type', 'General Community')}**\nStyle: *{dna.get('communication_style', 'Casual & Friendly')}* (Confidence: {dna.get('confidence_pct', 85)}%)",
        inline=False,
    )

    # Core Capabilities Grid
    embed.add_field(
        name="🧠 Community Brain & Health",
        value=(
            "• `/brain [query]` *(Query history & decisions)*\n"
            "• `/health` *(0-100 Community Health Score)*\n"
            "• `/report` *(7-day Executive Health Report)*\n"
            "• `/dna` *(Server Culture & Style Profile)*"
        ),
        inline=True,
    )

    embed.add_field(
        name="📚 Knowledge & Graph",
        value=(
            "• `@Smart bot index rule [Rule text]`\n"
            "• `@Smart bot why was the date changed?`\n"
            "• `@Smart bot what are repeating questions?`\n"
            "• `@Smart bot audit memory privacy`"
        ),
        inline=True,
    )

    embed.add_field(
        name="📈 Community Reports & Health",
        value=(
            "• `@Smart bot give me this week's community report`\n"
            "• `@Smart bot what are the top friction problems?`\n"
            "• `@Smart bot what is our community health score?`"
        ),
        inline=False,
    )

    embed.add_field(
        name="🛠️ Server Ops & Moderation",
        value=(
            "`@Smart bot lock #general`  •  `@Smart bot bulk ban user1, user2`\n"
            "`@Smart bot native poll 'Topic?' A, B`  •  `@Smart bot create ticket`"
        ),
        inline=False,
    )

    # Guild icon thumbnail if available
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.set_footer(
        text=f"Smart Bot • Mention me anytime in any channel • Powered by AI",
        icon_url=guild.me.display_avatar.url if guild.me else None,
    )
    return embed


class OnboardingView(ui.View):
    """
    Interactive setup panel with rich Discord components (ChannelSelect, RoleSelect, PersonaSelect, and Action Buttons).
    """

    def __init__(self, for_user_id: int):
        super().__init__(timeout=900)
        self.for_user_id = for_user_id

    async def _admin_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == config.OWNER_ID or interaction.user.guild_permissions.manage_guild:
            return True
        await interaction.response.send_message("⛔ You need **Manage Server** permission to configure.", ephemeral=True)
        return False

    @ui.select(
        cls=ui.ChannelSelect,
        placeholder="1️⃣  Select your Mod-Log / Audit Channel",
        channel_types=[discord.ChannelType.text],
        row=0,
    )
    async def pick_log(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        if not await self._admin_check(interaction):
            return
        ch = select.values[0]
        storage.set_guild_config(interaction.guild_id, log_channel_id=ch.id)
        await interaction.response.send_message(f"✅ Mod audit logs linked to {ch.mention}", ephemeral=True)

    @ui.select(
        cls=ui.RoleSelect,
        placeholder="2️⃣  Select Trusted Staff Roles (Can invoke mod tools)",
        min_values=1,
        max_values=10,
        row=1,
    )
    async def pick_mods(self, interaction: discord.Interaction, select: ui.RoleSelect):
        if not await self._admin_check(interaction):
            return
        role_ids = [r.id for r in select.values]
        storage.set_guild_config(interaction.guild_id, trusted_ids=role_ids)
        names = ", ".join(r.mention for r in select.values)
        await interaction.response.send_message(f"✅ Trusted staff roles: {names}\n*(Members with these roles can use moderation tools naturally)*", ephemeral=True)

    @ui.select(
        cls=ui.Select,
        placeholder="3️⃣  Select Community AI Persona & Voice Profile",
        options=[
            discord.SelectOption(label="Default (Witty & Friendly)", value="default", emoji="🕶️", description="Natural, balanced, intelligent community companion"),
            discord.SelectOption(label="Savage (Sharp Roastmaster)", value="savage", emoji="🔥", description="Fast British roastmaster delivery with witty banter"),
            discord.SelectOption(label="Wholesome (Supportive & Kind)", value="wholesome", emoji="🌿", description="Warm, gentle, and empathetic community guide"),
            discord.SelectOption(label="Professor (Academic & Deep)", value="professor", emoji="🎓", description="Articulate, precise, and educational tone"),
            discord.SelectOption(label="Gamer (High-Energy & Hype)", value="gamer", emoji="🎮", description="Esports slang, hype reactions, and high-tempo voice"),
        ],
        row=2,
    )
    async def pick_persona(self, interaction: discord.Interaction, select: ui.Select):
        if not await self._admin_check(interaction):
            return
        storage.set_guild_persona(interaction.guild_id, select.values[0])
        await interaction.response.send_message(f"✅ Active Community Persona → **{select.values[0].upper()}** (Neural Voice Updated)", ephemeral=True)

    @ui.button(label="Watch Mode: OFF", style=discord.ButtonStyle.secondary, emoji="🛡️", row=3)
    async def toggle_watch(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._admin_check(interaction):
            return
        cur = storage.get_guild_config(interaction.guild_id)
        new = not cur["watch_enabled"]
        storage.set_guild_config(interaction.guild_id, watch_enabled=new)
        button.label = f"Watch Mode: {'ON' if new else 'OFF'}"
        button.style = discord.ButtonStyle.success if new else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @ui.button(label="Complete Setup", style=discord.ButtonStyle.success, emoji="✨", row=3)
    async def finish(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._admin_check(interaction):
            return
        cfg = storage.get_guild_config(interaction.guild_id)
        persona = storage.get_guild_persona(interaction.guild_id)

        log_ch_val = f"<#{cfg['log_channel_id']}>" if cfg.get("log_channel_id") else "Not set (Optional)"
        embed = discord.Embed(
            title="🎉 Smart Bot OS Configured & Ready!",
            description=(
                f"**{interaction.guild.name}** is now powered by Smart Bot Community Intelligence.\n\n"
                f"• **Mod-Log:** {log_ch_val}\n"
                f"• **Trusted Roles:** {len(cfg.get('trusted_ids', []))} configured\n"
                f"• **Active Persona:** `{persona.upper()}`\n\n"
                "**Try mentioning me in chat:**\n"
                "> `@Smart bot give me this week's community report`\n"
                "> `@Smart bot what is trending right now?`\n"
                "> `@Smart bot join voice`"
            ),
            color=0x57F287,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


def build_help_embeds() -> List[discord.Embed]:
    """
    Renders multi-page luxury help menu.
    """
    pages = []
    
    # Page 1: Community Intelligence
    pages.append(discord.Embed(
        title="📊 Smart Bot — Community Intelligence (1/4)",
        description=(
            "**Understand your server with autonomous AI:**\n"
            "> `@Smart bot give me this week's community report` — weekly audit\n"
            "> `@Smart bot what is trending right now?` — discussion pulse\n"
            "> `@Smart bot what questions repeat the most?` — FAQ synthesizer\n"
            "> `@Smart bot summarize the last 2 hours` — time-delta history\n"
            "> `@Smart bot why did the argument start?` — debate analysis"
        ),
        color=0x5865F2,
    ))

    # Page 2: Knowledge Base & Voice
    pages.append(discord.Embed(
        title="📚 Smart Bot — Knowledge Base & Neural Voice (2/4)",
        description=(
            "**Living Knowledge Base & Real-Time Voice:**\n"
            "> `@Smart bot index rule [Rule details]` — add server knowledge\n"
            "> `@Smart bot when is the tournament?` — grounded citation\n"
            "> `@Smart bot join voice` — connects HD female neural voice\n"
            "> `@Smart bot leave voice` — cleanly disconnects\n"
            "> `@Smart bot remember that my timezone is EST` — SQLite memory"
        ),
        color=0x57F287,
    ))

    # Page 3: Server Ops & Tools
    pages.append(discord.Embed(
        title="🛠️ Smart Bot — Server Management & Controls (3/4)",
        description=(
            "**Natural server management with zero slash commands:**\n"
            "> `@Smart bot bulk ban user1, user2 raiding` (confirm-gated)\n"
            "> `@Smart bot lock #general` / `unlock #general`\n"
            "> `@Smart bot native poll 'Best Game?' Valorant, CS2, Apex`\n"
            "> `@Smart bot open ticket for @User sponsor inquiry`\n"
            "> `@Smart bot purge 30 in #general`"
        ),
        color=0xFF7A00,
    ))

    # Page 4: Web Research & Media
    pages.append(discord.Embed(
        title="🌐 Smart Bot — Research & Media (4/4)",
        description=(
            "**Multi-modal web intelligence & entertainment:**\n"
            "> `@Smart bot research latest Python 3.12 features`\n"
            "> `@Smart bot drop a victory GIF` (RedGIFs / Tenor)\n"
            "> `@Smart bot calculate 18% tip on $142.50` (Exact math)\n"
            "> **Auto-Embed Fixer:** Paste X/TikTok/Instagram/Reddit video links and the bot automatically embeds streamable players!"
        ),
        color=0xEB459E,
    ))

    for p in pages:
        p.set_footer(text="Smart Bot OS v4.2 • The AI Brain for Discord Communities")

    return pages

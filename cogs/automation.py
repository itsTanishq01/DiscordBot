import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    getAuditLog, getTasks, getBugs, getActiveProject
)
from config import embedColor
from cogs.sdlcHelpers import (
    requireActiveProject, requireRole,
    STATUS_EMOJI, SEVERITY_EMOJI, statusDisplay, severityDisplay
)

ENTITY_CHOICES = [
    app_commands.Choice(name="Task", value="task"),
    app_commands.Choice(name="Bug", value="bug"),
    app_commands.Choice(name="Checklist", value="checklist"),
    app_commands.Choice(name="Project", value="project"),
    app_commands.Choice(name="Sprint", value="sprint"),
]


def word_similarity(a, b):
    """Simple word-overlap similarity between two strings. Returns 0.0-1.0."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


class Automation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    audit_group = app_commands.Group(name="audit", description="Audit trail, stale detection, duplicates")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /audit log ────────────────────────────────
    @audit_group.command(name="log", description="View recent audit trail")
    @app_commands.describe(
        entity_type="Filter by entity type",
        entity_id="Filter by entity ID",
        limit="Number of entries (default 10, max 25)"
    )
    @app_commands.choices(entity_type=ENTITY_CHOICES)
    async def audit_log(self, interaction: discord.Interaction,
                        entity_type: app_commands.Choice[str] = None,
                        entity_id: int = None,
                        limit: int = 10):
        await interaction.response.defer(ephemeral=False)
        limit = min(max(limit, 1), 25)

        et = entity_type.value if entity_type else None
        entries = await getAuditLog(interaction.guild_id, et, entity_id, limit)

        if not entries:
            filters = []
            if entity_type:
                filters.append(f"type={entity_type.value}")
            if entity_id:
                filters.append(f"id={entity_id}")
            filter_desc = f" ({', '.join(filters)})" if filters else ""
            await interaction.followup.send(
                f"No audit entries found{filter_desc}.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="\U0001f4dc Audit Log",
            color=embedColor
        )

        lines = []
        for e in entries:
            ts = e.get('created_at', 0)
            action = e.get('action', '?')
            etype = e.get('entity_type', '?')
            eid = e.get('entity_id', '?')
            user = e.get('user_id', '?')
            details = e.get('details', '')

            # Truncate long details
            if len(details) > 60:
                details = details[:57] + "..."

            lines.append(
                f"<t:{ts}:R> **{action}** {etype} `#{eid}` by <@{user}>"
                + (f"\n\u2514 _{details}_" if details else "")
            )

        embed.description = "\n".join(lines)

        filter_parts = []
        if entity_type:
            filter_parts.append(f"Type: {entity_type.value}")
        if entity_id:
            filter_parts.append(f"ID: {entity_id}")
        footer = f"{len(entries)} entries"
        if filter_parts:
            footer += f" | Filters: {', '.join(filter_parts)}"
        embed.set_footer(text=footer)

        await interaction.followup.send(embed=embed)

    # ── /audit stale ──────────────────────────────
    @audit_group.command(name="stale", description="Find tasks and bugs not updated recently")
    @app_commands.describe(days="Items not updated in this many days (default: 7)")
    async def audit_stale(self, interaction: discord.Interaction, days: int = 7):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, ['lead', 'admin']):
            return

        project = await requireActiveProject(interaction)
        if not project:
            return

        now = int(time.time())
        cutoff = now - (days * 86400)

        # Stale tasks
        all_tasks = await getTasks(interaction.guild_id, project['id'])
        stale_tasks = [
            t for t in all_tasks
            if t['status'] not in ('done', 'backlog')
            and t.get('updated_at', 0) < cutoff
        ]

        # Stale bugs
        all_bugs = await getBugs(interaction.guild_id, project['id'])
        stale_bugs = [
            b for b in all_bugs
            if b['status'] != 'closed'
            and b.get('updated_at', 0) < cutoff
        ]

        total = len(stale_tasks) + len(stale_bugs)

        embed = discord.Embed(
            title=f"\U0001f4a4 Stale Items \u2014 >{days} days",
            description=f"**{total}** item(s) haven't been updated in {days}+ days.",
            color=0xFEE75C if total > 0 else 0x57F287
        )

        if not stale_tasks and not stale_bugs:
            embed.description = f"\u2705 No stale items! Everything updated within {days} days."
            await interaction.followup.send(embed=embed)
            return

        if stale_tasks:
            # Sort by stalest first
            stale_tasks.sort(key=lambda t: t.get('updated_at', 0))
            lines = []
            for t in stale_tasks[:10]:
                age = (now - t.get('updated_at', 0)) // 86400
                s_emoji = STATUS_EMOJI.get(t['status'], '')
                assignee = f" \u2192 <@{t['assignee_id']}>" if t.get('assignee_id') else ""
                lines.append(f"{s_emoji} `#{t['id']}` **{t['title']}** \u2014 {age}d ago{assignee}")
            if len(stale_tasks) > 10:
                lines.append(f"*...and {len(stale_tasks) - 10} more*")
            embed.add_field(
                name=f"\U0001f4cb Stale Tasks ({len(stale_tasks)})",
                value="\n".join(lines),
                inline=False
            )

        if stale_bugs:
            stale_bugs.sort(key=lambda b: b.get('updated_at', 0))
            lines = []
            for b in stale_bugs[:10]:
                age = (now - b.get('updated_at', 0)) // 86400
                sv_emoji = SEVERITY_EMOJI.get(b.get('severity', 'medium'), '')
                assignee = f" \u2192 <@{b['assignee_id']}>" if b.get('assignee_id') else ""
                lines.append(f"{sv_emoji} `#{b['id']}` **{b['title']}** \u2014 {age}d ago{assignee}")
            if len(stale_bugs) > 10:
                lines.append(f"*...and {len(stale_bugs) - 10} more*")
            embed.add_field(
                name=f"\U0001f41b Stale Bugs ({len(stale_bugs)})",
                value="\n".join(lines),
                inline=False
            )

        embed.set_footer(text=f"Threshold: {days} days | Project: {project['name']}")
        await interaction.followup.send(embed=embed)

    # ── /audit duplicates ─────────────────────────
    @audit_group.command(name="duplicates", description="Detect potential duplicate bugs")
    async def audit_duplicates(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        all_bugs = await getBugs(interaction.guild_id, project['id'])
        open_bugs = [b for b in all_bugs if b['status'] != 'closed']

        if len(open_bugs) < 2:
            await interaction.followup.send(
                "Need at least 2 open bugs to check for duplicates.", ephemeral=True
            )
            return

        # Find potential duplicates
        duplicates = []
        checked = set()

        for i, bug_a in enumerate(open_bugs):
            for j, bug_b in enumerate(open_bugs):
                if i >= j:
                    continue
                pair_key = (bug_a['id'], bug_b['id'])
                if pair_key in checked:
                    continue
                checked.add(pair_key)

                title_a = bug_a['title'].lower().strip()
                title_b = bug_b['title'].lower().strip()

                # Check substring match
                is_substring = title_a in title_b or title_b in title_a

                # Check word similarity
                similarity = word_similarity(bug_a['title'], bug_b['title'])

                if is_substring or similarity >= 0.6:
                    duplicates.append({
                        'a': bug_a,
                        'b': bug_b,
                        'similarity': similarity if not is_substring else 1.0,
                        'reason': 'substring' if is_substring else 'word overlap'
                    })

        embed = discord.Embed(
            title="\U0001f50d Duplicate Detection",
            color=embedColor
        )

        if not duplicates:
            embed.description = "\u2705 No potential duplicates found among open bugs."
            embed.set_footer(text=f"Scanned {len(open_bugs)} open bugs")
            await interaction.followup.send(embed=embed)
            return

        # Sort by similarity descending
        duplicates.sort(key=lambda d: d['similarity'], reverse=True)

        lines = []
        for dup in duplicates[:10]:
            pct = int(dup['similarity'] * 100)
            sv_a = SEVERITY_EMOJI.get(dup['a'].get('severity', ''), '')
            sv_b = SEVERITY_EMOJI.get(dup['b'].get('severity', ''), '')
            lines.append(
                f"\u26a0\ufe0f **{pct}%** match ({dup['reason']})\n"
                f"\u2514 {sv_a} `#{dup['a']['id']}` {dup['a']['title']}\n"
                f"\u2514 {sv_b} `#{dup['b']['id']}` {dup['b']['title']}"
            )

        embed.description = "\n\n".join(lines)
        if len(duplicates) > 10:
            embed.description += f"\n\n*...and {len(duplicates) - 10} more potential matches*"

        embed.set_footer(
            text=f"{len(duplicates)} potential duplicate(s) | {len(open_bugs)} open bugs scanned"
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Automation(bot))

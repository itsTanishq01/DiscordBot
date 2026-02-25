import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createBug, getBug, updateBugStatus, assignBug, getBugs, closeBug,
    getActiveProject, logAudit
)
from config import embedColor
from cogs.sdlcHelpers import (
    requireActiveProject, requireRole, getGroupRoles, parseBulkNames, buildBulkEmbed,
    BUG_STATUSES, BUG_SEVERITIES, STATUS_EMOJI, SEVERITY_EMOJI,
    statusDisplay, severityDisplay
)

STATUS_CHOICES = [
    app_commands.Choice(name="New", value="new"),
    app_commands.Choice(name="Acknowledged", value="acknowledged"),
    app_commands.Choice(name="In Progress", value="in_progress"),
    app_commands.Choice(name="Needs QA", value="needs_qa"),
    app_commands.Choice(name="Closed", value="closed"),
]

SEVERITY_CHOICES = [
    app_commands.Choice(name="\U0001f534 Critical", value="critical"),
    app_commands.Choice(name="\U0001f7e1 Medium", value="medium"),
    app_commands.Choice(name="\U0001f7e0 Minor", value="minor"),
]


class Bugs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    bug_group = app_commands.Group(name="bug", description="Manage and track bugs")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /bug report ───────────────────────────────
    @bug_group.command(name="report", description="Report bug(s). Comma-separate titles for bulk.")
    @app_commands.describe(
        title="Bug title (comma-separate for bulk: 'Crash on load, UI glitch')",
        severity="Severity level",
        description="Description (single bug only)",
        assignee="Assign to a member (optional)"
    )
    @app_commands.choices(severity=SEVERITY_CHOICES)
    async def bug_report(self, interaction: discord.Interaction, title: str,
                         severity: app_commands.Choice[str] = None,
                         description: str = "",
                         assignee: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'bugs')):
            return

        project = await requireActiveProject(interaction)
        if not project:
            return

        gid = interaction.guild_id
        severity_val = severity.value if severity else 'medium'
        titles = parseBulkNames(title)
        if not titles:
            await interaction.followup.send("No valid titles provided.", ephemeral=True)
            return

        now = int(time.time())
        created = []
        errors = []

        for bug_title in titles:
            try:
                seq = await createBug(
                    gid, project['id'],
                    bug_title,
                    description if len(titles) == 1 else "",
                    severity_val,
                    str(interaction.user.id),
                    [],
                    now
                )
                # assign if provided
                if assignee:
                    await assignBug(gid, seq, str(assignee.id), now)
                created.append((seq, bug_title))
                await logAudit(gid, "create", "bug", seq,
                               str(interaction.user.id), f"Reported bug: {bug_title}", now)
            except Exception as e:
                errors.append(f"\u274c `{bug_title}`: {e}")

        extra_fields = [("Severity", severityDisplay(severity_val), True)]
        if assignee:
            extra_fields.append(("Assignee", assignee.mention, True))
        extra_fields.append(("Project", project['name'], True))

        embed = buildBulkEmbed(created, errors, "bug", extra_fields)
        await interaction.followup.send(embed=embed)

    # ── /bug status ───────────────────────────────
    @bug_group.command(name="status", description="Update bug lifecycle status")
    @app_commands.describe(bug_id="Bug ID", status="New status")
    @app_commands.choices(status=STATUS_CHOICES)
    async def bug_status(self, interaction: discord.Interaction, bug_id: int,
                         status: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'bugs')):
            return

        gid = interaction.guild_id
        bug = await getBug(gid, bug_id)
        if not bug:
            await interaction.followup.send("Bug not found.", ephemeral=True)
            return

        new_status = status.value
        old_status = bug['status']

        if old_status == new_status:
            await interaction.followup.send(
                f"Bug `#{bug_id}` is already **{statusDisplay(new_status)}**.", ephemeral=True
            )
            return

        now = int(time.time())
        await updateBugStatus(gid, bug_id, new_status, now)
        await logAudit(gid, "status_change", "bug", bug_id,
                       str(interaction.user.id), f"{old_status} -> {new_status}", now)

        embed = discord.Embed(
            title=f"Bug #{bug_id} \u2014 Status Updated",
            description=f"**{bug['title']}**",
            color=embedColor
        )
        embed.add_field(name="Severity", value=severityDisplay(bug['severity']), inline=True)
        embed.add_field(name="From", value=statusDisplay(old_status), inline=True)
        embed.add_field(name="\u27a1\ufe0f To", value=statusDisplay(new_status), inline=True)

        if bug.get('assignee_id') and bug['assignee_id'] != str(interaction.user.id):
            embed.set_footer(text="Assignee notified")
            await interaction.followup.send(content=f"<@{bug['assignee_id']}>", embed=embed)
        else:
            await interaction.followup.send(embed=embed)

    # ── /bug assign ───────────────────────────────
    @bug_group.command(name="assign", description="Assign or reassign a bug")
    @app_commands.describe(bug_id="Bug ID", assignee="Member to assign")
    async def bug_assign(self, interaction: discord.Interaction, bug_id: int,
                         assignee: discord.Member):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'bugs')):
            return

        gid = interaction.guild_id
        bug = await getBug(gid, bug_id)
        if not bug:
            await interaction.followup.send("Bug not found.", ephemeral=True)
            return

        now = int(time.time())
        await assignBug(gid, bug_id, str(assignee.id), now)
        await logAudit(gid, "assign", "bug", bug_id,
                       str(interaction.user.id), f"Assigned to {assignee.display_name}", now)

        embed = discord.Embed(
            title=f"Bug #{bug_id} \u2014 Assigned",
            description=f"**{bug['title']}** \u2192 {assignee.mention}",
            color=embedColor
        )
        embed.add_field(name="Severity", value=severityDisplay(bug['severity']), inline=True)
        await interaction.followup.send(embed=embed)

    # ── /bug list ─────────────────────────────────
    @bug_group.command(name="list", description="List bugs with optional filters")
    @app_commands.describe(
        status="Filter by status",
        severity="Filter by severity",
        assignee="Filter by assignee"
    )
    @app_commands.choices(status=STATUS_CHOICES, severity=SEVERITY_CHOICES)
    async def bug_list(self, interaction: discord.Interaction,
                       status: app_commands.Choice[str] = None,
                       severity: app_commands.Choice[str] = None,
                       assignee: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        filters = {}
        if status:
            filters['status'] = status.value
        if severity:
            filters['severity'] = severity.value
        if assignee:
            filters['assignee_id'] = str(assignee.id)

        bugs = await getBugs(interaction.guild_id, project['id'], filters if filters else None)

        if not bugs:
            parts = []
            if status:
                parts.append(f"status={status.value}")
            if severity:
                parts.append(f"severity={severity.value}")
            if assignee:
                parts.append(f"assignee={assignee.display_name}")
            filter_desc = f" (filters: {', '.join(parts)})" if parts else ""
            await interaction.followup.send(
                f"No bugs found{filter_desc}. Report one with `/bug report`.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"\U0001f41b Bugs \u2014 {project['name']}",
            color=embedColor
        )

        if not status:
            status_groups = {}
            for b in bugs:
                s = b['status']
                if s not in status_groups:
                    status_groups[s] = []
                status_groups[s].append(b)

            display_order = ['new', 'acknowledged', 'in_progress', 'needs_qa', 'closed']
            for s in display_order:
                if s not in status_groups:
                    continue
                group = status_groups[s]
                lines = []
                for b in group[:5]:
                    sv_emoji = SEVERITY_EMOJI.get(b['severity'], '')
                    assignee_str = f" \u2192 <@{b['assignee_id']}>" if b.get('assignee_id') else ""
                    lines.append(f"`#{b['guild_seq']}` {sv_emoji} **{b['title']}**{assignee_str}")
                if len(group) > 5:
                    lines.append(f"*...and {len(group) - 5} more*")
                embed.add_field(
                    name=f"{statusDisplay(s)} ({len(group)})",
                    value="\n".join(lines),
                    inline=False
                )
        else:
            lines = []
            for b in bugs[:25]:
                sv_emoji = SEVERITY_EMOJI.get(b['severity'], '')
                st_emoji = STATUS_EMOJI.get(b['status'], '')
                assignee_str = f" \u2192 <@{b['assignee_id']}>" if b.get('assignee_id') else ""
                lines.append(f"{st_emoji} `#{b['guild_seq']}` {sv_emoji} **{b['title']}**{assignee_str}")
            if len(bugs) > 25:
                lines.append(f"\n*...and {len(bugs) - 25} more bugs*")
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"{len(bugs)} bug(s) total")
        await interaction.followup.send(embed=embed)

    # ── /bug view ─────────────────────────────────
    @bug_group.command(name="view", description="View bug details")
    @app_commands.describe(bug_id="Bug ID to view")
    async def bug_view(self, interaction: discord.Interaction, bug_id: int):
        await interaction.response.defer(ephemeral=False)
        gid = interaction.guild_id
        bug = await getBug(gid, bug_id)
        if not bug:
            await interaction.followup.send("Bug not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Bug #{bug_id}: {bug['title']}",
            color=embedColor
        )

        if bug.get('description'):
            embed.description = bug['description']

        embed.add_field(name="Status", value=statusDisplay(bug['status']), inline=True)
        embed.add_field(name="Severity", value=severityDisplay(bug['severity']), inline=True)

        if bug.get('assignee_id'):
            embed.add_field(name="Assignee", value=f"<@{bug['assignee_id']}>", inline=True)
        else:
            embed.add_field(name="Assignee", value="Unassigned", inline=True)

        embed.add_field(name="Reporter", value=f"<@{bug['reporter_id']}>", inline=True)

        created_ts = bug.get('created_at', 0)
        updated_ts = bug.get('updated_at', 0)
        embed.add_field(name="Reported", value=f"<t:{created_ts}:R>", inline=True)
        if updated_ts != created_ts:
            embed.add_field(name="Updated", value=f"<t:{updated_ts}:R>", inline=True)

        await interaction.followup.send(embed=embed)

    # ── /bug close ────────────────────────────────
    @bug_group.command(name="close", description="Close a bug (QA verified)")
    @app_commands.describe(bug_id="Bug ID to close")
    async def bug_close(self, interaction: discord.Interaction, bug_id: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'bugs')):
            return

        gid = interaction.guild_id
        bug = await getBug(gid, bug_id)
        if not bug:
            await interaction.followup.send("Bug not found.", ephemeral=True)
            return

        if bug['status'] == 'closed':
            await interaction.followup.send(
                f"Bug `#{bug_id}` is already closed.", ephemeral=True
            )
            return

        now = int(time.time())
        await closeBug(gid, bug_id, now)
        await logAudit(gid, "close", "bug", bug_id,
                       str(interaction.user.id), f"Closed bug: {bug['title']}", now)

        embed = discord.Embed(
            title=f"\u2705 Bug #{bug_id} Closed",
            description=f"**{bug['title']}**",
            color=0x57F287
        )
        embed.add_field(name="Severity", value=severityDisplay(bug['severity']), inline=True)
        embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Bugs(bot))

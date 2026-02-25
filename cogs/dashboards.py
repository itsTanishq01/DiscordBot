import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    getTaskCounts, getBugCounts, getActiveSprint, getTasks, getBugs,
    getActiveProject
)
from config import embedColor
from cogs.sdlcHelpers import (
    requireActiveProject, statusDisplay, severityDisplay,
    STATUS_EMOJI, SEVERITY_EMOJI, PRIORITY_EMOJI
)


class Dashboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    dash_group = app_commands.Group(name="dashboard", description="Visual project summaries")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /dashboard project ────────────────────────
    @dash_group.command(name="project", description="Project health overview")
    async def dash_project(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        task_counts = await getTaskCounts(interaction.guild_id, project['id'])
        bug_counts = await getBugCounts(interaction.guild_id, project['id'])

        # Task metrics
        total_tasks = sum(task_counts.values())
        done_tasks = task_counts.get('done', 0)
        task_pct = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        task_filled = task_pct // 10
        task_bar = "\u2588" * task_filled + "\u2591" * (10 - task_filled)

        # Bug metrics
        total_bugs = sum(bug_counts.values())
        critical_bugs = bug_counts.get('critical', 0)

        embed = discord.Embed(
            title=f"\U0001f4ca Dashboard \u2014 {project['name']}",
            color=embedColor
        )

        # Task summary
        task_lines = [f"**Completion:** `{task_bar}` {task_pct}% ({done_tasks}/{total_tasks})"]
        task_order = ['backlog', 'todo', 'in_progress', 'blocked', 'review', 'done']
        for s in task_order:
            count = task_counts.get(s, 0)
            if count > 0:
                emoji = STATUS_EMOJI.get(s, '')
                task_lines.append(f"{emoji} {s.replace('_', ' ').title()}: **{count}**")
        embed.add_field(
            name=f"\U0001f4cb Tasks ({total_tasks})",
            value="\n".join(task_lines),
            inline=False
        )

        # Bug summary
        if total_bugs > 0:
            bug_lines = []
            for sev in ['critical', 'medium', 'minor']:
                count = bug_counts.get(sev, 0)
                if count > 0:
                    emoji = SEVERITY_EMOJI.get(sev, '')
                    bug_lines.append(f"{emoji} {sev.title()}: **{count}**")
            embed.add_field(
                name=f"\U0001f41b Open Bugs ({total_bugs})",
                value="\n".join(bug_lines) if bug_lines else "None",
                inline=False
            )
        else:
            embed.add_field(
                name="\U0001f41b Open Bugs",
                value="\u2705 No open bugs!",
                inline=False
            )

        # Health indicator
        if critical_bugs > 0:
            embed.set_footer(text=f"\U0001f534 {critical_bugs} critical bug(s) need attention!")
        elif task_pct >= 80:
            embed.set_footer(text="\U0001f7e2 Project is on track!")
        elif task_pct >= 50:
            embed.set_footer(text="\U0001f7e1 Project is progressing.")
        else:
            embed.set_footer(text="\U0001f7e0 Early stages \u2014 keep going!")

        await interaction.followup.send(embed=embed)

    # ── /dashboard sprint ─────────────────────────
    @dash_group.command(name="sprint", description="Active sprint progress and burndown")
    async def dash_sprint(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        sprint = await getActiveSprint(interaction.guild_id, project['id'])
        if not sprint:
            await interaction.followup.send(
                "No active sprint. Start one with `/sprint activate`.", ephemeral=True
            )
            return

        # Get tasks in this sprint
        tasks = await getTasks(interaction.guild_id, project['id'],
                               {'sprint_id': sprint['id']})

        total = len(tasks)
        if total == 0:
            await interaction.followup.send(
                f"Sprint **{sprint['name']}** has no tasks yet. Add tasks with `/task new`.",
                ephemeral=True
            )
            return

        # Status breakdown
        status_counts = {}
        for t in tasks:
            s = t['status']
            status_counts[s] = status_counts.get(s, 0) + 1

        done = status_counts.get('done', 0)
        in_progress = status_counts.get('in_progress', 0)
        blocked = status_counts.get('blocked', 0)
        pct = int((done / total) * 100) if total > 0 else 0

        # Progress bar
        filled = pct // 10
        bar = "\u2588" * filled + "\u2591" * (10 - filled)

        embed = discord.Embed(
            title=f"\U0001f3c3 Sprint \u2014 {sprint['name']}",
            color=embedColor
        )

        embed.description = f"**Progress:** `{bar}` {pct}% ({done}/{total} done)"

        # Sprint dates
        if sprint.get('start_date'):
            embed.add_field(name="Start", value=f"<t:{sprint['start_date']}:D>", inline=True)
        if sprint.get('end_date'):
            embed.add_field(name="End", value=f"<t:{sprint['end_date']}:D>", inline=True)
            # Days remaining
            now = int(time.time())
            remaining = (sprint['end_date'] - now) // 86400
            if remaining > 0:
                embed.add_field(name="Remaining", value=f"**{remaining}** days", inline=True)
            elif remaining == 0:
                embed.add_field(name="Remaining", value="**Today!**", inline=True)
            else:
                embed.add_field(name="Overdue", value=f"**{abs(remaining)}** days", inline=True)

        # Status breakdown
        status_lines = []
        for s in ['todo', 'in_progress', 'blocked', 'review', 'done']:
            count = status_counts.get(s, 0)
            if count > 0:
                emoji = STATUS_EMOJI.get(s, '')
                status_lines.append(f"{emoji} {s.replace('_', ' ').title()}: **{count}**")
        if status_lines:
            embed.add_field(
                name="Breakdown",
                value="\n".join(status_lines),
                inline=False
            )

        # Warnings
        warnings = []
        if blocked > 0:
            warnings.append(f"\u26a0\ufe0f {blocked} blocked task(s)")
        if pct < 50 and sprint.get('end_date'):
            now = int(time.time())
            total_duration = sprint['end_date'] - sprint.get('start_date', sprint.get('created_at', now))
            elapsed = now - sprint.get('start_date', sprint.get('created_at', now))
            if total_duration > 0 and elapsed / total_duration > 0.5:
                warnings.append("\u26a0\ufe0f Less than 50% done past halfway point")
        if warnings:
            embed.add_field(name="Warnings", value="\n".join(warnings), inline=False)

        await interaction.followup.send(embed=embed)

    # ── /dashboard my_day ─────────────────────────
    @dash_group.command(name="my_day", description="Your daily priorities")
    async def dash_my_day(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        user_id = str(interaction.user.id)

        # Fetch assigned tasks (not done/backlog)
        all_tasks = await getTasks(interaction.guild_id, project['id'],
                                    {'assignee_id': user_id})
        active_tasks = [t for t in all_tasks if t['status'] not in ('done', 'backlog')]

        # Fetch assigned bugs (not closed)
        all_bugs = await getBugs(interaction.guild_id, project['id'],
                                  {'assignee_id': user_id})
        active_bugs = [b for b in all_bugs if b['status'] != 'closed']

        total = len(active_tasks) + len(active_bugs)

        embed = discord.Embed(
            title=f"\u2600\ufe0f My Day \u2014 {interaction.user.display_name}",
            description=f"**{total}** active item(s) in **{project['name']}**",
            color=embedColor
        )

        if not active_tasks and not active_bugs:
            embed.description = "\u2705 **All clear!** No active tasks or bugs assigned to you."
            embed.set_footer(text="Pick up new work with /task new or check /workload team")
            await interaction.followup.send(embed=embed)
            return

        # Priority order for tasks
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        active_tasks.sort(key=lambda t: priority_order.get(t.get('priority', 'medium'), 2))

        # Show tasks
        if active_tasks:
            task_lines = []
            for t in active_tasks[:8]:
                p_emoji = PRIORITY_EMOJI.get(t.get('priority', 'medium'), '')
                s_emoji = STATUS_EMOJI.get(t['status'], '')
                task_lines.append(f"{s_emoji} `#{t['id']}` {p_emoji} **{t['title']}**")
            if len(active_tasks) > 8:
                task_lines.append(f"*...and {len(active_tasks) - 8} more*")
            embed.add_field(
                name=f"\U0001f4cb Tasks ({len(active_tasks)})",
                value="\n".join(task_lines),
                inline=False
            )

        # Severity order for bugs
        severity_order = {'critical': 0, 'medium': 1, 'minor': 2}
        active_bugs.sort(key=lambda b: severity_order.get(b.get('severity', 'medium'), 1))

        # Show bugs
        if active_bugs:
            bug_lines = []
            for b in active_bugs[:5]:
                sv_emoji = SEVERITY_EMOJI.get(b.get('severity', 'medium'), '')
                s_emoji = STATUS_EMOJI.get(b['status'], '')
                bug_lines.append(f"{s_emoji} `#{b['id']}` {sv_emoji} **{b['title']}**")
            if len(active_bugs) > 5:
                bug_lines.append(f"*...and {len(active_bugs) - 5} more*")
            embed.add_field(
                name=f"\U0001f41b Bugs ({len(active_bugs)})",
                value="\n".join(bug_lines),
                inline=False
            )

        # Focus suggestion
        if active_bugs and active_bugs[0].get('severity') == 'critical':
            embed.set_footer(text="\U0001f534 Critical bug(s) should be your top priority!")
        elif any(t['status'] == 'blocked' for t in active_tasks):
            embed.set_footer(text="\u26a0\ufe0f You have blocked tasks \u2014 try to unblock them first.")
        else:
            embed.set_footer(text="\U0001f4aa Focus on the top items first!")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Dashboards(bot))

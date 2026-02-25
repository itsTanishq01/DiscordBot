import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createTask, getTask, updateTaskStatus, assignTask, getTasks, deleteTask,
    getActiveProject, logAudit, getConfig,
    addTaskComment, getTaskComments
)
from config import embedColor
from cogs.sdlcHelpers import (
    requireActiveProject, requireRole, getGroupRoles, parseBulkNames, buildBulkEmbed,
    TASK_STATUSES, TASK_PRIORITIES, STATUS_EMOJI, PRIORITY_EMOJI,
    statusDisplay, priorityDisplay
)

STATUS_CHOICES = [
    app_commands.Choice(name="Backlog", value="backlog"),
    app_commands.Choice(name="Todo", value="todo"),
    app_commands.Choice(name="In Progress", value="in_progress"),
    app_commands.Choice(name="Blocked", value="blocked"),
    app_commands.Choice(name="Review", value="review"),
    app_commands.Choice(name="Done", value="done"),
]

PRIORITY_CHOICES = [
    app_commands.Choice(name="\U0001f534 Critical", value="critical"),
    app_commands.Choice(name="\U0001f7e0 High", value="high"),
    app_commands.Choice(name="\U0001f7e1 Medium", value="medium"),
    app_commands.Choice(name="\U0001f7e2 Low", value="low"),
]


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    task_group = app_commands.Group(name="task", description="Manage tasks (Kanban)")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /task new ──────────────────────────────────
    @task_group.command(name="new", description="Create task(s). Comma-separate titles for bulk.")
    @app_commands.describe(
        title="Task title (comma-separate for bulk: 'Fix login, Add logout')",
        priority="Priority level",
        assignee="Assign to a member (optional)",
        description="Description (single task only)"
    )
    @app_commands.choices(priority=PRIORITY_CHOICES)
    async def task_new(self, interaction: discord.Interaction, title: str,
                       priority: app_commands.Choice[str] = None,
                       assignee: discord.Member = None,
                       description: str = ""):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'tasks')):
            return

        project = await requireActiveProject(interaction)
        if not project:
            return

        sprint = await getActiveSprint(interaction.guild_id, project['id'])
        sprint_id = sprint['id'] if sprint else None
        priority_val = priority.value if priority else 'medium'
        assignee_id = str(assignee.id) if assignee else None

        titles = parseBulkNames(title)
        if not titles:
            await interaction.followup.send("No valid titles provided.", ephemeral=True)
            return

        now = int(time.time())
        created = []
        errors = []

        for task_title in titles:
            try:
                tid = await createTask(
                    interaction.guild_id, project['id'], sprint_id,
                    task_title, description if len(titles) == 1 else "",
                    priority_val, assignee_id, str(interaction.user.id), now
                )
                created.append((tid, task_title))
                await logAudit(interaction.guild_id, "create", "task", tid,
                               str(interaction.user.id), f"Created task: {task_title}", now)
            except Exception as e:
                errors.append(f"\u274c `{task_title}`: {e}")

        extra_fields = []
        extra_fields.append(("Priority", priorityDisplay(priority_val), True))
        if assignee:
            extra_fields.append(("Assignee", assignee.mention, True))
        if sprint:
            extra_fields.append(("Sprint", sprint['name'], True))
        extra_fields.append(("Project", project['name'], True))

        embed = buildBulkEmbed(created, errors, "task", extra_fields)
        await interaction.followup.send(embed=embed)

    # ── /task status ──────────────────────────────
    @task_group.command(name="status", description="Update task status (Kanban column)")
    @app_commands.describe(task_id="Task ID", status="New status")
    @app_commands.choices(status=STATUS_CHOICES)
    async def task_status(self, interaction: discord.Interaction, task_id: int,
                          status: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'tasks')):
            return

        task = await getTask(task_id)
        if not task or str(task['guild_id']) != str(interaction.guild_id):
            await interaction.followup.send("Task not found.", ephemeral=True)
            return

        new_status = status.value
        old_status = task['status']

        if old_status == new_status:
            await interaction.followup.send(
                f"Task `#{task_id}` is already **{statusDisplay(new_status)}**.", ephemeral=True
            )
            return

        # WIP limit check
        if new_status == 'in_progress':
            wip_limit_str = await getConfig(interaction.guild_id, "wipLimit")
            wip_limit = int(wip_limit_str) if wip_limit_str else 5
            current_wip = await getTasks(interaction.guild_id, task['project_id'],
                                         {'status': 'in_progress'})
            if len(current_wip) >= wip_limit:
                await interaction.followup.send(
                    f"\u26a0\ufe0f **WIP limit reached!** {len(current_wip)}/{wip_limit} tasks already in progress.\n"
                    f"Finish or move existing tasks before starting new ones.",
                    ephemeral=True
                )
                return

        now = int(time.time())
        await updateTaskStatus(task_id, new_status, now)
        await logAudit(interaction.guild_id, "status_change", "task", task_id,
                       str(interaction.user.id),
                       f"{old_status} -> {new_status}", now)

        embed = discord.Embed(
            title=f"Task #{task_id} — Status Updated",
            description=f"**{task['title']}**",
            color=embedColor
        )
        embed.add_field(name="From", value=statusDisplay(old_status), inline=True)
        embed.add_field(name="\u27a1\ufe0f", value="To", inline=True)
        embed.add_field(name="To", value=statusDisplay(new_status), inline=True)

        # Notify assignee if different from the person changing status
        if task.get('assignee_id') and task['assignee_id'] != str(interaction.user.id):
            embed.set_footer(text=f"Assignee notified")
            await interaction.followup.send(
                content=f"<@{task['assignee_id']}>",
                embed=embed
            )
        else:
            await interaction.followup.send(embed=embed)

    # ── /task assign ──────────────────────────────
    @task_group.command(name="assign", description="Assign or reassign a task")
    @app_commands.describe(task_id="Task ID", assignee="Member to assign")
    async def task_assign(self, interaction: discord.Interaction, task_id: int,
                          assignee: discord.Member):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'tasks')):
            return

        task = await getTask(task_id)
        if not task or str(task['guild_id']) != str(interaction.guild_id):
            await interaction.followup.send("Task not found.", ephemeral=True)
            return

        now = int(time.time())
        await assignTask(task_id, str(assignee.id), now)
        await logAudit(interaction.guild_id, "assign", "task", task_id,
                       str(interaction.user.id),
                       f"Assigned to {assignee.display_name}", now)

        embed = discord.Embed(
            title=f"Task #{task_id} — Assigned",
            description=f"**{task['title']}** \u2192 {assignee.mention}",
            color=embedColor
        )
        await interaction.followup.send(embed=embed)

    # ── /task list ────────────────────────────────
    @task_group.command(name="list", description="List tasks with optional filters")
    @app_commands.describe(
        status="Filter by status",
        priority="Filter by priority",
        assignee="Filter by assignee"
    )
    @app_commands.choices(status=STATUS_CHOICES, priority=PRIORITY_CHOICES)
    async def task_list(self, interaction: discord.Interaction,
                        status: app_commands.Choice[str] = None,
                        priority: app_commands.Choice[str] = None,
                        assignee: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        project = await requireActiveProject(interaction)
        if not project:
            return

        filters = {}
        if status:
            filters['status'] = status.value
        if priority:
            filters['priority'] = priority.value
        if assignee:
            filters['assignee_id'] = str(assignee.id)

        tasks = await getTasks(interaction.guild_id, project['id'], filters if filters else None)

        if not tasks:
            filter_desc = ""
            if filters:
                parts = []
                if status:
                    parts.append(f"status={status.value}")
                if priority:
                    parts.append(f"priority={priority.value}")
                if assignee:
                    parts.append(f"assignee={assignee.display_name}")
                filter_desc = f" (filters: {', '.join(parts)})"
            await interaction.followup.send(
                f"No tasks found{filter_desc}. Create one with `/task new`.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"\U0001f4cb Tasks \u2014 {project['name']}",
            color=embedColor
        )

        # Group by status for Kanban-style display
        if not status:
            status_groups = {}
            for t in tasks:
                s = t['status']
                if s not in status_groups:
                    status_groups[s] = []
                status_groups[s].append(t)

            for s in TASK_STATUSES:
                if s in status_groups:
                    group_tasks = status_groups[s]
                    lines = []
                    for t in group_tasks[:5]:
                        p_emoji = PRIORITY_EMOJI.get(t['priority'], '')
                        assignee_str = f" \u2192 <@{t['assignee_id']}>" if t.get('assignee_id') else ""
                        lines.append(f"`#{t['id']}` {p_emoji} **{t['title']}**{assignee_str}")
                    if len(group_tasks) > 5:
                        lines.append(f"*...and {len(group_tasks) - 5} more*")
                    embed.add_field(
                        name=f"{statusDisplay(s)} ({len(group_tasks)})",
                        value="\n".join(lines),
                        inline=False
                    )
        else:
            lines = []
            display_tasks = tasks[:25]
            for t in display_tasks:
                p_emoji = PRIORITY_EMOJI.get(t['priority'], '')
                s_emoji = STATUS_EMOJI.get(t['status'], '')
                assignee_str = f" \u2192 <@{t['assignee_id']}>" if t.get('assignee_id') else ""
                lines.append(f"{s_emoji} `#{t['id']}` {p_emoji} **{t['title']}**{assignee_str}")
            if len(tasks) > 25:
                lines.append(f"\n*...and {len(tasks) - 25} more tasks*")
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"{len(tasks)} task(s) total")
        await interaction.followup.send(embed=embed)

    # ── /task delete ──────────────────────────────
    @task_group.command(name="delete", description="Delete a task")
    @app_commands.describe(task_id="Task ID to delete")
    async def task_delete(self, interaction: discord.Interaction, task_id: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'tasks')):
            return

        task = await getTask(task_id)
        if not task or str(task['guild_id']) != str(interaction.guild_id):
            await interaction.followup.send("Task not found.", ephemeral=True)
            return

        title = task['title']
        await deleteTask(task_id)
        await logAudit(interaction.guild_id, "delete", "task", task_id,
                       str(interaction.user.id), f"Deleted task: {title}", int(time.time()))

        await interaction.followup.send(f"\U0001f5d1\ufe0f Deleted task `#{task_id}`: **{title}**")

    # ── /task view ────────────────────────────────
    @task_group.command(name="view", description="View task details")
    @app_commands.describe(task_id="Task ID to view")
    async def task_view(self, interaction: discord.Interaction, task_id: int):
        await interaction.response.defer(ephemeral=False)
        task = await getTask(task_id)
        if not task or str(task['guild_id']) != str(interaction.guild_id):
            await interaction.followup.send("Task not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Task #{task_id}: {task['title']}",
            color=embedColor
        )

        if task.get('description'):
            embed.description = task['description']

        embed.add_field(name="Status", value=statusDisplay(task['status']), inline=True)
        embed.add_field(name="Priority", value=priorityDisplay(task['priority']), inline=True)

        if task.get('assignee_id'):
            embed.add_field(name="Assignee", value=f"<@{task['assignee_id']}>", inline=True)
        else:
            embed.add_field(name="Assignee", value="Unassigned", inline=True)

        embed.add_field(name="Creator", value=f"<@{task['creator_id']}>", inline=True)

        if task.get('sprint_id'):
            embed.add_field(name="Sprint ID", value=f"`#{task['sprint_id']}`", inline=True)

        created_ts = task.get('created_at', 0)
        updated_ts = task.get('updated_at', 0)
        embed.add_field(name="Created", value=f"<t:{created_ts}:R>", inline=True)
        if updated_ts != created_ts:
            embed.add_field(name="Updated", value=f"<t:{updated_ts}:R>", inline=True)

        # Recent comments
        comments = await getTaskComments(task_id)
        if comments:
            recent = comments[-5:]
            comment_lines = []
            for c in recent:
                preview = c['content'][:80] + ("..." if len(c['content']) > 80 else "")
                comment_lines.append(f"<@{c['user_id']}>: {preview}")
            if len(comments) > 5:
                comment_lines.insert(0, f"*Showing last 5 of {len(comments)} comments:*")
            embed.add_field(name="Comments", value="\n".join(comment_lines), inline=False)

        await interaction.followup.send(embed=embed)

    # ── /task comment ─────────────────────────────
    @task_group.command(name="comment", description="Add a comment to a task")
    @app_commands.describe(task_id="Task ID", text="Comment text")
    async def task_comment(self, interaction: discord.Interaction, task_id: int, text: str):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'tasks')):
            return

        task = await getTask(task_id)
        if not task or str(task['guild_id']) != str(interaction.guild_id):
            await interaction.followup.send("Task not found.", ephemeral=True)
            return

        now = int(time.time())
        cid = await addTaskComment(task_id, str(interaction.user.id), text, now)
        await logAudit(interaction.guild_id, "comment", "task", task_id,
                       str(interaction.user.id), f"Added comment: {text[:100]}", now)

        embed = discord.Embed(
            title=f"\U0001f4ac Comment Added \u2014 Task #{task_id}",
            description=f"**{task['title']}**\n\n{text}",
            color=embedColor
        )
        embed.set_footer(text=f"Comment #{cid} by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tasks(bot))

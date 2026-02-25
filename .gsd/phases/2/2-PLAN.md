---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Sprints Cog

## Objective
Create the `cogs/sprints.py` cog with sprint lifecycle commands. Sprints are time-boxed iterations within a project. Support bulk sprint creation.

**Bulk support:** `/sprint new` supports creating multiple sprints via comma-separated names.

## Context
- `.gsd/SPEC.md` — Section 4 (sprints provide time-boxed tracking)
- `cogs/projects.py` — Pattern established in Plan 2.1 (command group, permission gates, embeds, bulk creation)
- `database.py` — createSprint, getSprints, updateSprintStatus, getActiveSprint, getActiveProject, hasTeamPermission, logAudit

## Tasks

<task type="auto">
  <name>Create sprints cog with all commands</name>
  <files>cogs/sprints.py</files>
  <action>
    Create a new file `cogs/sprints.py`:

    ```python
    import time
    import discord
    from discord import app_commands
    from discord.ext import commands
    from database import (
        createSprint, getSprints, updateSprintStatus, getActiveSprint,
        getActiveProject, hasTeamPermission, logAudit
    )
    from config import embedColor

    SPRINT_STATUSES = ['planning', 'active', 'closed']

    class Sprints(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        sprint_group = app_commands.Group(name="sprint", description="Manage sprints")

        async def cog_app_command_error(self, interaction, error):
            if isinstance(error, app_commands.MissingPermissions):
                await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Error: {error}", ephemeral=True)

        async def _require_active_project(self, interaction):
            """Helper: checks for active project, sends error if none. Returns project dict or None."""
            project = await getActiveProject(interaction.guild_id)
            if not project:
                await interaction.response.send_message("❌ No active project. Set one with `/project set`.", ephemeral=True)
                return None
            return project

        # ── /sprint new ──
        # Bulk: /sprint new name:"Sprint 1, Sprint 2, Sprint 3"
        @sprint_group.command(name="new", description="Create sprint(s). Comma-separate names for bulk.")
        @app_commands.describe(
            name="Sprint name (comma-separate for bulk)",
            start_date="Start date (YYYY-MM-DD, optional)",
            end_date="End date (YYYY-MM-DD, optional)"
        )
        async def sprint_new(self, interaction, name: str, start_date: str = None, end_date: str = None):
            if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Requires **Lead** role or Admin.", ephemeral=True)
                    return

            project = await self._require_active_project(interaction)
            if not project:
                return

            # Parse dates if provided
            import datetime
            start_ts = None
            end_ts = None
            if start_date:
                try:
                    start_ts = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())
                except ValueError:
                    await interaction.response.send_message("❌ Invalid start date. Use YYYY-MM-DD.", ephemeral=True)
                    return
            if end_date:
                try:
                    end_ts = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp())
                except ValueError:
                    await interaction.response.send_message("❌ Invalid end date. Use YYYY-MM-DD.", ephemeral=True)
                    return

            names = [n.strip() for n in name.split(",") if n.strip()]
            now = int(time.time())
            created = []
            errors = []

            for sprint_name in names:
                try:
                    sid = await createSprint(interaction.guild_id, project['id'], sprint_name,
                                            start_ts if len(names) == 1 else None,
                                            end_ts if len(names) == 1 else None, now)
                    created.append((sid, sprint_name))
                    await logAudit(interaction.guild_id, "create", "sprint", sid, str(interaction.user.id), f"Created sprint: {sprint_name}", now)
                except Exception as e:
                    errors.append(f"❌ `{sprint_name}`: {e}")

            embed = discord.Embed(color=embedColor)
            if len(created) == 1:
                sid, sname = created[0]
                embed.title = "✅ Sprint Created"
                embed.description = f"**{sname}** (ID: `{sid}`) in project **{project['name']}**"
                if start_date:
                    embed.add_field(name="Start", value=start_date, inline=True)
                if end_date:
                    embed.add_field(name="End", value=end_date, inline=True)
            elif created:
                embed.title = f"✅ {len(created)} Sprints Created"
                embed.description = "\n".join([f"• **{sname}** (ID: `{sid}`)" for sid, sname in created])
                embed.set_footer(text=f"Project: {project['name']}")

            if errors:
                embed.add_field(name="Errors", value="\n".join(errors), inline=False)

            if not created and not errors:
                await interaction.response.send_message("❌ No valid names provided.", ephemeral=True)
                return

            await interaction.response.send_message(embed=embed)

        # ── /sprint list ──
        @sprint_group.command(name="list", description="List sprints in active project")
        async def sprint_list(self, interaction):
            project = await self._require_active_project(interaction)
            if not project:
                return

            sprints = await getSprints(interaction.guild_id, project['id'])
            if not sprints:
                await interaction.response.send_message(f"No sprints in **{project['name']}**. Create one with `/sprint new`.", ephemeral=True)
                return

            embed = discord.Embed(title=f"🏃 Sprints — {project['name']}", color=embedColor)
            status_emoji = {'planning': '📋', 'active': '🟢', 'closed': '⬛'}
            lines = []
            for s in sprints:
                emoji = status_emoji.get(s['status'], '❓')
                lines.append(f"{emoji} `#{s['id']}` **{s['name']}** — {s['status']}")
            embed.description = "\n".join(lines)
            await interaction.response.send_message(embed=embed)

        # ── /sprint activate ──
        @sprint_group.command(name="activate", description="Set a sprint as active")
        @app_commands.describe(sprint_id="Sprint ID to activate")
        async def sprint_activate(self, interaction, sprint_id: int):
            if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Requires **Lead** role or Admin.", ephemeral=True)
                    return

            project = await self._require_active_project(interaction)
            if not project:
                return

            # Close any currently active sprint first
            current = await getActiveSprint(interaction.guild_id, project['id'])
            if current:
                await updateSprintStatus(current['id'], 'closed')

            await updateSprintStatus(sprint_id, 'active')
            await logAudit(interaction.guild_id, "activate", "sprint", sprint_id, str(interaction.user.id), "Sprint activated", int(time.time()))
            await interaction.response.send_message(f"✅ Sprint `#{sprint_id}` is now **active**.")

        # ── /sprint close ──
        @sprint_group.command(name="close", description="Close the active sprint")
        async def sprint_close(self, interaction):
            if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Requires **Lead** role or Admin.", ephemeral=True)
                    return

            project = await self._require_active_project(interaction)
            if not project:
                return

            current = await getActiveSprint(interaction.guild_id, project['id'])
            if not current:
                await interaction.response.send_message("❌ No active sprint to close.", ephemeral=True)
                return

            await updateSprintStatus(current['id'], 'closed')
            await logAudit(interaction.guild_id, "close", "sprint", current['id'], str(interaction.user.id), f"Closed sprint: {current['name']}", int(time.time()))
            await interaction.response.send_message(f"⬛ Sprint **{current['name']}** closed.")

    async def setup(bot):
        await bot.add_cog(Sprints(bot))
    ```

    **Key design decisions:**
    - `_require_active_project` helper avoids repeating "no active project" check in every command
    - Bulk sprint creation: comma-separated names, dates only apply to single sprint
    - Sprint activation auto-closes previous active sprint (only one active per project)
    - Status emojis: 📋 planning, 🟢 active, ⬛ closed
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/sprints.py').read()); print('Syntax OK')"</verify>
  <done>cogs/sprints.py exists with 4 commands (new with bulk, list, activate, close). Syntax validates.</done>
</task>

<task type="auto">
  <name>Register sprints cog in main.py</name>
  <files>main.py</files>
  <action>
    Add `"cogs.sprints"` to the `cogExtensions` list in main.py, right after `"cogs.projects"`.
  </action>
  <verify>python -c "import ast; ast.parse(open('main.py').read()); print('main.py OK')"</verify>
  <done>"cogs.sprints" is in the cogExtensions list in main.py.</done>
</task>

## Success Criteria
- [ ] `cogs/sprints.py` exists with Sprints cog class
- [ ] `/sprint new` supports comma-separated bulk creation
- [ ] `/sprint list` shows sprints with status emojis
- [ ] `/sprint activate` auto-closes previous active sprint
- [ ] `/sprint close` closes active sprint
- [ ] `_require_active_project` helper prevents commands without active project
- [ ] Cog registered in main.py
- [ ] Syntax validates

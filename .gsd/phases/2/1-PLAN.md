---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Projects Cog

## Objective
Create the `cogs/projects.py` cog with project CRUD commands and active project selection. This is the first SDLC-facing cog — it establishes the pattern all other SDLC cogs will follow (command groups, embeds, permission checks, error handling).

**Bulk support:** `/project new` supports creating multiple projects at once via comma-separated names.

## Context
- `.gsd/SPEC.md` — Section 4.1 (projects scope tasks and bugs)
- `cogs/slashCommands.py` — Existing cog pattern (app_commands.Group, setup function, error handler)
- `cogs/moderation.py` — check_auth pattern for permission gates
- `database.py` — createProject, getProject, getProjects, deleteProject, setActiveProject, getActiveProject, hasTeamPermission
- `config.py` — embedColor

## Tasks

<task type="auto">
  <name>Create projects cog with all commands</name>
  <files>cogs/projects.py</files>
  <action>
    Create a new file `cogs/projects.py` with the following structure:

    ```python
    import time
    import discord
    from discord import app_commands
    from discord.ext import commands
    from database import (
        createProject, getProject, getProjects, deleteProject,
        setActiveProject, getActiveProject, hasTeamPermission, logAudit
    )
    from config import embedColor

    class Projects(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        project_group = app_commands.Group(name="project", description="Manage projects")

        # Error handler — same pattern as slashCommands.py
        async def cog_app_command_error(self, interaction, error):
            ...

        # ── /project new ──
        # Accepts comma-separated names for BULK creation:
        #   /project new name:"Bug Tracker, Auth System, Dashboard"
        # Single name also works:
        #   /project new name:"Bug Tracker" description:"Track all bugs"
        @project_group.command(name="new", description="Create project(s). Comma-separate names for bulk creation.")
        @app_commands.describe(name="Project name (comma-separate for bulk: 'Proj1, Proj2, Proj3')", description="Description (applies to single project only)")
        async def project_new(self, interaction, name: str, description: str = ""):
            # Permission check: requires 'lead' role
            if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
                # Fallback: allow Discord admin
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Requires **Lead** role or Admin.", ephemeral=True)
                    return

            names = [n.strip() for n in name.split(",") if n.strip()]
            now = int(time.time())
            created = []
            errors = []

            for proj_name in names:
                try:
                    pid = await createProject(interaction.guild_id, proj_name, description if len(names) == 1 else "", now)
                    created.append((pid, proj_name))
                    await logAudit(interaction.guild_id, "create", "project", pid, str(interaction.user.id), f"Created project: {proj_name}", now)
                except Exception as e:
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                        errors.append(f"⚠ `{proj_name}` already exists")
                    else:
                        errors.append(f"❌ `{proj_name}`: {e}")

            # Build response embed
            embed = discord.Embed(color=embedColor)
            if len(created) == 1:
                pid, pname = created[0]
                embed.title = "✅ Project Created"
                embed.description = f"**{pname}** (ID: `{pid}`)"
                if description:
                    embed.add_field(name="Description", value=description, inline=False)
                # Auto-set as active if no active project
                active = await getActiveProject(interaction.guild_id)
                if not active:
                    await setActiveProject(interaction.guild_id, pid)
                    embed.set_footer(text=f"Auto-set as active project")
            elif created:
                embed.title = f"✅ {len(created)} Projects Created"
                embed.description = "\n".join([f"• **{pname}** (ID: `{pid}`)" for pid, pname in created])

            if errors:
                embed.add_field(name="Errors", value="\n".join(errors), inline=False)

            if not created and not errors:
                await interaction.response.send_message("❌ No valid names provided.", ephemeral=True)
                return

            await interaction.response.send_message(embed=embed)

        # ── /project list ──
        @project_group.command(name="list", description="List all projects")
        async def project_list(self, interaction):
            projects = await getProjects(interaction.guild_id)
            active = await getActiveProject(interaction.guild_id)
            active_id = active['id'] if active else None

            if not projects:
                await interaction.response.send_message("No projects yet. Create one with `/project new`.", ephemeral=True)
                return

            embed = discord.Embed(title="📋 Projects", color=embedColor)
            lines = []
            for p in projects:
                marker = " ← **active**" if p['id'] == active_id else ""
                desc = f" — {p['description']}" if p['description'] else ""
                lines.append(f"`#{p['id']}` **{p['name']}**{desc}{marker}")
            embed.description = "\n".join(lines)
            await interaction.response.send_message(embed=embed)

        # ── /project set ──
        @project_group.command(name="set", description="Set the active project")
        @app_commands.describe(project_id="Project ID to make active")
        async def project_set(self, interaction, project_id: int):
            project = await getProject(project_id)
            if not project or str(project['guild_id']) != str(interaction.guild_id):
                await interaction.response.send_message("❌ Project not found.", ephemeral=True)
                return
            await setActiveProject(interaction.guild_id, project_id)
            await interaction.response.send_message(f"✅ Active project set to **{project['name']}** (`#{project_id}`).")

        # ── /project delete ──
        @project_group.command(name="delete", description="Delete a project (cascades tasks, bugs, sprints)")
        @app_commands.describe(project_id="Project ID to delete")
        async def project_delete(self, interaction, project_id: int):
            if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'admin'):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Requires **Admin** role.", ephemeral=True)
                    return

            project = await getProject(project_id)
            if not project or str(project['guild_id']) != str(interaction.guild_id):
                await interaction.response.send_message("❌ Project not found.", ephemeral=True)
                return
            await deleteProject(project_id)
            await logAudit(interaction.guild_id, "delete", "project", project_id, str(interaction.user.id), f"Deleted project: {project['name']}", int(time.time()))
            await interaction.response.send_message(f"🗑️ Deleted project **{project['name']}** and all related tasks/bugs/sprints.")

    async def setup(bot):
        await bot.add_cog(Projects(bot))
    ```

    **Key patterns to follow:**
    - Use `app_commands.Group(name="project", ...)` for the command group (same as `spam_group`, `word_group` etc in slashCommands.py)
    - Use `from config import embedColor` for consistent embed styling
    - Use `ephemeral=True` for errors, `ephemeral=False` (default) for success
    - Permission gate: `hasTeamPermission` from database.py, with fallback to Discord admin
    - Bulk creation: split `name` on commas, create each, collect results + errors, show summary embed
    - Auto-set first created project as active if none is active

    **AVOID:**
    - Do NOT use `@app_commands.checks.has_permissions` for SDLC commands — use `hasTeamPermission` instead (SDLC roles are separate from Discord roles)
    - Do NOT forget the guild_id check in project_set and project_delete (prevent cross-guild access)
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/projects.py').read()); print('Syntax OK')"</verify>
  <done>cogs/projects.py exists with 4 commands (new with bulk support, list, set, delete). Syntax validates.</done>
</task>

<task type="auto">
  <name>Register projects cog in main.py</name>
  <files>main.py</files>
  <action>
    Add `"cogs.projects"` to the `cogExtensions` list in main.py.
    Add it after the existing cogs (e.g., after `"cogs.customHelp"`).
  </action>
  <verify>python -c "import ast; ast.parse(open('main.py').read()); print('main.py OK')"</verify>
  <done>"cogs.projects" is in the cogExtensions list in main.py.</done>
</task>

## Success Criteria
- [ ] `cogs/projects.py` exists with Project cog class
- [ ] `/project new` supports comma-separated bulk creation
- [ ] `/project list` shows all projects with active marker
- [ ] `/project set` changes active project
- [ ] `/project delete` requires admin, cascades
- [ ] Permission gates use hasTeamPermission with Discord admin fallback
- [ ] Cog registered in main.py cogExtensions
- [ ] Both files pass syntax validation

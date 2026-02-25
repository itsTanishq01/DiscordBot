---
phase: 2
plan: 3
wave: 2
---

# Plan 2.3: Shared SDLC Helpers & Verification

## Objective
Create a shared utility module for common SDLC patterns (active project check, permission checks, embed builders) to reduce code duplication across cogs. Then verify both cogs load correctly.

## Context
- `cogs/projects.py` — Pattern from Plan 2.1
- `cogs/sprints.py` — Pattern from Plan 2.2  
- `database.py` — hasTeamPermission, getActiveProject
- `config.py` — embedColor

## Tasks

<task type="auto">
  <name>Create shared SDLC helpers module</name>
  <files>cogs/sdlcHelpers.py</files>
  <action>
    Create `cogs/sdlcHelpers.py` with reusable helpers that Phase 3+ cogs will use:

    ```python
    import discord
    from database import getActiveProject, hasTeamPermission
    from config import embedColor

    async def requireActiveProject(interaction):
        """Check for active project. Sends error if none. Returns project dict or None."""
        project = await getActiveProject(interaction.guild_id)
        if not project:
            await interaction.response.send_message(
                "❌ No active project. Set one with `/project set`.", ephemeral=True
            )
            return None
        return project

    async def requireRole(interaction, role):
        """Check SDLC role permission with Discord admin fallback. Returns True if allowed."""
        if await hasTeamPermission(interaction.guild_id, str(interaction.user.id), role):
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message(
            f"❌ Requires **{role.capitalize()}** role or Admin.", ephemeral=True
        )
        return False

    def parseBulkNames(raw):
        """Split comma-separated string into list of trimmed, non-empty names."""
        return [n.strip() for n in raw.split(",") if n.strip()]

    def buildBulkEmbed(created, errors, entity_type, extra_fields=None):
        """Build a summary embed for bulk or single creation operations.

        Args:
            created: list of (id, name) tuples
            errors: list of error strings
            entity_type: "project", "sprint", "task", "bug", etc.
            extra_fields: optional list of (name, value, inline) tuples
        """
        embed = discord.Embed(color=embedColor)

        if len(created) == 1:
            eid, ename = created[0]
            embed.title = f"✅ {entity_type.capitalize()} Created"
            embed.description = f"**{ename}** (ID: `{eid}`)"
        elif created:
            embed.title = f"✅ {len(created)} {entity_type.capitalize()}s Created"
            embed.description = "\n".join([f"• **{ename}** (ID: `{eid}`)" for eid, ename in created])

        if extra_fields:
            for fname, fval, finline in extra_fields:
                embed.add_field(name=fname, value=fval, inline=finline)

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)

        return embed

    # Status constants used across cogs
    TASK_STATUSES = ['backlog', 'todo', 'in_progress', 'blocked', 'review', 'done']
    BUG_STATUSES = ['new', 'acknowledged', 'in_progress', 'needs_qa', 'closed']
    BUG_SEVERITIES = ['critical', 'medium', 'minor']
    TASK_PRIORITIES = ['critical', 'high', 'medium', 'low']

    # Emoji maps
    STATUS_EMOJI = {
        'backlog': '📥', 'todo': '📋', 'in_progress': '🔨',
        'blocked': '🚫', 'review': '🔍', 'done': '✅',
        'new': '🆕', 'acknowledged': '👀', 'needs_qa': '🧪', 'closed': '⬛'
    }
    SEVERITY_EMOJI = {'critical': '🔴', 'medium': '🟡', 'minor': '🟠'}
    PRIORITY_EMOJI = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
    ```

    This module is NOT a cog (no setup function, no class). It's a pure utility module imported by other cogs.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/sdlcHelpers.py').read()); print('Syntax OK')"</verify>
  <done>cogs/sdlcHelpers.py exists with requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed, and all status/emoji constants.</done>
</task>

<task type="auto">
  <name>Verify all cogs are importable</name>
  <files>cogs/projects.py, cogs/sprints.py, cogs/sdlcHelpers.py</files>
  <action>
    Run verification commands to prove everything works:

    1. Syntax check all 3 new files
    2. Import check all new modules
    3. Verify main.py has both cogs registered
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/projects.py').read()); ast.parse(open('cogs/sprints.py').read()); ast.parse(open('cogs/sdlcHelpers.py').read()); ast.parse(open('main.py').read()); print('All files valid ✓')"</verify>
  <done>All 3 new files + main.py parse without errors. cogs.projects and cogs.sprints in cogExtensions.</done>
</task>

## Success Criteria
- [ ] `cogs/sdlcHelpers.py` exists with shared helpers
- [ ] requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed functions available
- [ ] Status constants (TASK_STATUSES, BUG_STATUSES, etc.) and emoji maps defined
- [ ] All files (projects.py, sprints.py, sdlcHelpers.py, main.py) pass syntax validation

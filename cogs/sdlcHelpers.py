import discord
from database import getActiveProject, hasTeamPermission
from config import embedColor


async def requireActiveProject(interaction):
    """Check for active project. Sends error if none. Returns project dict or None."""
    project = await getActiveProject(interaction.guild_id)
    if not project:
        await interaction.response.send_message(
            "No active project. Set one with `/project set`.", ephemeral=True
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
        f"Requires **{role.capitalize()}** role or Admin.", ephemeral=True
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

    if not created and errors:
        embed.title = f"⚠ No {entity_type.capitalize()}s Created"
        embed.color = 0xFFAA00

    return embed


# ─────────────────────────────────────────────
# Status / Enum Constants
# ─────────────────────────────────────────────

TASK_STATUSES = ['backlog', 'todo', 'in_progress', 'blocked', 'review', 'done']
BUG_STATUSES = ['new', 'acknowledged', 'in_progress', 'needs_qa', 'closed']
BUG_SEVERITIES = ['critical', 'medium', 'minor']
TASK_PRIORITIES = ['critical', 'high', 'medium', 'low']
SPRINT_STATUSES = ['planning', 'active', 'closed']

# ─────────────────────────────────────────────
# Emoji Maps
# ─────────────────────────────────────────────

STATUS_EMOJI = {
    'backlog': '📥', 'todo': '📋', 'in_progress': '🔨',
    'blocked': '🚫', 'review': '🔍', 'done': '✅',
    'new': '🆕', 'acknowledged': '👀', 'needs_qa': '🧪', 'closed': '⬛',
    'planning': '📋', 'active': '🟢',
}

SEVERITY_EMOJI = {'critical': '🔴', 'medium': '🟡', 'minor': '🟠'}
PRIORITY_EMOJI = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}


def statusDisplay(status):
    """Format a status with its emoji for display."""
    emoji = STATUS_EMOJI.get(status, '❓')
    clean = status.replace('_', ' ').title()
    return f"{emoji} {clean}"


def severityDisplay(severity):
    """Format a severity with its emoji for display."""
    emoji = SEVERITY_EMOJI.get(severity, '❓')
    return f"{emoji} {severity.capitalize()}"


def priorityDisplay(priority):
    """Format a priority with its emoji for display."""
    emoji = PRIORITY_EMOJI.get(priority, '❓')
    return f"{emoji} {priority.capitalize()}"

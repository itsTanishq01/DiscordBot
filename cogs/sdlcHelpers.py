import discord
from database import getActiveProject, getConfig
from config import embedColor

# ─────────────────────────────────────────────
# Configurable Permission Groups
# ─────────────────────────────────────────────

VALID_GROUPS = {'bugs', 'checklists', 'projects', 'tasks'}


async def getGroupRoles(guildId, group):
    """Get the allowed Discord role IDs for a command group.
    Returns a list of role ID strings, or empty list (= everyone allowed).
    """
    val = await getConfig(guildId, f"devperm_{group}")
    if val:
        return [r.strip() for r in val.split(",") if r.strip()]
    return []  # empty = no restrictions (everyone can use)


async def requireActiveProject(interaction):
    """Check for active project. Sends error if none. Returns project dict or None."""
    project = await getActiveProject(interaction.guild_id)
    if not project:
        error_msg = "No active project. Set one with `/project set`."
        if interaction.response.is_done():
            await interaction.followup.send(error_msg, ephemeral=True)
        else:
            await interaction.response.send_message(error_msg, ephemeral=True)
        return None
    return project


async def requireRole(interaction, allowed_role_ids):
    """Check if user has one of the allowed Discord roles.

    Args:
        interaction: Discord interaction
        allowed_role_ids: list of Discord role ID strings.
                          If empty, everyone is allowed.

    Discord server admins always pass as a fallback.
    """
    # If no roles configured, everyone can use it
    if not allowed_role_ids:
        return True

    # Discord admin always passes
    if interaction.user.guild_permissions.administrator:
        return True

    # Check if user has any of the allowed roles
    user_role_ids = {str(role.id) for role in interaction.user.roles}
    for role_id in allowed_role_ids:
        if role_id in user_role_ids:
            return True

    # Build a nice error message with @role mentions
    role_mentions = ", ".join([f"<@&{rid}>" for rid in allowed_role_ids])
    error_msg = f"❌ You need one of these roles: {role_mentions}"

    if interaction.response.is_done():
        await interaction.followup.send(error_msg, ephemeral=True)
    else:
        await interaction.response.send_message(error_msg, ephemeral=True)

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

# ─────────────────────────────────────────────
# Emoji Maps
# ─────────────────────────────────────────────

STATUS_EMOJI = {
    'backlog': '📥', 'todo': '📋', 'in_progress': '🔨',
    'blocked': '🚫', 'review': '🔍', 'done': '✅',
    'new': '🆕', 'acknowledged': '👀', 'needs_qa': '🧪', 'closed': '⬛',
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

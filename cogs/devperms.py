import discord
from discord import app_commands
from discord.ext import commands
from database import getConfig, setConfig
from config import embedColor
from cogs.sdlcHelpers import (
    requireRole, getGroupRoles,
    VALID_GROUPS, VALID_ROLES, DEFAULT_GROUP_ROLES
)

GROUP_CHOICES = [app_commands.Choice(name=g.capitalize(), value=g) for g in sorted(VALID_GROUPS)]
ROLE_CHOICES = [
    app_commands.Choice(name="Admin", value="admin"),
    app_commands.Choice(name="Lead", value="lead"),
    app_commands.Choice(name="Developer", value="developer"),
    app_commands.Choice(name="QA / Tester", value="qa"),
    app_commands.Choice(name="Viewer", value="viewer"),
]

ROLE_EMOJI = {
    'admin': '👑', 'lead': '🧠', 'developer': '💻', 'qa': '🧪', 'viewer': '👁'
}


class DevPerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    dp_group = app_commands.Group(name="devperm", description="Configure which roles can use dev commands")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /devperm add ─────────────────────────────
    @dp_group.command(name="add", description="Allow a role to use a command group")
    @app_commands.describe(group="Command group (e.g. bugs, tasks)", role="Role to add")
    @app_commands.choices(group=GROUP_CHOICES, role=ROLE_CHOICES)
    async def devperm_add(self, interaction: discord.Interaction,
                          group: app_commands.Choice[str],
                          role: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, ['admin']):
            return

        current = await getGroupRoles(interaction.guild_id, group.value)

        if role.value in current:
            await interaction.followup.send(
                f"{ROLE_EMOJI.get(role.value, '')} **{role.name}** already has access to **{group.name}** commands.",
                ephemeral=True
            )
            return

        current.append(role.value)
        await setConfig(interaction.guild_id, f"devperm_{group.value}", ",".join(current))

        role_display = " ".join([f"`{ROLE_EMOJI.get(r, '')} {r}`" for r in current])
        embed = discord.Embed(
            title=f"✅ Permission Added",
            description=f"{ROLE_EMOJI.get(role.value, '')} **{role.name}** can now use **{group.name}** commands.",
            color=0x57F287
        )
        embed.add_field(name=f"{group.name} — Allowed Roles", value=role_display, inline=False)
        await interaction.followup.send(embed=embed)

    # ── /devperm remove ──────────────────────────
    @dp_group.command(name="remove", description="Remove a role from a command group")
    @app_commands.describe(group="Command group", role="Role to remove")
    @app_commands.choices(group=GROUP_CHOICES, role=ROLE_CHOICES)
    async def devperm_remove(self, interaction: discord.Interaction,
                             group: app_commands.Choice[str],
                             role: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, ['admin']):
            return

        current = await getGroupRoles(interaction.guild_id, group.value)

        if role.value not in current:
            await interaction.followup.send(
                f"{ROLE_EMOJI.get(role.value, '')} **{role.name}** doesn't have access to **{group.name}** commands.",
                ephemeral=True
            )
            return

        if len(current) <= 1:
            await interaction.followup.send(
                "⚠️ Can't remove the last role. At least one role must have access.",
                ephemeral=True
            )
            return

        current.remove(role.value)
        await setConfig(interaction.guild_id, f"devperm_{group.value}", ",".join(current))

        role_display = " ".join([f"`{ROLE_EMOJI.get(r, '')} {r}`" for r in current])
        embed = discord.Embed(
            title=f"🗑️ Permission Removed",
            description=f"{ROLE_EMOJI.get(role.value, '')} **{role.name}** can no longer use **{group.name}** commands.",
            color=0xED4245
        )
        embed.add_field(name=f"{group.name} — Allowed Roles", value=role_display, inline=False)
        await interaction.followup.send(embed=embed)

    # ── /devperm view ────────────────────────────
    @dp_group.command(name="view", description="View current permission settings for all command groups")
    async def devperm_view(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        embed = discord.Embed(
            title="⚙️ Dev Command Permissions",
            description="Which roles can use which command groups.\n*Defaults shown unless customized.*",
            color=embedColor
        )

        for group in sorted(VALID_GROUPS):
            current = await getGroupRoles(interaction.guild_id, group)
            default = DEFAULT_GROUP_ROLES.get(group, [])

            is_custom = set(current) != set(default)
            marker = " ✏️" if is_custom else ""

            role_display = " ".join([f"`{ROLE_EMOJI.get(r, '')} {r}`" for r in current])
            embed.add_field(
                name=f"/{group}{marker}",
                value=role_display or "*No roles*",
                inline=False
            )

        embed.set_footer(text="✏️ = customized | Use /devperm add or /devperm remove to change")
        await interaction.followup.send(embed=embed)

    # ── /devperm reset ───────────────────────────
    @dp_group.command(name="reset", description="Reset a command group back to default permissions")
    @app_commands.describe(group="Command group to reset")
    @app_commands.choices(group=GROUP_CHOICES)
    async def devperm_reset(self, interaction: discord.Interaction,
                            group: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, ['admin']):
            return

        default = DEFAULT_GROUP_ROLES.get(group.value, ['developer', 'lead', 'admin'])
        await setConfig(interaction.guild_id, f"devperm_{group.value}", ",".join(default))

        role_display = " ".join([f"`{ROLE_EMOJI.get(r, '')} {r}`" for r in default])
        embed = discord.Embed(
            title=f"🔄 Permissions Reset",
            description=f"**{group.name}** reset to default roles.",
            color=embedColor
        )
        embed.add_field(name="Default Roles", value=role_display, inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DevPerms(bot))

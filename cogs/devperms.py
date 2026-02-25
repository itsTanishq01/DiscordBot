import discord
from discord import app_commands
from discord.ext import commands
from database import getConfig, setConfig
from config import embedColor
from cogs.sdlcHelpers import getGroupRoles, VALID_GROUPS

GROUP_CHOICES = [app_commands.Choice(name=g.capitalize(), value=g) for g in sorted(VALID_GROUPS)]


class DevPerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    dp_group = app_commands.Group(name="devperm", description="Configure which @roles can use dev commands")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /devperm add ─────────────────────────────
    @dp_group.command(name="add", description="Allow a Discord @role to use a command group")
    @app_commands.describe(group="Command group (e.g. bugs, tasks)", role="Discord role to allow")
    @app_commands.choices(group=GROUP_CHOICES)
    @app_commands.checks.has_permissions(administrator=True)
    async def devperm_add(self, interaction: discord.Interaction,
                          group: app_commands.Choice[str],
                          role: discord.Role):
        await interaction.response.defer(ephemeral=False)

        current = await getGroupRoles(interaction.guild_id, group.value)
        role_id = str(role.id)

        if role_id in current:
            await interaction.followup.send(
                f"{role.mention} already has access to **{group.name}** commands.",
                ephemeral=True
            )
            return

        current.append(role_id)
        await setConfig(interaction.guild_id, f"devperm_{group.value}", ",".join(current))

        role_display = " ".join([f"<@&{rid}>" for rid in current])
        embed = discord.Embed(
            title="✅ Permission Added",
            description=f"{role.mention} can now use **{group.name}** commands.",
            color=0x57F287
        )
        embed.add_field(name=f"{group.name} — Allowed Roles", value=role_display, inline=False)
        await interaction.followup.send(embed=embed)

    # ── /devperm remove ──────────────────────────
    @dp_group.command(name="remove", description="Remove a Discord @role from a command group")
    @app_commands.describe(group="Command group", role="Discord role to remove")
    @app_commands.choices(group=GROUP_CHOICES)
    @app_commands.checks.has_permissions(administrator=True)
    async def devperm_remove(self, interaction: discord.Interaction,
                             group: app_commands.Choice[str],
                             role: discord.Role):
        await interaction.response.defer(ephemeral=False)

        current = await getGroupRoles(interaction.guild_id, group.value)
        role_id = str(role.id)

        if role_id not in current:
            await interaction.followup.send(
                f"{role.mention} doesn't have access to **{group.name}** commands.",
                ephemeral=True
            )
            return

        current.remove(role_id)
        if current:
            await setConfig(interaction.guild_id, f"devperm_{group.value}", ",".join(current))
        else:
            # Clear config = everyone allowed again
            await setConfig(interaction.guild_id, f"devperm_{group.value}", "")

        if current:
            role_display = " ".join([f"<@&{rid}>" for rid in current])
        else:
            role_display = "*Everyone (no restrictions)*"

        embed = discord.Embed(
            title="🗑️ Permission Removed",
            description=f"{role.mention} can no longer use **{group.name}** commands.",
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
            description="Which @roles can use which command groups.\n*No roles configured = everyone can use.*",
            color=embedColor
        )

        for group in sorted(VALID_GROUPS):
            current = await getGroupRoles(interaction.guild_id, group)

            if current:
                role_display = " ".join([f"<@&{rid}>" for rid in current])
                marker = " 🔒"
            else:
                role_display = "*Everyone (no restrictions)*"
                marker = ""

            embed.add_field(
                name=f"/{group}{marker}",
                value=role_display,
                inline=False
            )

        embed.set_footer(text="🔒 = restricted | Use /devperm add @role or /devperm remove @role")
        await interaction.followup.send(embed=embed)

    # ── /devperm reset ───────────────────────────
    @dp_group.command(name="reset", description="Reset a command group — removes all role restrictions")
    @app_commands.describe(group="Command group to reset")
    @app_commands.choices(group=GROUP_CHOICES)
    @app_commands.checks.has_permissions(administrator=True)
    async def devperm_reset(self, interaction: discord.Interaction,
                            group: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)

        await setConfig(interaction.guild_id, f"devperm_{group.value}", "")

        embed = discord.Embed(
            title="🔄 Permissions Reset",
            description=f"**{group.name}** — all role restrictions removed.\nEveryone can now use these commands.",
            color=embedColor
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DevPerms(bot))

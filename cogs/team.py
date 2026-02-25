import discord
from discord import app_commands
from discord.ext import commands
from database import (
    setTeamRole, removeTeamRole, getTeamRole, getTeamMembers
)
from config import embedColor
from cogs.sdlcHelpers import requireRole

ROLE_CHOICES = [
    app_commands.Choice(name="Admin (Full Access)", value="admin"),
    app_commands.Choice(name="Lead (Manage Sprints & Assign)", value="lead"),
    app_commands.Choice(name="Developer (Move Tasks & Bugs)", value="developer"),
    app_commands.Choice(name="QA (Close Bugs)", value="qa"),
    app_commands.Choice(name="Viewer (Read Only)", value="viewer"),
]

ROLE_EMOJI = {
    'admin': '\U0001f451',      # 👑
    'lead': '\U0001f9e0',       # 🧠
    'developer': '\U0001f4bb',  # 💻
    'qa': '\U0001f9ea',         # 🧪
    'viewer': '\U0001f441',     # 👁
}

# Display order for team list (highest to lowest)
ROLE_ORDER = ['admin', 'lead', 'developer', 'qa', 'viewer']


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    team_group = app_commands.Group(name="team", description="Manage SDLC team roles")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    # ── /team assign ──────────────────────────────
    @team_group.command(name="assign", description="Assign an SDLC role to a member")
    @app_commands.describe(member="Member to assign a role to", role="SDLC role to assign")
    @app_commands.choices(role=ROLE_CHOICES)
    async def team_assign(self, interaction: discord.Interaction,
                          member: discord.Member, role: app_commands.Choice[str]):
        if not await requireRole(interaction, 'admin'):
            return

        await setTeamRole(interaction.guild_id, str(member.id), role.value)

        emoji = ROLE_EMOJI.get(role.value, '')
        embed = discord.Embed(
            title=f"{emoji} Role Assigned",
            description=f"{member.mention} is now a **{role.name.split(' (')[0]}**.",
            color=embedColor
        )
        embed.add_field(name="Role", value=f"{emoji} {role.value.capitalize()}", inline=True)
        embed.add_field(name="Assigned by", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    # ── /team unassign ────────────────────────────
    @team_group.command(name="unassign", description="Remove a member's SDLC role")
    @app_commands.describe(member="Member whose role should be removed")
    async def team_unassign(self, interaction: discord.Interaction, member: discord.Member):
        if not await requireRole(interaction, 'admin'):
            return

        current = await getTeamRole(interaction.guild_id, str(member.id))
        if not current:
            await interaction.response.send_message(
                f"{member.mention} has no SDLC role assigned.", ephemeral=True
            )
            return

        await removeTeamRole(interaction.guild_id, str(member.id))

        embed = discord.Embed(
            title="\U0001f6ab Role Removed",
            description=f"{member.mention} no longer has an SDLC role.",
            color=embedColor
        )
        embed.add_field(name="Previous Role", value=f"{ROLE_EMOJI.get(current, '')} {current.capitalize()}", inline=True)
        embed.add_field(name="Removed by", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    # ── /team list ────────────────────────────────
    @team_group.command(name="list", description="View all SDLC team members grouped by role")
    async def team_list(self, interaction: discord.Interaction):
        members = await getTeamMembers(interaction.guild_id)

        if not members:
            await interaction.response.send_message(
                "No SDLC team members yet. Use `/team assign` to add members.", ephemeral=True
            )
            return

        # Group by role
        groups = {r: [] for r in ROLE_ORDER}
        for m in members:
            role = m['role']
            if role in groups:
                groups[role].append(m['user_id'])

        embed = discord.Embed(
            title="\U0001f465 SDLC Team",
            color=embedColor
        )

        total = 0
        for role in ROLE_ORDER:
            user_ids = groups[role]
            if not user_ids:
                continue
            emoji = ROLE_EMOJI.get(role, '')
            mentions = " ".join([f"<@{uid}>" for uid in user_ids])
            embed.add_field(
                name=f"{emoji} {role.capitalize()} ({len(user_ids)})",
                value=mentions,
                inline=False
            )
            total += len(user_ids)

        embed.set_footer(text=f"{total} member(s) total")
        await interaction.response.send_message(embed=embed)

    # ── /team myrole ──────────────────────────────
    @team_group.command(name="myrole", description="Check your current SDLC role")
    async def team_myrole(self, interaction: discord.Interaction):
        role = await getTeamRole(interaction.guild_id, str(interaction.user.id))

        if not role:
            await interaction.response.send_message(
                "You don't have an SDLC role yet. Ask an Admin to assign you one with `/team assign`.",
                ephemeral=True
            )
            return

        emoji = ROLE_EMOJI.get(role, '')
        embed = discord.Embed(
            title=f"{emoji} Your SDLC Role",
            description=f"You are a **{role.capitalize()}** on this server's SDLC team.",
            color=embedColor
        )

        # Show what they can do
        permissions_map = {
            'admin':     "Assign roles, delete projects, full access to all commands.",
            'lead':      "Create sprints, assign tasks/bugs, manage team assignments.",
            'developer': "Create & update tasks, report & triage bugs, add comments.",
            'qa':        "Close bugs (QA-gate), manage checklists.",
            'viewer':    "View tasks, bugs, and project status (read-only).",
        }
        embed.add_field(name="Permissions", value=permissions_map.get(role, "Unknown"), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Team(bot))

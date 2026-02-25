import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createProject, getProject, getProjects, deleteProject,
    setActiveProject, getActiveProject, logAudit
)
from config import embedColor
from cogs.sdlcHelpers import requireRole, getGroupRoles


class Projects(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    project_group = app_commands.Group(name="project", description="Manage projects")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @project_group.command(name="new", description="Create project(s). Comma-separate names for bulk creation.")
    @app_commands.describe(
        name="Project name (comma-separate for bulk: 'Proj1, Proj2, Proj3')",
        description="Description (applies to single project only)"
    )
    async def project_new(self, interaction: discord.Interaction, name: str, description: str = ""):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'projects')):
            return

        names = [n.strip() for n in name.split(",") if n.strip()]
        if not names:
            await interaction.followup.send("❌ No valid names provided.", ephemeral=True)
            return

        now = int(time.time())
        created = []
        errors = []

        for proj_name in names:
            try:
                seq = await createProject(interaction.guild_id, proj_name, description if len(names) == 1 else "", now)
                created.append((seq, proj_name))
                await logAudit(interaction.guild_id, "create", "project", seq, str(interaction.user.id), f"Created project: {proj_name}", now)
            except Exception as e:
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    errors.append(f"⚠ `{proj_name}` already exists")
                else:
                    errors.append(f"❌ `{proj_name}`: {e}")

        embed = discord.Embed(color=embedColor)

        if len(created) == 1:
            seq, pname = created[0]
            embed.title = "✅ Project Created"
            embed.description = f"**{pname}** (ID: `#{seq}`)"
            if description:
                embed.add_field(name="Description", value=description, inline=False)
            active = await getActiveProject(interaction.guild_id)
            if not active:
                await setActiveProject(interaction.guild_id, seq)
                embed.set_footer(text="Auto-set as active project")
        elif created:
            embed.title = f"✅ {len(created)} Projects Created"
            embed.description = "\n".join([f"• **{pname}** (ID: `#{seq}`)" for seq, pname in created])
            active = await getActiveProject(interaction.guild_id)
            if not active and created:
                first_seq, first_name = created[0]
                await setActiveProject(interaction.guild_id, first_seq)
                embed.set_footer(text=f"Auto-set '{first_name}' as active project")

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)

        if not created and errors:
            embed.title = "⚠ No Projects Created"
            embed.color = 0xFFAA00

        await interaction.followup.send(embed=embed)

    @project_group.command(name="list", description="List all projects")
    async def project_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        projects = await getProjects(interaction.guild_id)
        active = await getActiveProject(interaction.guild_id)
        active_seq = active['guild_seq'] if active else None

        if not projects:
            await interaction.followup.send("No projects yet. Create one with `/project new`.", ephemeral=True)
            return

        embed = discord.Embed(title="📋 Projects", color=embedColor)
        lines = []
        for p in projects:
            marker = " ← **active**" if p['guild_seq'] == active_seq else ""
            desc = f" — {p['description']}" if p['description'] else ""
            lines.append(f"`#{p['guild_seq']}` **{p['name']}**{desc}{marker}")
        embed.description = "\n".join(lines)
        await interaction.followup.send(embed=embed)

    @project_group.command(name="set", description="Set the active project")
    @app_commands.describe(project_id="Project ID to make active")
    async def project_set(self, interaction: discord.Interaction, project_id: int):
        await interaction.response.defer(ephemeral=False)
        project = await getProject(interaction.guild_id, project_id)
        if not project:
            await interaction.followup.send("❌ Project not found.", ephemeral=True)
            return
        await setActiveProject(interaction.guild_id, project_id)
        await interaction.followup.send(f"✅ Active project set to **{project['name']}** (`#{project_id}`).")

    @project_group.command(name="delete", description="Delete a project (cascades tasks, bugs)")
    @app_commands.describe(project_id="Project ID to delete")
    async def project_delete(self, interaction: discord.Interaction, project_id: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'projects')):
            return

        project = await getProject(interaction.guild_id, project_id)
        if not project:
            await interaction.followup.send("❌ Project not found.", ephemeral=True)
            return

        pname = project['name']
        await deleteProject(interaction.guild_id, project_id)
        await logAudit(interaction.guild_id, "delete", "project", project_id, str(interaction.user.id), f"Deleted project: {pname}", int(time.time()))

        active = await getActiveProject(interaction.guild_id)
        footer = ""
        if active and active['guild_seq'] == project_id:
            await setActiveProject(interaction.guild_id, "")
            footer = " Active project cleared."

        await interaction.followup.send(f"🗑️ Deleted project **{pname}** and all related tasks/bugs.{footer}")


async def setup(bot):
    await bot.add_cog(Projects(bot))

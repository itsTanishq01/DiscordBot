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

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    @project_group.command(name="new", description="Create project(s). Comma-separate names for bulk creation.")
    @app_commands.describe(
        name="Project name (comma-separate for bulk: 'Proj1, Proj2, Proj3')",
        description="Description (applies to single project only)"
    )
    async def project_new(self, interaction: discord.Interaction, name: str, description: str = ""):
        if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Requires **Lead** role or Admin.", ephemeral=True)
                return

        names = [n.strip() for n in name.split(",") if n.strip()]
        if not names:
            await interaction.response.send_message("❌ No valid names provided.", ephemeral=True)
            return

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

        embed = discord.Embed(color=embedColor)

        if len(created) == 1:
            pid, pname = created[0]
            embed.title = "✅ Project Created"
            embed.description = f"**{pname}** (ID: `{pid}`)"
            if description:
                embed.add_field(name="Description", value=description, inline=False)
            active = await getActiveProject(interaction.guild_id)
            if not active:
                await setActiveProject(interaction.guild_id, pid)
                embed.set_footer(text="Auto-set as active project")
        elif created:
            embed.title = f"✅ {len(created)} Projects Created"
            embed.description = "\n".join([f"• **{pname}** (ID: `{pid}`)" for pid, pname in created])
            active = await getActiveProject(interaction.guild_id)
            if not active and created:
                first_pid, first_name = created[0]
                await setActiveProject(interaction.guild_id, first_pid)
                embed.set_footer(text=f"Auto-set '{first_name}' as active project")

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)

        if not created and errors:
            embed.title = "⚠ No Projects Created"
            embed.color = 0xFFAA00

        await interaction.response.send_message(embed=embed)

    @project_group.command(name="list", description="List all projects")
    async def project_list(self, interaction: discord.Interaction):
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

    @project_group.command(name="set", description="Set the active project")
    @app_commands.describe(project_id="Project ID to make active")
    async def project_set(self, interaction: discord.Interaction, project_id: int):
        project = await getProject(project_id)
        if not project or str(project['guild_id']) != str(interaction.guild_id):
            await interaction.response.send_message("❌ Project not found.", ephemeral=True)
            return
        await setActiveProject(interaction.guild_id, project_id)
        await interaction.response.send_message(f"✅ Active project set to **{project['name']}** (`#{project_id}`).")

    @project_group.command(name="delete", description="Delete a project (cascades tasks, bugs, sprints)")
    @app_commands.describe(project_id="Project ID to delete")
    async def project_delete(self, interaction: discord.Interaction, project_id: int):
        if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'admin'):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Requires **Admin** role.", ephemeral=True)
                return

        project = await getProject(project_id)
        if not project or str(project['guild_id']) != str(interaction.guild_id):
            await interaction.response.send_message("❌ Project not found.", ephemeral=True)
            return

        pname = project['name']
        await deleteProject(project_id)
        await logAudit(interaction.guild_id, "delete", "project", project_id, str(interaction.user.id), f"Deleted project: {pname}", int(time.time()))

        active = await getActiveProject(interaction.guild_id)
        footer = ""
        if active and active['id'] == project_id:
            await setActiveProject(interaction.guild_id, "")
            footer = " Active project cleared."

        await interaction.response.send_message(f"🗑️ Deleted project **{pname}** and all related tasks/bugs/sprints.{footer}")


async def setup(bot):
    await bot.add_cog(Projects(bot))

import time
import datetime
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createSprint, getSprints, updateSprintStatus, getActiveSprint,
    getActiveProject, hasTeamPermission, logAudit
)
from config import embedColor

SPRINT_STATUSES = ['planning', 'active', 'closed']
STATUS_EMOJI = {'planning': '📋', 'active': '🟢', 'closed': '⬛'}


class Sprints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    sprint_group = app_commands.Group(name="sprint", description="Manage sprints")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    async def _require_active_project(self, interaction):
        project = await getActiveProject(interaction.guild_id)
        if not project:
            await interaction.response.send_message(
                "No active project. Set one with `/project set`.", ephemeral=True
            )
            return None
        return project

    @sprint_group.command(name="new", description="Create sprint(s). Comma-separate names for bulk.")
    @app_commands.describe(
        name="Sprint name (comma-separate for bulk: 'Sprint 1, Sprint 2')",
        start_date="Start date (YYYY-MM-DD, optional)",
        end_date="End date (YYYY-MM-DD, optional)"
    )
    async def sprint_new(self, interaction: discord.Interaction, name: str, start_date: str = None, end_date: str = None):
        if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Requires **Lead** role or Admin.", ephemeral=True)
                return

        project = await self._require_active_project(interaction)
        if not project:
            return

        start_ts = None
        end_ts = None
        if start_date:
            try:
                start_ts = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            except ValueError:
                await interaction.response.send_message("Invalid start date. Use YYYY-MM-DD.", ephemeral=True)
                return
        if end_date:
            try:
                end_ts = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            except ValueError:
                await interaction.response.send_message("Invalid end date. Use YYYY-MM-DD.", ephemeral=True)
                return

        names = [n.strip() for n in name.split(",") if n.strip()]
        if not names:
            await interaction.response.send_message("No valid names provided.", ephemeral=True)
            return

        now = int(time.time())
        created = []
        errors = []

        for sprint_name in names:
            try:
                sid = await createSprint(
                    interaction.guild_id, project['id'], sprint_name,
                    start_ts if len(names) == 1 else None,
                    end_ts if len(names) == 1 else None,
                    now
                )
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

        if not created and errors:
            embed.title = "⚠ No Sprints Created"
            embed.color = 0xFFAA00

        await interaction.response.send_message(embed=embed)

    @sprint_group.command(name="list", description="List sprints in active project")
    async def sprint_list(self, interaction: discord.Interaction):
        project = await self._require_active_project(interaction)
        if not project:
            return

        sprints = await getSprints(interaction.guild_id, project['id'])
        if not sprints:
            await interaction.response.send_message(
                f"No sprints in **{project['name']}**. Create one with `/sprint new`.", ephemeral=True
            )
            return

        embed = discord.Embed(title=f"🏃 Sprints — {project['name']}", color=embedColor)
        lines = []
        for s in sprints:
            emoji = STATUS_EMOJI.get(s['status'], '❓')
            date_info = ""
            if s.get('start_date'):
                start = datetime.datetime.fromtimestamp(s['start_date']).strftime('%m/%d')
                date_info += f" | Start: {start}"
            if s.get('end_date'):
                end = datetime.datetime.fromtimestamp(s['end_date']).strftime('%m/%d')
                date_info += f" → {end}"
            lines.append(f"{emoji} `#{s['id']}` **{s['name']}** — {s['status']}{date_info}")
        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @sprint_group.command(name="activate", description="Set a sprint as active")
    @app_commands.describe(sprint_id="Sprint ID to activate")
    async def sprint_activate(self, interaction: discord.Interaction, sprint_id: int):
        if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Requires **Lead** role or Admin.", ephemeral=True)
                return

        project = await self._require_active_project(interaction)
        if not project:
            return

        current = await getActiveSprint(interaction.guild_id, project['id'])
        if current and current['id'] != sprint_id:
            await updateSprintStatus(current['id'], 'closed')

        await updateSprintStatus(sprint_id, 'active')
        await logAudit(interaction.guild_id, "activate", "sprint", sprint_id, str(interaction.user.id), "Sprint activated", int(time.time()))
        await interaction.response.send_message(f"✅ Sprint `#{sprint_id}` is now **active**.")

    @sprint_group.command(name="close", description="Close the active sprint")
    async def sprint_close(self, interaction: discord.Interaction):
        if not await hasTeamPermission(interaction.guild_id, str(interaction.user.id), 'lead'):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Requires **Lead** role or Admin.", ephemeral=True)
                return

        project = await self._require_active_project(interaction)
        if not project:
            return

        current = await getActiveSprint(interaction.guild_id, project['id'])
        if not current:
            await interaction.response.send_message("No active sprint to close.", ephemeral=True)
            return

        await updateSprintStatus(current['id'], 'closed')
        await logAudit(interaction.guild_id, "close", "sprint", current['id'], str(interaction.user.id), f"Closed sprint: {current['name']}", int(time.time()))
        await interaction.response.send_message(f"⬛ Sprint **{current['name']}** closed.")


async def setup(bot):
    await bot.add_cog(Sprints(bot))

import discord
from discord import app_commands
from discord.ext import commands
from database import (
    getUserWorkload, getTeamMembers, getConfig, setConfig
)
from config import embedColor
from cogs.sdlcHelpers import requireRole


class Workload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    wl_group = app_commands.Group(name="workload", description="Track developer workload")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    # ── /workload check ───────────────────────────
    @wl_group.command(name="check", description="Check workload for yourself or another member")
    @app_commands.describe(member="Member to check (defaults to you)")
    async def workload_check(self, interaction: discord.Interaction,
                             member: discord.Member = None):
        target = member or interaction.user

        # If checking someone else, require lead role
        if member and member.id != interaction.user.id:
            if not await requireRole(interaction, 'lead'):
                return

        load = await getUserWorkload(interaction.guild_id, str(target.id))
        max_str = await getConfig(interaction.guild_id, "workloadMaxTasks")
        max_tasks = int(max_str) if max_str else 10

        total = load['tasks'] + load['bugs']

        # Color indicator
        ratio = total / max_tasks if max_tasks > 0 else 0
        if ratio >= 1.0:
            indicator = "\U0001f534"  # 🔴
            status_text = "**OVERLOADED**"
            color = 0xED4245
        elif ratio >= 0.7:
            indicator = "\U0001f7e1"  # 🟡
            status_text = "**High Load**"
            color = 0xFEE75C
        else:
            indicator = "\U0001f7e2"  # 🟢
            status_text = "**Available**"
            color = 0x57F287

        # Progress bar
        filled = min(int(ratio * 10), 10)
        bar = "\u2588" * filled + "\u2591" * (10 - filled)

        embed = discord.Embed(
            title=f"{indicator} Workload \u2014 {target.display_name}",
            color=color
        )
        embed.description = f"**Status:** {status_text}\n`{bar}` {total}/{max_tasks}"
        embed.add_field(name="\U0001f4cb Tasks", value=str(load['tasks']), inline=True)
        embed.add_field(name="\U0001f41b Bugs", value=str(load['bugs']), inline=True)
        embed.add_field(name="Total", value=f"**{total}**", inline=True)

        if total == 0:
            embed.set_footer(text="No active items. Ready for new assignments!")
        elif ratio >= 1.0:
            embed.set_footer(text="Consider completing existing items before assigning more.")

        await interaction.response.send_message(embed=embed)

    # ── /workload team ────────────────────────────
    @wl_group.command(name="team", description="View workload across all team members")
    async def workload_team(self, interaction: discord.Interaction):
        if not await requireRole(interaction, 'lead'):
            return

        members = await getTeamMembers(interaction.guild_id)
        if not members:
            await interaction.response.send_message(
                "No team members. Use `/team assign` to add them.", ephemeral=True
            )
            return

        max_str = await getConfig(interaction.guild_id, "workloadMaxTasks")
        max_tasks = int(max_str) if max_str else 10

        # Gather workloads
        workloads = []
        for m in members:
            load = await getUserWorkload(interaction.guild_id, m['user_id'])
            total = load['tasks'] + load['bugs']
            workloads.append({
                'user_id': m['user_id'],
                'role': m['role'],
                'tasks': load['tasks'],
                'bugs': load['bugs'],
                'total': total,
            })

        # Sort by total workload descending
        workloads.sort(key=lambda x: x['total'], reverse=True)

        embed = discord.Embed(
            title="\U0001f465 Team Workload",
            color=embedColor
        )

        lines = []
        for w in workloads:
            ratio = w['total'] / max_tasks if max_tasks > 0 else 0
            if ratio >= 1.0:
                indicator = "\U0001f534"
            elif ratio >= 0.7:
                indicator = "\U0001f7e1"
            else:
                indicator = "\U0001f7e2"

            bar_filled = min(int(ratio * 5), 5)
            mini_bar = "\u2588" * bar_filled + "\u2591" * (5 - bar_filled)

            lines.append(
                f"{indicator} <@{w['user_id']}> `{mini_bar}` "
                f"**{w['total']}**/{max_tasks} "
                f"({w['tasks']}T {w['bugs']}B)"
            )

        embed.description = "\n".join(lines) if lines else "No team members found."

        # Summary stats
        total_active = sum(w['total'] for w in workloads)
        overloaded = sum(1 for w in workloads if w['total'] >= max_tasks)
        embed.set_footer(
            text=f"{len(workloads)} members | {total_active} active items | {overloaded} overloaded"
        )

        await interaction.response.send_message(embed=embed)

    # ── /workload settings ────────────────────────
    @wl_group.command(name="settings", description="View or update workload settings")
    @app_commands.describe(
        max_tasks="Max active items per person (default: 10)",
        wip_limit="Max in-progress tasks before blocking (default: 5)"
    )
    async def workload_settings(self, interaction: discord.Interaction,
                                max_tasks: int = None, wip_limit: int = None):
        if not await requireRole(interaction, 'admin'):
            return

        updated = []

        if max_tasks is not None:
            await setConfig(interaction.guild_id, "workloadMaxTasks", str(max_tasks))
            updated.append(f"**workloadMaxTasks**: `{max_tasks}`")

        if wip_limit is not None:
            await setConfig(interaction.guild_id, "wipLimit", str(wip_limit))
            updated.append(f"**wipLimit**: `{wip_limit}`")

        # Always show current values
        current_max = await getConfig(interaction.guild_id, "workloadMaxTasks")
        current_wip = await getConfig(interaction.guild_id, "wipLimit")

        embed = discord.Embed(
            title="\u2699\ufe0f Workload Settings",
            color=embedColor
        )
        embed.add_field(
            name="Max Active Items Per Person",
            value=f"`{current_max or '10'}`",
            inline=True
        )
        embed.add_field(
            name="WIP Limit (In-Progress Cap)",
            value=f"`{current_wip or '5'}`",
            inline=True
        )

        if updated:
            embed.description = "\u2705 Updated:\n" + "\n".join(updated)
        else:
            embed.description = "*Pass `max_tasks` or `wip_limit` to update.*"

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Workload(bot))

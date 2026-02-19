import discord
from discord import app_commands
from discord.ext import commands
import time
import datetime
from database import addWarning, getWarnings, clearWarnings, hasCommandPerm, setConfig, getConfig
from modlog import sendModLog

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_auth(self, interaction: discord.Interaction, command: str, native_perm: bool) -> bool:
        if native_perm:
            return True
        if await hasCommandPerm(interaction.guild_id, command, interaction.user.roles):
            return True
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="warn", description="Warn a user. 3 warnings = 1h timeout.")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not await self.check_auth(interaction, "warn", interaction.user.guild_permissions.moderate_members): return

        if member.top_role >= interaction.user.top_role:
             await interaction.response.send_message("You cannot warn this member.", ephemeral=True)
             return

        timestamp = time.time()
        await addWarning(interaction.guild_id, member.id, interaction.user.id, reason, timestamp)
        
        # Check warning count
        warnings = await getWarnings(interaction.guild_id, member.id)
        count = len(warnings)
        
        response_msg = f"⚠️ Warned {member.mention}. They now have **{count}** warnings."
        action_msg = ""

        # Auto-punish at threshold
        threshold = int(await getConfig(interaction.guild_id, "warnThreshold") or 3)
        if count >= threshold:
            try:
                duration = datetime.timedelta(hours=1)
                await member.timeout(discord.utils.utcnow() + duration, reason=f"Auto-punish: {threshold} warnings")
                action_msg = "\n🚫 **Auto-Punish**: User timed out for 1 hour."
            except discord.Forbidden:
                action_msg = "\n❌ Failed to auto-timeout (missing permissions)."

        await interaction.response.send_message(f"{response_msg}{action_msg}", ephemeral=True)
        
        try:
            await member.send(f"You were warned in **{interaction.guild.name}**.\nReason: {reason}\nYour total warnings: {count}")
        except:
            pass

        await sendModLog(
            self.bot, interaction.guild_id,
            user=member,
            channel=interaction.channel,
            rule="Warning System",
            messageContent=f"Reason: {reason}\nTotal Warnings: {count}{action_msg}\nModerator: {interaction.user.mention}"
        )

    @app_commands.command(name="warnings", description="List warnings for a user")
    @app_commands.describe(member="Member to check")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_auth(interaction, "warnings", interaction.user.guild_permissions.moderate_members): return

        warnings = await getWarnings(interaction.guild_id, member.id)
        
        if not warnings:
            await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Warnings for {member.display_name}", color=0xFFAA00)
        for modId, reason, ts in warnings[:10]: # Show last 10
            mod = interaction.guild.get_member(int(modId))
            modName = mod.display_name if mod else "Unknown"
            date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            embed.add_field(name=f"{date} by {modName}", value=reason, inline=False)
        
        embed.set_footer(text=f"Total Warnings: {len(warnings)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_auth(interaction, "clearwarnings", interaction.user.guild_permissions.moderate_members): return

        await clearWarnings(interaction.guild_id, member.id)
        await interaction.response.send_message(f"✅ Cleared all warnings for {member.mention}.", ephemeral=True)
        
        await sendModLog(
            self.bot, interaction.guild_id,
            user=member,
            channel=interaction.channel,
            rule="Clear Warnings",
            messageContent=f"All warnings cleared by {interaction.user.mention}"
        )

    @app_commands.command(name="setthreshold", description="Set the warning auto-punish threshold")
    @app_commands.describe(amount="Number of warnings to trigger timeout (default: 3)")
    async def setthreshold(self, interaction: discord.Interaction, amount: int):
        if not await self.check_auth(interaction, "setthreshold", interaction.user.guild_permissions.administrator): return

        if amount < 1:
            await interaction.response.send_message("Threshold must be at least 1.", ephemeral=True)
            return

        await setConfig(interaction.guild_id, "warnThreshold", str(amount))
        await interaction.response.send_message(f"✅ Warning threshold set to **{amount}**. Users will be timed out on their {amount}th warning.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Warnings(bot))

import discord
from discord import app_commands
from discord.ext import commands
import datetime
from modlog import sendModLog
from database import hasCommandPerm

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, duration: str) -> datetime.timedelta:
        """Parses duration string like '10m', '1h' into timedelta."""
        duration = duration.replace(" ", "").lower()
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        
        if not duration or not duration[-1].isalpha():
            raise ValueError("No unit provided")

        amount_str = duration[:-1]
        unit = duration[-1]
        
        if not amount_str.isdigit():
             raise ValueError("Amount not a number")
        
        amount = int(amount_str)
        if unit not in multiplier:
            raise ValueError("Invalid time unit")
            
        return datetime.timedelta(seconds=amount * multiplier[unit])

    async def check_auth(self, interaction: discord.Interaction, command: str, native_perm: bool) -> bool:
        if native_perm:
            return True
        if await hasCommandPerm(interaction.guild_id, command, interaction.user.roles):
            return True
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not await self.check_auth(interaction, "kick", interaction.user.guild_permissions.kick_members): return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot kick this member due to role hierarchy.", ephemeral=True)
            return
            
        from database import getConfig
        adminRoleId = await getConfig(interaction.guild_id, "adminRoleId")
        if adminRoleId:
            adminRole = interaction.guild.get_role(int(adminRoleId))
            if adminRole and adminRole in member.roles:
                await interaction.response.send_message(f"You cannot kick a member with the **{adminRole.name}** role.", ephemeral=True)
                return

        try:
            await member.send(f"You were kicked from **{interaction.guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass 

        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ Kicked {member.mention}.", ephemeral=True)
            
            await sendModLog(
                self.bot, interaction.guild_id,
                user=member,
                channel=interaction.channel,
                rule="Manual Kick",
                messageContent=f"Reason: {reason}\nModerator: {interaction.user.mention}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick this user.", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban", delete_days="Days of messages to delete (0-7)")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        if not await self.check_auth(interaction, "ban", interaction.user.guild_permissions.ban_members): return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot ban this member due to role hierarchy.", ephemeral=True)
            return

        from database import getConfig
        adminRoleId = await getConfig(interaction.guild_id, "adminRoleId")
        if adminRoleId:
            adminRole = interaction.guild.get_role(int(adminRoleId))
            if adminRole and adminRole in member.roles:
                await interaction.response.send_message(f"You cannot ban a member with the **{adminRole.name}** role.", ephemeral=True)
                return

        try:
            await member.send(f"You were banned from **{interaction.guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass

        try:
            await member.ban(reason=reason, delete_message_days=delete_days)
            await interaction.response.send_message(f"✅ Banned {member.mention}.", ephemeral=True)
            
            await sendModLog(
                self.bot, interaction.guild_id,
                user=member,
                channel=interaction.channel,
                rule="Manual Ban",
                messageContent=f"Reason: {reason}\nModerator: {interaction.user.mention}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban this user.", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.describe(user_id="The ID of the user to unban")
    async def unban(self, interaction: discord.Interaction, user_id: str):
        if not await self.check_auth(interaction, "unban", interaction.user.guild_permissions.ban_members): return

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Unbanned {user.mention}.", ephemeral=True)

            await sendModLog(
                self.bot, interaction.guild_id,
                user=user,
                channel=interaction.channel,
                rule="Manual Unban",
                messageContent=f"Moderator: {interaction.user.mention}"
            )
        except discord.NotFound:
            await interaction.response.send_message("User not found or not banned.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid User ID.", ephemeral=True)

    @app_commands.command(name="mute", description="Mute (timeout) a member")
    @app_commands.describe(member="Member to mute", duration="Duration (e.g. 10m, 1h, 1d)", reason="Reason")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided"):
        if not await self.check_auth(interaction, "mute", interaction.user.guild_permissions.moderate_members): return

        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot mute this member (hierarchy).", ephemeral=True)
            return

        if member.top_role >= interaction.guild.me.top_role:
             await interaction.response.send_message("I cannot mute this member (their role is higher than mine).", ephemeral=True)
             return
        
        try:
            delta = self.parse_time(duration)
        except (ValueError, IndexError):
            await interaction.response.send_message("Invalid duration format. Use 10m, 1h, 1d, etc.", ephemeral=True)
            return

        try:
            await member.timeout(discord.utils.utcnow() + delta, reason=reason)
            await interaction.response.send_message(f"✅ Muted {member.mention} for {duration}.", ephemeral=True)
             
            await sendModLog(
                self.bot, interaction.guild_id,
                user=member,
                channel=interaction.channel,
                rule="Manual Mute",
                messageContent=f"Duration: {duration}\nReason: {reason}\nModerator: {interaction.user.mention}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("Missing permissions to mute this user.", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a member")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_auth(interaction, "unmute", interaction.user.guild_permissions.moderate_members): return

        try:
            await member.timeout(None, reason="Unmuted by moderator")
            await interaction.response.send_message(f"✅ Unmuted {member.mention}.", ephemeral=True)

            await sendModLog(
                self.bot, interaction.guild_id,
                user=member,
                channel=interaction.channel,
                rule="Manual Unmute",
                messageContent=f"Moderator: {interaction.user.mention}"
            )
        except discord.Forbidden:
             await interaction.response.send_message("Missing permissions.", ephemeral=True)

    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not await self.check_auth(interaction, "purge", interaction.user.guild_permissions.manage_messages): return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
            return
        
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)
        
        await sendModLog(
            self.bot, interaction.guild_id,
            user=interaction.user,
            channel=interaction.channel,
            rule="Manual Purge",
            messageContent=f"Deleted {len(deleted)} messages."
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))

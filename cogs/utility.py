import discord
from discord.ext import commands
from discord import app_commands
from database import hasCommandPerm

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_auth(self, interaction: discord.Interaction, command: str, native_perm: bool) -> bool:
        if native_perm:
            return True
        if await hasCommandPerm(interaction.guild_id, command, interaction.user.roles):
            return True
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="lock", description="Lock the current channel")
    async def lock(self, interaction: discord.Interaction):
        if not await self.check_auth(interaction, "lock", interaction.user.guild_permissions.manage_channels): return

        # Overwrite @everyone send_messages=False
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Channel locked.", ephemeral=True)
        await interaction.channel.send("🔒 This channel has been locked.")

    @app_commands.command(name="unlock", description="Unlock the current channel")
    async def unlock(self, interaction: discord.Interaction):
        if not await self.check_auth(interaction, "unlock", interaction.user.guild_permissions.manage_channels): return

        # Overwrite @everyone send_messages=True
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Channel unlocked.", ephemeral=True)
        await interaction.channel.send("🔓 This channel has been unlocked.")

    @app_commands.command(name="slowmode", description="Set slowmode for the channel")
    @app_commands.describe(seconds="Slowmode duration in seconds (0 to disable)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if not await self.check_auth(interaction, "slowmode", interaction.user.guild_permissions.manage_channels): return

        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message("Duration must be between 0 (off) and 21600 (6 hours).", ephemeral=True)
            return
        
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await interaction.response.send_message("🐢 Slowmode disabled.", ephemeral=True)
        else:
            await interaction.response.send_message(f"🐢 Slowmode set to {seconds} seconds.", ephemeral=True)

    @app_commands.command(name="userinfo", description="Get info about a user")
    @app_commands.describe(member="Member to inspect")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"User Info: {member.name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        
        roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles), inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))

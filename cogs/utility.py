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

    @app_commands.command(name="whois", description="Get detailed info about a user (warnings, roles, etc.)")
    @app_commands.describe(member="Member to inspect")
    async def whois(self, interaction: discord.Interaction, member: discord.Member):
        # Fetch detailed info
        roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
        role_str = " ".join(roles) if roles else "None"
        
        # Get Warnings Count
        from database import getWarnings
        warnings = await getWarnings(interaction.guild_id, member.id)
        warn_count = len(warnings)
        
        # Create Embed
        embed = discord.Embed(title=f"User Info: {member.display_name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Identity", value=f"**Mention:** {member.mention}\n**ID:** `{member.id}`", inline=False)
        
        created = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
        joined = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
        embed.add_field(name="Dates", value=f"**Created:** {created}\n**Joined:** {joined}", inline=False)
        
        embed.add_field(name="Moderation", value=f"**Warnings:** {warn_count}", inline=True)
        
        if warnings:
             last_warn_reason = warnings[-1][1] # (modId, reason, timestamp)
             embed.add_field(name="Last Warning", value=last_warn_reason, inline=True)
        
        if roles:
            embed.add_field(name=f"Roles [{len(roles)}]", value=role_str, inline=False)
            
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        embed.timestamp = discord.utils.utcnow()
            
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(Utility(bot))

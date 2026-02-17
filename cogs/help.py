import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show bot commands and help")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Bot Help Menu", description="Here are the available commands:", color=0x3498db)
        
        embed.add_field(name="🛡️ Moderation", value="`/kick`, `/ban`, `/unban`, `/timeout`, `/warn`, `/warnings`, `/purge`", inline=False)
        embed.add_field(name="⚙️ Configuration", value="`/config view`, `/spam`, `/attachment`, `/mention`, `/linkfilter`, `/wordfilter`, `/msglimit`", inline=False)
        embed.add_field(name="🔧 Utility", value="`/lock`, `/unlock`, `/slowmode`, `/userinfo`, `/modlog`, `/prefix`", inline=False)
        embed.add_field(name="👥 Roles & Permissions", value="`/setroles admin @Role` - Set Admin Role\n`/setroles mod @Role` - Set Mod Role\n`/setperm <cmd> <role> allow/remove` - Override command perms\n`/listperms <cmd>` - See permissions", inline=False)
        
        embed.set_footer(text="Use /command for more details on specific parameters.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))

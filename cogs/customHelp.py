import discord
from discord.ext import commands
from discord import app_commands
from config import embedColor

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="🤖 Bot Commands", color=embedColor)
        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if filtered:
                cog_name = cog.qualified_name if cog else "No Category"
                command_signatures = [f"`{c.name}`" for c in filtered]
                if command_signatures:
                    embed.add_field(name=cog_name, value=", ".join(command_signatures), inline=False)
        
        embed.set_footer(text=f"Type {self.context.prefix}help <command> for more info.")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f"Command: {command.qualified_name}", color=embedColor)
        embed.description = command.help or "No description provided."
        
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            
        embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"Group: {group.qualified_name}", color=embedColor)
        embed.description = group.help or "No description provided."
        
        filtered = await self.filter_commands(group.commands, sort=True)
        if filtered:
            command_list = [f"`{c.name}`: {c.short_doc or 'No description'}" for c in filtered]
            embed.add_field(name="Subcommands", value="\n".join(command_list), inline=False)
            
        embed.add_field(name="Usage", value=f"`{self.get_command_signature(group)}`", inline=False)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"Category: {cog.qualified_name}", color=embedColor)
        embed.description = cog.description or "No description."
        
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if filtered:
            command_list = [f"`{c.name}`: {c.short_doc or 'No description'}" for c in filtered]
            embed.add_field(name="Commands", value=", ".join([f"`{c.name}`" for c in filtered]), inline=False)
            
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(title="Error", description=error, color=embedColor)
        await self.get_destination().send(embed=embed)

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @app_commands.command(name="help", description="Show all bot slash commands")
    async def slash_help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Bot Slash Commands", description="Here are the available slash commands:", color=embedColor)
        
        commands_dict = {}
        for cmd in self.bot.tree.walk_commands():
            if isinstance(cmd, app_commands.Command):
                cog_name = cmd.binding.__class__.__name__ if cmd.binding else "General"
                if cog_name not in commands_dict:
                    commands_dict[cog_name] = []
                commands_dict[cog_name].append(f"`/{cmd.qualified_name}`")
                
        for cog_name, cmd_list in commands_dict.items():
            if cmd_list:
                embed.add_field(name=cog_name, value=", ".join(cmd_list), inline=False)
                
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))

import discord
from discord.ext import commands
from discord import app_commands
from config import embedColor

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="🤖 Bot Commands", color=embedColor)
        
        dev_cogs = {"Projects", "Sprints", "Tasks", "Bugs", "Team", "Checklists", "Workload", "Dashboards", "Ingestion", "Automation"}
        mod_cogs = {"Moderation", "Warnings"}
        
        mod_cmds = {"spam", "attachment", "mention", "msglimit", "linkfilter", "wordfilter", "exempt", "kick", "ban", "unban", "mute", "unmute", "purge", "warn", "warnings", "clearwarnings", "setthreshold"}
        config_cmds = {"config", "modlog", "prefix", "setroles", "setperm", "listperms"}
        util_cmds = {"ping", "lock", "unlock", "slowmode", "whois", "exemptchannel", "unexemptchannel", "listexemptions", "help"}
        
        grouped_commands = {
            "1️⃣ Moderation & Automod": [],
            "2️⃣ Configuration & Setup": [],
            "3️⃣ Utility & General": [],
            "Dev": []
        }
        
        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if filtered:
                cog_name = cog.qualified_name if cog else "No Category"
                
                for c in filtered:
                    cmd_base = c.qualified_name.split()[0]
                    cat_name = "3️⃣ Utility & General"
                    
                    if cog_name in dev_cogs:
                        cat_name = "Dev"
                    elif cog_name in mod_cogs or cmd_base in mod_cmds:
                        cat_name = "1️⃣ Moderation & Automod"
                    elif cmd_base in config_cmds:
                        cat_name = "2️⃣ Configuration & Setup"
                    elif cmd_base in util_cmds or cmd_base == "help":
                        cat_name = "3️⃣ Utility & General"
                    
                    grouped_commands[cat_name].append(f"`{c.name}`")
                
        for cat_name, cmd_list in grouped_commands.items():
            if cmd_list:
                embed.add_field(name=cat_name, value=", ".join(cmd_list), inline=False)
        
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
    @app_commands.describe(command_name="Command to get help for (e.g. 'exempt list' or 'warn')")
    async def slash_help(self, interaction: discord.Interaction, command_name: str = None):
        if not command_name:
            embed = discord.Embed(title="🤖 Bot Slash Commands", description="Here are the available slash commands. Use `/help <command>` for details.", color=embedColor)
            
            grouped_commands = {
                "1️⃣ Moderation & Automod": [],
                "2️⃣ Configuration & Setup": [],
                "3️⃣ Utility & General": [],
                "Dev": []
            }
            
            dev_cogs = {"Projects", "Sprints", "Tasks", "Bugs", "Team", "Checklists", "Workload", "Dashboards", "Ingestion", "Automation"}
            mod_cogs = {"Moderation", "Warnings"}
            
            mod_cmds = {"spam", "attachment", "mention", "msglimit", "linkfilter", "wordfilter", "exempt", "kick", "ban", "unban", "mute", "unmute", "purge", "warn", "warnings", "clearwarnings", "setthreshold"}
            config_cmds = {"config", "modlog", "prefix", "setroles", "setperm", "listperms"}
            util_cmds = {"ping", "lock", "unlock", "slowmode", "whois", "exemptchannel", "unexemptchannel", "listexemptions", "help"}
            
            for cmd in self.bot.tree.walk_commands():
                if isinstance(cmd, app_commands.Command):
                    cog_name = cmd.binding.__class__.__name__ if cmd.binding else "General"
                    cmd_base = cmd.qualified_name.split()[0]
                    
                    cat_name = "3️⃣ Utility & General"
                    if cog_name in dev_cogs:
                        cat_name = "Dev"
                    elif cog_name in mod_cogs or cmd_base in mod_cmds:
                        cat_name = "1️⃣ Moderation & Automod"
                    elif cmd_base in config_cmds:
                        cat_name = "2️⃣ Configuration & Setup"
                    elif cmd_base in util_cmds or cmd_base == "help":
                        cat_name = "3️⃣ Utility & General"
                        
                    grouped_commands[cat_name].append(f"`/{cmd.qualified_name}`")
                    
            for cat_name, cmd_list in grouped_commands.items():
                if cmd_list:
                    embed.add_field(name=cat_name, value=", ".join(cmd_list), inline=False)
                    
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        target = None
        for cmd in self.bot.tree.walk_commands():
            if cmd.qualified_name.lower() == command_name.lower().strip("/ "):
                target = cmd
                break
                
        if not target:
            await interaction.response.send_message(f"❌ Command `{command_name}` not found.", ephemeral=False)
            return

        embed = discord.Embed(title=f"Command Help: /{target.qualified_name}", color=embedColor)
        embed.description = target.description or "No description provided."
        
        if isinstance(target, app_commands.Group):
            subcommands = [f"`/{c.qualified_name}` - {c.description}" for c in target.walk_commands() if isinstance(c, app_commands.Command)]
            if subcommands:
                 embed.add_field(name="Subcommands", value="\n".join(subcommands[:15]) + ("\n..." if len(subcommands)>15 else ""), inline=False)
        elif isinstance(target, app_commands.Command):
            if target.parameters:
                params_list = []
                for p in target.parameters:
                    req = "Required" if p.required else "Optional"
                    params_list.append(f"• `{p.name}` ({req}): {p.description}")
                embed.add_field(name="Parameters", value="\n".join(params_list), inline=False)
            else:
                embed.add_field(name="Parameters", value="None", inline=False)
                
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))

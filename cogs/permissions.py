import discord
from discord import app_commands
from discord.ext import commands
from database import setConfig, getConfig, addCommandPerm, removeCommandPerm, getCommandPerms

class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setroles", description="Set Admin or Mod roles for the bot")
    @app_commands.choices(level=[
        app_commands.Choice(name="Admin", value="admin"),
        app_commands.Choice(name="Mod", value="mod")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def setroles(self, interaction: discord.Interaction, level: app_commands.Choice[str], role: discord.Role):
        key = "adminRoleId" if level.value == "admin" else "modRoleId"
        await setConfig(interaction.guild_id, key, str(role.id))
        await interaction.response.send_message(f"✅ Set **{level.name}** role to {role.mention}.", ephemeral=True)

    @app_commands.command(name="setperm", description="Allow a role to use a specific command")
    @app_commands.describe(command="Command name (e.g. kick, warn, lock)", role="Role to allow", action="Allow or Remove permission")
    @app_commands.choices(action=[
        app_commands.Choice(name="Allow", value="allow"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def setperm(self, interaction: discord.Interaction, command: str, role: discord.Role, action: app_commands.Choice[str]):
        command = command.lower()
        if action.value == "allow":
            await addCommandPerm(interaction.guild_id, command, role.id)
            await interaction.response.send_message(f"✅ Role {role.mention} can now use `/{command}`.", ephemeral=True)
        else:
            await removeCommandPerm(interaction.guild_id, command, role.id)
            await interaction.response.send_message(f"🗑️ Removed permission for {role.mention} to use `/{command}`.", ephemeral=True)

    @app_commands.command(name="listperms", description="List custom permissions for a command")
    async def listperms(self, interaction: discord.Interaction, command: str):
        roleIds = await getCommandPerms(interaction.guild_id, command.lower())
        if not roleIds:
            await interaction.response.send_message(f"No custom permissions set for `/{command}`.", ephemeral=True)
        else:
            roles = [f"<@&{rid}>" for rid in roleIds]
            await interaction.response.send_message(f"Roles allowed to use `/{command}`:\n" + ", ".join(roles), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Permissions(bot))

import json
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    setConfig, getConfig, getAllConfig,
    addExemptRole, removeExemptRole, getExemptRoles,
    addBannedWord, removeBannedWord, getBannedWords,
    addWhitelistDomain, removeWhitelistDomain, getWhitelistDomains
)
from config import embedColor

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You need Administrator permission.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    @app_commands.command(name="config", description="View current configuration")
    @app_commands.checks.has_permissions(administrator=True)
    async def view_config(self, interaction: discord.Interaction):
        guildId = interaction.guild_id
        config = await getAllConfig(guildId)
        
        embed = discord.Embed(title="Current Configuration", color=embedColor)
        
        # General Settings
        embed.add_field(name="General", value=f"Prefix: `{config.get('prefix', '.')}`\nModLog: <#{config.get('modLogChannel', 'None')}>", inline=False)
        
        # Filter Statuses
        spam = "✅" if config.get("spamEnabled") == "1" else "❌"
        attach = "✅" if config.get("attachmentEnabled") == "1" else "❌"
        mention = "✅" if config.get("mentionEnabled") == "1" else "❌"
        msg = "✅" if config.get("messageLimitEnabled") == "1" else "❌"
        link = "✅" if config.get("linkFilterEnabled") == "1" else "❌"
        word = "✅" if config.get("wordFilterEnabled") == "1" else "❌"
        
        embed.add_field(name="Filter Status", value=f"Spam: {spam}\nAttachment: {attach}\nMention: {mention}\nMsg Limit: {msg}\nLink: {link}\nWord: {word}", inline=False)
        
        # Detailed Config
        embed.add_field(name="Spam", value=f"Max: {config.get('spamMaxMessages')}\nWindow: {config.get('spamTimeWindow')}s", inline=True)
        embed.add_field(name="Attachment", value=f"Max: {config.get('maxAttachments')}\nBlocked: {len(json.loads(config.get('blockedFileTypes', '[]')))} types", inline=True)
        embed.add_field(name="Mention", value=f"Max: {config.get('maxMentions')}\nBlock @everyone: {config.get('blockEveryone')}\nBlock @here: {config.get('blockHere')}", inline=True)
        embed.add_field(name="Msg Limit", value=f"Lines: {config.get('maxLines')}\nWords: {config.get('maxWords')}\nChars: {config.get('maxCharacters')}", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="modlog", description="Set mod-log channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_modlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await setConfig(interaction.guild_id, "modLogChannel", str(channel.id))
        await interaction.response.send_message(f"Mod-log channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="prefix", description="Set command prefix")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, prefix: str):
        await setConfig(interaction.guild_id, "prefix", prefix)
        await interaction.response.send_message(f"Prefix set to `{prefix}`", ephemeral=True)

    # Spam Group
    spam_group = app_commands.Group(name="spam", description="Configure spam filter")

    @spam_group.command(name="enable", description="Enable spam filter")
    async def spam_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "spamEnabled", "1")
        await interaction.response.send_message("Spam filter enabled.", ephemeral=True)

    @spam_group.command(name="disable", description="Disable spam filter")
    async def spam_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "spamEnabled", "0")
        await interaction.response.send_message("Spam filter disabled.", ephemeral=True)

    @spam_group.command(name="set", description="Set spam thresholds")
    async def spam_set(self, interaction: discord.Interaction, max_messages: int, time_window: int):
        await setConfig(interaction.guild_id, "spamMaxMessages", str(max_messages))
        await setConfig(interaction.guild_id, "spamTimeWindow", str(time_window))
        await interaction.response.send_message(f"Spam thresholds set: {max_messages} msgs per {time_window}s", ephemeral=True)

    # Attachment Group
    attach_group = app_commands.Group(name="attachment", description="Configure attachment filter")

    @attach_group.command(name="enable", description="Enable attachment filter")
    async def attach_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "attachmentEnabled", "1")
        await interaction.response.send_message("Attachment filter enabled.", ephemeral=True)

    @attach_group.command(name="disable", description="Disable attachment filter")
    async def attach_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "attachmentEnabled", "0")
        await interaction.response.send_message("Attachment filter disabled.", ephemeral=True)

    @attach_group.command(name="limit", description="Set attachment count limit")
    async def attach_limit(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxAttachments", str(count))
        await interaction.response.send_message(f"Max attachments set to {count}", ephemeral=True)

    @attach_group.command(name="block", description="Block a file extension")
    async def attach_block(self, interaction: discord.Interaction, filetype: str):
        ft = filetype.lower().strip(".")
        current = json.loads(await getConfig(interaction.guild_id, "blockedFileTypes") or "[]")
        if ft not in current:
            current.append(ft)
            await setConfig(interaction.guild_id, "blockedFileTypes", json.dumps(current))
            await interaction.response.send_message(f"Blocked file type: .{ft}", ephemeral=True)
        else:
            await interaction.response.send_message(f".{ft} is already blocked.", ephemeral=True)

    @attach_group.command(name="unblock", description="Unblock a file extension")
    async def attach_unblock(self, interaction: discord.Interaction, filetype: str):
        ft = filetype.lower().strip(".")
        current = json.loads(await getConfig(interaction.guild_id, "blockedFileTypes") or "[]")
        if ft in current:
            current.remove(ft)
            await setConfig(interaction.guild_id, "blockedFileTypes", json.dumps(current))
            await interaction.response.send_message(f"Unblocked file type: .{ft}", ephemeral=True)
        else:
            await interaction.response.send_message(f".{ft} was not blocked.", ephemeral=True)

    # Mention Group
    mention_group = app_commands.Group(name="mention", description="Configure mention filter")

    @mention_group.command(name="enable", description="Enable mention filter")
    async def mention_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "mentionEnabled", "1")
        await interaction.response.send_message("Mention filter enabled.", ephemeral=True)

    @mention_group.command(name="disable", description="Disable mention filter")
    async def mention_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "mentionEnabled", "0")
        await interaction.response.send_message("Mention filter disabled.", ephemeral=True)

    @mention_group.command(name="limit", description="Set mention count limit")
    async def mention_limit(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxMentions", str(count))
        await interaction.response.send_message(f"Max mentions set to {count}", ephemeral=True)

    @mention_group.command(name="blockeveryone", description="Block @everyone mentions")
    async def mention_blockeveryone(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "blockEveryone", "1" if enabled else "0")
        await interaction.response.send_message(f"Block @everyone: {enabled}", ephemeral=True)

    @mention_group.command(name="blockhere", description="Block @here mentions")
    async def mention_blockhere(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "blockHere", "1" if enabled else "0")
        await interaction.response.send_message(f"Block @here: {enabled}", ephemeral=True)

    # Message Limit Group
    msglimit_group = app_commands.Group(name="msglimit", description="Configure message limits")

    @msglimit_group.command(name="enable", description="Enable message limits")
    async def msglimit_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "messageLimitEnabled", "1")
        await interaction.response.send_message("Message limits enabled.", ephemeral=True)

    @msglimit_group.command(name="disable", description="Disable message limits")
    async def msglimit_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "messageLimitEnabled", "0")
        await interaction.response.send_message("Message limits disabled.", ephemeral=True)

    @msglimit_group.command(name="lines", description="Set max lines")
    async def msglimit_lines(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxLines", str(count))
        await interaction.response.send_message(f"Max lines set to {count}", ephemeral=True)

    @msglimit_group.command(name="words", description="Set max words")
    async def msglimit_words(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxWords", str(count))
        await interaction.response.send_message(f"Max words set to {count}", ephemeral=True)

    @msglimit_group.command(name="characters", description="Set max characters")
    async def msglimit_characters(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxCharacters", str(count))
        await interaction.response.send_message(f"Max characters set to {count}", ephemeral=True)

    # Link Filter Group
    link_group = app_commands.Group(name="linkfilter", description="Configure link filter")

    @link_group.command(name="enable", description="Enable link filter")
    async def link_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "linkFilterEnabled", "1")
        await interaction.response.send_message("Link filter enabled.", ephemeral=True)

    @link_group.command(name="disable", description="Disable link filter")
    async def link_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "linkFilterEnabled", "0")
        await interaction.response.send_message("Link filter disabled.", ephemeral=True)

    @link_group.command(name="whitelist_add", description="Add domain to whitelist")
    async def link_whitelist_add(self, interaction: discord.Interaction, domain: str):
        await addWhitelistDomain(interaction.guild_id, domain)
        await interaction.response.send_message(f"Added {domain} to whitelist.", ephemeral=True)

    @link_group.command(name="whitelist_remove", description="Remove domain from whitelist")
    async def link_whitelist_remove(self, interaction: discord.Interaction, domain: str):
        await removeWhitelistDomain(interaction.guild_id, domain)
        await interaction.response.send_message(f"Removed {domain} from whitelist.", ephemeral=True)

    @link_group.command(name="whitelist_list", description="List whitelisted domains")
    async def link_whitelist_list(self, interaction: discord.Interaction):
        domains = await getWhitelistDomains(interaction.guild_id)
        if not domains:
            await interaction.response.send_message("No whitelisted domains.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Whitelisted domains:\n" + "\n".join(domains), ephemeral=True)

    @link_group.command(name="regex_add", description="Add custom regex pattern")
    async def link_regex_add(self, interaction: discord.Interaction, pattern: str):
        current = json.loads(await getConfig(interaction.guild_id, "linkRegexPatterns") or "[]")
        if pattern not in current:
            current.append(pattern)
            await setConfig(interaction.guild_id, "linkRegexPatterns", json.dumps(current))
            await interaction.response.send_message(f"Added regex pattern: `{pattern}`", ephemeral=True)
        else:
            await interaction.response.send_message("Pattern already exists.", ephemeral=True)

    @link_group.command(name="regex_remove", description="Remove custom regex pattern")
    async def link_regex_remove(self, interaction: discord.Interaction, pattern: str):
        current = json.loads(await getConfig(interaction.guild_id, "linkRegexPatterns") or "[]")
        if pattern in current:
            current.remove(pattern)
            await setConfig(interaction.guild_id, "linkRegexPatterns", json.dumps(current))
            await interaction.response.send_message(f"Removed regex pattern: `{pattern}`", ephemeral=True)
        else:
            await interaction.response.send_message("Pattern not found.", ephemeral=True)

    # Word Filter Group
    word_group = app_commands.Group(name="wordfilter", description="Configure word filter")

    @word_group.command(name="enable", description="Enable word filter")
    async def word_enable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "wordFilterEnabled", "1")
        await interaction.response.send_message("Word filter enabled.", ephemeral=True)

    @word_group.command(name="disable", description="Disable word filter")
    async def word_disable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "wordFilterEnabled", "0")
        await interaction.response.send_message("Word filter disabled.", ephemeral=True)

    @word_group.command(name="add", description="Add banned word")
    async def word_add(self, interaction: discord.Interaction, word: str):
        await addBannedWord(interaction.guild_id, word)
        await interaction.response.send_message(f"Added banned word: `{word}`", ephemeral=True)

    @word_group.command(name="remove", description="Remove banned word")
    async def word_remove(self, interaction: discord.Interaction, word: str):
        await removeBannedWord(interaction.guild_id, word)
        await interaction.response.send_message(f"Removed banned word: `{word}`", ephemeral=True)

    @word_group.command(name="list", description="List banned words")
    async def word_list(self, interaction: discord.Interaction):
        words = await getBannedWords(interaction.guild_id)
        if not words:
            await interaction.response.send_message("No banned words.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Banned words:\n" + ", ".join(words), ephemeral=True)

    @word_group.command(name="partial", description="Toggle partial matching")
    async def word_partial(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "wordFilterPartialMatch", "1" if enabled else "0")
        await interaction.response.send_message(f"Partial matching: {enabled}", ephemeral=True)

    @word_group.command(name="regex", description="Toggle regex matching")
    async def word_regex(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "wordFilterRegex", "1" if enabled else "0")
        await interaction.response.send_message(f"Regex matching: {enabled}", ephemeral=True)

    # Exempt Group
    exempt_group = app_commands.Group(name="exempt", description="Manage role exemptions")

    @exempt_group.command(name="add", description="Exempt role from filter")
    @app_commands.choices(rule=[
        app_commands.Choice(name="Spam", value="spam"),
        app_commands.Choice(name="Attachment", value="attachment"),
        app_commands.Choice(name="Mention", value="mention"),
        app_commands.Choice(name="Message Limit", value="messageLimit"),
        app_commands.Choice(name="Link", value="link"),
        app_commands.Choice(name="Word", value="word"),
    ])
    async def exempt_add(self, interaction: discord.Interaction, rule: app_commands.Choice[str], role: discord.Role):
        await addExemptRole(interaction.guild_id, rule.value, str(role.id))
        await interaction.response.send_message(f"Exempted {role.mention} from {rule.name} filter.", ephemeral=True)

    @exempt_group.command(name="remove", description="Remove role exemption")
    @app_commands.choices(rule=[
        app_commands.Choice(name="Spam", value="spam"),
        app_commands.Choice(name="Attachment", value="attachment"),
        app_commands.Choice(name="Mention", value="mention"),
        app_commands.Choice(name="Message Limit", value="messageLimit"),
        app_commands.Choice(name="Link", value="link"),
        app_commands.Choice(name="Word", value="word"),
    ])
    async def exempt_remove(self, interaction: discord.Interaction, rule: app_commands.Choice[str], role: discord.Role):
        await removeExemptRole(interaction.guild_id, rule.value, str(role.id))
        await interaction.response.send_message(f"Removed exemption for {role.mention} from {rule.name} filter.", ephemeral=True)

    @exempt_group.command(name="list", description="List exempt roles")
    @app_commands.choices(rule=[
        app_commands.Choice(name="Spam", value="spam"),
        app_commands.Choice(name="Attachment", value="attachment"),
        app_commands.Choice(name="Mention", value="mention"),
        app_commands.Choice(name="Message Limit", value="messageLimit"),
        app_commands.Choice(name="Link", value="link"),
        app_commands.Choice(name="Word", value="word"),
    ])
    async def exempt_list(self, interaction: discord.Interaction, rule: app_commands.Choice[str]):
        roleIds = await getExemptRoles(interaction.guild_id, rule.value)
        if not roleIds:
            await interaction.response.send_message(f"No exempt roles for {rule.name} filter.", ephemeral=True)
        else:
            roles = [f"<@&{rid}>" for rid in roleIds]
            await interaction.response.send_message(f"Exempt roles for {rule.name} filter:\n" + ", ".join(roles), ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))

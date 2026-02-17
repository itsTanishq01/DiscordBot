import json
import discord
from discord import app_commands
from discord.ext import commands
from config import embedColor
from database import (
    setConfig, getConfig, getAllConfig,
    addExemptRole, removeExemptRole, getExemptRoles,
    addBannedWord, removeBannedWord, getBannedWords,
    addWhitelistDomain, removeWhitelistDomain, getWhitelistDomains
)

ruleChoices = [
    app_commands.Choice(name="Spam", value="spam"),
    app_commands.Choice(name="Attachment", value="attachment"),
    app_commands.Choice(name="Mention", value="mention"),
    app_commands.Choice(name="Message Limit", value="messageLimit"),
    app_commands.Choice(name="Link", value="link"),
    app_commands.Choice(name="Word", value="word"),
]

def successEmbed(description):
    return discord.Embed(description=f"✅ {description}", color=embedColor)

def infoEmbed(title, description=""):
    return discord.Embed(title=title, description=description, color=embedColor)

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    configGroup = app_commands.Group(name="config", description="View bot configuration")
    spamGroup = app_commands.Group(name="spam", description="Spam filter settings")
    attachmentGroup = app_commands.Group(name="attachment", description="Attachment filter settings")
    mentionGroup = app_commands.Group(name="mention", description="Mention filter settings")
    msglimitGroup = app_commands.Group(name="msglimit", description="Message limit settings")
    linkfilterGroup = app_commands.Group(name="linkfilter", description="Link filter settings")
    wordfilterGroup = app_commands.Group(name="wordfilter", description="Word filter settings")
    exemptGroup = app_commands.Group(name="exempt", description="Role exemption settings")

    @configGroup.command(name="view", description="View all current automod settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def configView(self, interaction: discord.Interaction):
        cfg = await getAllConfig(interaction.guild_id)
        embed = discord.Embed(title="⚙️ AutoMod Configuration", color=embedColor)
        embed.add_field(name="General", value=(
            f"**Prefix:** `{cfg.get('prefix', '.')}`\n"
            f"**Mod-Log:** {'<#' + cfg['modLogChannel'] + '>' if cfg.get('modLogChannel') else 'Not set'}"
        ), inline=False)
        embed.add_field(name="Spam Filter", value=(
            f"**Enabled:** {'✅' if cfg.get('spamEnabled') == '1' else '❌'}\n"
            f"**Max Messages:** {cfg.get('spamMaxMessages', '5')}\n"
            f"**Time Window:** {cfg.get('spamTimeWindow', '10')}s"
        ), inline=True)
        embed.add_field(name="Attachment Filter", value=(
            f"**Enabled:** {'✅' if cfg.get('attachmentEnabled') == '1' else '❌'}\n"
            f"**Max Attachments:** {cfg.get('maxAttachments', '5')}\n"
            f"**Blocked Types:** {cfg.get('blockedFileTypes', '[]')}"
        ), inline=True)
        embed.add_field(name="Mention Filter", value=(
            f"**Enabled:** {'✅' if cfg.get('mentionEnabled') == '1' else '❌'}\n"
            f"**Max Mentions:** {cfg.get('maxMentions', '10')}\n"
            f"**Block @everyone:** {'✅' if cfg.get('blockEveryone') == '1' else '❌'}\n"
            f"**Block @here:** {'✅' if cfg.get('blockHere') == '1' else '❌'}"
        ), inline=True)
        embed.add_field(name="Message Limits", value=(
            f"**Enabled:** {'✅' if cfg.get('messageLimitEnabled') == '1' else '❌'}\n"
            f"**Max Lines:** {cfg.get('maxLines', '30')}\n"
            f"**Max Words:** {cfg.get('maxWords', '500')}\n"
            f"**Max Chars:** {cfg.get('maxCharacters', '2000')}"
        ), inline=True)
        embed.add_field(name="Link Filter", value=(
            f"**Enabled:** {'✅' if cfg.get('linkFilterEnabled') == '1' else '❌'}"
        ), inline=True)
        embed.add_field(name="Word Filter", value=(
            f"**Enabled:** {'✅' if cfg.get('wordFilterEnabled') == '1' else '❌'}\n"
            f"**Partial Match:** {'✅' if cfg.get('wordFilterPartialMatch') == '1' else '❌'}\n"
            f"**Regex:** {'✅' if cfg.get('wordFilterRegex') == '1' else '❌'}"
        ), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="modlog", description="Set the mod-log channel")
    @app_commands.describe(channel="The channel to send mod-log messages to")
    @app_commands.checks.has_permissions(administrator=True)
    async def modlogSet(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await setConfig(interaction.guild_id, "modLogChannel", str(channel.id))
        await interaction.response.send_message(embed=successEmbed(f"Mod-log channel set to {channel.mention}"), ephemeral=True)

    @app_commands.command(name="prefix", description="Set the command prefix")
    @app_commands.describe(prefix="The new prefix to use")
    @app_commands.checks.has_permissions(administrator=True)
    async def prefixSet(self, interaction: discord.Interaction, prefix: str):
        await setConfig(interaction.guild_id, "prefix", prefix)
        await interaction.response.send_message(embed=successEmbed(f"Prefix set to `{prefix}`"), ephemeral=True)

    @spamGroup.command(name="enable", description="Enable the spam filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def spamEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "spamEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Spam filter enabled"), ephemeral=True)

    @spamGroup.command(name="disable", description="Disable the spam filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def spamDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "spamEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Spam filter disabled"), ephemeral=True)

    @spamGroup.command(name="set", description="Set spam filter thresholds")
    @app_commands.describe(max_messages="Max messages allowed", time_window="Time window in seconds")
    @app_commands.checks.has_permissions(administrator=True)
    async def spamSet(self, interaction: discord.Interaction, max_messages: int, time_window: int):
        await setConfig(interaction.guild_id, "spamMaxMessages", str(max_messages))
        await setConfig(interaction.guild_id, "spamTimeWindow", str(time_window))
        await interaction.response.send_message(embed=successEmbed(f"Spam limit: {max_messages} messages per {time_window}s"), ephemeral=True)

    @attachmentGroup.command(name="enable", description="Enable the attachment filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def attachmentEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "attachmentEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Attachment filter enabled"), ephemeral=True)

    @attachmentGroup.command(name="disable", description="Disable the attachment filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def attachmentDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "attachmentEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Attachment filter disabled"), ephemeral=True)

    @attachmentGroup.command(name="limit", description="Set max attachments per message")
    @app_commands.describe(count="Maximum number of attachments")
    @app_commands.checks.has_permissions(administrator=True)
    async def attachmentLimit(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxAttachments", str(count))
        await interaction.response.send_message(embed=successEmbed(f"Max attachments set to {count}"), ephemeral=True)

    @attachmentGroup.command(name="block", description="Block a file type")
    @app_commands.describe(filetype="File extension to block (e.g. exe)")
    @app_commands.checks.has_permissions(administrator=True)
    async def attachmentBlock(self, interaction: discord.Interaction, filetype: str):
        raw = await getConfig(interaction.guild_id, "blockedFileTypes") or "[]"
        try:
            types = json.loads(raw)
        except json.JSONDecodeError:
            types = []
        ft = filetype.lower().lstrip(".")
        if ft not in types:
            types.append(ft)
        await setConfig(interaction.guild_id, "blockedFileTypes", json.dumps(types))
        await interaction.response.send_message(embed=successEmbed(f"Blocked file type: .{ft}"), ephemeral=True)

    @attachmentGroup.command(name="unblock", description="Unblock a file type")
    @app_commands.describe(filetype="File extension to unblock")
    @app_commands.checks.has_permissions(administrator=True)
    async def attachmentUnblock(self, interaction: discord.Interaction, filetype: str):
        raw = await getConfig(interaction.guild_id, "blockedFileTypes") or "[]"
        try:
            types = json.loads(raw)
        except json.JSONDecodeError:
            types = []
        ft = filetype.lower().lstrip(".")
        if ft in types:
            types.remove(ft)
        await setConfig(interaction.guild_id, "blockedFileTypes", json.dumps(types))
        await interaction.response.send_message(embed=successEmbed(f"Unblocked file type: .{ft}"), ephemeral=True)

    @mentionGroup.command(name="enable", description="Enable the mention filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "mentionEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Mention filter enabled"), ephemeral=True)

    @mentionGroup.command(name="disable", description="Disable the mention filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "mentionEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Mention filter disabled"), ephemeral=True)

    @mentionGroup.command(name="limit", description="Set max mentions per message")
    @app_commands.describe(count="Maximum number of mentions")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionLimit(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxMentions", str(count))
        await interaction.response.send_message(embed=successEmbed(f"Max mentions set to {count}"), ephemeral=True)

    @mentionGroup.command(name="blockeveryone", description="Toggle @everyone blocking")
    @app_commands.describe(enabled="Enable or disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionBlockEveryone(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "blockEveryone", "1" if enabled else "0")
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=successEmbed(f"@everyone blocking {state}"), ephemeral=True)

    @mentionGroup.command(name="blockhere", description="Toggle @here blocking")
    @app_commands.describe(enabled="Enable or disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionBlockHere(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "blockHere", "1" if enabled else "0")
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=successEmbed(f"@here blocking {state}"), ephemeral=True)

    @msglimitGroup.command(name="enable", description="Enable message limit filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def msglimitEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "messageLimitEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Message limit filter enabled"), ephemeral=True)

    @msglimitGroup.command(name="disable", description="Disable message limit filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def msglimitDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "messageLimitEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Message limit filter disabled"), ephemeral=True)

    @msglimitGroup.command(name="lines", description="Set max lines per message")
    @app_commands.describe(count="Maximum number of lines")
    @app_commands.checks.has_permissions(administrator=True)
    async def msglimitLines(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxLines", str(count))
        await interaction.response.send_message(embed=successEmbed(f"Max lines set to {count}"), ephemeral=True)

    @msglimitGroup.command(name="words", description="Set max words per message")
    @app_commands.describe(count="Maximum number of words")
    @app_commands.checks.has_permissions(administrator=True)
    async def msglimitWords(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxWords", str(count))
        await interaction.response.send_message(embed=successEmbed(f"Max words set to {count}"), ephemeral=True)

    @msglimitGroup.command(name="characters", description="Set max characters per message")
    @app_commands.describe(count="Maximum number of characters")
    @app_commands.checks.has_permissions(administrator=True)
    async def msglimitCharacters(self, interaction: discord.Interaction, count: int):
        await setConfig(interaction.guild_id, "maxCharacters", str(count))
        await interaction.response.send_message(embed=successEmbed(f"Max characters set to {count}"), ephemeral=True)

    @linkfilterGroup.command(name="enable", description="Enable the link filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "linkFilterEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Link filter enabled"), ephemeral=True)

    @linkfilterGroup.command(name="disable", description="Disable the link filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "linkFilterEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Link filter disabled"), ephemeral=True)

    @linkfilterGroup.command(name="whitelist_add", description="Add a domain to the whitelist")
    @app_commands.describe(domain="Domain to whitelist (e.g. youtube.com)")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterWhitelistAdd(self, interaction: discord.Interaction, domain: str):
        await addWhitelistDomain(interaction.guild_id, domain)
        await interaction.response.send_message(embed=successEmbed(f"Whitelisted: {domain}"), ephemeral=True)

    @linkfilterGroup.command(name="whitelist_remove", description="Remove a domain from the whitelist")
    @app_commands.describe(domain="Domain to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterWhitelistRemove(self, interaction: discord.Interaction, domain: str):
        await removeWhitelistDomain(interaction.guild_id, domain)
        await interaction.response.send_message(embed=successEmbed(f"Removed from whitelist: {domain}"), ephemeral=True)

    @linkfilterGroup.command(name="whitelist_list", description="Show all whitelisted domains")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterWhitelistList(self, interaction: discord.Interaction):
        domains = await getWhitelistDomains(interaction.guild_id)
        desc = "\n".join(f"• {d}" for d in domains) if domains else "No domains whitelisted"
        await interaction.response.send_message(embed=infoEmbed("Whitelisted Domains", desc), ephemeral=True)

    @linkfilterGroup.command(name="regex_add", description="Add a custom regex pattern")
    @app_commands.describe(pattern="Regex pattern to add")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterRegexAdd(self, interaction: discord.Interaction, pattern: str):
        raw = await getConfig(interaction.guild_id, "linkRegexPatterns") or "[]"
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            patterns = []
        if pattern not in patterns:
            patterns.append(pattern)
        await setConfig(interaction.guild_id, "linkRegexPatterns", json.dumps(patterns))
        await interaction.response.send_message(embed=successEmbed(f"Added regex pattern: `{pattern}`"), ephemeral=True)

    @linkfilterGroup.command(name="regex_remove", description="Remove a custom regex pattern")
    @app_commands.describe(pattern="Regex pattern to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def linkfilterRegexRemove(self, interaction: discord.Interaction, pattern: str):
        raw = await getConfig(interaction.guild_id, "linkRegexPatterns") or "[]"
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            patterns = []
        if pattern in patterns:
            patterns.remove(pattern)
        await setConfig(interaction.guild_id, "linkRegexPatterns", json.dumps(patterns))
        await interaction.response.send_message(embed=successEmbed(f"Removed regex pattern: `{pattern}`"), ephemeral=True)

    @wordfilterGroup.command(name="enable", description="Enable the word filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterEnable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "wordFilterEnabled", "1")
        await interaction.response.send_message(embed=successEmbed("Word filter enabled"), ephemeral=True)

    @wordfilterGroup.command(name="disable", description="Disable the word filter")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterDisable(self, interaction: discord.Interaction):
        await setConfig(interaction.guild_id, "wordFilterEnabled", "0")
        await interaction.response.send_message(embed=successEmbed("Word filter disabled"), ephemeral=True)

    @wordfilterGroup.command(name="add", description="Add a banned word")
    @app_commands.describe(word="Word to ban")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterAdd(self, interaction: discord.Interaction, word: str):
        await addBannedWord(interaction.guild_id, word)
        await interaction.response.send_message(embed=successEmbed(f"Banned word added: ||{word}||"), ephemeral=True)

    @wordfilterGroup.command(name="remove", description="Remove a banned word")
    @app_commands.describe(word="Word to unban")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterRemove(self, interaction: discord.Interaction, word: str):
        await removeBannedWord(interaction.guild_id, word)
        await interaction.response.send_message(embed=successEmbed(f"Banned word removed: {word}"), ephemeral=True)

    @wordfilterGroup.command(name="list", description="Show all banned words")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterList(self, interaction: discord.Interaction):
        words = await getBannedWords(interaction.guild_id)
        desc = "\n".join(f"• ||{w}||" for w in words) if words else "No banned words"
        await interaction.response.send_message(embed=infoEmbed("Banned Words", desc), ephemeral=True)

    @wordfilterGroup.command(name="partial", description="Toggle partial match mode")
    @app_commands.describe(enabled="Enable or disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterPartial(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "wordFilterPartialMatch", "1" if enabled else "0")
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=successEmbed(f"Partial match {state}"), ephemeral=True)

    @wordfilterGroup.command(name="regex", description="Toggle regex mode")
    @app_commands.describe(enabled="Enable or disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def wordfilterRegex(self, interaction: discord.Interaction, enabled: bool):
        await setConfig(interaction.guild_id, "wordFilterRegex", "1" if enabled else "0")
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=successEmbed(f"Regex mode {state}"), ephemeral=True)

    @exemptGroup.command(name="add", description="Add a role exemption")
    @app_commands.describe(rule="Filter rule to exempt from", role="Role to exempt")
    @app_commands.choices(rule=ruleChoices)
    @app_commands.checks.has_permissions(administrator=True)
    async def exemptAdd(self, interaction: discord.Interaction, rule: app_commands.Choice[str], role: discord.Role):
        await addExemptRole(interaction.guild_id, rule.value, role.id)
        await interaction.response.send_message(embed=successEmbed(f"{role.mention} exempted from {rule.name} filter"), ephemeral=True)

    @exemptGroup.command(name="remove", description="Remove a role exemption")
    @app_commands.describe(rule="Filter rule", role="Role to un-exempt")
    @app_commands.choices(rule=ruleChoices)
    @app_commands.checks.has_permissions(administrator=True)
    async def exemptRemove(self, interaction: discord.Interaction, rule: app_commands.Choice[str], role: discord.Role):
        await removeExemptRole(interaction.guild_id, rule.value, role.id)
        await interaction.response.send_message(embed=successEmbed(f"{role.mention} removed from {rule.name} exemptions"), ephemeral=True)

    @exemptGroup.command(name="list", description="List exempt roles for a filter")
    @app_commands.describe(rule="Filter rule to check")
    @app_commands.choices(rule=ruleChoices)
    @app_commands.checks.has_permissions(administrator=True)
    async def exemptList(self, interaction: discord.Interaction, rule: app_commands.Choice[str]):
        roleIds = await getExemptRoles(interaction.guild_id, rule.value)
        if roleIds:
            mentions = [f"<@&{rid}>" for rid in roleIds]
            desc = "\n".join(f"• {m}" for m in mentions)
        else:
            desc = "No exempt roles"
        await interaction.response.send_message(embed=infoEmbed(f"Exempt Roles — {rule.name}", desc), ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ You need Administrator permission.", color=embedColor),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))

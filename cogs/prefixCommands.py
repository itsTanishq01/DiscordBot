import json
import discord
from discord.ext import commands
from config import embedColor
from database import (
    setConfig, getConfig, getAllConfig,
    addExemptRole, removeExemptRole, getExemptRoles,
    addBannedWord, removeBannedWord, getBannedWords,
    addWhitelistDomain, removeWhitelistDomain, getWhitelistDomains
)

validRules = ["spam", "attachment", "mention", "messageLimit", "link", "word"]

def successEmbed(description):
    return discord.Embed(description=f"✅ {description}", color=embedColor)

def infoEmbed(title, description=""):
    return discord.Embed(title=title, description=description, color=embedColor)

def parseBool(value):
    return value.lower() in ("on", "true", "1", "yes")

class PrefixCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="config", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def configGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @configGroup.command(name="view")
    @commands.has_permissions(administrator=True)
    async def configView(self, ctx):
        cfg = await getAllConfig(ctx.guild.id)
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
        await ctx.send(embed=embed)

    @commands.command(name="modlog")
    @commands.has_permissions(administrator=True)
    async def modlogSet(self, ctx, channel: discord.TextChannel):
        await setConfig(ctx.guild.id, "modLogChannel", str(channel.id))
        await ctx.send(embed=successEmbed(f"Mod-log channel set to {channel.mention}"))

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def prefixSet(self, ctx, newPrefix: str):
        await setConfig(ctx.guild.id, "prefix", newPrefix)
        await ctx.send(embed=successEmbed(f"Prefix set to `{newPrefix}`"))

    @commands.group(name="spam", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def spamGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @spamGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def spamEnable(self, ctx):
        await setConfig(ctx.guild.id, "spamEnabled", "1")
        await ctx.send(embed=successEmbed("Spam filter enabled"))

    @spamGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def spamDisable(self, ctx):
        await setConfig(ctx.guild.id, "spamEnabled", "0")
        await ctx.send(embed=successEmbed("Spam filter disabled"))

    @spamGroup.command(name="set")
    @commands.has_permissions(administrator=True)
    async def spamSet(self, ctx, maxMessages: int, timeWindow: int):
        await setConfig(ctx.guild.id, "spamMaxMessages", str(maxMessages))
        await setConfig(ctx.guild.id, "spamTimeWindow", str(timeWindow))
        await ctx.send(embed=successEmbed(f"Spam limit: {maxMessages} messages per {timeWindow}s"))

    @commands.group(name="attachment", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def attachmentGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @attachmentGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def attachmentEnable(self, ctx):
        await setConfig(ctx.guild.id, "attachmentEnabled", "1")
        await ctx.send(embed=successEmbed("Attachment filter enabled"))

    @attachmentGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def attachmentDisable(self, ctx):
        await setConfig(ctx.guild.id, "attachmentEnabled", "0")
        await ctx.send(embed=successEmbed("Attachment filter disabled"))

    @attachmentGroup.command(name="limit")
    @commands.has_permissions(administrator=True)
    async def attachmentLimit(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxAttachments", str(count))
        await ctx.send(embed=successEmbed(f"Max attachments set to {count}"))

    @attachmentGroup.command(name="block")
    @commands.has_permissions(administrator=True)
    async def attachmentBlock(self, ctx, filetype: str):
        raw = await getConfig(ctx.guild.id, "blockedFileTypes") or "[]"
        try:
            types = json.loads(raw)
        except json.JSONDecodeError:
            types = []
        ft = filetype.lower().lstrip(".")
        if ft not in types:
            types.append(ft)
        await setConfig(ctx.guild.id, "blockedFileTypes", json.dumps(types))
        await ctx.send(embed=successEmbed(f"Blocked file type: .{ft}"))

    @attachmentGroup.command(name="unblock")
    @commands.has_permissions(administrator=True)
    async def attachmentUnblock(self, ctx, filetype: str):
        raw = await getConfig(ctx.guild.id, "blockedFileTypes") or "[]"
        try:
            types = json.loads(raw)
        except json.JSONDecodeError:
            types = []
        ft = filetype.lower().lstrip(".")
        if ft in types:
            types.remove(ft)
        await setConfig(ctx.guild.id, "blockedFileTypes", json.dumps(types))
        await ctx.send(embed=successEmbed(f"Unblocked file type: .{ft}"))

    @commands.group(name="mention", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mentionGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @mentionGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def mentionEnable(self, ctx):
        await setConfig(ctx.guild.id, "mentionEnabled", "1")
        await ctx.send(embed=successEmbed("Mention filter enabled"))

    @mentionGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def mentionDisable(self, ctx):
        await setConfig(ctx.guild.id, "mentionEnabled", "0")
        await ctx.send(embed=successEmbed("Mention filter disabled"))

    @mentionGroup.command(name="limit")
    @commands.has_permissions(administrator=True)
    async def mentionLimit(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxMentions", str(count))
        await ctx.send(embed=successEmbed(f"Max mentions set to {count}"))

    @mentionGroup.command(name="blockeveryone")
    @commands.has_permissions(administrator=True)
    async def mentionBlockEveryone(self, ctx, toggle: str):
        val = "1" if parseBool(toggle) else "0"
        await setConfig(ctx.guild.id, "blockEveryone", val)
        state = "enabled" if val == "1" else "disabled"
        await ctx.send(embed=successEmbed(f"@everyone blocking {state}"))

    @mentionGroup.command(name="blockhere")
    @commands.has_permissions(administrator=True)
    async def mentionBlockHere(self, ctx, toggle: str):
        val = "1" if parseBool(toggle) else "0"
        await setConfig(ctx.guild.id, "blockHere", val)
        state = "enabled" if val == "1" else "disabled"
        await ctx.send(embed=successEmbed(f"@here blocking {state}"))

    @commands.group(name="msglimit", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def msglimitGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @msglimitGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def msglimitEnable(self, ctx):
        await setConfig(ctx.guild.id, "messageLimitEnabled", "1")
        await ctx.send(embed=successEmbed("Message limit filter enabled"))

    @msglimitGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def msglimitDisable(self, ctx):
        await setConfig(ctx.guild.id, "messageLimitEnabled", "0")
        await ctx.send(embed=successEmbed("Message limit filter disabled"))

    @msglimitGroup.command(name="lines")
    @commands.has_permissions(administrator=True)
    async def msglimitLines(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxLines", str(count))
        await ctx.send(embed=successEmbed(f"Max lines set to {count}"))

    @msglimitGroup.command(name="words")
    @commands.has_permissions(administrator=True)
    async def msglimitWords(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxWords", str(count))
        await ctx.send(embed=successEmbed(f"Max words set to {count}"))

    @msglimitGroup.command(name="characters")
    @commands.has_permissions(administrator=True)
    async def msglimitCharacters(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxCharacters", str(count))
        await ctx.send(embed=successEmbed(f"Max characters set to {count}"))

    @commands.group(name="linkfilter", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def linkfilterGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @linkfilterGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def linkfilterEnable(self, ctx):
        await setConfig(ctx.guild.id, "linkFilterEnabled", "1")
        await ctx.send(embed=successEmbed("Link filter enabled"))

    @linkfilterGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def linkfilterDisable(self, ctx):
        await setConfig(ctx.guild.id, "linkFilterEnabled", "0")
        await ctx.send(embed=successEmbed("Link filter disabled"))

    @linkfilterGroup.command(name="whitelist_add")
    @commands.has_permissions(administrator=True)
    async def linkfilterWhitelistAdd(self, ctx, domain: str):
        await addWhitelistDomain(ctx.guild.id, domain)
        await ctx.send(embed=successEmbed(f"Whitelisted: {domain}"))

    @linkfilterGroup.command(name="whitelist_remove")
    @commands.has_permissions(administrator=True)
    async def linkfilterWhitelistRemove(self, ctx, domain: str):
        await removeWhitelistDomain(ctx.guild.id, domain)
        await ctx.send(embed=successEmbed(f"Removed from whitelist: {domain}"))

    @linkfilterGroup.command(name="whitelist_list")
    @commands.has_permissions(administrator=True)
    async def linkfilterWhitelistList(self, ctx):
        domains = await getWhitelistDomains(ctx.guild.id)
        desc = "\n".join(f"• {d}" for d in domains) if domains else "No domains whitelisted"
        await ctx.send(embed=infoEmbed("Whitelisted Domains", desc))

    @linkfilterGroup.command(name="regex_add")
    @commands.has_permissions(administrator=True)
    async def linkfilterRegexAdd(self, ctx, *, pattern: str):
        raw = await getConfig(ctx.guild.id, "linkRegexPatterns") or "[]"
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            patterns = []
        if pattern not in patterns:
            patterns.append(pattern)
        await setConfig(ctx.guild.id, "linkRegexPatterns", json.dumps(patterns))
        await ctx.send(embed=successEmbed(f"Added regex pattern: `{pattern}`"))

    @linkfilterGroup.command(name="regex_remove")
    @commands.has_permissions(administrator=True)
    async def linkfilterRegexRemove(self, ctx, *, pattern: str):
        raw = await getConfig(ctx.guild.id, "linkRegexPatterns") or "[]"
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            patterns = []
        if pattern in patterns:
            patterns.remove(pattern)
        await setConfig(ctx.guild.id, "linkRegexPatterns", json.dumps(patterns))
        await ctx.send(embed=successEmbed(f"Removed regex pattern: `{pattern}`"))

    @commands.group(name="wordfilter", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def wordfilterGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @wordfilterGroup.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def wordfilterEnable(self, ctx):
        await setConfig(ctx.guild.id, "wordFilterEnabled", "1")
        await ctx.send(embed=successEmbed("Word filter enabled"))

    @wordfilterGroup.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def wordfilterDisable(self, ctx):
        await setConfig(ctx.guild.id, "wordFilterEnabled", "0")
        await ctx.send(embed=successEmbed("Word filter disabled"))

    @wordfilterGroup.command(name="add")
    @commands.has_permissions(administrator=True)
    async def wordfilterAdd(self, ctx, *, word: str):
        await addBannedWord(ctx.guild.id, word)
        await ctx.send(embed=successEmbed(f"Banned word added: ||{word}||"))

    @wordfilterGroup.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def wordfilterRemove(self, ctx, *, word: str):
        await removeBannedWord(ctx.guild.id, word)
        await ctx.send(embed=successEmbed(f"Banned word removed: {word}"))

    @wordfilterGroup.command(name="list")
    @commands.has_permissions(administrator=True)
    async def wordfilterList(self, ctx):
        words = await getBannedWords(ctx.guild.id)
        desc = "\n".join(f"• ||{w}||" for w in words) if words else "No banned words"
        await ctx.send(embed=infoEmbed("Banned Words", desc))

    @wordfilterGroup.command(name="partial")
    @commands.has_permissions(administrator=True)
    async def wordfilterPartial(self, ctx, toggle: str):
        val = "1" if parseBool(toggle) else "0"
        await setConfig(ctx.guild.id, "wordFilterPartialMatch", val)
        state = "enabled" if val == "1" else "disabled"
        await ctx.send(embed=successEmbed(f"Partial match {state}"))

    @wordfilterGroup.command(name="regex")
    @commands.has_permissions(administrator=True)
    async def wordfilterRegex(self, ctx, toggle: str):
        val = "1" if parseBool(toggle) else "0"
        await setConfig(ctx.guild.id, "wordFilterRegex", val)
        state = "enabled" if val == "1" else "disabled"
        await ctx.send(embed=successEmbed(f"Regex mode {state}"))

    @commands.group(name="exempt", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def exemptGroup(self, ctx):
        await ctx.send_help(ctx.command)

    @exemptGroup.command(name="add")
    @commands.has_permissions(administrator=True)
    async def exemptAdd(self, ctx, rule: str, role: discord.Role):
        if rule not in validRules:
            await ctx.send(embed=discord.Embed(description=f"❌ Invalid rule. Use: {', '.join(validRules)}", color=embedColor))
            return
        await addExemptRole(ctx.guild.id, rule, role.id)
        await ctx.send(embed=successEmbed(f"{role.mention} exempted from {rule} filter"))

    @exemptGroup.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def exemptRemove(self, ctx, rule: str, role: discord.Role):
        if rule not in validRules:
            await ctx.send(embed=discord.Embed(description=f"❌ Invalid rule. Use: {', '.join(validRules)}", color=embedColor))
            return
        await removeExemptRole(ctx.guild.id, rule, role.id)
        await ctx.send(embed=successEmbed(f"{role.mention} removed from {rule} exemptions"))

    @exemptGroup.command(name="list")
    @commands.has_permissions(administrator=True)
    async def exemptList(self, ctx, rule: str):
        if rule not in validRules:
            await ctx.send(embed=discord.Embed(description=f"❌ Invalid rule. Use: {', '.join(validRules)}", color=embedColor))
            return
        roleIds = await getExemptRoles(ctx.guild.id, rule)
        if roleIds:
            mentions = [f"<@&{rid}>" for rid in roleIds]
            desc = "\n".join(f"• {m}" for m in mentions)
        else:
            desc = "No exempt roles"
        await ctx.send(embed=infoEmbed(f"Exempt Roles — {rule}", desc))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(description="❌ You need Administrator permission.", color=embedColor))

async def setup(bot):
    await bot.add_cog(PrefixCommands(bot))

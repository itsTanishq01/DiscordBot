import re
import json
from urllib.parse import urlparse
import discord
from discord.ext import commands
from database import getConfig, isRoleExempt, getWhitelistDomains, isChannelExempt
from modlog import sendModLog

urlPattern = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
invitePattern = re.compile(r"(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9]+", re.IGNORECASE)

class LinkFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.content:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id

        linkFilterEnabled = await getConfig(guildId, "linkFilterEnabled")
        if linkFilterEnabled != "1":
            return

        if await isRoleExempt(guildId, "link", message.author.roles):
            return

        if await isChannelExempt(guildId, "link", message.channel.id):
            return

        whitelist = await getWhitelistDomains(guildId)
        content = message.content

        urls = urlPattern.findall(content)
        if urls:
            for url in urls:
                try:
                    parsed = urlparse(url if url.startswith("http") else f"http://{url}")
                    domain = parsed.netloc.lower()
                except Exception:
                    domain = ""
                if domain and domain not in whitelist:
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass
                    await sendModLog(
                        self.bot, guildId,
                        user=message.author,
                        channel=message.channel,
                        rule="Link Filter (URL)",
                        messageContent=content
                    )
                    return

        if invitePattern.search(content):
            inviteDomains = ["discord.gg", "discord.com", "discordapp.com"]
            isWhitelisted = any(d in whitelist for d in inviteDomains)
            if not isWhitelisted:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
                await sendModLog(
                    self.bot, guildId,
                    user=message.author,
                    channel=message.channel,
                    rule="Link Filter (Invite)",
                    messageContent=content
                )
                return

        linkRegexRaw = await getConfig(guildId, "linkRegexPatterns") or "[]"
        try:
            linkRegexPatterns = json.loads(linkRegexRaw)
        except json.JSONDecodeError:
            linkRegexPatterns = []

        for pattern in linkRegexPatterns:
            try:
                if re.search(pattern, content, re.IGNORECASE):
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass
                    await sendModLog(
                        self.bot, guildId,
                        user=message.author,
                        channel=message.channel,
                        rule="Link Filter (Custom Pattern)",
                        messageContent=content
                    )
                    return
            except re.error:
                continue

async def setup(bot):
    await bot.add_cog(LinkFilter(bot))

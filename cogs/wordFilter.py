import re
import discord
from discord.ext import commands
from database import getConfig, isRoleExempt, getBannedWords, isChannelExempt
from modlog import sendModLog

class WordFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.content:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id

        wordFilterEnabled = await getConfig(guildId, "wordFilterEnabled")
        if wordFilterEnabled != "1":
            return

        if await isRoleExempt(guildId, "word", message.author.roles):
            return

        if await isChannelExempt(guildId, "word", message.channel.id):
            return

        bannedWords = await getBannedWords(guildId)
        if not bannedWords:
            return

        usePartial = (await getConfig(guildId, "wordFilterPartialMatch") or "0") == "1"
        useRegex = (await getConfig(guildId, "wordFilterRegex") or "0") == "1"

        contentLower = message.content.lower()
        contentWords = contentLower.split()

        for bannedWord in bannedWords:
            matched = False
            matchRule = ""

            if useRegex:
                try:
                    if re.search(bannedWord, message.content, re.IGNORECASE):
                        matched = True
                        matchRule = "Word Filter (Regex)"
                except re.error:
                    continue
            elif usePartial:
                if bannedWord in contentLower:
                    matched = True
                    matchRule = "Word Filter (Partial)"
            else:
                if bannedWord in contentWords:
                    matched = True
                    matchRule = "Word Filter (Exact)"

            if matched:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
                await sendModLog(
                    self.bot, guildId,
                    user=message.author,
                    channel=message.channel,
                    rule=matchRule,
                    messageContent=message.content
                )
                return

async def setup(bot):
    await bot.add_cog(WordFilter(bot))

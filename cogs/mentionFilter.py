import discord
from discord.ext import commands
from database import getConfig, isRoleExempt
from modlog import sendModLog

class MentionFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id

        mentionEnabled = await getConfig(guildId, "mentionEnabled")
        if mentionEnabled != "1":
            return

        if await isRoleExempt(guildId, "mention", message.author.roles):
            return

        blockEveryone = await getConfig(guildId, "blockEveryone") or "0"
        blockHere = await getConfig(guildId, "blockHere") or "0"
        maxMentions = int(await getConfig(guildId, "maxMentions") or 10)

        totalMentions = len(message.mentions) + len(message.role_mentions)

        if blockEveryone == "1" and message.mention_everyone:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Mention Filter (@everyone)",
                messageContent=message.content,
                mentionCount=totalMentions
            )
            return

        if blockHere == "1" and "@here" in message.content:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Mention Filter (@here)",
                messageContent=message.content,
                mentionCount=totalMentions
            )
            return

        if totalMentions > maxMentions:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Mention Filter (Count)",
                messageContent=message.content,
                mentionCount=totalMentions
            )

async def setup(bot):
    await bot.add_cog(MentionFilter(bot))

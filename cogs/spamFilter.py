import time
from collections import defaultdict
import discord
from discord.ext import commands
from database import getConfig, isRoleExempt, isChannelExempt

from modlog import sendModLog

class SpamFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.userMessages = defaultdict(lambda: defaultdict(list))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id
        userId = message.author.id

        spamEnabled = await getConfig(guildId, "spamEnabled")
        if spamEnabled != "1":
            return

        if await isRoleExempt(guildId, "spam", message.author.roles):
            return

        if await isChannelExempt(guildId, "spam", message.channel.id):
            return

        spamMaxMessages = int(await getConfig(guildId, "spamMaxMessages") or 5)
        spamTimeWindow = int(await getConfig(guildId, "spamTimeWindow") or 10)

        now = time.time()
        timestamps = self.userMessages[guildId][userId]
        self.userMessages[guildId][userId] = [t for t in timestamps if now - t < spamTimeWindow]
        self.userMessages[guildId][userId].append(now)

        if len(self.userMessages[guildId][userId]) > spamMaxMessages:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Spam Filter",
                messageContent=message.content
            )
            self.userMessages[guildId][userId] = []

async def setup(bot):
    await bot.add_cog(SpamFilter(bot))

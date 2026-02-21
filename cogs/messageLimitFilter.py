import discord
from discord.ext import commands
from database import getConfig, isRoleExempt
from modlog import sendModLog

class MessageLimitFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.content:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id

        messageLimitEnabled = await getConfig(guildId, "messageLimitEnabled")
        if messageLimitEnabled != "1":
            return

        if await isRoleExempt(guildId, "messageLimit", message.author.roles):
            return

        maxCharacters = int(await getConfig(guildId, "maxCharacters") or 2000)
        maxWords = int(await getConfig(guildId, "maxWords") or 500)
        maxLines = int(await getConfig(guildId, "maxLines") or 30)

        content = message.content

        if len(content) > maxCharacters:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Message Limit (Characters)",
                messageContent=content
            )
            return

        if len(content.split()) > maxWords:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Message Limit (Words)",
                messageContent=content
            )
            return

        if content.count("\n") + 1 > maxLines:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Message Limit (Lines)",
                messageContent=content
            )

async def setup(bot):
    await bot.add_cog(MessageLimitFilter(bot))

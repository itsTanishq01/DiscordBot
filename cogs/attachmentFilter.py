import json
import discord
from discord.ext import commands
from database import getConfig, isRoleExempt
from modlog import sendModLog

class AttachmentFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.attachments:
            return

        if getattr(message.author, "guild_permissions", None) and message.author.guild_permissions.administrator:
            return

        guildId = message.guild.id

        attachmentEnabled = await getConfig(guildId, "attachmentEnabled")
        if attachmentEnabled != "1":
            return

        if await isRoleExempt(guildId, "attachment", message.author.roles):
            return

        maxAttachments = int(await getConfig(guildId, "maxAttachments") or 5)
        blockedRaw = await getConfig(guildId, "blockedFileTypes") or "[]"
        try:
            blockedFileTypes = json.loads(blockedRaw)
        except json.JSONDecodeError:
            blockedFileTypes = []

        if len(message.attachments) > maxAttachments:
            attachmentInfo = "\n".join(
                f"{a.filename} ({a.size} bytes)" for a in message.attachments
            )
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            await sendModLog(
                self.bot, guildId,
                user=message.author,
                channel=message.channel,
                rule="Attachment Filter (Count)",
                messageContent=message.content,
                attachmentInfo=attachmentInfo
            )
            return

        if blockedFileTypes:
            for attachment in message.attachments:
                ext = attachment.filename.rsplit(".", 1)[-1].lower() if "." in attachment.filename else ""
                if ext in blockedFileTypes:
                    attachmentInfo = f"{attachment.filename} (blocked type: .{ext})"
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass
                    await sendModLog(
                        self.bot, guildId,
                        user=message.author,
                        channel=message.channel,
                        rule="Attachment Filter (File Type)",
                        messageContent=message.content,
                        attachmentInfo=attachmentInfo
                    )
                    return

async def setup(bot):
    await bot.add_cog(AttachmentFilter(bot))

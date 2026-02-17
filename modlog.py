import discord
from config import embedColor
from database import getConfig

async def sendModLog(bot, guildId, **kwargs):
    channelId = await getConfig(guildId, "modLogChannel")
    if not channelId:
        return

    channel = bot.get_channel(int(channelId))
    if not channel:
        return

    user = kwargs.get("user")
    msgChannel = kwargs.get("channel")
    rule = kwargs.get("rule", "Unknown")
    messageContent = kwargs.get("messageContent", "N/A")
    attachmentInfo = kwargs.get("attachmentInfo")
    mentionCount = kwargs.get("mentionCount")

    embed = discord.Embed(
        title="⚠️ AutoMod Action",
        color=embedColor,
        timestamp=discord.utils.utcnow()
    )

    if user:
        embed.add_field(
            name="User",
            value=f"{user.mention} ({user.id})",
            inline=True
        )
        roleNames = [r.name for r in user.roles if r.name != "@everyone"]
        embed.add_field(
            name="Roles",
            value=", ".join(roleNames) if roleNames else "None",
            inline=True
        )

    if msgChannel:
        embed.add_field(
            name="Channel",
            value=msgChannel.mention,
            inline=True
        )

    embed.add_field(name="Rule Violated", value=rule, inline=False)

    truncated = messageContent[:1024] if len(messageContent) > 1024 else messageContent
    embed.add_field(name="Message Content", value=truncated or "N/A", inline=False)

    if attachmentInfo:
        embed.add_field(name="Attachments", value=attachmentInfo, inline=True)

    if mentionCount is not None:
        embed.add_field(name="Mention Count", value=str(mentionCount), inline=True)

    guild = bot.get_guild(int(guildId))
    footerText = f"AutoMod • {guild.name}" if guild else "AutoMod"
    embed.set_footer(text=footerText)

    await channel.send(embed=embed)

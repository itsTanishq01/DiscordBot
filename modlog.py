import discord
from database import getConfig

async def sendModLog(bot, guildId, user, channel, rule, messageContent=None, attachment=None, **kwargs):
    logChannelId = await getConfig(guildId, "modLogChannel")
    
    if not logChannelId:
        return

    try:
        logChannel = bot.get_channel(int(logChannelId))
        if not logChannel:
            return
            
        embed = discord.Embed(title=f"Auto-Mod Action: {rule}", color=0xFF0000)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=True)
        embed.add_field(name="Channel", value=f"{channel.mention} (`{channel.id}`)", inline=True)
        
        if messageContent:
            # Truncate if too long
            content = (messageContent[:1000] + '...') if len(messageContent) > 1000 else messageContent
            embed.add_field(name="Content", value=content, inline=False)
            
        if attachment:
            embed.add_field(name="Attachment", value=attachment.filename, inline=False)
            
        for key, value in kwargs.items():
            embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=True)
            
        embed.set_footer(text=f"User ID: {user.id}")
        embed.timestamp = discord.utils.utcnow()
        
        await logChannel.send(embed=embed)
        
    except Exception as e:
        print(f"Failed to send mod log: {e}")

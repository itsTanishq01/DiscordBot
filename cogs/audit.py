import discord
from discord.ext import commands
from database import getConfig
import datetime

class Audit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def getLogChannel(self, guild):
        channelId = await getConfig(guild.id, "modLogChannel")
        if channelId:
            return guild.get_channel(int(channelId))
        return None

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = await self.getLogChannel(message.guild)
        if not channel: return
        
        embed = discord.Embed(title="Message Deleted", color=0xFF0000)
        embed.set_author(name=f"{message.author} ({message.author.display_name})", icon_url=message.author.display_avatar.url)
        embed.add_field(name="Content", value=message.content[:1024] if message.content else "*No text content*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.set_footer(text=f"User ID: {message.author.id}")
        embed.timestamp = datetime.datetime.now()
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content: return
        channel = await self.getLogChannel(before.guild)
        if not channel: return

        embed = discord.Embed(title="Message Edited", color=0xFFAA00)
        embed.set_author(name=f"{before.author} ({before.author.display_name})", icon_url=before.author.display_avatar.url)
        embed.add_field(name="Before", value=before.content[:1024], inline=False)
        embed.add_field(name="After", value=after.content[:1024], inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.set_footer(text=f"User ID: {before.author.id} • Message ID: {before.id}")
        embed.timestamp = datetime.datetime.now()
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.getLogChannel(member.guild)
        if not channel: return

        embed = discord.Embed(title="Member Joined", color=0x00FF00)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.add_field(name="Account Age", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.timestamp = datetime.datetime.now()
        await channel.send(embed=embed)

        sys_channel = member.guild.system_channel
        if sys_channel:
            await sys_channel.send(f"Welcome to the server, {member.mention}! 👋")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.getLogChannel(member.guild)
        if not channel: return

        embed = discord.Embed(title="Member Left", color=0x333333)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.timestamp = datetime.datetime.now()
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Audit(bot))

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import defaultPrefix, requiredIntents
from database import initDb, initDefaults, getConfig

load_dotenv()

async def getPrefix(bot, message):
    if message.guild:
        prefix = await getConfig(message.guild.id, "prefix")
        return prefix if prefix else defaultPrefix
    return defaultPrefix

bot = commands.Bot(
    command_prefix=getPrefix,
    intents=requiredIntents
)

cogExtensions = [
    "cogs.spamFilter",
    "cogs.attachmentFilter",
    "cogs.mentionFilter",
    "cogs.messageLimitFilter",
    "cogs.linkFilter",
    "cogs.wordFilter",
    "cogs.slashCommands",
    "cogs.prefixCommands",
]

@bot.event
async def on_ready():
    await initDb()
    for guild in bot.guilds:
        await initDefaults(guild.id)
    for ext in cogExtensions:
        await bot.load_extension(ext)
    await bot.tree.sync()
    print(f"Bot ready as {bot.user} in {len(bot.guilds)} guild(s)")

@bot.event
async def on_guild_join(guild):
    await initDefaults(guild.id)

bot.run(os.getenv("BOT_TOKEN"))

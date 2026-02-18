import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import defaultPrefix, requiredIntents
from database import initDb, initDefaults, getConfig
from keep_alive import keep_alive

load_dotenv()

async def getPrefix(bot, message):
    try:
        if message.guild:
            prefix = await getConfig(message.guild.id, "prefix")
            return prefix if prefix else defaultPrefix
    except AttributeError:
        # DB pool might be None during startup
        pass
    except Exception as e:
        print(f"Error fetching prefix: {e}")
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
    "cogs.moderation",
    "cogs.warnings",
    "cogs.audit",
    "cogs.utility",
    "cogs.permissions",
    "cogs.customHelp",
]

@bot.event
async def on_ready():
    success = await initDb()
    if success:
        print("Database initialized successfully.")
    else:
        print("CRITICAL: Database connection failed. Bot features may be broken.")
        # We continue just to let bot stay online, but skip initDefaults which would crash
        return

    for guild in bot.guilds:
        await initDefaults(guild.id)
        
    print(f"Loading {len(cogExtensions)} extensions...")
    for ext in cogExtensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"FAILED to load extension {ext}: {e}")
    
    # Sync commands to all guilds for instant update
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Synced commands to guild: {guild.name} ({guild.id})")
        except Exception as e:
            print(f"Failed to sync to {guild.name}: {e}")

    print(f"Bot ready as {bot.user} in {len(bot.guilds)} guild(s)")

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Syncs slash commands globally."""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        await ctx.send(f"Failed to sync: {e}")

@bot.event
async def on_guild_join(guild):
    await initDefaults(guild.id)

keep_alive()
bot.run(os.getenv("BOT_TOKEN"))

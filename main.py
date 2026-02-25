import os
import asyncio
import discord
from discord.ext import commands, tasks
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
        pass
    except Exception as e:
        print(f"Error fetching prefix: {e}")
    return defaultPrefix

bot = commands.Bot(
    command_prefix=getPrefix,
    intents=requiredIntents
)

@tasks.loop(minutes=10)
async def update_status():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Servers"))

@update_status.before_loop
async def before_status():
    await bot.wait_until_ready()

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
    "cogs.projects",
    "cogs.sprints",
    "cogs.tasks",
    "cogs.bugs",
    "cogs.team",
    "cogs.checklists",
    "cogs.workload",
]

@bot.event
async def on_ready():
    if getattr(bot, '__startup_done', False):
        return
    bot.__startup_done = True

    await asyncio.sleep(5)
    success = await initDb()
    if success:
        print("Database initialized successfully.")
    else:
        print("CRITICAL: Database connection failed. Bot features may be broken.")
        return

    for guild in bot.guilds:
        await initDefaults(guild.id)
        
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Wiped global commands from Discord.")
    except Exception as e:
        print(f"Failed to wipe global commands: {e}")

    print(f"Loading {len(cogExtensions)} extensions...")
    for ext in cogExtensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"FAILED to load extension {ext}: {e}")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally!")
    except Exception as e:
        print(f"Failed to sync globally: {e}")

    print(f"AbyssBot ready as {bot.user} in {len(bot.guilds)} guild(s)")
    if not update_status.is_running():
        update_status.start()

@bot.command()
@commands.is_owner()
async def sync(ctx, spec: str = None):
    """Syncs slash commands. Usage: .sync [global/clear/guild]"""
    try:
        if spec == "global":
            synced = await bot.tree.sync()
            await ctx.send(f"Synced {len(synced)} commands globally.")
        elif spec == "clear":
            bot.tree.clear_commands(guild=ctx.guild)
            await bot.tree.sync(guild=ctx.guild)
            await ctx.send("Cleared guild commands. Discord should now fall back to the global commands (might require restarting your client).")
        else:
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Synced {len(synced)} command(s) to this guild.")
    except Exception as e:
        await ctx.send(f"Failed to sync: {e}")

@bot.event
async def on_guild_join(guild):
    await initDefaults(guild.id)

keep_alive()
bot.run(os.getenv("BOT_TOKEN"))

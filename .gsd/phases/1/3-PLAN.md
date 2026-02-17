---
phase: 1
plan: 3
wave: 2
---

# Plan 1.3: Mod-Log, Main Entry Point & Cog Stubs

## Objective
Create the mod-log embed utility, the main bot entry point that loads cogs, and empty cog stub files for all 6 filters. After this plan, the bot boots, connects to Discord, and is ready for Phase 2 filter implementation.

## Context
- .gsd/SPEC.md
- config.py (Plan 1.1)
- database.py (Plan 1.2)

## Tasks

<task type="auto" effort="medium">
  <name>Create modlog.py embed builder</name>
  <files>modlog.py</files>
  <action>
    Create `modlog.py` with camelCase naming, minimal comments.

    Function: async sendModLog(bot, guildId, **kwargs)
    Parameters via kwargs:
    - user (discord.Member)
    - channel (discord.TextChannel)
    - rule (str — which filter triggered, e.g. "Spam Filter", "Word Filter")
    - messageContent (str — original message text)
    - attachmentInfo (str or None — attachment filenames/types)
    - mentionCount (int or None)

    Behavior:
    1. Get mod-log channel ID from database: getConfig(guildId, "modLogChannel")
    2. If no mod-log channel configured, return silently (no error)
    3. Build discord.Embed with:
       - Title: "⚠️ AutoMod Action"
       - Color: embedColor from config.py
       - Fields:
         - "User" — user.mention + f" ({user.id})"
         - "Channel" — channel.mention
         - "Rule Violated" — rule string
         - "Message Content" — messageContent (truncate to 1024 chars if longer)
         - "Roles" — comma-separated list of user's role names (excluding @everyone)
         - "Timestamp" — discord.utils.utcnow() formatted
         - "Attachments" — attachmentInfo (only if not None)
         - "Mention Count" — mentionCount (only if not None)
       - Footer: "AutoMod • {guild.name}"
       - Timestamp: set embed timestamp
    4. Send embed to mod-log channel

    USE: embed.add_field() for each field.
    AVOID: Raising exceptions if mod-log channel is not configured or not found.
  </action>
  <verify>python -c "import ast; tree=ast.parse(open('modlog.py').read()); funcs=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]; assert 'sendModLog' in funcs; print('OK')"</verify>
  <done>modlog.py exports sendModLog that builds and sends full embed to configured channel</done>
</task>

<task type="auto" effort="medium">
  <name>Create main.py entry point and cog stubs</name>
  <files>main.py, cogs/spamFilter.py, cogs/attachmentFilter.py, cogs/mentionFilter.py, cogs/messageLimitFilter.py, cogs/linkFilter.py, cogs/wordFilter.py</files>
  <action>
    1. Create `main.py` with camelCase naming, minimal comments:
       - Load .env using python-dotenv
       - Import database.initDb, database.initDefaults
       - Create bot with commands.Bot:
         - command_prefix pulled from database (default "." from config.py)
         - intents: messages, message_content, guilds, members
       - Dynamic prefix function: async getPrefix(bot, message) that queries database for prefix, falls back to defaultPrefix
       - on_ready event:
         - Call initDb()
         - For each guild bot is in, call initDefaults(guild.id)
         - Load all cog extensions from cogs/ directory
         - Sync slash commands with bot.tree.sync()
         - Print ready message
       - on_guild_join event:
         - Call initDefaults(guild.id) for the new guild
       - bot.run(os.getenv("BOT_TOKEN"))

    2. Create 6 cog stub files in cogs/:
       Each stub follows this pattern (example for spamFilter):
       ```python
       import discord
       from discord.ext import commands

       class SpamFilter(commands.Cog):
           def __init__(self, bot):
               self.bot = bot

       async def setup(bot):
           await bot.add_cog(SpamFilter(bot))
       ```

       Create stubs for:
       - cogs/spamFilter.py (class SpamFilter)
       - cogs/attachmentFilter.py (class AttachmentFilter)
       - cogs/mentionFilter.py (class MentionFilter)
       - cogs/messageLimitFilter.py (class MessageLimitFilter)
       - cogs/linkFilter.py (class LinkFilter)
       - cogs/wordFilter.py (class WordFilter)

    USE: bot.load_extension("cogs.spamFilter") pattern for loading cogs.
    AVOID: Hardcoding the token anywhere — always read from .env.
    AVOID: Using bot.command_prefix as a static string — use the dynamic getPrefix function.
  </action>
  <verify>python -c "import ast; tree=ast.parse(open('main.py').read()); print('main.py OK'); import os; cogs=['spamFilter','attachmentFilter','mentionFilter','messageLimitFilter','linkFilter','wordFilter']; missing=[c for c in cogs if not os.path.isfile(f'cogs/{c}.py')]; assert not missing, f'Missing cogs: {missing}'; print('All cogs OK')"</verify>
  <done>main.py boots bot with dynamic prefix, loads 6 cogs, inits DB on ready. All 6 cog stubs exist with proper class structure.</done>
</task>

## Success Criteria
- [ ] modlog.py sendModLog builds embed with all SPEC fields
- [ ] main.py creates bot with dynamic prefix, loads all cogs, inits DB
- [ ] All 6 cog stub files exist in cogs/ with proper setup() function
- [ ] Bot would connect to Discord if given a valid token

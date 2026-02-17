---
phase: 3
plan: 2
wave: 1
---

# Plan 3.2: Prefix Commands

## Objective
Create the prefix command cog mirroring all slash command functionality. Uses discord.ext.commands with command groups. Includes a command to change the prefix itself.

## Context
- .gsd/SPEC.md
- config.py
- database.py
- cogs/slashCommands.py (mirror its functionality)

## Tasks

<task type="auto" effort="high">
  <name>Create prefix commands cog</name>
  <files>cogs/prefixCommands.py</files>
  <action>
    Create `cogs/prefixCommands.py`. camelCase, minimal comments.

    Mirror all slash command functionality using prefix commands.
    All commands require administrator permission: @commands.has_permissions(administrator=True)

    Use commands.Group for organization. Default prefix is "." so commands look like:
    .config view, .modlog set #channel, .prefix set !, etc.

    **Commands to implement (mirror slash commands):**

    **Top-level:**
    - .config view — show all config as embed
    - .modlog set <channel> — set mod-log channel (channel converter)
    - .prefix set <new_prefix> — set prefix in DB

    **Group: .spam**
    - .spam enable / .spam disable
    - .spam set <maxMessages> <timeWindow>

    **Group: .attachment**
    - .attachment enable / .attachment disable
    - .attachment limit <count>
    - .attachment block <filetype> / .attachment unblock <filetype>

    **Group: .mention**
    - .mention enable / .mention disable
    - .mention limit <count>
    - .mention blockeveryone <on/off> / .mention blockhere <on/off>

    **Group: .msglimit**
    - .msglimit enable / .msglimit disable
    - .msglimit lines <count> / .msglimit words <count> / .msglimit characters <count>

    **Group: .linkfilter**
    - .linkfilter enable / .linkfilter disable
    - .linkfilter whitelist_add <domain> / .linkfilter whitelist_remove <domain> / .linkfilter whitelist_list
    - .linkfilter regex_add <pattern> / .linkfilter regex_remove <pattern>

    **Group: .wordfilter**
    - .wordfilter enable / .wordfilter disable
    - .wordfilter add <word> / .wordfilter remove <word> / .wordfilter list
    - .wordfilter partial <on/off> / .wordfilter regex <on/off>

    **Group: .exempt**
    - .exempt add <rule> <@role> / .exempt remove <rule> <@role> / .exempt list <rule>
    - Rule must be one of: spam, attachment, mention, messageLimit, link, word

    For boolean toggles (on/off), accept "on", "true", "1" as true, everything else as false.

    All responses as discord.Embed for consistency with slash commands.

    Error handler:
    ```python
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(description="You need Administrator permission.", color=0xFF4444))
    ```

    USE: commands.group(invoke_without_command=True) for groups
    USE: discord.TextChannel type hint for channel converter
    USE: discord.Role type hint for role converter
    AVOID: Duplicating business logic — call the same database functions as slash commands
  </action>
  <verify>Select-String -Path "cogs/prefixCommands.py" -Pattern "commands\.group|has_permissions|setConfig|getConfig|addBannedWord|addExemptRole|addWhitelistDomain" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>prefixCommands.py mirrors all slash command functionality with prefix-based interface</done>
</task>

## Success Criteria
- [ ] All prefix command groups mirror slash commands
- [ ] All commands have administrator permission check
- [ ] Boolean toggles accept on/off strings
- [ ] Channel and role converters work
- [ ] Prefix change command updates database
- [ ] All responses use embeds

---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Slash Commands

## Objective
Create the slash command cog providing admin-only configuration interface for all automod features. Uses discord.py app_commands with a group structure for organized commands. Register the cog in main.py.

## Context
- .gsd/SPEC.md
- config.py
- database.py
- cogs/ (all filter cogs for reference on config keys)

## Tasks

<task type="auto" effort="high">
  <name>Create slash commands cog</name>
  <files>cogs/slashCommands.py</files>
  <action>
    Create `cogs/slashCommands.py`. camelCase, minimal comments.

    Import: discord, app_commands, commands, json
    Import: database functions (setConfig, getConfig, getAllConfig, addExemptRole, removeExemptRole, getExemptRoles, addBannedWord, removeBannedWord, getBannedWords, addWhitelistDomain, removeWhitelistDomain, getWhitelistDomains)

    Class: SlashCommands(commands.Cog)

    All commands require administrator permission: @app_commands.checks.has_permissions(administrator=True)

    Use app_commands.Group for organization:

    **Top-level commands:**
    - /config view — show all current config as embed
    - /modlog set (channel: TextChannel) — set mod-log channel
    - /prefix set (prefix: str) — set command prefix

    **Group: /spam**
    - /spam enable — set spamEnabled=1
    - /spam disable — set spamEnabled=0
    - /spam set (maxMessages: int, timeWindow: int) — set spamMaxMessages, spamTimeWindow

    **Group: /attachment**
    - /attachment enable — set attachmentEnabled=1
    - /attachment disable — set attachmentEnabled=0
    - /attachment limit (count: int) — set maxAttachments
    - /attachment block (filetype: str) — add to blockedFileTypes (JSON list)
    - /attachment unblock (filetype: str) — remove from blockedFileTypes

    **Group: /mention**
    - /mention enable — set mentionEnabled=1
    - /mention disable — set mentionEnabled=0
    - /mention limit (count: int) — set maxMentions
    - /mention blockeveryone (enabled: bool) — set blockEveryone
    - /mention blockhere (enabled: bool) — set blockHere

    **Group: /msglimit**
    - /msglimit enable — set messageLimitEnabled=1
    - /msglimit disable — set messageLimitEnabled=0
    - /msglimit lines (count: int) — set maxLines
    - /msglimit words (count: int) — set maxWords
    - /msglimit characters (count: int) — set maxCharacters

    **Group: /linkfilter**
    - /linkfilter enable — set linkFilterEnabled=1
    - /linkfilter disable — set linkFilterEnabled=0
    - /linkfilter whitelist_add (domain: str) — addWhitelistDomain
    - /linkfilter whitelist_remove (domain: str) — removeWhitelistDomain
    - /linkfilter whitelist_list — show all whitelisted domains
    - /linkfilter regex_add (pattern: str) — add to linkRegexPatterns JSON list
    - /linkfilter regex_remove (pattern: str) — remove from linkRegexPatterns JSON list

    **Group: /wordfilter**
    - /wordfilter enable — set wordFilterEnabled=1
    - /wordfilter disable — set wordFilterEnabled=0
    - /wordfilter add (word: str) — addBannedWord
    - /wordfilter remove (word: str) — removeBannedWord
    - /wordfilter list — show all banned words
    - /wordfilter partial (enabled: bool) — set wordFilterPartialMatch
    - /wordfilter regex (enabled: bool) — set wordFilterRegex

    **Group: /exempt**
    - /exempt add (rule: str, role: Role) — addExemptRole (rule choices: spam, attachment, mention, messageLimit, link, word)
    - /exempt remove (rule: str, role: Role) — removeExemptRole
    - /exempt list (rule: str) — getExemptRoles, show as role mentions

    For the `rule` parameter in /exempt commands, use app_commands.Choice to provide dropdown:
    ```python
    @app_commands.choices(rule=[
        app_commands.Choice(name="Spam", value="spam"),
        app_commands.Choice(name="Attachment", value="attachment"),
        app_commands.Choice(name="Mention", value="mention"),
        app_commands.Choice(name="Message Limit", value="messageLimit"),
        app_commands.Choice(name="Link", value="link"),
        app_commands.Choice(name="Word", value="word"),
    ])
    ```

    All commands respond with ephemeral embed confirming the change (interaction.response.send_message with ephemeral=True).

    For /config view: build a rich embed showing all config values grouped by filter.

    For JSON list config (blockedFileTypes, linkRegexPatterns):
    - Read current value with getConfig
    - Parse with json.loads
    - Append/remove item
    - Save back with setConfig as json.dumps

    Error handler for permission check:
    ```python
    async def on_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You need Administrator permission.", ephemeral=True)
    ```

    USE: app_commands.Group(name="...", description="...") for command groups
    USE: ephemeral=True for all responses (only command user sees the response)
    USE: discord.Embed for all responses for consistency
    AVOID: Non-ephemeral responses for config commands (don't spam channels)
    AVOID: Hardcoding config keys — use the same key strings as in config.py defaultConfig
  </action>
  <verify>Select-String -Path "cogs/slashCommands.py" -Pattern "app_commands|Group|has_permissions|ephemeral|setConfig|getConfig|addBannedWord|addExemptRole|addWhitelistDomain" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>slashCommands.py has all command groups (spam, attachment, mention, msglimit, linkfilter, wordfilter, exempt) with admin permission checks and ephemeral responses</done>
</task>

<task type="auto" effort="low">
  <name>Register slash commands cog in main.py</name>
  <files>main.py</files>
  <action>
    Add "cogs.slashCommands" to the cogExtensions list in main.py.
    Add "cogs.prefixCommands" as well (for Plan 3.2).
  </action>
  <verify>Select-String -Path "main.py" -Pattern "cogs.slashCommands|cogs.prefixCommands" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>main.py loads both slashCommands and prefixCommands cogs</done>
</task>

## Success Criteria
- [ ] All slash command groups created with proper structure
- [ ] All commands have administrator permission check
- [ ] All responses are ephemeral embeds
- [ ] Config view shows all settings in organized embed
- [ ] JSON list operations (blockedFileTypes, linkRegexPatterns) work correctly
- [ ] Exempt role commands use app_commands.Choice dropdown
- [ ] Cog registered in main.py

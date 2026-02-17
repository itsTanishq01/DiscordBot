---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Mention Filter & Message Limit Filter

## Objective
Implement the mention filter (mention limits + @everyone/@here blocking) and message limit filter (line/word/character limits). Both delete violating messages and send mod-log embeds with role exemption checks.

## Context
- .gsd/SPEC.md
- config.py
- database.py
- modlog.py
- cogs/mentionFilter.py (stub)
- cogs/messageLimitFilter.py (stub)

## Tasks

<task type="auto" effort="medium">
  <name>Implement mention filter cog</name>
  <files>cogs/mentionFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Class: MentionFilter(commands.Cog)

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot or no guild
    2. Load config: mentionEnabled, maxMentions, blockEveryone, blockHere from database.getConfig()
    3. If mentionEnabled != "1", return
    4. Check role exemption: database.isRoleExempt(guildId, "mention", message.author.roles)
    5. Check @everyone: if blockEveryone == "1" and message.mention_everyone:
       - Delete message
       - Send mod-log with rule="Mention Filter (@everyone)", mentionCount=len(message.mentions)
       - Return
    6. Check @here: if blockHere == "1" and "@here" in message.content:
       - Delete message
       - Send mod-log with rule="Mention Filter (@here)", mentionCount=len(message.mentions)
       - Return
    7. Count mentions: len(message.mentions) + len(message.role_mentions)
       - If total > int(maxMentions):
         - Delete message
         - Send mod-log with rule="Mention Filter (Count)", mentionCount=total

    USE: message.mention_everyone for @everyone detection (Discord API property)
    USE: "@here" in message.content for @here detection (no built-in property)
    USE: message.mentions for user mentions, message.role_mentions for role mentions
  </action>
  <verify>Select-String -Path "cogs/mentionFilter.py" -Pattern "on_message|maxMentions|blockEveryone|blockHere|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>mentionFilter.py enforces mention count, blocks @everyone/@here, checks exemptions, logs violations</done>
</task>

<task type="auto" effort="medium">
  <name>Implement message limit filter cog</name>
  <files>cogs/messageLimitFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Class: MessageLimitFilter(commands.Cog)

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot or no guild or empty content
    2. Load config: messageLimitEnabled, maxLines, maxWords, maxCharacters from database.getConfig()
    3. If messageLimitEnabled != "1", return
    4. Check role exemption: database.isRoleExempt(guildId, "messageLimit", message.author.roles)
    5. Check character limit: if len(message.content) > int(maxCharacters):
       - Delete message
       - Send mod-log with rule="Message Limit (Characters)"
       - Return
    6. Check word limit: if len(message.content.split()) > int(maxWords):
       - Delete message
       - Send mod-log with rule="Message Limit (Words)"
       - Return
    7. Check line limit: if message.content.count("\n") + 1 > int(maxLines):
       - Delete message
       - Send mod-log with rule="Message Limit (Lines)"
       - Return

    USE: len(message.content) for character count
    USE: len(message.content.split()) for word count
    USE: message.content.count("\n") + 1 for line count
    AVOID: Processing messages with empty content
  </action>
  <verify>Select-String -Path "cogs/messageLimitFilter.py" -Pattern "on_message|maxLines|maxWords|maxCharacters|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>messageLimitFilter.py enforces line, word, and character limits with exemptions and logging</done>
</task>

## Success Criteria
- [ ] Mention filter enforces mention count limit
- [ ] Mention filter blocks @everyone and @here independently
- [ ] Message limit filter enforces line, word, and character limits
- [ ] Both filters check role exemptions before enforcing
- [ ] Both filters read thresholds from database and log violations

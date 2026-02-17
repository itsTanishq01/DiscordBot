---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Spam Filter & Attachment Filter

## Objective
Implement the spam filter (per-user rate limiting) and attachment filter (count + file type blocking). Both delete violating messages and send mod-log embeds. Both check role exemptions before enforcing.

## Context
- .gsd/SPEC.md
- config.py
- database.py
- modlog.py
- cogs/spamFilter.py (stub)
- cogs/attachmentFilter.py (stub)

## Tasks

<task type="auto" effort="high">
  <name>Implement spam filter cog</name>
  <files>cogs/spamFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Class: SpamFilter(commands.Cog)
    - __init__(self, bot): store bot, create dict `self.userMessages` to track per-user message timestamps
      - Structure: {guildId: {userId: [timestamp1, timestamp2, ...]}}

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot
    2. Skip if no guild (DMs)
    3. Load config: spamEnabled, spamMaxMessages, spamTimeWindow from database.getConfig()
    4. If spamEnabled != "1", return
    5. Check role exemption: database.isRoleExempt(guildId, "spam", message.author.roles) — if exempt, return
    6. Get current time, clean old timestamps outside the time window for this user
    7. Append current timestamp
    8. If message count exceeds spamMaxMessages:
       - Delete the message: await message.delete()
       - Send mod-log: await sendModLog(bot, guildId, user=message.author, channel=message.channel, rule="Spam Filter", messageContent=message.content)
       - Clear user's timestamp list to reset the window

    USE: time.time() for timestamps (float seconds)
    USE: collections.defaultdict for nested dict
    AVOID: Persisting spam tracking to database — in-memory only, resets on restart (acceptable)
    AVOID: Blocking the event loop — all DB calls are async
  </action>
  <verify>Select-String -Path "cogs/spamFilter.py" -Pattern "on_message|spamMaxMessages|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>spamFilter.py has on_message listener, reads config from DB, checks exemptions, deletes spam, sends mod-log</done>
</task>

<task type="auto" effort="medium">
  <name>Implement attachment filter cog</name>
  <files>cogs/attachmentFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Class: AttachmentFilter(commands.Cog)

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot, no guild, or no attachments
    2. Load config: attachmentEnabled, maxAttachments, blockedFileTypes from database.getConfig()
    3. If attachmentEnabled != "1", return
    4. Check role exemption: database.isRoleExempt(guildId, "attachment", message.author.roles)
    5. Parse blockedFileTypes from JSON string to list
    6. Check attachment count: if len(message.attachments) > int(maxAttachments):
       - Build attachmentInfo string: list filenames and sizes
       - Delete message
       - Send mod-log with rule="Attachment Filter (Count)", attachmentInfo=attachmentInfo
    7. Check file types: for each attachment, extract extension (split on ".")
       - If extension in blockedFileTypes list:
         - Build attachmentInfo with blocked filename + extension
         - Delete message
         - Send mod-log with rule="Attachment Filter (File Type)", attachmentInfo=attachmentInfo
         - Break after first violation

    USE: json.loads() to parse blockedFileTypes from config
    USE: attachment.filename to get filename and extract extension
    AVOID: Double-deleting if both count and type violations — check count first, return if deleted
  </action>
  <verify>Select-String -Path "cogs/attachmentFilter.py" -Pattern "on_message|maxAttachments|blockedFileTypes|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>attachmentFilter.py checks count and file types, deletes violations, logs to mod-log</done>
</task>

## Success Criteria
- [ ] Spam filter tracks per-user message frequency in-memory
- [ ] Spam filter deletes messages exceeding threshold and logs
- [ ] Attachment filter enforces count limit and file type blocking
- [ ] Both filters check role exemptions before enforcing
- [ ] Both filters read thresholds from database

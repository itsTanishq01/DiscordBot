---
phase: 2
plan: 3
wave: 1
---

# Plan 2.3: Link Filter & Word Filter

## Objective
Implement the link filter (URL/invite detection with whitelist and regex) and word filter (banned words with case-insensitive, partial, and regex modes). These are the most complex filters requiring pattern matching logic.

## Context
- .gsd/SPEC.md
- config.py
- database.py
- modlog.py
- cogs/linkFilter.py (stub)
- cogs/wordFilter.py (stub)

## Tasks

<task type="auto" effort="high">
  <name>Implement link filter cog</name>
  <files>cogs/linkFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Import: re, json, urllib.parse

    Class: LinkFilter(commands.Cog)

    Class-level constants:
    - urlPattern = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
    - invitePattern = re.compile(r"(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9]+", re.IGNORECASE)

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot or no guild or empty content
    2. Load config: linkFilterEnabled from database.getConfig()
    3. If linkFilterEnabled != "1", return
    4. Check role exemption: database.isRoleExempt(guildId, "link", message.author.roles)
    5. Find all URLs in message using urlPattern.findall(message.content)
    6. If no URLs found, skip to step 8
    7. For each URL found:
       a. Extract domain using urllib.parse.urlparse
       b. Get whitelist: database.getWhitelistDomains(guildId)
       c. If domain is in whitelist, skip this URL
       d. If not whitelisted:
          - Delete message
          - Send mod-log with rule="Link Filter (URL)"
          - Return
    8. Check for Discord invites: invitePattern.search(message.content)
       - If found and not whitelisted:
         - Delete message
         - Send mod-log with rule="Link Filter (Invite)"
         - Return
    9. Check custom regex patterns: load linkRegexPatterns from config (JSON list of strings)
       - For each pattern string, compile and test against message.content
       - If match found:
         - Delete message
         - Send mod-log with rule="Link Filter (Custom Pattern)"
         - Return

    USE: urllib.parse.urlparse(url).netloc for domain extraction
    USE: re.compile() for custom regex patterns with try/except for invalid regex
    AVOID: Crashing on malformed URLs — wrap urlparse in try/except
    AVOID: Crashing on invalid user-provided regex — wrap re.compile in try/except
  </action>
  <verify>Select-String -Path "cogs/linkFilter.py" -Pattern "on_message|urlPattern|invitePattern|getWhitelistDomains|linkRegexPatterns|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>linkFilter.py detects URLs and invites, supports whitelist and custom regex, deletes violations, logs to mod-log</done>
</task>

<task type="auto" effort="high">
  <name>Implement word filter cog</name>
  <files>cogs/wordFilter.py</files>
  <action>
    Replace stub with full implementation. camelCase, minimal comments.

    Import: re

    Class: WordFilter(commands.Cog)

    Listener: @commands.Cog.listener() on_message(self, message)
    1. Skip if message.author is bot or no guild or empty content
    2. Load config: wordFilterEnabled, wordFilterPartialMatch, wordFilterRegex from database.getConfig()
    3. If wordFilterEnabled != "1", return
    4. Check role exemption: database.isRoleExempt(guildId, "word", message.author.roles)
    5. Get banned words: database.getBannedWords(guildId)
    6. If no banned words, return
    7. contentLower = message.content.lower()
    8. For each bannedWord in bannedWords:

       Mode A — Regex mode (wordFilterRegex == "1"):
       - Try re.search(bannedWord, message.content, re.IGNORECASE)
       - If match: delete, log with rule="Word Filter (Regex)", return

       Mode B — Partial match (wordFilterPartialMatch == "1"):
       - If bannedWord in contentLower: delete, log with rule="Word Filter (Partial)", return

       Mode C — Exact word match (default):
       - Split contentLower into words
       - If bannedWord in words list: delete, log with rule="Word Filter (Exact)", return

    USE: re.IGNORECASE flag for regex mode
    USE: .lower() for case-insensitive comparison in non-regex modes
    AVOID: Crashing on invalid regex in banned words — wrap re.search in try/except, skip invalid patterns
    AVOID: Re-splitting content for every word — split once, reuse
  </action>
  <verify>Select-String -Path "cogs/wordFilter.py" -Pattern "on_message|wordFilterEnabled|getBannedWords|wordFilterPartialMatch|wordFilterRegex|message.delete|sendModLog" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>wordFilter.py supports case-insensitive, partial match, and regex modes with exemptions and logging</done>
</task>

## Success Criteria
- [ ] Link filter detects URLs and Discord invites
- [ ] Link filter supports domain whitelist
- [ ] Link filter supports custom regex patterns
- [ ] Word filter matches banned words case-insensitively
- [ ] Word filter supports partial match and regex modes
- [ ] Both filters handle malformed input gracefully (no crashes)
- [ ] Both filters check role exemptions and log violations

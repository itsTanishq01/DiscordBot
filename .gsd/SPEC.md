# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision
A Python Discord moderation bot providing an advanced, configurable automod system with more granular control than Discord's built-in AutoMod. Targets mid-to-large Discord servers needing stronger content moderation. Ships with sensible defaults and allows full configuration via slash commands. Deployed on Render for 24/7 uptime as a single-server bot.

## Goals
1. Granular automod with per-rule configurability (spam, attachments, mentions, message limits, links, words)
2. Rich enforcement with mod-log embeds containing full violation context
3. Role-based exemptions configurable per rule
4. Hybrid command system (slash commands primary, customizable prefix secondary)
5. Zero-config usability — works immediately after invite with sensible defaults

## Non-Goals (Out of Scope)
- Music playback
- Leveling / XP systems
- Economy systems
- Anything beyond pure moderation
- Multi-server sharding (single-server deployment)
- Web dashboard

## Users
Server administrators and moderators of mid-to-large Discord servers who need finer automod control than Discord natively provides. End users interact indirectly — their messages are filtered by the bot.

## Technical Stack
- **Language**: Python
- **Library**: discord.py
- **Database**: SQLite (per-server config storage)
- **Hosting**: Render (cloud VPS)
- **Architecture**: Modular — one file per feature, main file orchestrates
- **Naming Convention**: camelCase
- **Comments**: Minimal to none

## Feature Specifications

### 1. Spam Control
- Track messages per user: limit X messages per Y seconds
- Per-user tracking with timestamps
- Configurable thresholds stored in SQLite

### 2. Attachment Control
- Limit number of attachments per message
- Option to block specific file types (by extension)

### 3. Mention Control
- Limit mentions per message
- Separate toggles for blocking `@everyone` / `@here`

### 4. Message Limits
- Line count limit per message
- Word count limit per message
- Character count limit per message

### 5. Link Filtering
- Detect URLs and Discord invite links
- Whitelist/exclusion list for allowed domains
- Regex-based custom filtering support

### 6. Word Filtering
- Custom banned words list
- Case-insensitive matching
- Partial match option (substring detection)
- Regex support for advanced patterns

### 7. Enforcement Actions
- Delete violating message
- Send detailed embed to configured mod-log channel
- Optional warning system (future phase)
- Optional timeout (future phase)

### 8. Role Exemptions
- Exclude specific roles from any filter
- Configurable per rule type

## Mod-Log Embed Contents
- Username + User ID
- Channel where violation occurred
- Rule violated (which filter triggered)
- Original message content
- Timestamp
- User roles at time of violation
- Attachment info (if applicable)
- Mention count (if applicable)

## Command System
- **Primary**: Slash commands (always functional)
- **Secondary**: Prefix commands (customizable, default: `.`)
- Prefix stored in SQLite, changeable via command

## Defaults (Ship-Ready)
| Rule | Default |
|------|---------|
| Spam limit | 5 messages per 10 seconds |
| Max attachments | 5 per message |
| Max mentions | 10 per message |
| Block @everyone/@here | Off |
| Max lines | 30 per message |
| Max words | 500 per message |
| Max characters | 2000 per message |
| Link filtering | Off (opt-in) |
| Word filtering | Off (opt-in) |
| Mod-log channel | None (must be configured) |

## Constraints
- Single-server deployment on Render
- SQLite only (no external database dependencies)
- Must function with discord.py's latest stable release
- 24/7 uptime expected
- Minimal external dependencies

## Success Criteria
- [ ] Bot joins server and applies default automod rules immediately
- [ ] All 6 filter types (spam, attachments, mentions, message limits, links, words) functional
- [ ] Slash commands configure every threshold and toggle
- [ ] Prefix commands mirror slash command functionality
- [ ] Role exemptions work per-rule
- [ ] Mod-log embeds contain all specified fields
- [ ] SQLite persists all configuration across restarts
- [ ] Deploys successfully on Render

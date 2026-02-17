# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0

## Must-Haves (from SPEC)
- [ ] Bot connects and runs with discord.py
- [ ] SQLite config storage with defaults
- [ ] All 6 automod filters (spam, attachments, mentions, message limits, links, words)
- [ ] Role exemptions per rule
- [ ] Mod-log embeds
- [ ] Hybrid command system (slash + prefix)
- [ ] Render deployment

## Phases

### Phase 1: Foundation
**Status**: ✅ Complete
**Objective**: Bot boots, connects to Discord, SQLite schema ready, modular file structure in place, mod-log embed utility created.
**Requirements**: REQ-01, REQ-02, REQ-09, REQ-13, REQ-14

**Deliverables:**
- `main.py` — entry point, loads all cogs
- `database.py` — SQLite connection, schema init, default values
- `modlog.py` — embed builder for mod-log channel
- `config.py` — constants, default thresholds
- Project structure with one file per feature (empty cogs)
- `requirements.txt`

### Phase 2: Core Filters
**Status**: ⬜ Not Started
**Objective**: All 6 automod filters operational with default thresholds. Messages violating rules are deleted and logged.
**Requirements**: REQ-03, REQ-04, REQ-05, REQ-06, REQ-07, REQ-08, REQ-09, REQ-10

**Deliverables:**
- `cogs/spamFilter.py` — per-user rate limiting
- `cogs/attachmentFilter.py` — attachment count + file type blocking
- `cogs/mentionFilter.py` — mention limits + @everyone/@here
- `cogs/messageLimitFilter.py` — line/word/character limits
- `cogs/linkFilter.py` — URL/invite detection, whitelist, regex
- `cogs/wordFilter.py` — banned words, case-insensitive, partial, regex
- Role exemption checks integrated into each filter

### Phase 3: Command System
**Status**: ⬜ Not Started
**Objective**: Admins can configure every filter via slash commands and prefix commands. Prefix is customizable.
**Requirements**: REQ-11, REQ-12

**Deliverables:**
- `cogs/slashCommands.py` — slash command interface for all config
- `cogs/prefixCommands.py` — prefix command mirror
- Prefix storage and retrieval from SQLite
- Permission checks (admin-only commands)

### Phase 4: Deployment & Polish
**Status**: ⬜ Not Started
**Objective**: Bot runs on Render 24/7. Final testing, error handling, edge cases.
**Requirements**: REQ-15

**Deliverables:**
- `Procfile` or `render.yaml` for Render deployment
- `.env` handling for bot token
- Error handling and graceful reconnection
- Final integration test

# STATE.md

> **Last Updated**: 2026-02-25T16:07:00+05:30

## Current Position
- **Milestone**: SDLC Bot v1.0
- **Phase**: 1 — Database Schema & Foundation
- **Status**: Planning complete, ready for execution

## Plans Created
- `1-PLAN.md` — Core Entity Tables (projects, sprints, tasks, bugs) + CRUD (wave 1)
- `2-PLAN.md` — Supporting Tables (team_roles, checklists, comments, links, audit_log) + CRUD (wave 1)
- `3-PLAN.md` — Active Context Config + Helper Functions + Verification (wave 2)

## Context
- Existing bot: AbyssBot (Python/discord.py 2.3.2, asyncpg, Supabase PostgreSQL)
- Current capabilities: Moderation, automod filters, warnings, permissions, utility
- Existing tables: config, warnings, permissions, exemptions, filters, exempt_channels
- Hosting: Render (free tier)
- All new work extends `database.py` and `config.py` — no new files in Phase 1

## Decisions Made
- Framework: Python / discord.py (extend existing bot, not rewrite)
- Database: Extend existing asyncpg/Supabase setup
- Architecture: Cog-per-feature pattern (consistent with existing codebase)
- SDLC roles are bot-managed (DB), not Discord server roles
- Slash commands for all new SDLC features
- ROLE_HIERARCHY constant defined in database.py for permission checks
- All IDs stored as TEXT (consistent with existing pattern)
- All timestamps stored as BIGINT (consistent with existing pattern)

## Blockers
- None

## Next Action
- `/execute 1` — Execute Phase 1 plans

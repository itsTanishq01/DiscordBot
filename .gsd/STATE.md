# STATE.md

> **Last Updated**: 2026-02-25T15:39:00+05:30

## Current Position
- **Milestone**: SDLC Bot v1.0
- **Phase**: Not started
- **Status**: Milestone planned

## Context
- Existing bot: AbyssBot (Python/discord.py 2.3.2, asyncpg, Supabase PostgreSQL)
- Current capabilities: Moderation, automod filters, warnings, permissions, utility
- Existing tables: config, warnings, permissions, exemptions, filters, exempt_channels
- Hosting: Render (free tier)

## Decisions Made
- Framework: Python / discord.py (extend existing bot, not rewrite)
- Database: Extend existing asyncpg/Supabase setup
- Architecture: Cog-per-feature pattern (consistent with existing codebase)
- SDLC roles are bot-managed (DB), not Discord server roles
- Slash commands for all new SDLC features

## Blockers
- None

## Next Action
- `/plan 1` — Create Phase 1 (Database Schema & Foundation) execution plan

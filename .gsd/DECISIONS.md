# DECISIONS.md — Architecture Decision Records

## ADR-001: SQLite for Configuration Storage
**Date**: 2026-02-17
**Status**: Accepted
**Context**: Need persistent per-server config. Options: JSON files, SQLite, MongoDB/Redis.
**Decision**: SQLite — lightweight, no external dependencies, queryable, single-file deployment.
**Consequences**: No need for external database service. Config file is portable. Limited to single-server write concurrency (acceptable for single-server bot).

## ADR-002: Hybrid Command System
**Date**: 2026-02-17
**Status**: Accepted
**Context**: Discord deprecating prefix commands for verified bots. Need future-proof interface.
**Decision**: Slash commands as primary, prefix commands as secondary convenience layer. Both always functional.
**Consequences**: More code to maintain (two command interfaces). Slash commands are discoverable. Prefix commands offer quick access for power users.

## ADR-003: Modular Cog Architecture
**Date**: 2026-02-17
**Status**: Accepted
**Context**: Need clean separation of features.
**Decision**: One discord.py cog per feature. Main file loads all cogs.
**Consequences**: Each filter is isolated, testable, and can be enabled/disabled independently. Follows discord.py conventions.

## ADR-004: camelCase Convention
**Date**: 2026-02-17
**Status**: Accepted
**Context**: User preference for naming convention.
**Decision**: camelCase for all variable and function names. Minimal to no comments.
**Consequences**: Deviates from Python PEP 8 (snake_case), but matches user's preferred style across their projects.

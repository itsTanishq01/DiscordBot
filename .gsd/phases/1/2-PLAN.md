---
phase: 1
plan: 2
wave: 1
---

# Plan 1.2: Database Layer

## Objective
Create `database.py` with async SQLite connection, schema initialization, and config CRUD operations. This is the persistence backbone — every filter and command reads/writes config through this module.

## Context
- .gsd/SPEC.md
- config.py (created in Plan 1.1)

## Tasks

<task type="auto" effort="high">
  <name>Create database.py with schema and CRUD</name>
  <files>database.py</files>
  <action>
    Create `database.py` using aiosqlite. camelCase naming, minimal comments.

    Schema — single table `config`:
    - guildId TEXT PRIMARY KEY (for future-proofing, even though single-server)
    - key TEXT
    - value TEXT
    - Composite primary key on (guildId, key)

    Schema — table `exemptRoles`:
    - guildId TEXT
    - ruleType TEXT (e.g. "spam", "attachment", "mention", "messageLimit", "link", "word")
    - roleId TEXT
    - Composite primary key on (guildId, ruleType, roleId)

    Schema — table `bannedWords`:
    - guildId TEXT
    - word TEXT
    - Composite primary key on (guildId, word)

    Schema — table `linkWhitelist`:
    - guildId TEXT
    - domain TEXT
    - Composite primary key on (guildId, domain)

    Functions to create (all async):
    - initDb() — create connection, run CREATE TABLE IF NOT EXISTS for all tables
    - getConfig(guildId, key) — return value or None
    - setConfig(guildId, key, value) — upsert into config
    - getAllConfig(guildId) — return dict of all config for guild
    - initDefaults(guildId) — populate config with defaultConfig values if not already set
    - addExemptRole(guildId, ruleType, roleId) — insert exempt role
    - removeExemptRole(guildId, ruleType, roleId) — delete exempt role
    - getExemptRoles(guildId, ruleType) — return list of roleIds
    - isRoleExempt(guildId, ruleType, roleId) — check if any of user's roles are exempt
    - addBannedWord(guildId, word) — insert word
    - removeBannedWord(guildId, word) — delete word
    - getBannedWords(guildId) — return list
    - addWhitelistDomain(guildId, domain) — insert domain
    - removeWhitelistDomain(guildId, domain) — delete domain
    - getWhitelistDomains(guildId) — return list

    USE: aiosqlite context manager for all operations.
    USE: INSERT OR REPLACE for upsert behavior.
    AVOID: Synchronous sqlite3 — discord.py is async, blocking calls freeze the bot.
    AVOID: Storing Python objects — serialize lists as JSON strings in value column.

    Module-level variable `db` holds the aiosqlite connection, initialized by initDb().
  </action>
  <verify>python -c "import ast; tree=ast.parse(open('database.py').read()); funcs=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]; required=['initDb','getConfig','setConfig','getAllConfig','initDefaults','addExemptRole','removeExemptRole','getExemptRoles','addBannedWord','removeBannedWord','getBannedWords']; missing=[r for r in required if r not in funcs]; assert not missing, f'Missing: {missing}'; print('OK')"</verify>
  <done>database.py exports all CRUD functions, uses aiosqlite, creates 4 tables</done>
</task>

## Success Criteria
- [ ] database.py creates 4 tables: config, exemptRoles, bannedWords, linkWhitelist
- [ ] All 15 async functions present and use aiosqlite
- [ ] initDefaults populates from config.py defaults
- [ ] Upsert behavior for setConfig (no duplicate key errors)

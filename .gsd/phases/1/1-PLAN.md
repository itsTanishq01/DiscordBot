---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Project Skeleton & Configuration

## Objective
Create the project file structure, `requirements.txt`, `config.py` with all default thresholds, and `.env` template. This plan establishes the foundation every other file depends on.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md

## Tasks

<task type="auto" effort="low">
  <name>Create requirements.txt</name>
  <files>requirements.txt</files>
  <action>
    Create `requirements.txt` with:
    - discord.py (latest stable, >=2.3)
    - python-dotenv
    - aiosqlite

    AVOID: pinning exact versions (use >= for flexibility on Render).
  </action>
  <verify>python -c "import sys; lines=open('requirements.txt').readlines(); assert len(lines)>=3; print('OK')"</verify>
  <done>requirements.txt exists with discord.py, python-dotenv, aiosqlite listed</done>
</task>

<task type="auto" effort="medium">
  <name>Create config.py with default thresholds</name>
  <files>config.py</files>
  <action>
    Create `config.py` containing:
    - camelCase naming throughout, minimal comments
    - A defaults dictionary with all automod thresholds from SPEC:
      - spamLimit: 5 messages per 10 seconds (spamMaxMessages=5, spamTimeWindow=10)
      - maxAttachments: 5
      - blockedFileTypes: [] (empty list)
      - maxMentions: 10
      - blockEveryone: False
      - blockHere: False
      - maxLines: 30
      - maxWords: 500
      - maxCharacters: 2000
      - linkFilterEnabled: False
      - linkWhitelist: []
      - linkRegexPatterns: []
      - wordFilterEnabled: False
      - bannedWords: []
      - wordFilterPartialMatch: False
      - wordFilterRegex: False
    - A default prefix string: "."
    - Bot intents required: messages, message_content, guilds, members
    - Embed color constant for mod-log (hex color, e.g. 0xFF4444 for red)

    USE: A single flat dictionary named `defaultConfig` for all thresholds.
    AVOID: Nested config structures — SQLite stores flat key-value pairs.
  </action>
  <verify>python -c "from config import defaultConfig, defaultPrefix, embedColor; assert isinstance(defaultConfig, dict); assert len(defaultConfig) >= 15; print('OK')"</verify>
  <done>config.py exports defaultConfig dict with all thresholds, defaultPrefix, embedColor</done>
</task>

<task type="auto" effort="low">
  <name>Create .env template and cogs directory</name>
  <files>.env.example, cogs/__init__.py</files>
  <action>
    1. Create `.env.example` with:
       - BOT_TOKEN=your_token_here
    2. Create empty `cogs/` directory with `__init__.py` (empty file)
    3. Create `.gitignore` with:
       - .env
       - __pycache__/
       - *.pyc
       - *.db
       - .venv/
  </action>
  <verify>python -c "import os; assert os.path.isfile('.env.example'); assert os.path.isdir('cogs'); assert os.path.isfile('.gitignore'); print('OK')"</verify>
  <done>.env.example, cogs/, .gitignore all exist</done>
</task>

## Success Criteria
- [ ] requirements.txt lists all dependencies
- [ ] config.py exports defaultConfig with 15+ keys, defaultPrefix, embedColor
- [ ] .env.example provides token template
- [ ] cogs/ directory exists
- [ ] .gitignore covers sensitive and generated files

---
phase: 4
plan: 2
wave: 2
---

# Plan 4.2: Bugs Cog Registration & Verification

## Objective
Register the new `cogs/bugs.py` in `main.py`, perform comprehensive syntax validation, and verify all commands correctly map to the database functions.

## Context
- `cogs/bugs.py` — Created in Plan 4.1
- `main.py` — Holds `cogExtensions` list where the new cog must be registered.
- `database.py` — Verifies no missing function imports.

## Tasks

<task type="auto">
  <name>Register bugs cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.bugs"` to the `cogExtensions` list in `main.py`, directly after `"cogs.tasks"`.
  </action>
  <verify>python -c "import ast; ast.parse(open('main.py', encoding='utf-8').read()); content = open('main.py', encoding='utf-8').read(); assert 'cogs.bugs' in content; print('Registration OK')"</verify>
  <done>Cog registered in main.py</done>
</task>

<task type="auto">
  <name>Verify bugs ecosystem</name>
  <files>cogs/bugs.py, main.py</files>
  <action>
    1. Run AST parse verification on `cogs/bugs.py`.
    2. Check that all new SDLC files parse cleanly.
    3. Ensure no DB mapping errors (e.g., `createBug` uses `tags` while `createTask` does not).
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/bugs.py', encoding='utf-8').read()); print('Bugs Ecosystem OK')"</verify>
  <done>Full bug management lifecycle verified.</done>
</task>

## Success Criteria
- [ ] `cogs.bugs` registered in main.py extensions list.
- [ ] Code passes all syntax checks correctly.
- [ ] Readiness verified for Execution.

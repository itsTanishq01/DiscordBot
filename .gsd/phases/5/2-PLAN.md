---
phase: 5
plan: 2
wave: 2
---

# Plan 5.2: Register Team Cog

## Objective
Register `cogs/team.py` in `main.py` and verify syntax correctness.

## Context
- `main.py`
- `cogs/team.py`

## Tasks

<task type="auto">
  <name>Register team cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.team"` to `cogExtensions` inside `main.py` following the convention. (After `cogs.bugs`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.team' in content"</verify>
  <done>Registered cogs.team</done>
</task>

<task type="auto">
  <name>Verify the team role system</name>
  <files>cogs/team.py, main.py</files>
  <action>
    Use python's `ast` parser to verify the syntactical correctness of `cogs/team.py` and `main.py`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/team.py', encoding='utf-8').read()); ast.parse(open('main.py', encoding='utf-8').read())"</verify>
  <done>Code is valid and parseable.</done>
</task>

## Success Criteria
- [ ] `cogs.team` is registered.
- [ ] No syntax errors.

---
phase: 6
plan: 2
wave: 2
---

# Plan 6.2: Register Checklists Cog

## Objective
Register `cogs/checklists.py` in `main.py` and verify syntax correctness.

## Context
- `main.py`
- `cogs/checklists.py`

## Tasks

<task type="auto">
  <name>Register checklists cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.checklists"` to `cogExtensions` inside `main.py` following the convention. (After `cogs.team`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.checklists' in content"</verify>
  <done>Registered cogs.checklists</done>
</task>

<task type="auto">
  <name>Verify the checklists system</name>
  <files>cogs/checklists.py, main.py</files>
  <action>
    Use python's `ast` parser to verify the syntactical correctness of `cogs/checklists.py` and `main.py`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/checklists.py', encoding='utf-8').read()); ast.parse(open('main.py', encoding='utf-8').read())"</verify>
  <done>Code is valid and parseable.</done>
</task>

## Success Criteria
- [ ] `cogs.checklists` is registered.
- [ ] No syntax errors.

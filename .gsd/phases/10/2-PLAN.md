---
phase: 10
plan: 2
wave: 2
---

# Plan 10.2: Registration, Final Verification & Documentation

## Objective
Register the final cog, run comprehensive validation across ALL files and cogs, and create a help text summary for the entire SDLC command tree.

## Context
- `main.py` — all cog registrations
- All `cogs/*.py` files
- `database.py`

## Tasks

<task type="auto">
  <name>Register automation cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.automation"` to `cogExtensions` inside `main.py`. (After `cogs.ingestion`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.automation' in content"</verify>
  <done>Registered cogs.automation</done>
</task>

<task type="auto">
  <name>Full system verification</name>
  <files>ALL</files>
  <action>
    1. AST parse every SDLC cog file.
    2. Verify all 10 SDLC cogs are registered in main.py.
    3. Verify all DB function imports resolve.
    4. Count total slash commands across all cogs.
  </action>
  <verify>python -c "import ast; [ast.parse(open(f'cogs/{f}.py', encoding='utf-8').read()) for f in ['projects','sprints','tasks','bugs','team','checklists','workload','dashboards','ingestion','automation','sdlcHelpers']]"</verify>
  <done>Full system validated.</done>
</task>

## Success Criteria
- [ ] All 10 cogs registered and parsing clean.
- [ ] Total command count documented.
- [ ] Final git commit.

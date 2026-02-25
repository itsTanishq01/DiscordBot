---
phase: 8
plan: 2
wave: 2
---

# Plan 8.2: Register Dashboards Cog

## Objective
Register `cogs/dashboards.py` in `main.py` and verify syntax correctness.

## Context
- `main.py`
- `cogs/dashboards.py`

## Tasks

<task type="auto">
  <name>Register dashboards cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.dashboards"` to `cogExtensions` inside `main.py` following the convention. (After `cogs.workload`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.dashboards' in content"</verify>
  <done>Registered cogs.dashboards</done>
</task>

<task type="auto">
  <name>Verify the dashboards system</name>
  <files>cogs/dashboards.py, main.py</files>
  <action>
    Use python's `ast` parser to verify the syntactical correctness of `cogs/dashboards.py` and `main.py`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/dashboards.py', encoding='utf-8').read()); ast.parse(open('main.py', encoding='utf-8').read())"</verify>
  <done>Code is valid and parseable.</done>
</task>

## Success Criteria
- [ ] `cogs.dashboards` is registered.
- [ ] No syntax errors.

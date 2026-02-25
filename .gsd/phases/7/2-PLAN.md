---
phase: 7
plan: 2
wave: 2
---

# Plan 7.2: Register Workload Cog

## Objective
Register `cogs/workload.py` in `main.py` and verify syntax correctness.

## Context
- `main.py`
- `cogs/workload.py`

## Tasks

<task type="auto">
  <name>Register workload cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.workload"` to `cogExtensions` inside `main.py` following the convention. (After `cogs.checklists`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.workload' in content"</verify>
  <done>Registered cogs.workload</done>
</task>

<task type="auto">
  <name>Verify the workload system</name>
  <files>cogs/workload.py, main.py</files>
  <action>
    Use python's `ast` parser to verify the syntactical correctness of `cogs/workload.py` and `main.py`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/workload.py', encoding='utf-8').read()); ast.parse(open('main.py', encoding='utf-8').read())"</verify>
  <done>Code is valid and parseable.</done>
</task>

## Success Criteria
- [ ] `cogs.workload` is registered.
- [ ] No syntax errors.

---
phase: 9
plan: 2
wave: 2
---

# Plan 9.2: Register Ingestion Cog

## Objective
Register `cogs/ingestion.py` in `main.py` and verify syntax correctness.

## Context
- `main.py`
- `cogs/ingestion.py`

## Tasks

<task type="auto">
  <name>Register ingestion cog</name>
  <files>main.py</files>
  <action>
    Add `"cogs.ingestion"` to `cogExtensions` inside `main.py` following the convention. (After `cogs.dashboards`)
  </action>
  <verify>python -c "content = open('main.py').read(); assert 'cogs.ingestion' in content"</verify>
  <done>Registered cogs.ingestion</done>
</task>

<task type="auto">
  <name>Verify the ingestion system</name>
  <files>cogs/ingestion.py, main.py</files>
  <action>
    Use python's `ast` parser to verify the syntactical correctness of `cogs/ingestion.py` and `main.py`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/ingestion.py', encoding='utf-8').read()); ast.parse(open('main.py', encoding='utf-8').read())"</verify>
  <done>Code is valid and parseable.</done>
</task>

## Success Criteria
- [ ] `cogs.ingestion` is registered.
- [ ] No syntax errors.

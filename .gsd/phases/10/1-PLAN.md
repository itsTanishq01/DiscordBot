---
phase: 10
plan: 1
wave: 1
---

# Plan 10.1: Automation Cog — Stale Detection, Audit Viewer, Duplicate Check

## Objective
Create `cogs/automation.py` to provide stale item detection, a viewable audit trail, and duplicate bug detection. This is the final feature cog.

## Context
- `database.py` — `getAuditLog`, `getTasks`, `getBugs`, `getActiveProject`, `logAudit`
- `cogs/sdlcHelpers.py` — `requireActiveProject`, `requireRole`, `statusDisplay`, `severityDisplay`, `STATUS_EMOJI`, `SEVERITY_EMOJI`
- `config.py` — `embedColor`

## Tasks

<task type="auto">
  <name>Create automation cog</name>
  <files>cogs/automation.py</files>
  <action>
    Create a new file `cogs/automation.py` with the following structure:

    **1. `/audit log` — View recent audit trail**
    ```
    Parameters:
      entity_type: Choice (task, bug, checklist, project, sprint) — optional
      entity_id: int — optional
      limit: int — optional (default 10, max 25)
    ```
    - No strict permission required (viewer+).
    - Call `getAuditLog(guild_id, entity_type, entity_id, limit)`.
    - Format each entry as: `<t:timestamp:R> **action** on entity_type #entity_id by <@user_id> — details`
    - Paginate if many entries.

    **2. `/audit stale` — Find stale tasks and bugs**
    ```
    Parameters:
      days: int (default 7) — items not updated in this many days
    ```
    - Use `requireRole(interaction, 'lead')`.
    - Use `requireActiveProject`.
    - Fetch all tasks via `getTasks(guild_id, project_id)`.
    - Filter where `status` is NOT 'done' or 'backlog' AND `updated_at < now - days*86400`.
    - Similarly for bugs: `getBugs(guild_id, project_id)` where status is NOT 'closed' AND stale.
    - Display grouped by staleness.

    **3. `/audit duplicates` — Detect potential duplicate bugs**
    ```
    Parameters: None
    ```
    - Use `requireActiveProject`.
    - Fetch all non-closed bugs.
    - Compare titles using a simple similarity check (lowercase, strip, check if one title is a substring of another or if they share >70% of their words).
    - Group potential duplicates and display them.
    - This is a best-effort check — not a full NLP solution.

    **Entity Type Choices:**
    ```python
    ENTITY_CHOICES = [
        app_commands.Choice(name="Task", value="task"),
        app_commands.Choice(name="Bug", value="bug"),
        app_commands.Choice(name="Checklist", value="checklist"),
        app_commands.Choice(name="Project", value="project"),
        app_commands.Choice(name="Sprint", value="sprint"),
    ]
    ```
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/automation.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Automation cog created with audit viewer, stale detection, and duplicate detection.</done>
</task>

## Success Criteria
- [ ] `cogs/automation.py` exists.
- [ ] 3 commands: log, stale, duplicates.
- [ ] Stale detection uses configurable day threshold.
- [ ] Duplicate detection uses word-overlap similarity.
- [ ] Syntax validates.

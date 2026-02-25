---
phase: 4
plan: 1
wave: 1
---

# Plan 4.1: Bugs Cog — Core Commands

## Objective
Create `cogs/bugs.py` with the core bug tracking commands: report (bulk), status, assign, list, close, view.
Bugs are tracked separately from tasks but within the same project, and have a unique lifecycle and severity ratings.

**Bulk support:** `/bug report` accepts comma-separated titles to create multiple bugs with the same severity in one shot.

## Context
- `cogs/sdlcHelpers.py` — requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed, BUG_STATUSES, BUG_SEVERITIES, STATUS_EMOJI, SEVERITY_EMOJI, statusDisplay, severityDisplay
- `cogs/tasks.py` — Pattern: command group, bulk creation, Kanban-like list view, embed builders
- `database.py` — createBug, getBug, updateBugStatus, assignBug, getBugs, closeBug, getLinkedTasks, logAudit

## Tasks

<task type="auto">
  <name>Create bugs cog with core commands</name>
  <files>cogs/bugs.py</files>
  <action>
    Create `cogs/bugs.py` with the following commands:

    **Structure:**
    ```
    class Bugs(commands.Cog):
        bug_group = app_commands.Group(name="bug", description="Manage and track bugs")

        /bug report   — bulk creation, comma-separated titles
        /bug status   — move bug through lifecycle
        /bug assign   — assign/reassign bug
        /bug list     — list with filters
        /bug view     — view bug details
        /bug close    — quick close command
    ```

    **1. `/bug report` — Report bug(s)**
    ```
    Parameters:
      title: str       — "Crash on load, UI glitch, Auth fail" (comma-separated for bulk)
      severity: Choice  — critical/medium/minor (default: medium)
      description: str  — optional (applies to single bug only)
      assignee: Member  — optional
    ```
    - Use `parseBulkNames(title)` to split
    - Use `requireActiveProject(interaction)`
    - Anyone (or at least developer role - `requireRole(interaction, 'developer')`) can report. Let's use 'developer' to prevent spam.
    - For each name: `createBug(guild_id, project_id, name, desc, severity, assignee_id, reporter_id, now)`
    - Use `buildBulkEmbed(created, errors, "bug")` for response
    - Log each creation via `logAudit`

    **2. `/bug status` — Update bug lifecycle**
    ```
    Parameters:
      bug_id: int
      status: Choice  — new/acknowledged/in_progress/needs_qa/closed
    ```
    - Use `requireRole(interaction, 'developer')`
    - Validate bug exists
    - Update via `updateBugStatus(bug_id, status, now)`
    - Send embed with transition info (e.g., 🆕 New ➡️ 🧪 Needs Qa)
    - If assignee exists and is not the current user, notify them
    - Log via `logAudit`

    **3. `/bug assign` — Assign/reassign**
    ```
    Parameters:
      bug_id: int
      assignee: Member
    ```
    - Use `requireRole(interaction, 'lead')` (or 'developer' if teams self-assign) -> we'll use 'lead' to match tasks.
    - Update via `assignBug(bug_id, str(assignee.id), now)`
    - Send confirmation
    - Log via `logAudit`

    **4. `/bug list` — List with filters**
    ```
    Parameters (all optional):
      status: Choice     — filter by status
      severity: Choice   — filter by severity
      assignee: Member   — filter by assignee
    ```
    - Use `requireActiveProject(interaction)`
    - Call `getBugs(guild_id, project_id, filters)`
    - If no status filter, group bugs by severity (Critical, Medium, Minor) or status (New, Acknowledged, In Progress, Needs QA). Let's group by STATUS to match the Kanban board feel.
    - Display max 25 items

    **5. `/bug view` — View bug details**
    ```
    Parameters:
      bug_id: int
    ```
    - Get bug via `getBug(bug_id)`
    - Embed showing: Title, Description, Status (emoji), Severity (emoji), Assignee, Reporter, timestamps
    - Linked Tasks via `getLinkedTasks(bug_id)`

    **6. `/bug close` — Quick close command**
    ```
    Parameters:
      bug_id: int
    ```
    - `requireRole(interaction, 'qa')` (or 'developer' fallback if QA not strictly enforced) -> `requireRole(interaction, 'qa')` makes sense for bugs.
    - Call `closeBug(bug_id, now)`
    - Log via `logAudit`

    **Choice Definitions:**
    ```python
    STATUS_CHOICES = [
        app_commands.Choice(name="New", value="new"),
        app_commands.Choice(name="Acknowledged", value="acknowledged"),
        app_commands.Choice(name="In Progress", value="in_progress"),
        app_commands.Choice(name="Needs QA", value="needs_qa"),
        app_commands.Choice(name="Closed", value="closed"),
    ]
    SEVERITY_CHOICES = [
        app_commands.Choice(name="🔴 Critical", value="critical"),
        app_commands.Choice(name="🟡 Medium", value="medium"),
        app_commands.Choice(name="🟠 Minor", value="minor"),
    ]
    ```
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/bugs.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>cogs/bugs.py exists with 6 core commands and bulk support.</done>
</task>

## Success Criteria
- [ ] `cogs/bugs.py` exists
- [ ] 6 commands: report, status, assign, list, view, close
- [ ] `/bug report` supports bulk (comma-separated)
- [ ] Grouped board view in `/bug list`
- [ ] Syntax validates

---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Tasks Cog — Core Commands

## Objective
Create `cogs/tasks.py` with the core Kanban task commands: new (bulk), status, assign, list, delete. This is the biggest cog so far — the heart of the SDLC system.

**Bulk support:** `/task new` accepts comma-separated titles to create multiple tasks with the same priority/assignee in one shot.

## Context
- `cogs/sdlcHelpers.py` — requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed, TASK_STATUSES, TASK_PRIORITIES, STATUS_EMOJI, PRIORITY_EMOJI, statusDisplay, priorityDisplay
- `cogs/projects.py` — Pattern: command group, error handler, permission gates
- `database.py` — createTask, getTask, updateTaskStatus, assignTask, getTasks, deleteTask, getActiveSprint, logAudit, getConfig

## Tasks

<task type="auto">
  <name>Create tasks cog with core commands</name>
  <files>cogs/tasks.py</files>
  <action>
    Create `cogs/tasks.py` with the following commands:

    **Structure:**
    ```
    class Tasks(commands.Cog):
        task_group = app_commands.Group(name="task", description="Manage tasks (Kanban)")

        /task new     — bulk creation, comma-separated titles
        /task status  — move task through Kanban columns
        /task assign  — assign/reassign task
        /task list    — list with filters
        /task delete  — delete a task
        /task view    — view task details
    ```

    **1. `/task new` — Create task(s)**
    ```
    Parameters:
      title: str       — "Fix login, Add logout, Refactor auth" (comma-separated for bulk)
      priority: Choice  — critical/high/medium/low (default: medium)
      assignee: Member  — optional, assign on creation
      description: str  — optional (applies to single task only)
    ```
    - Use `parseBulkNames(title)` to split
    - Use `requireActiveProject(interaction)` to get project
    - Use `requireRole(interaction, 'developer')` for permission
    - Get active sprint via `getActiveSprint()` — auto-assign tasks to active sprint if one exists
    - For each name: `createTask(guild_id, project_id, sprint_id, name, desc, priority, assignee_id, creator_id, now)`
    - Use `buildBulkEmbed(created, errors, "task")` for response
    - If assignee specified on bulk, apply to ALL created tasks
    - Log each creation via `logAudit`

    **2. `/task status` — Update Kanban column**
    ```
    Parameters:
      task_id: int
      status: Choice  — backlog/todo/in_progress/blocked/review/done
    ```
    - Use `requireRole(interaction, 'developer')`
    - Validate task exists and belongs to guild
    - Check WIP limits: if moving to 'in_progress', count existing in_progress tasks, compare to wipLimit config
    - Update via `updateTaskStatus(task_id, status, now)`
    - Send embed with old→new status transition using statusDisplay()
    - If task has assignee and status changed, notify assignee (send a message mention)
    - Log via `logAudit`

    **3. `/task assign` — Assign/reassign**
    ```
    Parameters:
      task_id: int
      assignee: Member
    ```
    - Use `requireRole(interaction, 'lead')`
    - Update via `assignTask(task_id, str(assignee.id), now)`
    - Send confirmation embed
    - Log via `logAudit`

    **4. `/task list` — List with filters**
    ```
    Parameters (all optional):
      status: Choice     — filter by status
      priority: Choice   — filter by priority
      assignee: Member   — filter by assignee
    ```
    - Anyone can list (no permission check needed)
    - Use `requireActiveProject(interaction)` 
    - Build filters dict from provided params
    - Call `getTasks(guild_id, project_id, filters)`
    - Display as embed with status emoji + priority emoji per task
    - Show max 25 tasks (embed field limit), with "and X more..." if truncated
    - If no tasks match, show helpful message

    **5. `/task delete` — Delete a task**
    ```
    Parameters:
      task_id: int
    ```
    - Use `requireRole(interaction, 'lead')`
    - Validate task exists and belongs to guild
    - Delete via `deleteTask(task_id)`
    - Log via `logAudit`

    **6. `/task view` — View task details**
    ```
    Parameters:
      task_id: int
    ```
    - No permission check (anyone can view)
    - Get task via `getTask(task_id)`
    - Build detailed embed with: title, description, status (with emoji), priority (with emoji), assignee mention, creator mention, sprint info, created/updated timestamps
    - Show linked bugs count (via getLinkedBugs)

    **Key patterns from existing cogs to follow:**
    - `app_commands.choices()` decorator for status/priority enums
    - Discord `app_commands.Choice[str]` for the choices
    - `ephemeral=True` for errors, public for success
    - Consistent embed color from `config.embedColor`

    **Choice definitions to use:**
    ```python
    STATUS_CHOICES = [
        app_commands.Choice(name="Backlog", value="backlog"),
        app_commands.Choice(name="Todo", value="todo"),
        app_commands.Choice(name="In Progress", value="in_progress"),
        app_commands.Choice(name="Blocked", value="blocked"),
        app_commands.Choice(name="Review", value="review"),
        app_commands.Choice(name="Done", value="done"),
    ]
    PRIORITY_CHOICES = [
        app_commands.Choice(name="🔴 Critical", value="critical"),
        app_commands.Choice(name="🟠 High", value="high"),
        app_commands.Choice(name="🟡 Medium", value="medium"),
        app_commands.Choice(name="🟢 Low", value="low"),
    ]
    ```
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/tasks.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>cogs/tasks.py exists with 6 commands. Bulk creation via comma-separated titles. Kanban status transitions. Syntax validates.</done>
</task>

## Success Criteria
- [ ] `cogs/tasks.py` exists with Tasks cog class
- [ ] 6 commands: new (bulk), status, assign, list, delete, view
- [ ] Choice dropdowns for status (6 options) and priority (4 options)
- [ ] Uses shared helpers (requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed)
- [ ] WIP limit check on /task status → in_progress
- [ ] Rich embeds with status/priority emojis
- [ ] Syntax validates

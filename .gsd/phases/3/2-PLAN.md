---
phase: 3
plan: 2
wave: 2
---

# Plan 3.2: Task Comments, Link Bug & Registration

## Objective
Add the remaining task commands (/task comment, /task linkbug), register the cog in main.py, and verify the complete task system.

## Context
- `cogs/tasks.py` — Created in Plan 3.1 with core commands
- `cogs/sdlcHelpers.py` — requireRole
- `database.py` — addTaskComment, getTaskComments, linkTaskBug, getLinkedBugs, getTask, getBug, logAudit

## Tasks

<task type="auto">
  <name>Add comment and linkbug commands to tasks cog</name>
  <files>cogs/tasks.py</files>
  <action>
    Add 2 more commands to the existing Tasks cog in `cogs/tasks.py`:

    **1. `/task comment` — Add a comment to a task**
    ```
    Parameters:
      task_id: int
      text: str
    ```
    - Use `requireRole(interaction, 'developer')` — devs can comment
    - Validate task exists and belongs to guild
    - Call `addTaskComment(task_id, str(user.id), text, now)`
    - Show confirmation with comment preview
    - Log via `logAudit`

    **2. `/task linkbug` — Link a bug to a task**
    ```
    Parameters:
      task_id: int
      bug_id: int
    ```
    - Use `requireRole(interaction, 'developer')`
    - Validate both task and bug exist and belong to guild
    - Call `linkTaskBug(task_id, bug_id)`
    - Show confirmation embed with both IDs
    - Log via `logAudit`

    Also add to the `/task view` command:
    - Show task comments (last 5) in the embed
    - Show linked bug IDs

    **Place these commands inside the existing Tasks class, after the existing commands.**
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/tasks.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>/task comment and /task linkbug commands added. /task view shows comments and linked bugs. Syntax validates.</done>
</task>

<task type="auto">
  <name>Register tasks cog and run verification</name>
  <files>main.py</files>
  <action>
    1. Add `"cogs.tasks"` to `cogExtensions` in main.py (after `"cogs.sprints"`)
    2. Run full syntax validation on all SDLC files
    3. Verify all task-related database functions are importable from cogs/tasks.py
  </action>
  <verify>python -c "import ast; ast.parse(open('main.py', encoding='utf-8').read()); content = open('main.py', encoding='utf-8').read(); assert 'cogs.tasks' in content; print('Registered OK')"</verify>
  <done>"cogs.tasks" in cogExtensions. All syntax valid. Phase 3 complete.</done>
</task>

## Success Criteria
- [ ] `/task comment` command exists and works
- [ ] `/task linkbug` command exists and works
- [ ] `/task view` shows comments + linked bugs
- [ ] `cogs.tasks` registered in main.py
- [ ] All files pass syntax validation
- [ ] Total: 8 task commands (new, status, assign, list, delete, view, comment, linkbug)

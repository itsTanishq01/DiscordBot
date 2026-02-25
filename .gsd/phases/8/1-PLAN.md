---
phase: 8
plan: 1
wave: 1
---

# Plan 8.1: Dashboards Cog — Visual Summaries

## Objective
Create `cogs/dashboards.py` to provide high-level visual summaries of project health, sprint progress, and individual daily workloads.

## Context
- `cogs/sdlcHelpers.py` — `requireActiveProject`, `getTaskCounts`, `getBugCounts`, `statusDisplay`
- `database.py` — `getActiveSprint`, `getTasks`, `getBugs`
- `config.py` — `embedColor`

## Tasks

<task type="auto">
  <name>Create dashboards cog</name>
  <files>cogs/dashboards.py</files>
  <action>
    Create a new file `cogs/dashboards.py` with the following structure:

    **1. `/dashboard project`**
    ```
    Parameters: None
    ```
    - Use `requireActiveProject(interaction)`.
    - Fetch overall task metrics: `getTaskCounts(guild_id, project_id)`.
    - Fetch overall bug metrics: `getBugCounts(guild_id, project_id)`.
    - Calculate total tasks, total bugs, and completion percentage for tasks (done tasks / total tasks).
    - Render a clean, summarized embed with task status breakdown and bug severity breakdown.

    **2. `/dashboard sprint`**
    ```
    Parameters: None
    ```
    - Use `requireActiveProject`.
    - Fetch `getActiveSprint(guild_id, project_id)`.
    - If no active sprint, return error.
    - Call `getTasks(guild_id, project_id, {'sprint_id': active_sprint['id']})`.
    - Categorize tasks by status and calculate sprint completion.
    - Provide a "pseudo-burndown" visual (a progress bar or emoji ratio).
    - Display start date, end date, and days remaining.

    **3. `/dashboard my_day`**
    ```
    Parameters: None
    ```
    - Use `requireActiveProject`.
    - Fetch tasks assigned to the user `getTasks(...)` where `assignee_id` matches user. Filter in python to ignore 'done' and 'backlog' (or just show what's actionable).
    - Fetch bugs assigned to the user `getBugs(...)` ignoring 'closed'.
    - Limit the display to the most critical actionable items.
    - Output an embed focusing the developer on their day's priorities.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/dashboards.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Dashboards cog created with 3 commands for high-level tracking.</done>
</task>

## Success Criteria
- [ ] `cogs/dashboards.py` exists.
- [ ] `/dashboard project`, `/dashboard sprint`, and `/dashboard my_day` work as expected.
- [ ] Task and Bug counts correctly pull from the DB.
- [ ] Syntax validates.

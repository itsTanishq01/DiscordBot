---
phase: 1
plan: 3
wave: 2
---

# Plan 1.3: Active Context Config & Integration Verification

## Objective
Add guild-level config entries for active project/sprint context, verify all tables create successfully against the real database, and ensure backwards compatibility with the existing bot.

## Context
- `.gsd/SPEC.md` — Section 7 (Non-Functional Requirements)
- `database.py` — After Plans 1.1 and 1.2 have been executed
- `config.py` — Existing `defaultConfig` dict (line 13)
- `main.py` — Existing `initDb()` call in `on_ready()`

## Tasks

<task type="auto">
  <name>Add SDLC default config entries</name>
  <files>config.py</files>
  <action>
    Add the following keys to the `defaultConfig` dictionary in config.py (after line 34, before the closing `}`):

    ```python
    "activeProject": "",
    "sdlcNotifyChannel": "",
    "taskStaleThreshold": "7",
    "workloadMaxTasks": "10",
    "wipLimit": "5",
    ```

    These config keys control:
    - `activeProject` — The currently active project ID for the guild (set via /project set)
    - `sdlcNotifyChannel` — Channel ID where SDLC notifications go (status changes, alerts)
    - `taskStaleThreshold` — Days before a task is flagged as stale (default: 7)
    - `workloadMaxTasks` — Max active tasks before overload alert (default: 10)
    - `wipLimit` — Max tasks in "In Progress" column (default: 5)
  </action>
  <verify>python -c "from config import defaultConfig; assert 'activeProject' in defaultConfig; assert 'wipLimit' in defaultConfig; print('Config OK')"</verify>
  <done>config.py has 5 new SDLC config keys. Import and assertion pass.</done>
</task>

<task type="auto">
  <name>Add helper functions for common queries</name>
  <files>database.py</files>
  <action>
    Add the following convenience functions that will be widely used across cogs:

    1. `async def getActiveProject(guildId):`
       ```python
       async def getActiveProject(guildId):
           projectId = await getConfig(guildId, "activeProject")
           if not projectId:
               return None
           return await getProject(int(projectId))
       ```

    2. `async def setActiveProject(guildId, projectId):`
       ```python
       async def setActiveProject(guildId, projectId):
           await setConfig(guildId, "activeProject", str(projectId))
       ```

    3. `async def getTaskCounts(guildId, projectId):`
       - Returns dict of status → count for all tasks in project
       ```python
       async def getTaskCounts(guildId, projectId):
           async with pool.acquire() as conn:
               rows = await conn.fetch("""
                   SELECT status, COUNT(*) as count FROM tasks
                   WHERE guild_id = $1 AND project_id = $2
                   GROUP BY status
               """, str(guildId), int(projectId))
               return {row['status']: row['count'] for row in rows}
       ```

    4. `async def getBugCounts(guildId, projectId):`
       - Same pattern for bugs by severity
       ```python
       async def getBugCounts(guildId, projectId):
           async with pool.acquire() as conn:
               rows = await conn.fetch("""
                   SELECT severity, COUNT(*) as count FROM bugs
                   WHERE guild_id = $1 AND project_id = $2 AND status != 'closed'
                   GROUP BY severity
               """, str(guildId), int(projectId))
               return {row['severity']: row['count'] for row in rows}
       ```

    5. `async def getUserWorkload(guildId, userId):`
       - Returns dict with task_count and bug_count for user
       ```python
       async def getUserWorkload(guildId, userId):
           async with pool.acquire() as conn:
               taskCount = await conn.fetchval("""
                   SELECT COUNT(*) FROM tasks
                   WHERE guild_id = $1 AND assignee_id = $2 AND status NOT IN ('done', 'backlog')
               """, str(guildId), str(userId))
               bugCount = await conn.fetchval("""
                   SELECT COUNT(*) FROM bugs
                   WHERE guild_id = $1 AND assignee_id = $2 AND status NOT IN ('closed')
               """, str(guildId), str(userId))
               return {'tasks': taskCount or 0, 'bugs': bugCount or 0}
       ```

    Place these AFTER the audit log functions, at the very end of the file.
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>5 helper functions added. getActiveProject, setActiveProject, getTaskCounts, getBugCounts, getUserWorkload all present.</done>
</task>

<task type="checkpoint:human-verify">
  <name>Verify database tables create successfully</name>
  <files>database.py, main.py</files>
  <action>
    Run the bot locally (or a test script) to ensure all new tables are created without errors.

    Verification approach:
    1. Check database.py parses: `python -c "import ast; ast.parse(open('database.py').read())"`
    2. Check all imports resolve: `python -c "from database import createProject, createTask, createBug, setTeamRole, createChecklist, logAudit, getActiveProject"`
    3. If possible, run `python main.py` briefly to confirm initDb() creates all tables

    If running the bot isn't feasible locally, verify by:
    - Confirming SQL syntax is valid
    - Confirming all function signatures are correct
    - Confirming no circular imports
  </action>
  <verify>python -c "from database import createProject, getProject, getProjects, deleteProject, createSprint, getSprints, updateSprintStatus, getActiveSprint, createTask, getTask, updateTaskStatus, assignTask, getTasks, deleteTask, createBug, getBug, updateBugStatus, assignBug, getBugs, closeBug, setTeamRole, removeTeamRole, getTeamRole, getTeamMembers, hasTeamPermission, createChecklist, getChecklist, getChecklists, archiveChecklist, addChecklistItem, toggleChecklistItem, removeChecklistItem, getChecklistItems, addTaskComment, getTaskComments, linkTaskBug, unlinkTaskBug, getLinkedBugs, getLinkedTasks, logAudit, getAuditLog, getActiveProject, setActiveProject, getTaskCounts, getBugCounts, getUserWorkload; print('All 45 functions importable ✓')"</verify>
  <done>All new database functions are importable. SQL syntax is valid. Bot starts without errors (if tested). Phase 1 complete.</done>
</task>

## Success Criteria
- [ ] config.py has 5 new SDLC config keys
- [ ] 5 helper/convenience functions added to database.py
- [ ] All 45 new functions are importable without errors
- [ ] No circular imports
- [ ] Existing bot functionality is not broken (all original functions still work)
- [ ] Full syntax validation passes

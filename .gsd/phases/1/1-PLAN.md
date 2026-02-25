---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Core Entity Tables (Projects, Sprints, Tasks, Bugs)

## Objective
Create the 4 primary entity tables that form the backbone of the SDLC system. These tables hold projects, sprints, tasks, and bugs. All subsequent features depend on these existing.

## Context
- `.gsd/SPEC.md` — Section 6 (Data Model)
- `database.py` — Existing `initDb()` function (lines 10-106), existing CRUD pattern
- `config.py` — `defaultConfig` dict pattern

## Tasks

<task type="auto">
  <name>Create core entity tables in initDb()</name>
  <files>database.py</files>
  <action>
    Add 4 new CREATE TABLE IF NOT EXISTS statements inside the `async with pool.acquire() as conn:` block in `initDb()` (after line 100, before line 102):

    1. **projects** table:
       ```sql
       CREATE TABLE IF NOT EXISTS projects (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           name TEXT NOT NULL,
           description TEXT DEFAULT '',
           created_at BIGINT NOT NULL,
           UNIQUE(guild_id, name)
       );
       ```

    2. **sprints** table:
       ```sql
       CREATE TABLE IF NOT EXISTS sprints (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
           name TEXT NOT NULL,
           start_date BIGINT,
           end_date BIGINT,
           status TEXT DEFAULT 'planning',
           created_at BIGINT NOT NULL
       );
       ```

    3. **tasks** table:
       ```sql
       CREATE TABLE IF NOT EXISTS tasks (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
           sprint_id INTEGER REFERENCES sprints(id) ON DELETE SET NULL,
           title TEXT NOT NULL,
           description TEXT DEFAULT '',
           status TEXT DEFAULT 'backlog',
           priority TEXT DEFAULT 'medium',
           assignee_id TEXT,
           creator_id TEXT NOT NULL,
           created_at BIGINT NOT NULL,
           updated_at BIGINT NOT NULL
       );
       ```

    4. **bugs** table:
       ```sql
       CREATE TABLE IF NOT EXISTS bugs (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
           title TEXT NOT NULL,
           description TEXT DEFAULT '',
           severity TEXT DEFAULT 'medium',
           status TEXT DEFAULT 'new',
           assignee_id TEXT,
           reporter_id TEXT NOT NULL,
           tags TEXT DEFAULT '[]',
           created_at BIGINT NOT NULL,
           updated_at BIGINT NOT NULL
       );
       ```

    **IMPORTANT:**
    - Follow the exact same `await conn.execute("""...""")` pattern used for existing tables (e.g., lines 46-53)
    - Use TEXT for all Discord IDs (guild_id, user_id) — consistent with existing pattern
    - Use BIGINT for timestamps — consistent with existing `warnings` table
    - Use SERIAL PRIMARY KEY — consistent with existing `warnings` table
    - Do NOT alter any existing table definitions
    - Place new tables AFTER the `exempt_channels` table (after line 100)
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>database.py contains CREATE TABLE statements for projects, sprints, tasks, bugs — all with correct foreign keys and constraints. File parses without syntax errors.</done>
</task>

<task type="auto">
  <name>Create CRUD functions for projects</name>
  <files>database.py</files>
  <action>
    Add the following async functions at the END of database.py (after the existing `hasCommandPerm` function). Follow the exact same pattern as existing functions (use `pool.acquire()`, parameterized queries, return dicts/lists):

    1. `async def createProject(guildId, name, description, createdAt):`
       - INSERT INTO projects, RETURNING id
       - Return the new project id

    2. `async def getProject(projectId):`
       - SELECT * FROM projects WHERE id = $1
       - Return dict or None

    3. `async def getProjects(guildId):`
       - SELECT * FROM projects WHERE guild_id = $1 ORDER BY created_at DESC
       - Return list of dicts

    4. `async def deleteProject(projectId):`
       - DELETE FROM projects WHERE id = $1
       - CASCADE will handle related sprints/tasks/bugs

    5. `async def createSprint(guildId, projectId, name, startDate, endDate, createdAt):`
       - INSERT INTO sprints, RETURNING id

    6. `async def getSprints(guildId, projectId):`
       - SELECT * FROM sprints WHERE guild_id = $1 AND project_id = $2 ORDER BY created_at DESC

    7. `async def updateSprintStatus(sprintId, status):`
       - UPDATE sprints SET status = $2 WHERE id = $1

    8. `async def getActiveSprint(guildId, projectId):`
       - SELECT * FROM sprints WHERE guild_id = $1 AND project_id = $2 AND status = 'active' LIMIT 1

    **Pattern to follow (from existing code):**
    ```python
    async def createProject(guildId, name, description, createdAt):
        async with pool.acquire() as conn:
            row = await conn.fetchval("""
                INSERT INTO projects (guild_id, name, description, created_at)
                VALUES ($1, $2, $3, $4) RETURNING id
            """, str(guildId), name, description, int(createdAt))
            return row
    ```

    **AVOID:**
    - Do NOT use `fetchrow` to return raw Record — convert to dict with `dict(row)` when returning single rows
    - Do NOT forget `str(guildId)` casting — all existing code does this
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>database.py contains 8 new functions for projects and sprints CRUD. All functions use the pool.acquire() pattern. File parses without errors.</done>
</task>

<task type="auto">
  <name>Create CRUD functions for tasks and bugs</name>
  <files>database.py</files>
  <action>
    Add the following async functions AFTER the project/sprint functions:

    **Task CRUD:**

    1. `async def createTask(guildId, projectId, sprintId, title, description, priority, assigneeId, creatorId, createdAt):`
       - INSERT INTO tasks, RETURNING id

    2. `async def getTask(taskId):`
       - SELECT * FROM tasks WHERE id = $1
       - Return dict or None

    3. `async def updateTaskStatus(taskId, status, updatedAt):`
       - UPDATE tasks SET status = $2, updated_at = $3 WHERE id = $1

    4. `async def assignTask(taskId, assigneeId, updatedAt):`
       - UPDATE tasks SET assignee_id = $2, updated_at = $3 WHERE id = $1

    5. `async def getTasks(guildId, projectId, filters=None):`
       - Base query: SELECT * FROM tasks WHERE guild_id = $1 AND project_id = $2
       - Optional filters dict: status, priority, assignee_id, sprint_id
       - Build WHERE clauses dynamically
       - ORDER BY created_at DESC
       - Return list of dicts

    6. `async def deleteTask(taskId):`
       - DELETE FROM tasks WHERE id = $1

    **Bug CRUD:**

    7. `async def createBug(guildId, projectId, title, description, severity, reporterId, tags, createdAt):`
       - INSERT INTO bugs, RETURNING id

    8. `async def getBug(bugId):`
       - SELECT * FROM bugs WHERE id = $1

    9. `async def updateBugStatus(bugId, status, updatedAt):`
       - UPDATE bugs SET status = $2, updated_at = $3 WHERE id = $1

    10. `async def assignBug(bugId, assigneeId, updatedAt):`
        - UPDATE bugs SET assignee_id = $2, updated_at = $3 WHERE id = $1

    11. `async def getBugs(guildId, projectId, filters=None):`
        - Same dynamic filter pattern as getTasks

    12. `async def closeBug(bugId, updatedAt):`
        - UPDATE bugs SET status = 'closed', updated_at = $2 WHERE id = $1

    **For dynamic filters in getTasks/getBugs, use this pattern:**
    ```python
    async def getTasks(guildId, projectId, filters=None):
        async with pool.acquire() as conn:
            query = "SELECT * FROM tasks WHERE guild_id = $1 AND project_id = $2"
            params = [str(guildId), int(projectId)]
            idx = 3
            if filters:
                if 'status' in filters:
                    query += f" AND status = ${idx}"
                    params.append(filters['status'])
                    idx += 1
                if 'priority' in filters:
                    query += f" AND priority = ${idx}"
                    params.append(filters['priority'])
                    idx += 1
                if 'assignee_id' in filters:
                    query += f" AND assignee_id = ${idx}"
                    params.append(str(filters['assignee_id']))
                    idx += 1
                if 'sprint_id' in filters:
                    query += f" AND sprint_id = ${idx}"
                    params.append(int(filters['sprint_id']))
                    idx += 1
            query += " ORDER BY created_at DESC"
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    ```
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>database.py contains 12 new functions for task and bug CRUD. Dynamic filtering works for getTasks and getBugs. File parses without errors.</done>
</task>

## Success Criteria
- [ ] database.py contains CREATE TABLE for: projects, sprints, tasks, bugs
- [ ] Foreign keys: sprints→projects, tasks→projects, tasks→sprints, bugs→projects
- [ ] 8 project/sprint CRUD functions exist
- [ ] 12 task/bug CRUD functions exist
- [ ] All functions follow existing pool.acquire() pattern
- [ ] `python -c "import ast; ast.parse(open('database.py').read())"` passes

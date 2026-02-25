---
phase: 1
plan: 2
wave: 1
---

# Plan 1.2: Supporting Tables (Team Roles, Checklists, Comments, Links)

## Objective
Create the supporting entity tables that enable team management, checklists, task comments, and cross-linking between tasks and bugs. These complement the core entities from Plan 1.1.

## Context
- `.gsd/SPEC.md` — Section 6 (Data Model)
- `database.py` — After Plan 1.1 has added core tables and CRUD functions
- `.gsd/phases/1/1-PLAN.md` — Core tables already created

## Tasks

<task type="auto">
  <name>Create supporting tables in initDb()</name>
  <files>database.py</files>
  <action>
    Add 5 new CREATE TABLE statements in `initDb()`, AFTER the bugs table (added in Plan 1.1):

    1. **team_roles** table:
       ```sql
       CREATE TABLE IF NOT EXISTS team_roles (
           guild_id TEXT NOT NULL,
           user_id TEXT NOT NULL,
           role TEXT NOT NULL DEFAULT 'viewer',
           PRIMARY KEY (guild_id, user_id)
       );
       ```
       Role values: 'admin', 'lead', 'developer', 'qa', 'viewer'

    2. **checklists** table:
       ```sql
       CREATE TABLE IF NOT EXISTS checklists (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
           name TEXT NOT NULL,
           created_by TEXT NOT NULL,
           archived BOOLEAN DEFAULT FALSE,
           created_at BIGINT NOT NULL
       );
       ```

    3. **checklist_items** table:
       ```sql
       CREATE TABLE IF NOT EXISTS checklist_items (
           id SERIAL PRIMARY KEY,
           checklist_id INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
           text TEXT NOT NULL,
           completed BOOLEAN DEFAULT FALSE,
           toggled_by TEXT,
           toggled_at BIGINT
       );
       ```

    4. **task_comments** table:
       ```sql
       CREATE TABLE IF NOT EXISTS task_comments (
           id SERIAL PRIMARY KEY,
           task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
           user_id TEXT NOT NULL,
           content TEXT NOT NULL,
           created_at BIGINT NOT NULL
       );
       ```

    5. **task_bug_links** table:
       ```sql
       CREATE TABLE IF NOT EXISTS task_bug_links (
           task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
           bug_id INTEGER REFERENCES bugs(id) ON DELETE CASCADE,
           PRIMARY KEY (task_id, bug_id)
       );
       ```

    6. **audit_log** table:
       ```sql
       CREATE TABLE IF NOT EXISTS audit_log (
           id SERIAL PRIMARY KEY,
           guild_id TEXT NOT NULL,
           action TEXT NOT NULL,
           entity_type TEXT NOT NULL,
           entity_id INTEGER,
           user_id TEXT NOT NULL,
           details TEXT DEFAULT '',
           created_at BIGINT NOT NULL
       );
       ```

    **Pattern:** Same `await conn.execute("""...""")` as all other tables.
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>database.py contains CREATE TABLE for: team_roles, checklists, checklist_items, task_comments, task_bug_links, audit_log. All foreign keys reference correct parent tables.</done>
</task>

<task type="auto">
  <name>Create CRUD functions for team_roles</name>
  <files>database.py</files>
  <action>
    Add the following async functions for team role management. These control SDLC permissions:

    1. `async def setTeamRole(guildId, userId, role):`
       - UPSERT into team_roles (INSERT ... ON CONFLICT (guild_id, user_id) DO UPDATE SET role = $3)
       - Validate role is one of: 'admin', 'lead', 'developer', 'qa', 'viewer'

    2. `async def removeTeamRole(guildId, userId):`
       - DELETE FROM team_roles WHERE guild_id = $1 AND user_id = $2

    3. `async def getTeamRole(guildId, userId):`
       - SELECT role FROM team_roles WHERE guild_id = $1 AND user_id = $2
       - Return role string or None (None means no SDLC role assigned)

    4. `async def getTeamMembers(guildId, role=None):`
       - If role is None: SELECT * FROM team_roles WHERE guild_id = $1
       - If role specified: add AND role = $2
       - Return list of dicts with user_id and role

    5. `async def hasTeamPermission(guildId, userId, requiredRole):`
       - Get user's role, check against hierarchy
       - Hierarchy: admin > lead > developer > qa > viewer
       - Return True if user's role >= requiredRole
       - Implementation:
       ```python
       ROLE_HIERARCHY = {'admin': 5, 'lead': 4, 'developer': 3, 'qa': 2, 'viewer': 1}

       async def hasTeamPermission(guildId, userId, requiredRole):
           userRole = await getTeamRole(guildId, userId)
           if userRole is None:
               return False
           return ROLE_HIERARCHY.get(userRole, 0) >= ROLE_HIERARCHY.get(requiredRole, 0)
       ```

    **Place the ROLE_HIERARCHY constant near the top of the file (after imports, before pool = None) or right before hasTeamPermission.**
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>5 team role functions exist. ROLE_HIERARCHY constant defined. hasTeamPermission correctly checks hierarchy.</done>
</task>

<task type="auto">
  <name>Create CRUD functions for checklists, comments, links, and audit log</name>
  <files>database.py</files>
  <action>
    Add remaining CRUD functions:

    **Checklist CRUD:**
    1. `async def createChecklist(guildId, name, createdBy, taskId, createdAt):`
       - INSERT INTO checklists, RETURNING id (taskId can be None)

    2. `async def getChecklist(checklistId):`
       - SELECT * FROM checklists WHERE id = $1, return dict or None

    3. `async def getChecklists(guildId, archived=False):`
       - SELECT * FROM checklists WHERE guild_id = $1 AND archived = $2

    4. `async def archiveChecklist(checklistId):`
       - UPDATE checklists SET archived = TRUE WHERE id = $1

    5. `async def addChecklistItem(checklistId, text):`
       - INSERT INTO checklist_items, RETURNING id

    6. `async def toggleChecklistItem(itemId, userId, toggledAt):`
       - UPDATE checklist_items SET completed = NOT completed, toggled_by = $2, toggled_at = $3 WHERE id = $1
       - Return the new completed state

    7. `async def removeChecklistItem(itemId):`
       - DELETE FROM checklist_items WHERE id = $1

    8. `async def getChecklistItems(checklistId):`
       - SELECT * FROM checklist_items WHERE checklist_id = $1 ORDER BY id ASC
       - Return list of dicts

    **Comment CRUD:**
    9. `async def addTaskComment(taskId, userId, content, createdAt):`
       - INSERT INTO task_comments, RETURNING id

    10. `async def getTaskComments(taskId):`
        - SELECT * FROM task_comments WHERE task_id = $1 ORDER BY created_at ASC

    **Link CRUD:**
    11. `async def linkTaskBug(taskId, bugId):`
        - INSERT INTO task_bug_links ... ON CONFLICT DO NOTHING

    12. `async def unlinkTaskBug(taskId, bugId):`
        - DELETE FROM task_bug_links WHERE task_id = $1 AND bug_id = $2

    13. `async def getLinkedBugs(taskId):`
        - SELECT bug_id FROM task_bug_links WHERE task_id = $1
        - Return list of bug IDs

    14. `async def getLinkedTasks(bugId):`
        - SELECT task_id FROM task_bug_links WHERE bug_id = $1
        - Return list of task IDs

    **Audit Log:**
    15. `async def logAudit(guildId, action, entityType, entityId, userId, details, createdAt):`
        - INSERT INTO audit_log

    16. `async def getAuditLog(guildId, entityType=None, entityId=None, limit=50):`
        - SELECT * FROM audit_log WHERE guild_id = $1
        - Optional filters for entity_type and entity_id
        - ORDER BY created_at DESC LIMIT $N
        - Return list of dicts

    **Follow the exact same code style as existing CRUD functions.**
  </action>
  <verify>python -c "import ast; ast.parse(open('database.py').read()); print('Syntax OK')"</verify>
  <done>16 new functions for checklists (8), comments (2), links (4), and audit log (2). All follow pool.acquire() pattern.</done>
</task>

## Success Criteria
- [ ] database.py contains CREATE TABLE for: team_roles, checklists, checklist_items, task_comments, task_bug_links, audit_log
- [ ] 5 team role functions exist including hasTeamPermission with hierarchy check
- [ ] 8 checklist functions exist
- [ ] 2 comment functions exist
- [ ] 4 link functions exist
- [ ] 2 audit log functions exist
- [ ] ROLE_HIERARCHY constant defined
- [ ] `python -c "import ast; ast.parse(open('database.py').read())"` passes

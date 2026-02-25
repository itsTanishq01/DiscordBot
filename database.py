import os
import asyncpg
import json
import asyncio
import ssl
from config import defaultConfig

pool = None

ROLE_HIERARCHY = {'admin': 5, 'lead': 4, 'developer': 3, 'qa': 2, 'viewer': 1}

async def initDb():
    global pool
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("WARNING: DATABASE_URL is not set! Database functions will fail.")
        return False

    try:
        for attempt in range(5):
            try:
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                
                print(f"Connecting to Database (Attempt {attempt+1}/5)...")
                pool = await asyncpg.create_pool(db_url, ssl=ssl_ctx, command_timeout=30, statement_cache_size=0)
                print("Connected to Supabase/PostgreSQL!")
                break # Success
            except OSError as e:
                print(f"Network Error (Attempt {attempt+1}): {e}")
                if "Network is unreachable" in str(e) or (hasattr(e, 'errno') and e.errno == 101):
                    print("CRITICAL: Network execution failed. If using Supabase, you MUST use the Connection Pooler (Session Mode, port 5432) or Transaction Mode (port 6543) URL.")
                    print("Direct connection (db.project.supabase.co) does not support IPv4 on free tier.")
                if attempt == 4: raise e
                wait = 5 * (attempt + 1)
                print(f"Retrying in {wait}s...")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"Connection attempt {attempt+1} failed: {e}")
                print(f"Exception type: {type(e).__name__}")
                if attempt == 4: raise e
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s, 20s backoff
                print(f"Retrying in {wait}s...")
                await asyncio.sleep(wait)

        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    guild_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (guild_id, key)
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT,
                    user_id TEXT,
                    moderator_id TEXT,
                    reason TEXT,
                    timestamp BIGINT
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    guild_id TEXT,
                    command TEXT,
                    role_id TEXT,
                    PRIMARY KEY (guild_id, command, role_id)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS exemptions (
                    guild_id TEXT,
                    rule TEXT,
                    role_id TEXT,
                    PRIMARY KEY (guild_id, rule, role_id)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS filters (
                    guild_id TEXT,
                    type TEXT,
                    item TEXT,
                    PRIMARY KEY (guild_id, type, item)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS exempt_channels (
                    guild_id TEXT,
                    rule TEXT,
                    channel_id TEXT,
                    PRIMARY KEY (guild_id, rule, channel_id)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    guild_seq INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at BIGINT NOT NULL,
                    UNIQUE(guild_id, name),
                    UNIQUE(guild_id, guild_seq)
                );
            """)

            await conn.execute("""
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
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    guild_seq INTEGER NOT NULL,
                    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'backlog',
                    priority TEXT DEFAULT 'medium',
                    assignee_id TEXT,
                    creator_id TEXT NOT NULL,
                    created_at BIGINT NOT NULL,
                    updated_at BIGINT NOT NULL,
                    UNIQUE(guild_id, guild_seq)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bugs (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    guild_seq INTEGER NOT NULL,
                    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    severity TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'new',
                    assignee_id TEXT,
                    reporter_id TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    created_at BIGINT NOT NULL,
                    updated_at BIGINT NOT NULL,
                    UNIQUE(guild_id, guild_seq)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS team_roles (
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS checklists (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    guild_seq INTEGER NOT NULL,
                    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                    name TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    archived BOOLEAN DEFAULT FALSE,
                    created_at BIGINT NOT NULL,
                    UNIQUE(guild_id, guild_seq)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS checklist_items (
                    id SERIAL PRIMARY KEY,
                    checklist_id INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    toggled_by TEXT,
                    toggled_at BIGINT
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS task_comments (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at BIGINT NOT NULL
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS task_bug_links (
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    bug_id INTEGER REFERENCES bugs(id) ON DELETE CASCADE,
                    PRIMARY KEY (task_id, bug_id)
                );
            """)

            await conn.execute("""
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
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS guild_counters (
                    guild_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    next_seq INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (guild_id, entity_type)
                );
            """)

            # ── Migrations: add guild_seq to existing tables ──
            for table in ['projects', 'tasks', 'bugs', 'checklists']:
                col_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = $1 AND column_name = 'guild_seq'
                    )
                """, table)
                if not col_exists:
                    print(f"[Migration] Adding guild_seq to {table}...")
                    await conn.execute(f"ALTER TABLE {table} ADD COLUMN guild_seq INTEGER")

                    # Backfill: assign per-guild sequential IDs to existing rows
                    rows = await conn.fetch(f"""
                        SELECT id, guild_id FROM {table} ORDER BY guild_id, id
                    """)
                    guild_counters = {}
                    for row in rows:
                        gid = row['guild_id']
                        guild_counters[gid] = guild_counters.get(gid, 0) + 1
                        await conn.execute(f"UPDATE {table} SET guild_seq = $1 WHERE id = $2",
                                           guild_counters[gid], row['id'])

                    # Set NOT NULL after backfill
                    await conn.execute(f"ALTER TABLE {table} ALTER COLUMN guild_seq SET NOT NULL")

                    # Add UNIQUE constraint
                    try:
                        await conn.execute(f"""
                            ALTER TABLE {table} ADD CONSTRAINT {table}_guild_seq_unique
                            UNIQUE (guild_id, guild_seq)
                        """)
                    except Exception:
                        pass  # constraint may already exist

                    # Seed counters
                    entity_type = table.rstrip('s')  # projects -> project, tasks -> task, etc.
                    for gid, count in guild_counters.items():
                        await conn.execute("""
                            INSERT INTO guild_counters (guild_id, entity_type, next_seq)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (guild_id, entity_type)
                            DO UPDATE SET next_seq = GREATEST(guild_counters.next_seq, $3)
                        """, gid, entity_type, count)

                    print(f"[Migration] {table}: migrated {len(rows)} rows across {len(guild_counters)} guilds")

            # Remove sprint_id from tasks if it exists (sprints removed)
            sprint_col = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'sprint_id'
                )
            """)
            if sprint_col:
                try:
                    await conn.execute("ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_sprint_id_fkey")
                    await conn.execute("ALTER TABLE tasks DROP COLUMN sprint_id")
                    print("[Migration] Removed sprint_id column from tasks")
                except Exception as e:
                    print(f"[Migration] Note: Could not remove sprint_id: {e}")

        return True

    except Exception as e:
        print(f"Failed to connect to Database: {e}")
        return False

async def getConfig(guildId, key):
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT value FROM config WHERE guild_id = $1 AND key = $2", str(guildId), key)
        return val

async def setConfig(guildId, key, value):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO config (guild_id, key, value) 
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, key) 
            DO UPDATE SET value = $3
        """, str(guildId), key, str(value))

async def getAllConfig(guildId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT key, value FROM config WHERE guild_id = $1", str(guildId))
        return {row['key']: row['value'] for row in rows}

async def initDefaults(guildId):
    current = await getAllConfig(guildId)
    updates = []
    for key, val in defaultConfig.items():
        if key not in current:
            updates.append((str(guildId), key, val))
    
    if updates:
        async with pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO config (guild_id, key, value) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
            """, updates)

async def addExemptRole(guildId, ruleType, roleId):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO exemptions (guild_id, rule, role_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
        """, str(guildId), ruleType, str(roleId))

async def removeExemptRole(guildId, ruleType, roleId):
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM exemptions WHERE guild_id = $1 AND rule = $2 AND role_id = $3
        """, str(guildId), ruleType, str(roleId))

async def getExemptRoles(guildId, ruleType):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT role_id FROM exemptions WHERE guild_id = $1 AND rule = $2", str(guildId), ruleType)
        return [row['role_id'] for row in rows]

async def isRoleExempt(guildId, ruleType, memberRoles):
    exemptData = await getExemptRoles(guildId, ruleType)
    if not exemptData: return False
    
    for role in memberRoles:
        if str(role.id) in exemptData:
            return True
    return False

async def addExemptChannel(guildId, ruleType, channelId):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO exempt_channels (guild_id, rule, channel_id) 
            VALUES ($1, $2, $3) 
            ON CONFLICT DO NOTHING
        """, str(guildId), ruleType, str(channelId))

async def removeExemptChannel(guildId, ruleType, channelId):
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM exempt_channels 
            WHERE guild_id = $1 AND rule = $2 AND channel_id = $3
        """, str(guildId), ruleType, str(channelId))

async def getExemptChannels(guildId, ruleType):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT channel_id FROM exempt_channels 
            WHERE guild_id = $1 AND rule = $2
        """, str(guildId), ruleType)
        return [row['channel_id'] for row in rows]

async def isChannelExempt(guildId, ruleType, channelId):
    exemptChannels = await getExemptChannels(guildId, ruleType)
    return str(channelId) in exemptChannels

async def addBannedWord(guildId, word):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO filters (guild_id, type, item) VALUES ($1, 'banned_word', $2) ON CONFLICT DO NOTHING", str(guildId), word.lower())

async def removeBannedWord(guildId, word):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM filters WHERE guild_id = $1 AND type = 'banned_word' AND item = $2", str(guildId), word.lower())

async def getBannedWords(guildId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT item FROM filters WHERE guild_id = $1 AND type = 'banned_word'", str(guildId))
        return [row['item'] for row in rows]

async def addWhitelistDomain(guildId, domain):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO filters (guild_id, type, item) VALUES ($1, 'whitelist_domain', $2) ON CONFLICT DO NOTHING", str(guildId), domain.lower())

async def removeWhitelistDomain(guildId, domain):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM filters WHERE guild_id = $1 AND type = 'whitelist_domain' AND item = $2", str(guildId), domain.lower())

async def getWhitelistDomains(guildId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT item FROM filters WHERE guild_id = $1 AND type = 'whitelist_domain'", str(guildId))
        return [row['item'] for row in rows]

async def addWarning(guildId, userId, moderatorId, reason, timestamp):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
            VALUES ($1, $2, $3, $4, $5)
        """, str(guildId), str(userId), str(moderatorId), reason, int(timestamp))

async def getWarnings(guildId, userId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT moderator_id, reason, timestamp FROM warnings 
            WHERE guild_id = $1 AND user_id = $2 
            ORDER BY timestamp DESC
        """, str(guildId), str(userId))
        return [(row['moderator_id'], row['reason'], row['timestamp']) for row in rows]

async def clearWarnings(guildId, userId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM warnings WHERE guild_id = $1 AND user_id = $2", str(guildId), str(userId))

async def addCommandPerm(guildId, command, roleId):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO permissions (guild_id, command, role_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING", str(guildId), command, str(roleId))

async def removeCommandPerm(guildId, command, roleId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM permissions WHERE guild_id = $1 AND command = $2 AND role_id = $3", str(guildId), command, str(roleId))

async def getCommandPerms(guildId, command):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT role_id FROM permissions WHERE guild_id = $1 AND command = $2", str(guildId), command)
        return [row['role_id'] for row in rows]

async def hasCommandPerm(guildId, command, userRoles):
    allowed_roles = await getCommandPerms(guildId, command)
    if not allowed_roles: return None 
    
    for role in userRoles:
        if str(role.id) in allowed_roles:
            return True
    return False

# ─────────────────────────────────────────────
# Project CRUD
# ─────────────────────────────────────────────

async def nextGuildSeq(conn, guildId, entityType):
    """Atomically get and increment the next per-guild sequence number for an entity type."""
    row = await conn.fetchval("""
        INSERT INTO guild_counters (guild_id, entity_type, next_seq)
        VALUES ($1, $2, 1)
        ON CONFLICT (guild_id, entity_type)
        DO UPDATE SET next_seq = guild_counters.next_seq + 1
        RETURNING next_seq
    """, str(guildId), entityType)
    return row

async def createProject(guildId, name, description, createdAt):
    async with pool.acquire() as conn:
        seq = await nextGuildSeq(conn, guildId, 'project')
        await conn.execute("""
            INSERT INTO projects (guild_id, guild_seq, name, description, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, str(guildId), seq, name, description, int(createdAt))
        return seq

async def getProject(guildId, guildSeq):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM projects WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))
        return dict(row) if row else None

async def getProjectById(projectId):
    """Get project by internal ID (for FK lookups)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM projects WHERE id = $1", int(projectId))
        return dict(row) if row else None

async def getProjects(guildId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM projects WHERE guild_id = $1 ORDER BY created_at DESC", str(guildId))
        return [dict(row) for row in rows]

async def deleteProject(guildId, guildSeq):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM projects WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))

# ─────────────────────────────────────────────
# Sprint CRUD
# ─────────────────────────────────────────────

async def createSprint(guildId, projectId, name, startDate, endDate, createdAt):
    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            INSERT INTO sprints (guild_id, project_id, name, start_date, end_date, created_at)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """, str(guildId), int(projectId), name, int(startDate) if startDate else None, int(endDate) if endDate else None, int(createdAt))
        return row

async def getSprints(guildId, projectId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM sprints WHERE guild_id = $1 AND project_id = $2 ORDER BY created_at DESC
        """, str(guildId), int(projectId))
        return [dict(row) for row in rows]

async def updateSprintStatus(sprintId, status):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE sprints SET status = $2 WHERE id = $1", int(sprintId), status)

async def getActiveSprint(guildId, projectId):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM sprints WHERE guild_id = $1 AND project_id = $2 AND status = 'active' LIMIT 1
        """, str(guildId), int(projectId))
        return dict(row) if row else None

# ─────────────────────────────────────────────
# Task CRUD
# ─────────────────────────────────────────────

async def createTask(guildId, projectId, title, description, priority, assigneeId, creatorId, createdAt):
    async with pool.acquire() as conn:
        seq = await nextGuildSeq(conn, guildId, 'task')
        await conn.execute("""
            INSERT INTO tasks (guild_id, guild_seq, project_id, title, description, priority, assignee_id, creator_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
        """, str(guildId), seq, int(projectId), title, description, priority, str(assigneeId) if assigneeId else None, str(creatorId), int(createdAt))
        return seq

async def getTask(guildId, guildSeq):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))
        return dict(row) if row else None

async def updateTaskStatus(guildId, guildSeq, status, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET status = $3, updated_at = $4 WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq), status, int(updatedAt))

async def assignTask(guildId, guildSeq, assigneeId, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET assignee_id = $3, updated_at = $4 WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq), str(assigneeId), int(updatedAt))

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

async def deleteTask(guildId, guildSeq):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM tasks WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))

# ─────────────────────────────────────────────
# Bug CRUD
# ─────────────────────────────────────────────

async def createBug(guildId, projectId, title, description, severity, reporterId, tags, createdAt):
    async with pool.acquire() as conn:
        seq = await nextGuildSeq(conn, guildId, 'bug')
        await conn.execute("""
            INSERT INTO bugs (guild_id, guild_seq, project_id, title, description, severity, reporter_id, tags, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
        """, str(guildId), seq, int(projectId), title, description, severity, str(reporterId), json.dumps(tags) if isinstance(tags, list) else tags, int(createdAt))
        return seq

async def getBug(guildId, guildSeq):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM bugs WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))
        return dict(row) if row else None

async def updateBugStatus(guildId, guildSeq, status, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET status = $3, updated_at = $4 WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq), status, int(updatedAt))

async def assignBug(guildId, guildSeq, assigneeId, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET assignee_id = $3, updated_at = $4 WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq), str(assigneeId), int(updatedAt))

async def getBugs(guildId, projectId, filters=None):
    async with pool.acquire() as conn:
        query = "SELECT * FROM bugs WHERE guild_id = $1 AND project_id = $2"
        params = [str(guildId), int(projectId)]
        idx = 3
        if filters:
            if 'status' in filters:
                query += f" AND status = ${idx}"
                params.append(filters['status'])
                idx += 1
            if 'severity' in filters:
                query += f" AND severity = ${idx}"
                params.append(filters['severity'])
                idx += 1
            if 'assignee_id' in filters:
                query += f" AND assignee_id = ${idx}"
                params.append(str(filters['assignee_id']))
                idx += 1
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

async def closeBug(guildId, guildSeq, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET status = 'closed', updated_at = $3 WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq), int(updatedAt))

# ─────────────────────────────────────────────
# Team Role CRUD
# ─────────────────────────────────────────────

VALID_ROLES = {'admin', 'lead', 'developer', 'qa', 'viewer'}

async def setTeamRole(guildId, userId, role):
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of: {', '.join(sorted(VALID_ROLES))}")
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO team_roles (guild_id, user_id, role)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET role = $3
        """, str(guildId), str(userId), role)

async def removeTeamRole(guildId, userId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM team_roles WHERE guild_id = $1 AND user_id = $2", str(guildId), str(userId))

async def getTeamRole(guildId, userId):
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT role FROM team_roles WHERE guild_id = $1 AND user_id = $2", str(guildId), str(userId))
        return val

async def getTeamMembers(guildId, role=None):
    async with pool.acquire() as conn:
        if role:
            rows = await conn.fetch("SELECT user_id, role FROM team_roles WHERE guild_id = $1 AND role = $2", str(guildId), role)
        else:
            rows = await conn.fetch("SELECT user_id, role FROM team_roles WHERE guild_id = $1", str(guildId))
        return [dict(row) for row in rows]

async def hasTeamPermission(guildId, userId, requiredRole):
    userRole = await getTeamRole(guildId, userId)
    if userRole is None:
        return False
    return ROLE_HIERARCHY.get(userRole, 0) >= ROLE_HIERARCHY.get(requiredRole, 0)

# ─────────────────────────────────────────────
# Checklist CRUD
# ─────────────────────────────────────────────

async def createChecklist(guildId, name, createdBy, taskId, createdAt):
    async with pool.acquire() as conn:
        seq = await nextGuildSeq(conn, guildId, 'checklist')
        internalId = await conn.fetchval("""
            INSERT INTO checklists (guild_id, guild_seq, name, created_by, task_id, created_at)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """, str(guildId), seq, name, str(createdBy), int(taskId) if taskId else None, int(createdAt))
        return seq, internalId

async def getChecklist(guildId, guildSeq):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM checklists WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))
        return dict(row) if row else None

async def getChecklists(guildId, archived=False):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM checklists WHERE guild_id = $1 AND archived = $2 ORDER BY created_at DESC
        """, str(guildId), archived)
        return [dict(row) for row in rows]

async def archiveChecklist(guildId, guildSeq):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE checklists SET archived = TRUE WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(guildSeq))

async def addChecklistItem(checklistId, text):
    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            INSERT INTO checklist_items (checklist_id, text) VALUES ($1, $2) RETURNING id
        """, int(checklistId), text)
        return row

async def toggleChecklistItem(itemId, userId, toggledAt):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE checklist_items SET completed = NOT completed, toggled_by = $2, toggled_at = $3
            WHERE id = $1 RETURNING completed
        """, int(itemId), str(userId), int(toggledAt))
        return row['completed'] if row else None

async def removeChecklistItem(itemId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM checklist_items WHERE id = $1", int(itemId))

async def getChecklistItems(checklistId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM checklist_items WHERE checklist_id = $1 ORDER BY id ASC
        """, int(checklistId))
        return [dict(row) for row in rows]

# ─────────────────────────────────────────────
# Task Comment CRUD
# ─────────────────────────────────────────────

async def addTaskComment(guildId, taskGuildSeq, userId, content, createdAt):
    async with pool.acquire() as conn:
        # Get internal task ID from guild_seq
        taskId = await conn.fetchval("SELECT id FROM tasks WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(taskGuildSeq))
        if not taskId:
            return None
        row = await conn.fetchval("""
            INSERT INTO task_comments (task_id, user_id, content, created_at)
            VALUES ($1, $2, $3, $4) RETURNING id
        """, taskId, str(userId), content, int(createdAt))
        return row

async def getTaskComments(guildId, taskGuildSeq):
    async with pool.acquire() as conn:
        taskId = await conn.fetchval("SELECT id FROM tasks WHERE guild_id = $1 AND guild_seq = $2", str(guildId), int(taskGuildSeq))
        if not taskId:
            return []
        rows = await conn.fetch("""
            SELECT * FROM task_comments WHERE task_id = $1 ORDER BY created_at ASC
        """, taskId)
        return [dict(row) for row in rows]

# ─────────────────────────────────────────────
# Task-Bug Link CRUD
# ─────────────────────────────────────────────

async def linkTaskBug(taskId, bugId):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO task_bug_links (task_id, bug_id) VALUES ($1, $2) ON CONFLICT DO NOTHING
        """, int(taskId), int(bugId))

async def unlinkTaskBug(taskId, bugId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM task_bug_links WHERE task_id = $1 AND bug_id = $2", int(taskId), int(bugId))

async def getLinkedBugs(taskId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT bug_id FROM task_bug_links WHERE task_id = $1", int(taskId))
        return [row['bug_id'] for row in rows]

async def getLinkedTasks(bugId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT task_id FROM task_bug_links WHERE bug_id = $1", int(bugId))
        return [row['task_id'] for row in rows]

# ─────────────────────────────────────────────
# Audit Log CRUD
# ─────────────────────────────────────────────

async def logAudit(guildId, action, entityType, entityId, userId, details, createdAt):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO audit_log (guild_id, action, entity_type, entity_id, user_id, details, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, str(guildId), action, entityType, int(entityId) if entityId else None, str(userId), details, int(createdAt))

async def getAuditLog(guildId, entityType=None, entityId=None, limit=50):
    async with pool.acquire() as conn:
        query = "SELECT * FROM audit_log WHERE guild_id = $1"
        params = [str(guildId)]
        idx = 2
        if entityType:
            query += f" AND entity_type = ${idx}"
            params.append(entityType)
            idx += 1
        if entityId:
            query += f" AND entity_id = ${idx}"
            params.append(int(entityId))
            idx += 1
        query += f" ORDER BY created_at DESC LIMIT ${idx}"
        params.append(limit)
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

# ─────────────────────────────────────────────
# Helper / Convenience Functions
# ─────────────────────────────────────────────

async def getActiveProject(guildId):
    activeSeq = await getConfig(guildId, "activeProject")
    if not activeSeq:
        return None
    return await getProject(guildId, int(activeSeq))

async def setActiveProject(guildId, projectId):
    await setConfig(guildId, "activeProject", str(projectId))

async def getTaskCounts(guildId, projectId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT status, COUNT(*) as count FROM tasks
            WHERE guild_id = $1 AND project_id = $2
            GROUP BY status
        """, str(guildId), int(projectId))
        return {row['status']: row['count'] for row in rows}

async def getBugCounts(guildId, projectId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT severity, COUNT(*) as count FROM bugs
            WHERE guild_id = $1 AND project_id = $2 AND status != 'closed'
            GROUP BY severity
        """, str(guildId), int(projectId))
        return {row['severity']: row['count'] for row in rows}

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

import os
import asyncpg
import json
import asyncio
import ssl
from config import defaultConfig

pool = None

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
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at BIGINT NOT NULL,
                    UNIQUE(guild_id, name)
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
            """)

            await conn.execute("""
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
            """)

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

async def createProject(guildId, name, description, createdAt):
    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            INSERT INTO projects (guild_id, name, description, created_at)
            VALUES ($1, $2, $3, $4) RETURNING id
        """, str(guildId), name, description, int(createdAt))
        return row

async def getProject(projectId):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM projects WHERE id = $1", int(projectId))
        return dict(row) if row else None

async def getProjects(guildId):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM projects WHERE guild_id = $1 ORDER BY created_at DESC", str(guildId))
        return [dict(row) for row in rows]

async def deleteProject(projectId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM projects WHERE id = $1", int(projectId))

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

async def createTask(guildId, projectId, sprintId, title, description, priority, assigneeId, creatorId, createdAt):
    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            INSERT INTO tasks (guild_id, project_id, sprint_id, title, description, priority, assignee_id, creator_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9) RETURNING id
        """, str(guildId), int(projectId), int(sprintId) if sprintId else None, title, description, priority, str(assigneeId) if assigneeId else None, str(creatorId), int(createdAt))
        return row

async def getTask(taskId):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", int(taskId))
        return dict(row) if row else None

async def updateTaskStatus(taskId, status, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET status = $2, updated_at = $3 WHERE id = $1", int(taskId), status, int(updatedAt))

async def assignTask(taskId, assigneeId, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET assignee_id = $2, updated_at = $3 WHERE id = $1", int(taskId), str(assigneeId), int(updatedAt))

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

async def deleteTask(taskId):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM tasks WHERE id = $1", int(taskId))

# ─────────────────────────────────────────────
# Bug CRUD
# ─────────────────────────────────────────────

async def createBug(guildId, projectId, title, description, severity, reporterId, tags, createdAt):
    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            INSERT INTO bugs (guild_id, project_id, title, description, severity, reporter_id, tags, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8) RETURNING id
        """, str(guildId), int(projectId), title, description, severity, str(reporterId), json.dumps(tags) if isinstance(tags, list) else tags, int(createdAt))
        return row

async def getBug(bugId):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM bugs WHERE id = $1", int(bugId))
        return dict(row) if row else None

async def updateBugStatus(bugId, status, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET status = $2, updated_at = $3 WHERE id = $1", int(bugId), status, int(updatedAt))

async def assignBug(bugId, assigneeId, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET assignee_id = $2, updated_at = $3 WHERE id = $1", int(bugId), str(assigneeId), int(updatedAt))

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

async def closeBug(bugId, updatedAt):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bugs SET status = 'closed', updated_at = $2 WHERE id = $1", int(bugId), int(updatedAt))


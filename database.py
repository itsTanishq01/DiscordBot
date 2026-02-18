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
        # Retry loop for connection
        for attempt in range(5):
            try:
                # Create SSL context optimized for Windows/Supabase
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                
                print(f"Connecting to Database (Attempt {attempt+1}/5)...")
                pool = await asyncpg.create_pool(db_url, ssl=ssl_ctx, command_timeout=30)
                print("Connected to Supabase/PostgreSQL!")
                break # Success
            except Exception as e:
                print(f"Connection attempt {attempt+1} failed: {e}")
                print(f"Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                if attempt == 4: raise e
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s, 20s backoff
                print(f"Retrying in {wait}s...")
                await asyncio.sleep(wait)

        # Create Tables if not exist
        async with pool.acquire() as conn:
            # Config Table (Key-Value per Guild to mimic flexibility)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    guild_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (guild_id, key)
                );
            """)
            
            # Warnings Table
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

            # Permissions Table (Custom Command perms)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    guild_id TEXT,
                    command TEXT,
                    role_id TEXT,
                    PRIMARY KEY (guild_id, command, role_id)
                );
            """)

            # Exemptions Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS exemptions (
                    guild_id TEXT,
                    rule TEXT,
                    role_id TEXT,
                    PRIMARY KEY (guild_id, rule, role_id)
                );
            """)

            # Filters Table (Banned Words, whitelists, etc.)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS filters (
                    guild_id TEXT,
                    type TEXT,
                    item TEXT,
                    PRIMARY KEY (guild_id, type, item)
                );
            """)

        return True

    except Exception as e:
        print(f"Failed to connect to Database: {e}")
        return False

# --- Configuration ---
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

# --- Exemptions ---
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

# --- Filters (Words, Domains) ---
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

# --- Warnings ---
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

# --- Command Permissions ---
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

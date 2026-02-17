import aiosqlite
import json
import os
from config import defaultConfig

db = None

async def initDb():
    global db
    dbPath = "/data/bot.db" if os.path.isdir("/data") else "bot.db"
    db = await aiosqlite.connect(dbPath)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS config (
            guildId TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY (guildId, key)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS exemptRoles (
            guildId TEXT,
            ruleType TEXT,
            roleId TEXT,
            PRIMARY KEY (guildId, ruleType, roleId)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bannedWords (
            guildId TEXT,
            word TEXT,
            PRIMARY KEY (guildId, word)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS linkWhitelist (
            guildId TEXT,
            domain TEXT,
            PRIMARY KEY (guildId, domain)
        )
    """)
    await db.commit()

async def getConfig(guildId, key):
    async with db.execute(
        "SELECT value FROM config WHERE guildId = ? AND key = ?",
        (str(guildId), key)
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else None

async def setConfig(guildId, key, value):
    await db.execute(
        "INSERT OR REPLACE INTO config (guildId, key, value) VALUES (?, ?, ?)",
        (str(guildId), key, str(value))
    )
    await db.commit()

async def getAllConfig(guildId):
    async with db.execute(
        "SELECT key, value FROM config WHERE guildId = ?",
        (str(guildId),)
    ) as cursor:
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def initDefaults(guildId):
    guildStr = str(guildId)
    for key, value in defaultConfig.items():
        async with db.execute(
            "SELECT 1 FROM config WHERE guildId = ? AND key = ?",
            (guildStr, key)
        ) as cursor:
            exists = await cursor.fetchone()
            if not exists:
                await db.execute(
                    "INSERT INTO config (guildId, key, value) VALUES (?, ?, ?)",
                    (guildStr, key, value)
                )
    await db.commit()

async def addExemptRole(guildId, ruleType, roleId):
    await db.execute(
        "INSERT OR IGNORE INTO exemptRoles (guildId, ruleType, roleId) VALUES (?, ?, ?)",
        (str(guildId), ruleType, str(roleId))
    )
    await db.commit()

async def removeExemptRole(guildId, ruleType, roleId):
    await db.execute(
        "DELETE FROM exemptRoles WHERE guildId = ? AND ruleType = ? AND roleId = ?",
        (str(guildId), ruleType, str(roleId))
    )
    await db.commit()

async def getExemptRoles(guildId, ruleType):
    async with db.execute(
        "SELECT roleId FROM exemptRoles WHERE guildId = ? AND ruleType = ?",
        (str(guildId), ruleType)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def isRoleExempt(guildId, ruleType, memberRoles):
    exemptRoleIds = await getExemptRoles(guildId, ruleType)
    for role in memberRoles:
        if str(role.id) in exemptRoleIds:
            return True
    return False

async def addBannedWord(guildId, word):
    await db.execute(
        "INSERT OR IGNORE INTO bannedWords (guildId, word) VALUES (?, ?)",
        (str(guildId), word.lower())
    )
    await db.commit()

async def removeBannedWord(guildId, word):
    await db.execute(
        "DELETE FROM bannedWords WHERE guildId = ? AND word = ?",
        (str(guildId), word.lower())
    )
    await db.commit()

async def getBannedWords(guildId):
    async with db.execute(
        "SELECT word FROM bannedWords WHERE guildId = ?",
        (str(guildId),)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def addWhitelistDomain(guildId, domain):
    await db.execute(
        "INSERT OR IGNORE INTO linkWhitelist (guildId, domain) VALUES (?, ?)",
        (str(guildId), domain.lower())
    )
    await db.commit()

async def removeWhitelistDomain(guildId, domain):
    await db.execute(
        "DELETE FROM linkWhitelist WHERE guildId = ? AND domain = ?",
        (str(guildId), domain.lower())
    )
    await db.commit()

async def getWhitelistDomains(guildId):
    async with db.execute(
        "SELECT domain FROM linkWhitelist WHERE guildId = ?",
        (str(guildId),)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

import json
import discord
import datetime
from discord.ext import commands
from database import (
    setConfig, getConfig, getAllConfig,
    addExemptRole, removeExemptRole, getExemptRoles,
    addBannedWord, removeBannedWord, getBannedWords,
    addWhitelistDomain, removeWhitelistDomain, getWhitelistDomains,
    hasCommandPerm, addWarning, getWarnings, clearWarnings,
    addCommandPerm, removeCommandPerm, getCommandPerms
)
from modlog import sendModLog
from config import embedColor

class PrefixCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f"Pong! 🏓 {round(self.bot.latency * 1000)}ms")

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx):
        msg = await ctx.send("Syncing commands...")
        synced = await self.bot.tree.sync()
        await msg.edit(content=f"Synced {len(synced)} commands globally!")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(description="You need Administrator permission or a higher role.", color=embedColor)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
             await ctx.send(f"Missing argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
             await ctx.send(str(error))
        else:
            print(f"Prefix command error: {error}")
            await ctx.send(f"Error: {error}")

    def is_admin():
        return commands.has_permissions(administrator=True)
    
    async def check_auth(self, ctx, command: str, native_perm: bool) -> bool:
        if native_perm:
            return True
        # Check if user has explicit permission via DB
        if await hasCommandPerm(ctx.guild.id, command, ctx.author.roles):
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    def parse_time(self, duration: str) -> datetime.timedelta:
        """Parses duration string like '10m', '1h' into timedelta."""
        duration = duration.replace(" ", "").lower()
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        
        if not duration or not duration[-1].isalpha():
             raise ValueError("No unit provided")

        amount_str = duration[:-1]
        unit = duration[-1]
        
        if not amount_str.isdigit():
             raise ValueError("Amount not a number")
        
        amount = int(amount_str)
        if unit not in multiplier:
            raise ValueError("Invalid time unit")
            
        return datetime.timedelta(seconds=amount * multiplier[unit])

    def bool_converter(self, arg):
        return arg.lower() in ("yes", "y", "true", "t", "1", "enable", "on")

    # --- MODERATION COMMANDS ---

    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if not await self.check_auth(ctx, "kick", ctx.author.guild_permissions.kick_members): return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
             await ctx.send("You cannot kick this member due to role hierarchy.")
             return

        # Check against Admin Role from Config
        from database import getConfig
        adminRoleId = await getConfig(ctx.guild.id, "adminRoleId")
        if adminRoleId:
            adminRole = ctx.guild.get_role(int(adminRoleId))
            if adminRole and adminRole in member.roles:
                await ctx.send(f"You cannot kick a member with the **{adminRole.name}** role.")
                return
        
        if member.top_role >= ctx.guild.me.top_role:
             await ctx.send("I cannot kick this member (their role is higher than mine).")
             return

        try:
            await member.send(f"You were kicked from **{ctx.guild.name}**. Reason: {reason}")
        except: pass

        await member.kick(reason=reason)
        await ctx.send(f"✅ Kicked {member.mention}.")
        
        await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Manual Kick", messageContent=f"Reason: {reason}\nModerator: {ctx.author.mention}")

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member, delete_days: int = 0, *, reason: str = "No reason provided"):
        # Note: parsing args like this is tricky if delete_days is optional in middle. 
        # Easier to force order: !ban @User 0 Reason
        if not await self.check_auth(ctx, "ban", ctx.author.guild_permissions.ban_members): return

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
             await ctx.send("You cannot ban this member due to role hierarchy.")
             return
             
        # Check against Admin Role from Config
        from database import getConfig
        adminRoleId = await getConfig(ctx.guild.id, "adminRoleId")
        if adminRoleId:
            adminRole = ctx.guild.get_role(int(adminRoleId))
            if adminRole and adminRole in member.roles:
                await ctx.send(f"You cannot ban a member with the **{adminRole.name}** role.")
                return

        if member.top_role >= ctx.guild.me.top_role:
             await ctx.send("I cannot ban this member (their role is higher than mine).")
             return

        try:
            await member.send(f"You were banned from **{ctx.guild.name}**. Reason: {reason}")
        except: pass

        await member.ban(reason=reason, delete_message_days=delete_days)
        await ctx.send(f"✅ Banned {member.mention}.")

        await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Manual Ban", messageContent=f"Reason: {reason}\nModerator: {ctx.author.mention}")

    @commands.command(name="unban")
    async def unban(self, ctx, user_id: int):
        if not await self.check_auth(ctx, "unban", ctx.author.guild_permissions.ban_members): return
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user.mention}.")
            await sendModLog(self.bot, ctx.guild.id, user=user, channel=ctx.channel, rule="Manual Unban", messageContent=f"Moderator: {ctx.author.mention}")
        except discord.NotFound:
            await ctx.send("User not found or not banned.")

    @commands.command(name="mute")
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        if not await self.check_auth(ctx, "mute", ctx.author.guild_permissions.moderate_members): return

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
             await ctx.send("You cannot mute this member.")
             return
        
        if member.top_role >= ctx.guild.me.top_role:
             await ctx.send("I cannot mute this member (their role is higher than mine).")
             return

        try:
            delta = self.parse_time(duration)
            await member.timeout(discord.utils.utcnow() + delta, reason=reason)
            await ctx.send(f"✅ Muted {member.mention} for {duration}.")
            
            await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Manual Mute", messageContent=f"Duration: {duration}\nReason: {reason}\nModerator: {ctx.author.mention}")
        except Exception as e:
            await ctx.send(f"Failed to mute: {e}")

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: discord.Member):
        if not await self.check_auth(ctx, "unmute", ctx.author.guild_permissions.moderate_members): return

        await member.timeout(None, reason="Unmuted by moderator")
        await ctx.send(f"✅ Unmuted {member.mention}.")
        await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Manual Unmute", messageContent=f"Moderator: {ctx.author.mention}")

    @commands.command(name="purge")
    async def purge(self, ctx, amount: int):
        if not await self.check_auth(ctx, "purge", ctx.author.guild_permissions.manage_messages): return
        if amount < 1 or amount > 100:
            await ctx.send("Amount must be 1-100.")
            return
        
        deleted = await ctx.channel.purge(limit=amount+1) # +1 to include command msg
        await ctx.send(f"🗑️ Deleted {len(deleted)-1} messages.", delete_after=3)
        
        await sendModLog(self.bot, ctx.guild.id, user=ctx.author, channel=ctx.channel, rule="Manual Purge", messageContent=f"Deleted {len(deleted)-1} messages.")



    # --- WARNING COMMANDS ---

    @commands.command(name="warn")
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if not await self.check_auth(ctx, "warn", ctx.author.guild_permissions.moderate_members): return
        
        timestamp = datetime.datetime.now().timestamp()
        await addWarning(ctx.guild.id, member.id, ctx.author.id, reason, timestamp)
        
        try:
           await member.send(f"⚠️ You were warned in **{ctx.guild.name}**. Reason: {reason}")
        except: pass
        
        # Check warnings count for auto-punish
        warnings = await getWarnings(ctx.guild.id, member.id)
        count = len(warnings)
        
        action_msg = ""
        if count >= 3:
            try:
                duration = datetime.timedelta(hours=1)
                await member.timeout(discord.utils.utcnow() + duration, reason="Auto-punish: 3 warnings")
                action_msg = "\n🚫 **Auto-Punish**: User muted for 1 hour."
            except discord.Forbidden:
                action_msg = "\n❌ Failed to auto-mute (missing permissions)."
        
        await ctx.send(f"⚠️ Warned {member.mention} (Total: {count}).{action_msg}")
        await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Manual Warn", messageContent=f"Reason: {reason}\nModerator: {ctx.author.mention}\nTotal Warnings: {count}{action_msg}")

    @commands.command(name="warnings")
    async def warnings(self, ctx, member: discord.Member):
        warnings = await getWarnings(ctx.guild.id, member.id)
        if not warnings:
            await ctx.send(f"{member.display_name} has no warnings.")
            return

        embed = discord.Embed(title=f"Warnings for {member.display_name}", color=0xFFAA00)
        for modId, reason, ts in warnings[:10]: # Show last 10
            mod = ctx.guild.get_member(int(modId))
            modName = mod.display_name if mod else "Unknown"
            date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            embed.add_field(name=f"{date} by {modName}", value=reason, inline=False)
        
        embed.set_footer(text=f"Total Warnings: {len(warnings)}")
        await ctx.send(embed=embed)

    @commands.command(name="clearwarnings")
    async def clearwarnings(self, ctx, member: discord.Member):
        if not await self.check_auth(ctx, "clearwarnings", ctx.author.guild_permissions.moderate_members): return
        
        await clearWarnings(ctx.guild.id, member.id)
        await ctx.send(f"✅ Cleared all warnings for {member.mention}.")
        await sendModLog(self.bot, ctx.guild.id, user=member, channel=ctx.channel, rule="Clear Warnings", messageContent=f"Moderator: {ctx.author.mention}")


    # --- UTILITY COMMANDS ---

    @commands.command(name="lock")
    async def lock(self, ctx):
        if not await self.check_auth(ctx, "lock", ctx.author.guild_permissions.manage_channels): return
        
        # Try to overwrite send_messages for @everyone
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @commands.command(name="unlock")
    async def unlock(self, ctx):
        if not await self.check_auth(ctx, "unlock", ctx.author.guild_permissions.manage_channels): return
        
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked.")

    @commands.command(name="slowmode")
    async def slowmode(self, ctx, seconds: int):
        if not await self.check_auth(ctx, "slowmode", ctx.author.guild_permissions.manage_channels): return
        
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode must be between 0 and 21600 seconds.")
            return

        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
             await ctx.send("✅ Slowmode disabled.")
        else:
             await ctx.send(f"✅ Slowmode set to {seconds} seconds.")

    @commands.command(name="whois", aliases=["userinfo"])
    async def whois(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_str = ", ".join(roles) if roles else "None"
        
        # Get Warnings
        from database import getWarnings
        warnings = await getWarnings(ctx.guild.id, member.id)
        warn_count = len(warnings)
        
        embed = discord.Embed(title=f"User Info: {member.display_name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Identity", value=f"**Mention:** {member.mention}\n**ID:** `{member.id}`", inline=False)
        
        created = member.created_at.strftime("%Y-%m-%d %H:%M")
        joined = member.joined_at.strftime("%Y-%m-%d %H:%M")
        embed.add_field(name="Dates", value=f"**Created:** {created}\n**Joined:** {joined}", inline=False)
        
        embed.add_field(name="Moderation", value=f"**Warnings:** {warn_count}", inline=True)
        
        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)


    # --- ROLE & PERMISSION COMMANDS ---

    @commands.command(name="setroles")
    @is_admin()
    async def setroles(self, ctx, level: str, role: discord.Role):
        level = level.lower()
        if level not in ["admin", "mod"]:
             await ctx.send("Level must be 'admin' or 'mod'.")
             return
             
        key = "adminRoleId" if level == "admin" else "modRoleId"
        await setConfig(ctx.guild.id, key, str(role.id))
        await ctx.send(f"✅ Set **{level.upper()}** role to {role.mention}.")

    @commands.command(name="setperm")
    @is_admin()
    async def setperm(self, ctx, command: str, role: discord.Role, action: str):
        command = command.lower()
        action = action.lower()
        if action not in ["allow", "remove"]:
             await ctx.send("Action must be 'allow' or 'remove'.")
             return

        if action == "allow":
            await addCommandPerm(ctx.guild.id, command, role.id)
            await ctx.send(f"✅ Role {role.mention} can now use `{command}`.")
        else:
            await removeCommandPerm(ctx.guild.id, command, role.id)
            await ctx.send(f"🗑️ Removed permission for {role.mention} to use `{command}`.")

    @commands.command(name="listperms")
    async def listperms(self, ctx, command: str):
        roleIds = await getCommandPerms(ctx.guild.id, command.lower())
        if not roleIds:
            await ctx.send(f"No custom permissions set for `{command}`.")
        else:
            roles = [f"<@&{rid}>" for rid in roleIds]
            await ctx.send(f"Roles allowed to use `{command}`:\n" + ", ".join(roles))


    # --- CONFIGURATION COMMANDS (Existing) ---

    @commands.group(invoke_without_command=True)
    @is_admin()
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.config_view(ctx)

    @config.command(name="view")
    @is_admin()
    async def config_view(self, ctx):
        guildId = ctx.guild.id
        config = await getAllConfig(guildId)
        
        embed = discord.Embed(title="Current Configuration", color=embedColor)
        embed.add_field(name="General", value=f"Prefix: `{config.get('prefix', '.')}`\nModLog: <#{config.get('modLogChannel', 'None')}>", inline=False)
        
        spam = "✅" if config.get("spamEnabled") == "1" else "❌"
        attach = "✅" if config.get("attachmentEnabled") == "1" else "❌"
        mention = "✅" if config.get("mentionEnabled") == "1" else "❌"
        msg = "✅" if config.get("messageLimitEnabled") == "1" else "❌"
        link = "✅" if config.get("linkFilterEnabled") == "1" else "❌"
        word = "✅" if config.get("wordFilterEnabled") == "1" else "❌"
        
        embed.add_field(name="Filter Status", value=f"Spam: {spam}\nAttachment: {attach}\nMention: {mention}\nMsg Limit: {msg}\nLink: {link}\nWord: {word}", inline=False)
        
        embed.add_field(name="Spam", value=f"Max: {config.get('spamMaxMessages')}\nWindow: {config.get('spamTimeWindow')}s", inline=True)
        embed.add_field(name="Attachment", value=f"Max: {config.get('maxAttachments')}\nBlocked: {len(json.loads(config.get('blockedFileTypes', '[]')))} types", inline=True)
        embed.add_field(name="Mention", value=f"Max: {config.get('maxMentions')}\nBlock @everyone: {config.get('blockEveryone')}\nBlock @here: {config.get('blockHere')}", inline=True)
        embed.add_field(name="Msg Limit", value=f"Lines: {config.get('maxLines')}\nWords: {config.get('maxWords')}\nChars: {config.get('maxCharacters')}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @is_admin()
    async def modlog(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}modlog set <#channel>")

    @modlog.command(name="set")
    @is_admin()
    async def modlog_set(self, ctx, channel: discord.TextChannel):
        await setConfig(ctx.guild.id, "modLogChannel", str(channel.id))
        await ctx.send(embed=discord.Embed(description=f"Mod-log channel set to {channel.mention}", color=embedColor))

    @commands.group(invoke_without_command=True)
    @is_admin()
    async def prefix(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}prefix set <new_prefix>")

    @prefix.command(name="set")
    @is_admin()
    async def prefix_set(self, ctx, new_prefix: str):
        await setConfig(ctx.guild.id, "prefix", new_prefix)
        await ctx.send(embed=discord.Embed(description=f"Prefix set to `{new_prefix}`", color=embedColor))

    # Spam Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def spam(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}spam enable/disable/set")

    @spam.command(name="enable")
    @is_admin()
    async def spam_enable(self, ctx):
        await setConfig(ctx.guild.id, "spamEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Spam filter enabled.", color=embedColor))

    @spam.command(name="disable")
    @is_admin()
    async def spam_disable(self, ctx):
        await setConfig(ctx.guild.id, "spamEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Spam filter disabled.", color=embedColor))

    @spam.command(name="set")
    @is_admin()
    async def spam_set(self, ctx, max_messages: int, time_window: int):
        await setConfig(ctx.guild.id, "spamMaxMessages", str(max_messages))
        await setConfig(ctx.guild.id, "spamTimeWindow", str(time_window))
        await ctx.send(embed=discord.Embed(description=f"Spam thresholds set: {max_messages} msgs per {time_window}s", color=embedColor))

    # Attachment Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def attachment(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}attachment enable/disable/limit/block/unblock")

    @attachment.command(name="enable")
    @is_admin()
    async def attach_enable(self, ctx):
        await setConfig(ctx.guild.id, "attachmentEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Attachment filter enabled.", color=embedColor))

    @attachment.command(name="disable")
    @is_admin()
    async def attach_disable(self, ctx):
        await setConfig(ctx.guild.id, "attachmentEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Attachment filter disabled.", color=embedColor))

    @attachment.command(name="limit")
    @is_admin()
    async def attach_limit(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxAttachments", str(count))
        await ctx.send(embed=discord.Embed(description=f"Max attachments set to {count}", color=embedColor))

    @attachment.command(name="block")
    @is_admin()
    async def attach_block(self, ctx, filetype: str):
        ft = filetype.lower().strip(".")
        current = json.loads(await getConfig(ctx.guild.id, "blockedFileTypes") or "[]")
        if ft not in current:
            current.append(ft)
            await setConfig(ctx.guild.id, "blockedFileTypes", json.dumps(current))
            await ctx.send(embed=discord.Embed(description=f"Blocked file type: .{ft}", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description=f".{ft} is already blocked.", color=embedColor))

    @attachment.command(name="unblock")
    @is_admin()
    async def attach_unblock(self, ctx, filetype: str):
        ft = filetype.lower().strip(".")
        current = json.loads(await getConfig(ctx.guild.id, "blockedFileTypes") or "[]")
        if ft in current:
            current.remove(ft)
            await setConfig(ctx.guild.id, "blockedFileTypes", json.dumps(current))
            await ctx.send(embed=discord.Embed(description=f"Unblocked file type: .{ft}", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description=f".{ft} was not blocked.", color=embedColor))

    # Mention Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def mention(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}mention enable/disable/limit/blockeveryone/blockhere")

    @mention.command(name="enable")
    @is_admin()
    async def mention_enable(self, ctx):
        await setConfig(ctx.guild.id, "mentionEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Mention filter enabled.", color=embedColor))

    @mention.command(name="disable")
    @is_admin()
    async def mention_disable(self, ctx):
        await setConfig(ctx.guild.id, "mentionEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Mention filter disabled.", color=embedColor))

    @mention.command(name="limit")
    @is_admin()
    async def mention_limit(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxMentions", str(count))
        await ctx.send(embed=discord.Embed(description=f"Max mentions set to {count}", color=embedColor))

    @mention.command(name="blockeveryone")
    @is_admin()
    async def mention_blockeveryone(self, ctx, enabled: str):
        val = "1" if self.bool_converter(enabled) else "0"
        await setConfig(ctx.guild.id, "blockEveryone", val)
        await ctx.send(embed=discord.Embed(description=f"Block @everyone: {val=='1'}", color=embedColor))

    @mention.command(name="blockhere")
    @is_admin()
    async def mention_blockhere(self, ctx, enabled: str):
        val = "1" if self.bool_converter(enabled) else "0"
        await setConfig(ctx.guild.id, "blockHere", val)
        await ctx.send(embed=discord.Embed(description=f"Block @here: {val=='1'}", color=embedColor))

    # Message Limit Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def msglimit(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}msglimit enable/disable/lines/words/characters")

    @msglimit.command(name="enable")
    @is_admin()
    async def msglimit_enable(self, ctx):
        await setConfig(ctx.guild.id, "messageLimitEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Message limits enabled.", color=embedColor))

    @msglimit.command(name="disable")
    @is_admin()
    async def msglimit_disable(self, ctx):
        await setConfig(ctx.guild.id, "messageLimitEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Message limits disabled.", color=embedColor))

    @msglimit.command(name="lines")
    @is_admin()
    async def msglimit_lines(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxLines", str(count))
        await ctx.send(embed=discord.Embed(description=f"Max lines set to {count}", color=embedColor))

    @msglimit.command(name="words")
    @is_admin()
    async def msglimit_words(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxWords", str(count))
        await ctx.send(embed=discord.Embed(description=f"Max words set to {count}", color=embedColor))

    @msglimit.command(name="characters")
    @is_admin()
    async def msglimit_characters(self, ctx, count: int):
        await setConfig(ctx.guild.id, "maxCharacters", str(count))
        await ctx.send(embed=discord.Embed(description=f"Max characters set to {count}", color=embedColor))

    # Link Filter Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def linkfilter(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}linkfilter enable/disable/whitelist_add/whitelist_remove/whitelist_list/regex_add/regex_remove")

    @linkfilter.command(name="enable")
    @is_admin()
    async def link_enable(self, ctx):
        await setConfig(ctx.guild.id, "linkFilterEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Link filter enabled.", color=embedColor))

    @linkfilter.command(name="disable")
    @is_admin()
    async def link_disable(self, ctx):
        await setConfig(ctx.guild.id, "linkFilterEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Link filter disabled.", color=embedColor))

    @linkfilter.command(name="whitelist_add")
    @is_admin()
    async def link_whitelist_add(self, ctx, domain: str):
        await addWhitelistDomain(ctx.guild.id, domain)
        await ctx.send(embed=discord.Embed(description=f"Added {domain} to whitelist.", color=embedColor))

    @linkfilter.command(name="whitelist_remove")
    @is_admin()
    async def link_whitelist_remove(self, ctx, domain: str):
        await removeWhitelistDomain(ctx.guild.id, domain)
        await ctx.send(embed=discord.Embed(description=f"Removed {domain} from whitelist.", color=embedColor))

    @linkfilter.command(name="whitelist_list")
    @is_admin()
    async def link_whitelist_list(self, ctx):
        domains = await getWhitelistDomains(ctx.guild.id)
        if not domains:
            await ctx.send(embed=discord.Embed(description="No whitelisted domains.", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description=f"Whitelisted domains:\n" + "\n".join(domains), color=embedColor))

    @linkfilter.command(name="regex_add")
    @is_admin()
    async def link_regex_add(self, ctx, *, pattern: str):
        current = json.loads(await getConfig(ctx.guild.id, "linkRegexPatterns") or "[]")
        if pattern not in current:
            current.append(pattern)
            await setConfig(ctx.guild.id, "linkRegexPatterns", json.dumps(current))
            await ctx.send(embed=discord.Embed(description=f"Added regex pattern: `{pattern}`", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description="Pattern already exists.", color=embedColor))

    @linkfilter.command(name="regex_remove")
    @is_admin()
    async def link_regex_remove(self, ctx, *, pattern: str):
        current = json.loads(await getConfig(ctx.guild.id, "linkRegexPatterns") or "[]")
        if pattern in current:
            current.remove(pattern)
            await setConfig(ctx.guild.id, "linkRegexPatterns", json.dumps(current))
            await ctx.send(embed=discord.Embed(description=f"Removed regex pattern: `{pattern}`", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description="Pattern not found.", color=embedColor))

    # Word Filter Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def wordfilter(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}wordfilter enable/disable/add/remove/list/partial/regex")

    @wordfilter.command(name="enable")
    @is_admin()
    async def word_enable(self, ctx):
        await setConfig(ctx.guild.id, "wordFilterEnabled", "1")
        await ctx.send(embed=discord.Embed(description="Word filter enabled.", color=embedColor))

    @wordfilter.command(name="disable")
    @is_admin()
    async def word_disable(self, ctx):
        await setConfig(ctx.guild.id, "wordFilterEnabled", "0")
        await ctx.send(embed=discord.Embed(description="Word filter disabled.", color=embedColor))

    @wordfilter.command(name="add")
    @is_admin()
    async def word_add(self, ctx, word: str):
        await addBannedWord(ctx.guild.id, word)
        await ctx.send(embed=discord.Embed(description=f"Added banned word: `{word}`", color=embedColor))

    @wordfilter.command(name="remove")
    @is_admin()
    async def word_remove(self, ctx, word: str):
        await removeBannedWord(ctx.guild.id, word)
        await ctx.send(embed=discord.Embed(description=f"Removed banned word: `{word}`", color=embedColor))

    @wordfilter.command(name="list")
    @is_admin()
    async def word_list(self, ctx):
        words = await getBannedWords(ctx.guild.id)
        if not words:
            await ctx.send(embed=discord.Embed(description="No banned words.", color=embedColor))
        else:
            await ctx.send(embed=discord.Embed(description=f"**Banned words:**\n" + ", ".join(words), color=embedColor))

    @wordfilter.command(name="partial")
    @is_admin()
    async def word_partial(self, ctx, enabled: str):
        val = "1" if self.bool_converter(enabled) else "0"
        await setConfig(ctx.guild.id, "wordFilterPartialMatch", val)
        await ctx.send(embed=discord.Embed(description=f"Partial matching: {val=='1'}", color=embedColor))

    @wordfilter.command(name="regex")
    @is_admin()
    async def word_regex(self, ctx, enabled: str):
        val = "1" if self.bool_converter(enabled) else "0"
        await setConfig(ctx.guild.id, "wordFilterRegex", val)
        await ctx.send(embed=discord.Embed(description=f"Regex matching: {val=='1'}", color=embedColor))

    # Exempt Group
    @commands.group(invoke_without_command=True)
    @is_admin()
    async def exempt(self, ctx):
        await ctx.send(f"Usage: {ctx.prefix}exempt add/remove/list <rule>")

    @exempt.command(name="add")
    @is_admin()
    async def exempt_add(self, ctx, rule: str, role: discord.Role):
        valid_rules = ["spam", "attachment", "mention", "messageLimit", "link", "word"]
        if rule not in valid_rules:
            await ctx.send(f"Invalid rule. Choices: {', '.join(valid_rules)}")
            return
        await addExemptRole(ctx.guild.id, rule, str(role.id))
        await ctx.send(embed=discord.Embed(description=f"Exempted {role.mention} from {rule} filter.", color=embedColor))

    @exempt.command(name="remove")
    @is_admin()
    async def exempt_remove(self, ctx, rule: str, role: discord.Role):
        valid_rules = ["spam", "attachment", "mention", "messageLimit", "link", "word"]
        if rule not in valid_rules:
            await ctx.send(f"Invalid rule. Choices: {', '.join(valid_rules)}")
            return
        await removeExemptRole(ctx.guild.id, rule, str(role.id))
        await ctx.send(embed=discord.Embed(description=f"Removed exemption for {role.mention} from {rule} filter.", color=embedColor))

    @exempt.command(name="list")
    @is_admin()
    async def exempt_list(self, ctx, rule: str):
        valid_rules = ["spam", "attachment", "mention", "messageLimit", "link", "word"]
        if rule not in valid_rules:
            await ctx.send(f"Invalid rule. Choices: {', '.join(valid_rules)}")
            return
        roleIds = await getExemptRoles(ctx.guild.id, rule)
        if not roleIds:
            await ctx.send(embed=discord.Embed(description=f"No exempt roles for {rule} filter.", color=embedColor))
        else:
            roles = [f"<@&{rid}>" for rid in roleIds]
            await ctx.send(embed=discord.Embed(description=f"Exempt roles for {rule} filter:\n" + ", ".join(roles), color=embedColor))

async def setup(bot):
    await bot.add_cog(PrefixCommands(bot))

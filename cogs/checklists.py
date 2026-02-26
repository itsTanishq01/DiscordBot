import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createChecklist, getChecklist, getChecklists, archiveChecklist, deleteChecklist,
    addChecklistItem, toggleChecklistItem, removeChecklistItem,
    getChecklistItems, logAudit
)
from config import embedColor
from cogs.sdlcHelpers import requireActiveProject, requireRole, getGroupRoles, parseBulkNames


class Checklists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cl_group = app_commands.Group(name="checklist", description="Manage checklists")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        msg = f"Error: {error}"
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Missing permissions."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /checklist new ────────────────────────────
    @cl_group.command(name="new", description="Create a new checklist")
    @app_commands.describe(
        title="Checklist title",
        task_id="Optional: link to a task ID"
    )
    async def checklist_new(self, interaction: discord.Interaction, title: str,
                            task_id: int = None):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        now = int(time.time())
        seq, internal_id = await createChecklist(interaction.guild_id, title,
                                    str(interaction.user.id), task_id, now)
        await logAudit(interaction.guild_id, "create", "checklist", seq,
                       str(interaction.user.id), f"Created checklist: {title}", now)

        embed = discord.Embed(
            title="\u2705 Checklist Created",
            description=f"**{title}** (ID: `#{seq}`)",
            color=embedColor
        )
        if task_id:
            embed.add_field(name="Linked Task", value=f"`#{task_id}`", inline=True)
        embed.set_footer(text="Add items with /checklist add")
        await interaction.followup.send(embed=embed)

    # ── /checklist add ────────────────────────────
    @cl_group.command(name="add", description="Add item(s) to a checklist. Comma-separate for bulk.")
    @app_commands.describe(
        checklist_id="Checklist ID to add items to",
        items="Item text (comma-separate for bulk: 'Test login, Test logout, Deploy')"
    )
    async def checklist_add(self, interaction: discord.Interaction, checklist_id: int,
                            items: str):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        if checklist.get('archived'):
            await interaction.followup.send("This checklist is archived.", ephemeral=True)
            return

        item_texts = parseBulkNames(items)
        if not item_texts:
            await interaction.followup.send("No valid items provided.", ephemeral=True)
            return

        # Use internal ID for item operations
        internal_id = checklist['id']
        added = []
        errors = []
        for text in item_texts:
            try:
                item_seq = await addChecklistItem(internal_id, text)
                added.append((item_seq, text))
            except Exception as e:
                errors.append(f"\u274c `{text}`: {e}")

        embed = discord.Embed(color=embedColor)
        if len(added) == 1:
            item_seq, itext = added[0]
            embed.title = "\u2795 Item Added"
            embed.description = f"\u2b1c **{itext}** (Item `#{item_seq}`)"
        elif added:
            embed.title = f"\u2795 {len(added)} Items Added"
            embed.description = "\n".join([f"\u2b1c **{itext}** (Item `#{item_seq}`)" for item_seq, itext in added])

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)

        embed.set_footer(text=f"Checklist: {checklist['name']} (#{checklist_id})")
        await interaction.followup.send(embed=embed)

    # ── /checklist view ───────────────────────────
    @cl_group.command(name="view", description="View a checklist and its items")
    @app_commands.describe(checklist_id="Checklist ID to view")
    async def checklist_view(self, interaction: discord.Interaction, checklist_id: int):
        await interaction.response.defer(ephemeral=False)
        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        internal_id = checklist['id']
        items = await getChecklistItems(internal_id)

        embed = discord.Embed(
            title=f"\U0001f4cb {checklist['name']}",
            color=embedColor
        )

        if checklist.get('archived'):
            embed.title += " (Archived)"

        if not items:
            embed.description = "*No items yet. Add some with `/checklist add`.*"
        else:
            total = len(items)
            done = sum(1 for i in items if i.get('completed'))
            pct = int((done / total) * 100) if total > 0 else 0

            filled = pct // 10
            bar = "\u2588" * filled + "\u2591" * (10 - filled)
            embed.description = f"**Progress:** `{bar}` {pct}% ({done}/{total})\n"

            lines = []
            for item in items:
                check = "\u2705" if item.get('completed') else "\u2b1c"
                toggler = ""
                if item.get('completed') and item.get('toggled_by'):
                    toggler = f" \u2014 <@{item['toggled_by']}>"
                lines.append(f"{check} `#{item['item_seq']}` {item['text']}{toggler}")

            embed.description += "\n".join(lines)

        if checklist.get('task_id'):
            embed.add_field(name="Linked Task", value=f"`#{checklist['task_id']}`", inline=True)
        embed.add_field(name="Created by", value=f"<@{checklist['created_by']}>", inline=True)
        embed.set_footer(text=f"Checklist ID: #{checklist_id}")
        await interaction.followup.send(embed=embed)

    # ── /checklist toggle ─────────────────────
    @cl_group.command(name="toggle", description="Toggle a checklist item's completion")
    @app_commands.describe(
        checklist_id="Checklist ID",
        item_number="Item number within the checklist"
    )
    async def checklist_toggle(self, interaction: discord.Interaction,
                               checklist_id: int, item_number: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        now = int(time.time())
        new_state = await toggleChecklistItem(checklist['id'], item_number,
                                              str(interaction.user.id), now)

        if new_state is None:
            await interaction.followup.send("Item not found.", ephemeral=True)
            return

        status = "\u2705 Completed" if new_state else "\u2b1c Unchecked"
        await logAudit(gid, "toggle", "checklist_item", checklist_id,
                       str(interaction.user.id), f"Item #{item_number} toggled to: {status}", now)

        await interaction.followup.send(f"{status} \u2014 Checklist `#{checklist_id}` Item `#{item_number}`")

    # ── /checklist list ───────────────────────────
    @cl_group.command(name="list", description="List all active checklists")
    @app_commands.describe(show_archived="Show archived checklists instead")
    async def checklist_list(self, interaction: discord.Interaction,
                             show_archived: bool = False):
        await interaction.response.defer(ephemeral=False)
        checklists = await getChecklists(interaction.guild_id, archived=show_archived)

        if not checklists:
            label = "archived" if show_archived else "active"
            await interaction.followup.send(
                f"No {label} checklists. Create one with `/checklist new`.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="\U0001f4cb Checklists" + (" (Archived)" if show_archived else ""),
            color=embedColor
        )

        lines = []
        for cl in checklists:
            items = await getChecklistItems(cl['id'])
            total = len(items)
            done = sum(1 for i in items if i.get('completed'))
            pct = int((done / total) * 100) if total > 0 else 0
            filled = pct // 10
            bar = "\u2588" * filled + "\u2591" * (10 - filled)
            task_link = f" \u2192 Task `#{cl['task_id']}`" if cl.get('task_id') else ""
            lines.append(f"`#{cl['guild_seq']}` **{cl['name']}** `{bar}` {pct}% ({done}/{total}){task_link}")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"{len(checklists)} checklist(s)")
        await interaction.followup.send(embed=embed)

    # ── /checklist remove ─────────────────────
    @cl_group.command(name="remove", description="Remove an item from a checklist")
    @app_commands.describe(
        checklist_id="Checklist ID",
        item_number="Item number within the checklist"
    )
    async def checklist_remove(self, interaction: discord.Interaction,
                               checklist_id: int, item_number: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        await removeChecklistItem(checklist['id'], item_number)
        await interaction.followup.send(
            f"\U0001f5d1\ufe0f Removed item `#{item_number}` from checklist `#{checklist_id}`.")

    # ── /checklist archive ────────────────────────
    @cl_group.command(name="archive", description="Archive a completed checklist")
    @app_commands.describe(checklist_id="Checklist ID to archive")
    async def checklist_archive(self, interaction: discord.Interaction, checklist_id: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        if checklist.get('archived'):
            await interaction.followup.send("Already archived.", ephemeral=True)
            return

        await archiveChecklist(gid, checklist_id)
        await logAudit(gid, "archive", "checklist", checklist_id,
                       str(interaction.user.id), f"Archived: {checklist['name']}", int(time.time()))

        await interaction.followup.send(
            f"\U0001f4e6 Archived checklist **{checklist['name']}** (`#{checklist_id}`)."
        )

    # ── /checklist delete ─────────────────────
    @cl_group.command(name="delete", description="Permanently delete a checklist and all its items")
    @app_commands.describe(checklist_id="Checklist ID to delete")
    async def checklist_delete(self, interaction: discord.Interaction, checklist_id: int):
        await interaction.response.defer(ephemeral=False)
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'checklists')):
            return

        gid = interaction.guild_id
        checklist = await getChecklist(gid, checklist_id)
        if not checklist:
            await interaction.followup.send("Checklist not found.", ephemeral=True)
            return

        name = checklist['name']
        await deleteChecklist(gid, checklist_id)
        await logAudit(gid, "delete", "checklist", checklist_id,
                       str(interaction.user.id), f"Deleted: {name}", int(time.time()))

        await interaction.followup.send(
            f"\U0001f5d1\ufe0f Permanently deleted checklist **{name}** (`#{checklist_id}`) and all its items."
        )


async def setup(bot):
    await bot.add_cog(Checklists(bot))

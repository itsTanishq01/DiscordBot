import time
import discord
from discord import app_commands
from discord.ext import commands
from database import (
    createChecklist, getChecklist, getChecklists, archiveChecklist,
    addChecklistItem, toggleChecklistItem, removeChecklistItem,
    getChecklistItems, logAudit
)
from config import embedColor
from cogs.sdlcHelpers import requireActiveProject, requireRole, parseBulkNames


class Checklists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cl_group = app_commands.Group(name="checklist", description="Manage checklists")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    # ── /checklist new ────────────────────────────
    @cl_group.command(name="new", description="Create a new checklist")
    @app_commands.describe(
        title="Checklist title",
        task_id="Optional: link to a task ID"
    )
    async def checklist_new(self, interaction: discord.Interaction, title: str,
                            task_id: int = None):
        if not await requireRole(interaction, 'developer'):
            return

        now = int(time.time())
        cid = await createChecklist(interaction.guild_id, title,
                                    str(interaction.user.id), task_id, now)
        await logAudit(interaction.guild_id, "create", "checklist", cid,
                       str(interaction.user.id), f"Created checklist: {title}", now)

        embed = discord.Embed(
            title="\u2705 Checklist Created",
            description=f"**{title}** (ID: `{cid}`)",
            color=embedColor
        )
        if task_id:
            embed.add_field(name="Linked Task", value=f"`#{task_id}`", inline=True)
        embed.set_footer(text="Add items with /checklist add")
        await interaction.response.send_message(embed=embed)

    # ── /checklist add ────────────────────────────
    @cl_group.command(name="add", description="Add item(s) to a checklist. Comma-separate for bulk.")
    @app_commands.describe(
        checklist_id="Checklist ID to add items to",
        items="Item text (comma-separate for bulk: 'Test login, Test logout, Deploy')"
    )
    async def checklist_add(self, interaction: discord.Interaction, checklist_id: int,
                            items: str):
        if not await requireRole(interaction, 'developer'):
            return

        checklist = await getChecklist(checklist_id)
        if not checklist or str(checklist['guild_id']) != str(interaction.guild_id):
            await interaction.response.send_message("Checklist not found.", ephemeral=True)
            return

        if checklist.get('archived'):
            await interaction.response.send_message("This checklist is archived.", ephemeral=True)
            return

        item_texts = parseBulkNames(items)
        if not item_texts:
            await interaction.response.send_message("No valid items provided.", ephemeral=True)
            return

        added = []
        errors = []
        for text in item_texts:
            try:
                iid = await addChecklistItem(checklist_id, text)
                added.append((iid, text))
            except Exception as e:
                errors.append(f"\u274c `{text}`: {e}")

        embed = discord.Embed(color=embedColor)
        if len(added) == 1:
            iid, itext = added[0]
            embed.title = "\u2795 Item Added"
            embed.description = f"\u2b1c **{itext}** (ID: `{iid}`)"
        elif added:
            embed.title = f"\u2795 {len(added)} Items Added"
            embed.description = "\n".join([f"\u2b1c **{itext}** (ID: `{iid}`)" for iid, itext in added])

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)

        embed.set_footer(text=f"Checklist: {checklist['name']} (#{checklist_id})")
        await interaction.response.send_message(embed=embed)

    # ── /checklist view ───────────────────────────
    @cl_group.command(name="view", description="View a checklist and its items")
    @app_commands.describe(checklist_id="Checklist ID to view")
    async def checklist_view(self, interaction: discord.Interaction, checklist_id: int):
        checklist = await getChecklist(checklist_id)
        if not checklist or str(checklist['guild_id']) != str(interaction.guild_id):
            await interaction.response.send_message("Checklist not found.", ephemeral=True)
            return

        items = await getChecklistItems(checklist_id)

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

            # Progress bar
            filled = pct // 10
            bar = "\u2588" * filled + "\u2591" * (10 - filled)
            embed.description = f"**Progress:** `{bar}` {pct}% ({done}/{total})\n"

            lines = []
            for item in items:
                check = "\u2705" if item.get('completed') else "\u2b1c"
                toggler = ""
                if item.get('completed') and item.get('toggled_by'):
                    toggler = f" \u2014 <@{item['toggled_by']}>"
                lines.append(f"{check} `#{item['id']}` {item['text']}{toggler}")

            embed.description += "\n".join(lines)

        if checklist.get('task_id'):
            embed.add_field(name="Linked Task", value=f"`#{checklist['task_id']}`", inline=True)
        embed.add_field(name="Created by", value=f"<@{checklist['created_by']}>", inline=True)
        embed.set_footer(text=f"Checklist ID: {checklist_id}")
        await interaction.response.send_message(embed=embed)

    # ── /checklist toggle ─────────────────────────
    @cl_group.command(name="toggle", description="Toggle a checklist item's completion")
    @app_commands.describe(item_id="Item ID to toggle")
    async def checklist_toggle(self, interaction: discord.Interaction, item_id: int):
        if not await requireRole(interaction, 'developer'):
            return

        now = int(time.time())
        new_state = await toggleChecklistItem(item_id, str(interaction.user.id), now)

        if new_state is None:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            return

        status = "\u2705 Completed" if new_state else "\u2b1c Unchecked"
        await logAudit(interaction.guild_id, "toggle", "checklist_item", item_id,
                       str(interaction.user.id), f"Toggled to: {status}", now)

        await interaction.response.send_message(f"{status} \u2014 Item `#{item_id}`")

    # ── /checklist list ───────────────────────────
    @cl_group.command(name="list", description="List all active checklists")
    @app_commands.describe(show_archived="Show archived checklists instead")
    async def checklist_list(self, interaction: discord.Interaction,
                             show_archived: bool = False):
        checklists = await getChecklists(interaction.guild_id, archived=show_archived)

        if not checklists:
            label = "archived" if show_archived else "active"
            await interaction.response.send_message(
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
            lines.append(f"`#{cl['id']}` **{cl['name']}** `{bar}` {pct}% ({done}/{total}){task_link}")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"{len(checklists)} checklist(s)")
        await interaction.response.send_message(embed=embed)

    # ── /checklist remove ─────────────────────────
    @cl_group.command(name="remove", description="Remove an item from a checklist")
    @app_commands.describe(item_id="Item ID to remove")
    async def checklist_remove(self, interaction: discord.Interaction, item_id: int):
        if not await requireRole(interaction, 'developer'):
            return

        await removeChecklistItem(item_id)
        await interaction.response.send_message(f"\U0001f5d1\ufe0f Removed item `#{item_id}`.")

    # ── /checklist archive ────────────────────────
    @cl_group.command(name="archive", description="Archive a completed checklist")
    @app_commands.describe(checklist_id="Checklist ID to archive")
    async def checklist_archive(self, interaction: discord.Interaction, checklist_id: int):
        if not await requireRole(interaction, 'lead'):
            return

        checklist = await getChecklist(checklist_id)
        if not checklist or str(checklist['guild_id']) != str(interaction.guild_id):
            await interaction.response.send_message("Checklist not found.", ephemeral=True)
            return

        if checklist.get('archived'):
            await interaction.response.send_message("Already archived.", ephemeral=True)
            return

        await archiveChecklist(checklist_id)
        await logAudit(interaction.guild_id, "archive", "checklist", checklist_id,
                       str(interaction.user.id), f"Archived: {checklist['name']}", int(time.time()))

        await interaction.response.send_message(
            f"\U0001f4e6 Archived checklist **{checklist['name']}** (`#{checklist_id}`)."
        )


async def setup(bot):
    await bot.add_cog(Checklists(bot))

import re
import time
import discord
from discord import app_commands
from discord.ext import commands
from database import createBug, logAudit
from config import embedColor
from cogs.sdlcHelpers import (
    requireActiveProject, requireRole, getGroupRoles, parseBulkNames,
    BUG_SEVERITIES, SEVERITY_EMOJI, severityDisplay
)


def parse_markdown_table(text):
    """Parse a markdown table or line-by-line text into structured bug data.

    Supports formats:
    1. Markdown table: | Title | Severity |
    2. Simple line-by-line: one bug title per line
    3. Comma-separated: "Bug A, Bug B, Bug C"

    Returns list of dicts: [{'title': '...', 'severity': 'medium'}]
    """
    # Strip code block markers
    text = re.sub(r'^```\w*\n?', '', text.strip())
    text = re.sub(r'\n?```$', '', text.strip())
    text = text.strip()

    if not text:
        return []

    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    if not lines:
        return []

    # Try to detect markdown table format (lines containing pipes)
    pipe_lines = [l for l in lines if '|' in l]

    if len(pipe_lines) >= 2:
        return _parse_table_format(pipe_lines)

    # Try line-by-line format
    if len(lines) > 1:
        return _parse_line_format(lines)

    # Single line — try comma separation
    names = parseBulkNames(lines[0])
    return [{'title': n, 'severity': 'medium'} for n in names]


def _parse_table_format(lines):
    """Parse markdown table with pipe separators."""
    results = []

    # Find header row
    header = lines[0]
    cols = [c.strip().lower() for c in header.split('|') if c.strip()]

    # Find title column index
    title_idx = None
    severity_idx = None

    title_keywords = ['title', 'bug', 'issue', 'name', 'description', 'summary']
    severity_keywords = ['severity', 'level', 'priority', 'sev']

    for i, col in enumerate(cols):
        if any(kw in col for kw in title_keywords):
            title_idx = i
        if any(kw in col for kw in severity_keywords):
            severity_idx = i

    # Default to first column for title if not found
    if title_idx is None:
        title_idx = 0

    # Skip separator row (contains dashes like |---|---|)
    data_lines = []
    for line in lines[1:]:
        cleaned = line.replace('|', '').replace('-', '').strip()
        if cleaned:  # skip separator rows
            data_lines.append(line)

    for line in data_lines:
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if not cells or title_idx >= len(cells):
            continue

        title = cells[title_idx].strip()
        if not title or title == '---':
            continue

        severity = 'medium'
        if severity_idx is not None and severity_idx < len(cells):
            raw_sev = cells[severity_idx].strip().lower()
            if raw_sev in BUG_SEVERITIES:
                severity = raw_sev

        results.append({'title': title, 'severity': severity})

    return results


def _parse_line_format(lines):
    """Parse one bug per line, optionally with severity after a separator."""
    results = []
    for line in lines:
        line = line.lstrip('- *•>0123456789.) ')  # strip list markers

        if not line:
            continue

        # Try to extract severity from end: "Bug title [critical]" or "Bug title - critical"
        severity = 'medium'
        for sev in BUG_SEVERITIES:
            patterns = [
                rf'\[{sev}\]\s*$',
                rf'\({sev}\)\s*$',
                rf'\s+-\s+{sev}\s*$',
                rf'\s+{sev}\s*$',
            ]
            for pat in patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    severity = sev
                    line = line[:match.start()].strip()
                    break
            if severity != 'medium':
                break

        if line:
            results.append({'title': line, 'severity': severity})

    return results


class IngestConfirmView(discord.ui.View):
    """Interactive confirmation before bulk importing."""

    def __init__(self, parsed_data, guild_id, project_id, author_id):
        super().__init__(timeout=120)
        self.parsed_data = parsed_data
        self.guild_id = guild_id
        self.project_id = project_id
        self.author_id = author_id

    @discord.ui.button(label="Confirm Import", style=discord.ButtonStyle.success, emoji="\u2705")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the original user can confirm.", ephemeral=True)
            return

        now = int(time.time())
        created = []
        errors = []

        for item in self.parsed_data:
            try:
                bid = await createBug(
                    self.guild_id, self.project_id,
                    item['title'], "",
                    item['severity'],
                    str(self.author_id),
                    [],
                    now
                )
                created.append((bid, item['title']))
                await logAudit(self.guild_id, "ingest", "bug", bid,
                               str(self.author_id), f"Ingested: {item['title']}", now)
            except Exception as e:
                errors.append(f"\u274c `{item['title']}`: {e}")

        embed = discord.Embed(
            title=f"\u2705 Imported {len(created)} Bug(s)",
            color=0x57F287
        )

        if created:
            lines = [f"`#{bid}` {title}" for bid, title in created[:15]]
            if len(created) > 15:
                lines.append(f"*...and {len(created) - 15} more*")
            embed.description = "\n".join(lines)

        if errors:
            embed.add_field(name="Errors", value="\n".join(errors[:5]), inline=False)

        embed.set_footer(text=f"{len(created)} created, {len(errors)} failed")

        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="\u274c")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the original user can cancel.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="\u274c Import Cancelled",
            description="No bugs were created.",
            color=0xED4245
        )
        await interaction.response.edit_message(embed=embed, view=self)


class Ingestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ingest_group = app_commands.Group(name="ingest", description="Bulk import issues from text")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Missing permissions.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    # ── /ingest bugs ──────────────────────────────
    @ingest_group.command(name="bugs", description="Import bugs from pasted text or markdown table")
    @app_commands.describe(
        data="Paste a markdown table, line-by-line list, or comma-separated bug titles"
    )
    async def ingest_bugs(self, interaction: discord.Interaction, data: str):
        if not await requireRole(interaction, await getGroupRoles(interaction.guild_id, 'ingestion')):
            return

        project = await requireActiveProject(interaction)
        if not project:
            return

        parsed = parse_markdown_table(data)

        if not parsed:
            await interaction.response.send_message(
                "Could not parse any bugs from the input. Try:\n"
                "• **Comma-separated:** `Bug A, Bug B, Bug C`\n"
                "• **Line-by-line:** One bug per line\n"
                "• **Markdown table:** `| Title | Severity |`",
                ephemeral=True
            )
            return

        # Build preview embed
        embed = discord.Embed(
            title=f"\U0001f4e5 Import Preview \u2014 {len(parsed)} Bug(s)",
            description=f"Into project: **{project['name']}**\n\n"
                        f"Review the items below, then **Confirm** or **Cancel**.",
            color=embedColor
        )

        # Group by severity for preview
        by_severity = {}
        for item in parsed:
            sev = item['severity']
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(item['title'])

        for sev in ['critical', 'medium', 'minor']:
            if sev not in by_severity:
                continue
            titles = by_severity[sev]
            emoji = SEVERITY_EMOJI.get(sev, '')
            lines = [f"\u2022 {t}" for t in titles[:10]]
            if len(titles) > 10:
                lines.append(f"*...and {len(titles) - 10} more*")
            embed.add_field(
                name=f"{emoji} {sev.title()} ({len(titles)})",
                value="\n".join(lines),
                inline=False
            )

        view = IngestConfirmView(parsed, interaction.guild_id, project['id'], interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Ingestion(bot))

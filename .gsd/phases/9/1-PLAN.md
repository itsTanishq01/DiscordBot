---
phase: 9
plan: 1
wave: 1
---

# Plan 9.1: Ingestion Cog — Interactive Bulk Imports

## Objective
Create `cogs/ingestion.py` to allow leads and developers to paste markdown tables or structured text to automatically create bulk bug tickets.

## Context
- `cogs/sdlcHelpers.py` — `requireActiveProject`, `requireRole`, `parseBulkNames`, `BUG_SEVERITIES`
- `database.py` — `createBug`, `logAudit`
- `config.py` — `embedColor`

## Tasks

<task type="auto">
  <name>Create ingestion cog</name>
  <files>cogs/ingestion.py</files>
  <action>
    Create a new file `cogs/ingestion.py` with the following structure:

    **1. Markdown Table Parser**
    Implement a helper method `parse_markdown_table(text: str) -> list[dict]`.
    - It should strip outer markdown blocks (\`\`\`).
    - Detect the header row. Look for column names like "title", "bug", "issue" for the main text, and "severity", "level" for severity.
    - If format is simple line-by-line (not a true table), fall back to `parseBulkNames`.
    - Returns a list of dictionaries, e.g. `[{'title': '...', 'severity': 'medium'}]`.

    **2. `/ingest bugs` Command**
    ```
    Parameters:
      data: str (The pasted table or multi-line text)
    ```
    - Use `requireRole(interaction, 'developer')`.
    - Use `requireActiveProject(interaction)`.
    - Call the parser to extract title and severity.
    - Validate parsed data.
    - Instead of immediately creating the bugs, use a `discord.ui.View` with a "Confirm" and "Cancel" button.
    - Display an embed summarising what will be ingested (e.g. "Ready to create 5 bugs...").

    **3. Interactive View (`discord.ui.View`)**
    ```python
    class IngestConfirmView(discord.ui.View):
        def __init__(self, parsed_data, project_id, author_id):
            super().__init__(timeout=120)
            self.parsed_data = parsed_data
            self.project_id = project_id
            self.author_id = author_id

        @discord.ui.button(label="Confirm Import", style=discord.ButtonStyle.success)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            # perform database ingestion loop
            # send confirmation
    ```
    - The confirm button should verify `interaction.user.id == self.author_id`.
    - Loop through `self.parsed_data` and call `createBug(...)`.
    - Keep track of successes and failures.
    - Send a final summary embed showing IDs of created bugs.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/ingestion.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Ingestion cog created with robust markdown parsing and interactive confirmation.</done>
</task>

## Success Criteria
- [ ] `cogs/ingestion.py` exists.
- [ ] Parse logic gracefully handles standard markdown tables.
- [ ] Confirmation step guarantees users don't accidentally create 50 garbage bugs.
- [ ] Syntax validates.

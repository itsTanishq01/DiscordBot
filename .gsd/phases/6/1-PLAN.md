---
phase: 6
plan: 1
wave: 1
---

# Plan 6.1: Checklists Cog — Core Commands & Interactive UI

## Objective
Create `cogs/checklists.py` to manage pre-launch checklists, QA checklists, etc., with interactive UI elements (buttons/select menus) for toggling item statuses.

## Context
- `cogs/sdlcHelpers.py` — `requireActiveProject`, `requireRole`, `parseBulkNames`
- `cogs/projects.py` — General cog patterns.
- `database.py` — `createChecklist`, `getChecklists`, `getChecklist`, `archiveChecklist`, `addChecklistItem`, `toggleChecklistItem`, `removeChecklistItem`, `getChecklistItems`, `logAudit`

## Tasks

<task type="auto">
  <name>Create checklists cog with interactive UI</name>
  <files>cogs/checklists.py</files>
  <action>
    Create a new file `cogs/checklists.py` with the following structure:

    **1. Interactive UI View (`discord.ui.View`)**
    ```python
    class ChecklistView(discord.ui.View):
        def __init__(self, checklist_id):
            # Load items dynamically
            # Display rows of buttons or a interactive Select menu for toggling
            pass
    ```
    - The easiest and most scalable UI for Discord checklists is a custom `discord.ui.Select` menu where users can select the items they want to toggle, or dynamically building a `discord.ui.Button` per item if `< 25` items.
    - Let's use standard slash commands for management, but `/checklist view` returns an embed with the items numbered + standard `discord.ui.Button`s if we manage it simply, or just keep it entirely slash command based: `/checklist toggle <checklist_id> <item_id>`.
    - We will define both the standard slash commands AND an interactive view if possible. Since we can't reliably predict button limits (Discord limits buttons to 25 per message), we will use an `app_commands.Group` to handle everything via slash commands first, and dynamically generate an interactive embed string.

    **2. `/checklist new`**
    ```
    Parameters:
      title: str
    ```
    - Use `requireRole(interaction, 'developer')`
    - Create via `createChecklist(guild_id, project_id, title, creator_id, now)`
    - Return success embed.

    **3. `/checklist add`**
    ```
    Parameters:
      checklist_id: int
      items: str (comma-separated for bulk addition)
    ```
    - Use `requireRole(interaction, 'developer')`
    - Parses `items` using `parseBulkNames(items)`.
    - Loops and calls `addChecklistItem(checklist_id, item_content, now)`.
    - Returns confirmation of added items.

    **4. `/checklist view`**
    ```
    Parameters:
      checklist_id: int
    ```
    - Fetches the checklist and its items (`getChecklist`, `getChecklistItems`).
    - Format lines like: `[x] Item 1 (ID: 5)`, `[ ] Item 2 (ID: 6)`
    - Calculate completion percentage.
    - Sends a rich embed containing the checklist progress.

    **5. `/checklist toggle`**
    ```
    Parameters:
      item_id: int
    ```
    - Use `requireRole(interaction, 'developer')`
    - Calls `toggleChecklistItem(item_id)` which flips the boolean status.
    - Logs via `logAudit`.
    - Returns a confirmation message.

    **6. `/checklist list`**
    ```
    Parameters: None
    ```
    - Use `requireActiveProject(interaction)`.
    - Call `getChecklists(guild_id, project_id)`.
    - Loops through and displays all non-archived checklists with their completion stats.

    **7. `/checklist archive`**
    ```
    Parameters:
      checklist_id: int
    ```
    - Use `requireRole(interaction, 'lead')`.
    - Calls `archiveChecklist(checklist_id)`.

    **8. `/checklist remove`**
    ```
    Parameters:
      item_id: int
    ```
    - Use `requireRole(interaction, 'developer')`.
    - Calls `removeChecklistItem(item_id)`.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/checklists.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Checklists cog created with 7 commands mapping to the checklist database functions.</done>
</task>

## Success Criteria
- [ ] `cogs/checklists.py` created.
- [ ] All 7 slash commands defined.
- [ ] Uses formatting like `✅` and `⬛` dynamically in `/checklist view`.
- [ ] Bulk item additions supported via comma separation.
- [ ] Syntax is valid.

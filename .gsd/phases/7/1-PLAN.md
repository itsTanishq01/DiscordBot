---
phase: 7
plan: 1
wave: 1
---

# Plan 7.1: Workload Cog — Check and Manage Load

## Objective
Create `cogs/workload.py` to allow leads to verify developer workload (number of active bugs and tasks) before assigning new items, and allow developers to check their own load.

## Context
- `cogs/sdlcHelpers.py` — `requireRole`
- `database.py` — `getUserWorkload`, `getConfig`, `getTeamMembers`
- `config.py` — `embedColor`

## Tasks

<task type="auto">
  <name>Create workload cog</name>
  <files>cogs/workload.py</files>
  <action>
    Create a new file `cogs/workload.py` with the following structure:

    **1. `/workload check`**
    ```
    Parameters:
      member: Member (optional)
    ```
    - Fetches the current `workloadMaxTasks` config.
    - If `member` is not provided, defaults to `interaction.user`.
    - No strict role requirement if checking self. To check others, require 'lead'.
    - Calls `getUserWorkload(guild_id, str(member.id))`.
    - Returns an embed showing total active tasks + bugs vs the `workloadMaxTasks` limit. Visual indicator (e.g. 🟢, 🟡, 🔴) depending on how close they are to the cap.

    **2. `/workload team`**
    ```
    Parameters: None
    ```
    - Use `requireRole(interaction, 'lead')`.
    - Calls `getTeamMembers(guild_id)` to get all users with SDLC roles.
    - Loops through each member, calling `getUserWorkload(guild_id, member['user_id'])`.
    - Only display members who have active tasks or bugs.
    - Sorts the members by their total workload (descending).
    - Returns an embed listing the top loaded members, indicating how many tasks and bugs they have active.

    **3. `/workload settings`**
    ```
    Parameters:
      max_tasks: int (optional)
      wip_limit: int (optional)
    ```
    - Use `requireRole(interaction, 'admin')`.
    - Displays current settings from `getConfig` for `workloadMaxTasks` and `wipLimit` if no parameters are provided.
    - If parameters provided, updates them via `setConfig(guild_id, key, value)`.
    - Returns confirmation of the updated settings.
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/workload.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Workload cog created with 3 commands for tracking load.</done>
</task>

## Success Criteria
- [ ] `cogs/workload.py` created.
- [ ] 3 commands: check, team, settings.
- [ ] Incorporates `workloadMaxTasks` checks logically.
- [ ] `team` command handles iterating efficiently (for a typical small server team it will be fast).
- [ ] Syntax validates.

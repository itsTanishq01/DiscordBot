---
phase: 5
plan: 1
wave: 1
---

# Plan 5.1: Team Cog — Roles & Permissions

## Objective
Create `cogs/team.py` to manage SDLC roles (admin, lead, developer, qa, viewer). These roles govern permissions for the SDLC bot completely independently of Discord's native roles.

## Context
- `cogs/sdlcHelpers.py` — `requireRole`
- `database.py` — `setTeamRole`, `removeTeamRole`, `getTeamRole`, `getTeamMembers`
- `config.py` — `embedColor`

## Tasks

<task type="auto">
  <name>Create team cog</name>
  <files>cogs/team.py</files>
  <action>
    Create a new file `cogs/team.py` with the following structure:

    **Structure:**
    ```
    class Team(commands.Cog):
        team_group = app_commands.Group(name="team", description="Manage SDLC team roles")

        /team assign     — Assign a role to a member
        /team unassign   — Remove a member's role
        /team list       — List all team members grouped by role
        /team myrole     — Check your own role
    ```

    **1. `/team assign`**
    ```
    Parameters:
      member: Member
      role: Choice (admin, lead, developer, qa, viewer)
    ```
    - Use `requireRole(interaction, 'admin')` (only SDLC admins and Discord admins can manage roles).
    - Call `setTeamRole(guild_id, str(member.id), role.value)`
    - Send an embed confirming the new role assignment.

    **2. `/team unassign`**
    ```
    Parameters:
      member: Member
    ```
    - Use `requireRole(interaction, 'admin')`
    - Call `removeTeamRole(guild_id, str(member.id))`
    - Send a confirmation message.

    **3. `/team list`**
    ```
    Parameters: None
    ```
    - No permission required.
    - Call `getTeamMembers(guild_id)`
    - Group members by role (admin, lead, developer, qa, viewer) and sort by the hierarchy.
    - Create a rich embed displaying members by their roles (e.g., using mentions). 
    - Keep fields inline if possible. Use standard emojis for roles if desired (e.g. 👑 Admin, 👨‍💻 Developer).

    **4. `/team myrole`**
    ```
    Parameters: None
    ```
    - No permission required.
    - Call `getTeamRole(guild_id, str(user.id))`
    - Return a friendly message with the user's current SDLC role (or "None").

    **Role Choices:**
    ```python
    ROLE_CHOICES = [
        app_commands.Choice(name="Admin (Full Access)", value="admin"),
        app_commands.Choice(name="Lead (Manage Sprints & Assign)", value="lead"),
        app_commands.Choice(name="Developer (Move Tasks & Bugs)", value="developer"),
        app_commands.Choice(name="QA (Close Bugs)", value="qa"),
        app_commands.Choice(name="Viewer (Read Only)", value="viewer"),
    ]
    ```
  </action>
  <verify>python -c "import ast; ast.parse(open('cogs/team.py', encoding='utf-8').read()); print('Syntax OK')"</verify>
  <done>Team cog created with 4 commands.</done>
</task>

## Success Criteria
- [ ] `cogs/team.py` exists with Team cog class.
- [ ] 4 commands: assign, unassign, list, myrole.
- [ ] Role Choices correctly map to 'admin', 'lead', 'developer', 'qa', 'viewer'.
- [ ] Syntax validates.

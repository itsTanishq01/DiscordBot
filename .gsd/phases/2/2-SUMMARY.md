# Plan 2.2 Summary
- Created `cogs/sprints.py` with Sprints cog
- Commands: `/sprint new` (bulk), `/sprint list`, `/sprint activate`, `/sprint close`
- `_require_active_project` helper prevents commands without active project
- Sprint activation auto-closes previous active sprint
- Date parsing (YYYY-MM-DD) for start/end dates
- Status emojis: 📋 planning, 🟢 active, ⬛ closed
- Registered `cogs.sprints` in main.py cogExtensions
- Syntax validated ✓

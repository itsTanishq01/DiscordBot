# Phase 3 Verification

## Must-Haves
- [x] **Tasks cog** — VERIFIED: `cogs/tasks.py` with 8 commands
- [x] **8 commands** — new, status, assign, list, delete, view, comment, linkbug
- [x] **Bulk creation** — parseBulkNames for comma-separated titles
- [x] **Kanban columns** — 6 statuses: backlog, todo, in_progress, blocked, review, done
- [x] **Priority levels** — 4 levels: critical, high, medium, low with emojis
- [x] **WIP limits** — Checks wipLimit config before allowing in_progress
- [x] **Assignee notifications** — Mentions assignee on status changes
- [x] **Task comments** — /task comment with comment preview
- [x] **Bug linking** — /task linkbug with bidirectional validation
- [x] **Task view** — Shows comments, linked bugs, timestamps, all fields
- [x] **Kanban board** — /task list groups by status when unfiltered
- [x] **Choice dropdowns** — STATUS_CHOICES and PRIORITY_CHOICES
- [x] **Uses shared helpers** — requireActiveProject, requireRole, parseBulkNames, buildBulkEmbed
- [x] **Cog registered** — cogs.tasks in main.py
- [x] **Syntax valid** — ast.parse passes
- [x] **Helpers valid** — All imports resolve

## Verdict: PASS ✓

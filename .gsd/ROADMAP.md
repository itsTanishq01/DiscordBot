# ROADMAP.md

> **Current Milestone**: SDLC Bot v1.0
> **Goal**: Transform AbyssBot from a moderation-only bot into a full SDLC/Kanban/QA management platform

## Must-Haves
- [x] Database schema for all SDLC entities (tasks, bugs, projects, sprints, checklists, team roles)
- [ ] Task management with Kanban workflow (6 columns)
- [ ] Bug reporting and tracking with severity levels
- [ ] Team roles and permission system (Admin, Lead, Developer, QA, Viewer)
- [ ] Checklist system with templates
- [ ] Dashboard embeds (project, sprint, team)
- [ ] Workload tracking and alerts
- [ ] Issue table ingestion from pasted markdown

## Nice-to-Haves
- [ ] Automation rules engine (trigger/condition/action)
- [ ] Stale task auto-detection
- [ ] Duplicate bug detection
- [ ] Velocity/burn-down charts
- [ ] GitHub/GitLab integration

---

## Phases

### Phase 1: Database Schema & Foundation
**Status**: ✅ Complete
**Objective**: Design and implement all new database tables for SDLC features. Extend `database.py` with new table creation and CRUD functions. Establish the data layer that all subsequent phases build on.

**Deliverables:**
- New tables: `projects`, `sprints`, `tasks`, `bugs`, `team_roles`, `checklists`, `checklist_items`, `task_comments`, `task_bug_links`, `audit_log`
- CRUD functions for each table
- Database migration logic in `initDb()`

**Dependencies:** None (foundation phase)

---

### Phase 2: Project & Sprint Management
**Status**: ✅ Complete
**Objective**: Implement project and sprint creation/management. Projects scope all tasks and bugs. Sprints provide time-boxed iteration tracking.

**Deliverables:**
- `/project new`, `/project list`, `/project set` commands
- `/sprint new`, `/sprint list`, `/sprint active`, `/sprint close` commands
- Active project/sprint context per guild
- `cogs/projects.py` cog

**Dependencies:** Phase 1

---

### Phase 3: Task Management (Kanban)
**Status**: ✅ Complete
**Objective**: Full Kanban task lifecycle — create, assign, move through columns, comment, and filter tasks.

**Deliverables:**
- `/task new`, `/task status`, `/task assign`, `/task list`, `/task delete`, `/task comment` commands
- 6-column workflow: Backlog → Todo → In Progress → Blocked → Review → Done
- Priority levels (Critical, High, Medium, Low)
- Rich embed display for task details
- Assignee notification on status change
- `cogs/tasks.py` cog

**Dependencies:** Phase 1, Phase 2

---

### Phase 4: Bug Tracking & Reporting
**Status**: ⬜ Not Started
**Objective**: Bug reporting system with severity levels, lifecycle management, and cross-linking to tasks.

**Deliverables:**
- `/bug report`, `/bug status`, `/bug assign`, `/bug list`, `/bug close` commands
- `/task linkbug` — cross-link tasks and bugs
- Severity levels (🔴 Critical, 🟡 Medium, 🟠 Minor)
- Bug lifecycle: New → Acknowledged → In Progress → Needs QA → Closed
- Rich embed display for bug details
- `cogs/bugs.py` cog

**Dependencies:** Phase 1, Phase 2

---

### Phase 5: Team Roles & Permissions
**Status**: ⬜ Not Started
**Objective**: Bot-managed role system (separate from Discord roles) controlling who can do what in the SDLC workflow.

**Deliverables:**
- `/team addrole`, `/team removerole`, `/team list` commands
- Role hierarchy: Admin > Lead > Developer > QA > Viewer
- Permission checks on all SDLC commands
- Integration with existing `permissions` system
- `cogs/teamRoles.py` cog

**Dependencies:** Phase 1

---

### Phase 6: Checklist System
**Status**: ⬜ Not Started
**Objective**: Reusable checklists for QA, release prep, feature readiness, and onboarding.

**Deliverables:**
- `/checklist new`, `/checklist additem`, `/checklist toggle`, `/checklist removeitem`, `/checklist progress`, `/checklist archive` commands
- Checklist templates (create from existing checklist)
- Auto-attach checklists to tasks
- Progress bar embed display
- `cogs/checklists.py` cog

**Dependencies:** Phase 1, Phase 3 (task linking)

---

### Phase 7: Workload Tracking & Alerts
**Status**: ⬜ Not Started
**Objective**: Track team member workload and surface imbalances automatically.

**Deliverables:**
- `/workload @user` — individual workload summary
- `/workload team` — team heatmap embed
- `/workload unbalanced` — highlight overloaded/idle members
- Automatic alerts when user exceeds task threshold
- Configurable thresholds via config system
- `cogs/workload.py` cog

**Dependencies:** Phase 1, Phase 3, Phase 4, Phase 5

---

### Phase 8: Dashboards
**Status**: ⬜ Not Started
**Objective**: Rich Discord embed dashboards providing at-a-glance project health.

**Deliverables:**
- `/dashboard project` — project summary (tasks by status, bugs by severity)
- `/dashboard sprint` — sprint progress, velocity, overdue items
- `/dashboard team` — team workload distribution
- Consistent visual styling with charts (text-based bar charts in embeds)
- Auto-refresh option (post dashboard that auto-updates)
- `cogs/dashboards.py` cog

**Dependencies:** Phase 1-7 (reads from all entities)

---

### Phase 9: Issue Table Ingestion
**Status**: ⬜ Not Started
**Objective**: Parse pasted markdown/text tables and auto-create bug tickets from structured data.

**Deliverables:**
- `/bug ingestlist` command
- Markdown table parser
- Auto-create bugs with severity, tags, assignee
- Confirmation embed before bulk creation
- `cogs/ingestion.py` cog (or method in bugs cog)

**Dependencies:** Phase 4

---

### Phase 10: Polish, Automation & Verification
**Status**: ⬜ Not Started
**Objective**: Add automation rules, stale detection, duplicate detection, and full end-to-end verification.

**Deliverables:**
- Automation rules engine (configurable trigger/condition/action)
- Stale task detection (tasks stuck > N days)
- Duplicate bug detection (title/description similarity)
- Audit log cog — track all SDLC actions
- Full integration testing
- Documentation / help text updates
- `cogs/automation.py` cog

**Dependencies:** All previous phases

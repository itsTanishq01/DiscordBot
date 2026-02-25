# SPEC.md — Discord SDLC / Kanban / QA Bot

> **Product**: AbyssBot — SDLC Extension
> **Created**: 2026-02-25
> **Status**: FINALIZED

---

## 1. Product Overview

Extend the existing AbyssBot Discord bot to provide end-to-end SDLC support:

- **Kanban** task creation & progression (6 columns)
- **Bug reporting** & triage with severity levels
- **Team roles**, permissions & workload allocation
- **Checklists** (QA scripts, feature readiness, deployment steps)
- **Dashboards** summarizing progress, blockers, and risk
- **Issue table ingestion** — auto-generate tasks/bugs from pasted tables

The bot plugs into the **existing Supabase/PostgreSQL database** and acts as a UX layer + logic processor.

---

## 2. Existing System

| Component | Details |
|-----------|---------|
| Language | Python 3.11 |
| Framework | discord.py 2.3.2 |
| Database | Supabase PostgreSQL via asyncpg |
| Hosting | Render (free tier) |
| Architecture | Cog-based (moderation, filters, warnings, permissions, utility) |

### Existing Tables
- `config` — guild key-value settings
- `warnings` — moderation warnings
- `permissions` — command-role mappings
- `exemptions` — role exemptions from automod
- `filters` — banned words, whitelisted domains
- `exempt_channels` — channel exemptions from filters

---

## 3. Target Users

| Role | Permissions | Purpose |
|------|------------|---------|
| Admin | Full access | Setup, configure workflows, manage roles |
| Project Manager / Tech Lead | Create tasks, manage assignments, prioritize | Sprint + release management |
| Developer | Update status, submit bugs, receive assignments | Execute |
| QA | Submit, verify, and close bugs | Quality control |
| Guest / Stakeholder | Read only | Progress monitoring |

---

## 4. Core Features

### 4.1 Task & Progress Tracking (Kanban)

**Commands:**
- `/task new <title> <description> <assignee> <priority>`
- `/task status <task_id> <new_status>`
- `/task assign <task_id> <user>`
- `/task list [filters]`
- `/task delete <task_id>`
- `/task comment <task_id> <text>`
- `/task linkbug <task_id> <bug_id>`

**Columns:** Backlog → Todo → In Progress → Blocked → Review → Done

**Auto-Behaviors:**
- Notify assignees on status change
- Detect tasks stuck > X days → auto-flag as "⚠ Stale"
- Optional WIP limits per column

### 4.2 Bug Reporting & Tracking

**Commands:**
- `/bug report <title> <severity> <description> [attachment]`
- `/bug status <bug_id> <new_status>`
- `/bug assign <bug_id> <user>`
- `/bug list [filters]`
- `/bug close <bug_id>`
- `/bug ingestlist` (table ingestion)

**Severity:** 🔴 Critical | 🟡 Medium | 🟠 Minor

**Lifecycle:** New → Acknowledged → In Progress → Needs QA → Closed

**Auto-Behaviors:**
- Duplicate detection (matching title + description similarity)
- Auto-assign bugs based on subsystem tags
- Daily smart summaries

### 4.3 Team Roles & Structure

**Bot-managed roles (DB-level, not Discord roles):**

| Role | Permissions |
|------|------------|
| Admin | All commands |
| Lead | Task & bug assign |
| Developer | Update tasks / bugs |
| QA | Mark bugs as verified |
| Viewer | Read only |

**Commands:**
- `/team addrole @user <role>`
- `/team removerole @user <role>`
- `/team list`

### 4.4 User Workload Tracking

**Tracked Metrics:**
- Tasks in progress
- Bugs assigned
- Avg resolution time
- Completed tasks per sprint

**Commands:**
- `/workload @user`
- `/workload team` (heatmap)
- `/workload unbalanced` → highlights overloaded or idle members

**Alerts:**
- User has > N active tasks → warn leads
- User has 0 tasks → suggest assignment

### 4.5 Checklists

**Used for:** QA test passes, feature readiness, release prep, onboarding

**Commands:**
- `/checklist new <name>`
- `/checklist additem <id> <text>`
- `/checklist toggle <id> <item>`
- `/checklist removeitem <id> <item>`
- `/checklist progress <id>`
- `/checklist archive <id>`

**Features:**
- Checklist templates
- Auto-attach checklists to tasks

### 4.6 Dashboards

**Generated as Discord embeds.**

**Dashboard Types:**
- Project Summary
- Active Tasks
- Bug Heatmap
- Team Workload
- Velocity / Burn-down (per sprint)
- Overdue Tasks

**Commands:**
- `/dashboard project`
- `/dashboard sprint`
- `/dashboard team`

---

## 5. Advanced Features

### 5.1 Issue Table Ingestion

User pastes a markdown table → bot parses → auto-creates bug tickets with:
- Severity levels
- File names auto-tagged
- Assigned to default subsystem owners

### 5.2 Automation Rules

- If severity = Critical → auto-assign lead + ping team
- If bug touches specific subsystem → auto-assign subsystem owner
- If status = Done → update linked checklist / close related bug

### 5.3 Projects & Sprints

- Multi-project support per guild
- Sprint creation with start/end dates
- Velocity tracking across sprints

---

## 6. Data Model (New Tables)

```
projects          — id, guild_id, name, description, created_at
sprints           — id, guild_id, project_id, name, start_date, end_date, status
tasks             — id, guild_id, project_id, sprint_id, title, description, status, priority, assignee_id, creator_id, created_at, updated_at
bugs              — id, guild_id, project_id, title, description, severity, status, assignee_id, reporter_id, tags, created_at, updated_at
team_roles        — guild_id, user_id, role (enum)
checklists        — id, guild_id, task_id (nullable), name, created_by, archived, created_at
checklist_items   — id, checklist_id, text, completed, toggled_by, toggled_at
task_comments     — id, task_id, user_id, content, created_at
task_bug_links    — task_id, bug_id
audit_log         — id, guild_id, action, entity_type, entity_id, user_id, details, created_at
automation_rules  — id, guild_id, trigger, condition, action, enabled
```

---

## 7. Non-Functional Requirements

- All commands respond within 3 seconds
- Embeds use consistent branding (color: 0xFF4444)
- Graceful error handling with user-friendly messages
- Database operations use connection pooling (existing asyncpg pool)
- All SDLC features are per-guild isolated

---

## 8. Out of Scope (for MVP)

- GitHub/GitLab integration
- External webhook integrations
- Web dashboard (Discord-only)
- AI-powered task suggestions

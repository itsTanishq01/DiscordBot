---
phase: 4
plan: 1
wave: 1
---

# Plan 4.1: Render Deployment Configuration

## Objective
Create the necessary configuration files for deploying the bot on Render. This includes `render.yaml` for blueprint deployment (infrastructure as code) and `Procfile` for manual deployment.

## Context
- .gsd/SPEC.md
- requirements.txt

## Tasks

<task type="auto" effort="low">
  <name>Create render.yaml blueprint</name>
  <files>render.yaml</files>
  <action>
    Create `render.yaml` with:
    - service type: worker (bots are workers, not web services)
    - name: discord-automod-bot
    - env: python
    - buildCommand: pip install -r requirements.txt
    - startCommand: python main.py
    - disk: mount point /data for SQLite persistence (critical)
    - envVars:
      - key: BOT_TOKEN
        sync: false (user must provide)
  </action>
  <verify>Select-String -Path "render.yaml" -Pattern "type: worker|buildCommand|startCommand|disk" | Measure-Object | Select-Object -ExpandProperty Count</verify>
  <done>render.yaml created with worker service and persistent disk configuration</done>
</task>

<task type="auto" effort="low">
  <name>Create Procfile</name>
  <files>Procfile</files>
  <action>
    Create `Procfile` for alternative deployment methods (Heroku-style):
    `worker: python main.py`
  </action>
  <verify>Get-Content "Procfile" | Select-String "worker: python main.py"</verify>
  <done>Procfile exists</done>
</task>

## Success Criteria
- [ ] render.yaml defines a worker service
- [ ] render.yaml includes disk mount for SQLite database persistence
- [ ] Procfile defines worker process

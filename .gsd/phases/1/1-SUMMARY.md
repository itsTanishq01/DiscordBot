# Plan 1.1 Summary

## Completed
- Added 4 CREATE TABLE statements to `initDb()`: `projects`, `sprints`, `tasks`, `bugs`
- All tables use `SERIAL PRIMARY KEY`, `TEXT` for IDs, `BIGINT` for timestamps
- Foreign keys: sprints→projects (CASCADE), tasks→projects (CASCADE), tasks→sprints (SET NULL), bugs→projects (CASCADE)
- Added 4 project CRUD functions: createProject, getProject, getProjects, deleteProject
- Added 4 sprint CRUD functions: createSprint, getSprints, updateSprintStatus, getActiveSprint
- Added 6 task CRUD functions: createTask, getTask, updateTaskStatus, assignTask, getTasks (with dynamic filters), deleteTask
- Added 6 bug CRUD functions: createBug, getBug, updateBugStatus, assignBug, getBugs (with dynamic filters), closeBug

## Verification
- `python -c "import ast; ast.parse(open('database.py').read())"` → Syntax OK ✓
- All 20 functions importable ✓

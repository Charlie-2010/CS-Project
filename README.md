# CogniPlan

CogniPlan is a digital task planner with a Flask backend, MySQL storage, and a browser-based interface.

## Requirements

- Python 3.10 or newer
- MySQL Server 8.0

## Database setup

The schema is in [`Database/db.sql`](Database/db.sql). Run it once in MySQL Workbench or with the MySQL command-line client. It creates the `cogniplan_db` database and the tables used by the app. Do not drop or reset an existing database if you need to keep its data.

If you already created the database before this update, run [`Database/migration_add_calendar_display_fields.sql`](Database/migration_add_calendar_display_fields.sql) once. It adds persisted calendar priority/color fields and profile time zones without removing existing data.

## Configure and run

1. Create or edit `.env` in the project root with these settings:

   ```dotenv
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=cogniplan_db
   FLASK_SECRET_KEY=replace-with-a-long-random-secret
   ```

2. In PowerShell, create and activate a virtual environment, then install the dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Start the app:

   ```powershell
   py server.py
   ```

4. Open <http://127.0.0.1:5000> and register an account. Keep the terminal open while using the app.

Check the server and database connection at <http://127.0.0.1:5000/api/health>.

If that address reports a `503` database error, start MySQL and confirm that `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `.env` point to an accessible server. The app cannot save or demonstrate user data until this check reports `"database": "connected"`.

## Backend features

- Password-hashed registration and login with signed session cookies
- User-scoped profile, task, category, project, preference, calendar, and productivity APIs
- Task synchronization that preserves existing cloud tasks when a browser has no local cache
- User search and direct messaging with conversation membership checks
- Static file serving limited to the public `pages` and `assets` directories

See [`API.md`](API.md) for the route reference. The current interface does not provide every API feature; for example, projects and productivity logs are available through the API but do not yet have complete management screens.

## Deployment

Use a long random `FLASK_SECRET_KEY`, serve the app behind HTTPS, and set `SESSION_COOKIE_SECURE=1` when HTTPS is enabled. Keep `.env` private. Do not expose MySQL port 3306 to the public internet. This development setup does not include password-reset email delivery, production rate limiting, or a full CSRF protection layer.

# CogniPlan — Full-stack edition

CogniPlan keeps the supplied HTML/CSS/JavaScript interface and adds a Flask + MySQL backend.

## Requirements
- Windows 10/11
- Python 3.10 or newer
- MySQL Server 8.0 (Workbench is useful for running the schema)

## 1. Create the database
1. Open MySQL Workbench and connect to your local MySQL server.
2. Because this project is replacing the earlier broken schema, open `database/reset_database.sql` and execute it **only if you are certain you want to erase the old `cogniplan_db` and all its data**.
3. Open `database/schema.sql` and execute the complete script.
4. Run `USE cogniplan_db; SHOW TABLES;` and confirm these nine tables appear: `users`, `user_preferences`, `categories`, `projects`, `tasks`, `calendar_events`, `productivity_logs`, `conversations`, `messages`.

`database/db.sql` is a copy of the same schema for compatibility with the earlier project layout. Do not execute both; one is enough. If you need to preserve any existing data, do not run the reset file.

## 2. Configure the backend
1. Double-click `run_windows.bat` once. It creates `.env` and stops.
2. Open `.env` in VS Code and set `DB_PASSWORD` to your MySQL password.
3. Save and double-click `run_windows.bat` again. It creates a virtual environment, installs dependencies, and starts Flask.

Alternatively, in a VS Code terminal:
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env, then:
python server.py
```

## 3. Open the app
Visit http://127.0.0.1:5000. Register a new account. Keep the terminal window open while using the app; closing it stops the server.

## Implemented backend
- Password-hashed registration and login with server-side sessions
- Profile read/update
- User-scoped task CRUD and task sync for the existing task board
- User-scoped categories
- Preferences
- Calendar event API
- Productivity log and report summary APIs
- User search, conversations and message APIs with participant checks

The frontend's login/registration, task board, profile, preferences, calendar events, reports data and direct user messaging are connected to the backend. Voice messages, file attachments, password-reset email delivery and some presentation-only controls are not implemented yet.

## API
See `API.md`. Health check: `GET /api/health`.

## Security and deployment notes
- Never commit `.env` or share your MySQL root password.
- For real multi-location use, deploy Flask behind HTTPS and use a managed cloud MySQL database. Do not expose MySQL port 3306 directly to the public internet.
- Set a long random `FLASK_SECRET_KEY` before deployment.
- Set secure cookies / HTTPS configuration when deploying.
- Password reset email delivery and production-grade CSRF/rate limiting are not configured in this local development version.

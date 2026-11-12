# CogniPlan API reference
All JSON routes use same-origin session cookies. Protected routes require a signed-in user.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check MySQL connectivity and version |
| POST | `/api/auth/register` | Create account and sign in |
| POST | `/api/auth/login` | Sign in with username/email and password |
| POST | `/api/auth/logout` | End session |
| GET | `/api/auth/me` | Current session status |
| GET / PUT | `/api/profile` | Read/update current user's profile |
| GET / POST | `/api/tasks` | List/create tasks |
| PUT / DELETE | `/api/tasks/<id>` | Update/delete owned task |
| POST | `/api/tasks/sync` | Sync task-board client model to MySQL |
| GET / POST | `/api/categories` | List/create categories |
| PUT / DELETE | `/api/categories/<id>` | Update/delete owned category |
| GET / PUT | `/api/preferences` | Read/save preferences |
| GET / POST | `/api/projects` | List/create projects |
| PUT / DELETE | `/api/projects/<id>` | Update/delete owned project |
| GET / POST | `/api/calendar/events` | List/create calendar events |
| DELETE | `/api/calendar/events/<id>` | Delete owned event |
| GET | `/api/reports/summary` | Task and productivity summary |
| GET / POST | `/api/productivity` | Read/upsert daily productivity logs |
| GET | `/api/users/search?q=...` | Find users to message |
| GET / POST | `/api/conversations` | List/start conversations |
| GET / POST | `/api/conversations/<id>/messages` | Read/send messages after membership check |

## Request examples
Register:
```json
{"username":"Alex","email":"alex@example.com","password":"at-least-8-characters"}
```
Create task:
```json
{"title":"Finish report","status":"In Progress","priority":"HIGH","description":"Draft the summary"}
```
Save preferences:
```json
{"theme_mode":"dark","daily_task_goal":5,"widget_layout":{}}
```

The frontend currently calls the backend for authentication, task-board persistence, profile updates, preferences, calendar events, report task data, and direct user-to-user messaging. Voice messages and file attachments are not implemented. Password reset requires an email provider and is not implemented.

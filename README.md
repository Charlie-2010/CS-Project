# CS-Project
Digital Task Planner

## Frontend prototype status

The current pages are a frontend prototype; they do not call a backend API.

- Dashboard and Tasks share browser-local sample tasks through `localStorage` (`cogniplan.tasks`). Changes sync between those pages in the same browser origin.
- The UI currently uses `Draft`, `In Progress`, `Editing`, and `Done`. Their backend enum mapping is intentionally unresolved; in particular, `Editing` has not been assumed to mean `REVIEW`.
- Task priorities use `LOW`, `MEDIUM`, `HIGH`, and `URGENT`. Legacy `mid` values are normalized to `MEDIUM`.
- Reports calculate metrics from their own sample task records. Calendar events and Messages conversations are temporary in-memory demo data.
- Profile and Settings are stored in browser `localStorage`.
- Authentication is a demo flow only; it does not create accounts, authenticate credentials, or invalidate a server session.

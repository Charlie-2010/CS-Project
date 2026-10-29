# ScholarSync Integration Contract

## Database

- Database name: `scholarsync_db`.
- Apply `database/schema.sql`, then `database/seed.sql`.
- Connection configuration comes only from `DB_HOST`, `DB_PORT`, `DB_USER`,
  `DB_PASSWORD`, and `DB_NAME` environment variables.
- SQL values use `%s` placeholders through `database.connection`.

## Authentication

- `users.password_hash` is a 64-character hexadecimal PBKDF2-SHA256 value.
- `users.password_salt` is a unique 32-character hexadecimal value.
- New accounts use `auth.hash_utils.create_password_record`; login uses
  `auth.hash_utils.verify_password(hash, entered_password, salt)`.
- `auth.login.authenticate_user(username, password, portal_role)` returns `None`
  for invalid credentials, raises `WrongRoleError` for the wrong portal, and
  otherwise returns an immutable session:

  ```python
  Session(
      user_id=...,
      username="...",
      role="teacher" | "student",
      teacher_id=... | None,
      student_id=... | None,
  )
  ```
- Exactly one of `teacher_id` and `student_id` is populated for valid sessions.

## Web API

- Start the Flask server with `py server.py`. Frontend templates are served from
  `templates/`, and assets in `assets/` are available under `/assets/`.
- `POST /api/auth/login` accepts `username`, `password`, and `role`
  (`teacher` or `student`) as JSON and creates an HTTP-only session cookie.
  `POST /api/auth/logout` clears the session and `GET /api/auth/me` returns the
  signed-in user's public identity.
- `GET /api/teacher/dashboard` and `GET /api/student/dashboard` return the
  corresponding dashboard data for the matching authenticated role.
- Teacher-only student management is available through
  `GET`/`POST /api/students`, `GET /api/students/<student_id>`,
  `PATCH`/`DELETE /api/students/<student_id>`, and
  `GET /api/students/<student_id>/delete-impact`.
- API successes return a JSON `data` value. Validation failures return HTTP 422
  with `field_errors`; unauthenticated and unauthorized requests return HTTP
  401 and 403; conflicting database constraints return HTTP 409, and database
  availability or operation failures return HTTP 503.
- Request handlers use `services.academic` for validated, role-aware workflows
  and `database.connection` helpers for direct database reads. No API handler
  updates desktop widgets.

## Service Results And Errors

Application services return `ServiceResult` values with `ok`, `data`, `error`,
`error_code`, and `field_errors` attributes. Validation returns all field errors
in `field_errors`; expected database failures return a clean message and the
MySQL code when available. Low-level database helpers raise
`DatabaseUnavailableError`, `ConstraintViolationError`, or
`DatabaseOperationError`; they do not report failures as a successful zero-row
write. Common MySQL codes map to actionable messages: 1048 required value,
1062 duplicate value, 1451 referenced row, and 1452 missing parent row.

Student account and profile creation is one transaction. It inserts the user
first, uses `lastrowid` for the student profile, and rolls back both records if
either insert fails. `student_delete_impact` and `class_delete_impact` return
related-row counts for confirmation dialogs.

`services.academic.create_attendance` is teacher-only. It validates the
attendance date and status, rejects an existing `(student_id, date)` entry with
a date field error, and relies on the database unique key to guard concurrent
inserts. `services.academic.create_exam_result` is teacher-only and accepts
finite marks from 0 through 100 inclusive; it also rejects marks above the
selected paper's configured maximum.

For batch entry, teacher-only `services.academic.create_attendance_batch` and
`services.academic.create_exam_results_batch` accept a non-empty list of the
same row dictionaries used by their single-entry counterparts. Each batch is
validated before writes, then all rows are checked/inserted in one transaction
and committed together. A validation or database error rolls back the entire
batch; successful results report the created count and batch total.

## Policies

- Roll numbers are unique across the student table, as enforced by the unique
  constraint on `students.roll_number`.
- Authenticated teachers may create and manage teacher accounts and classes.
  Teacher deletion is blocked while classes, allocations, or assignments still
  reference that teacher.
- A class may have at most one homeroom teacher; a teacher may manage at most one
  homeroom class, matching the current `classes.class_teacher_id` constraint.

## Partner hand-off

Frontend and UI code must not execute direct SQL or handle password hashes. It
passes plain form data to the backend, which validates it before database
access. Database-backed access requires the documented `DB_*` environment
variables and a MySQL instance initialized from the schema and seed scripts.

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

## UI Navigation

- `ScholarSync.show_dashboard(session)` is the authenticated entry point.
- `ScholarSync.navigate(page)` accepts `dashboard`, `students`, `teachers`,
  `classes`, and `subjects`; management routes are available only to teacher
  sessions.
- The student portal opens its dashboard directly. The teacher dashboard
  provides navigation to student, teacher, class, and subject/allocation
  management.
- Tkinter modules call `services.academic`; they do not execute SQL directly.

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

# Phase 1 Integration Contract

## Database

- Database name: `student_performance_system`.
- Apply `database/schema.sql`, then `database/seed.sql`.
- Connection configuration comes only from `DB_HOST`, `DB_PORT`, `DB_USER`,
  `DB_PASSWORD`, and `DB_NAME` environment variables.
- SQL values use `%s` placeholders through `database.connection`.

## Authentication

- `users.password_hash` is a 64-character hexadecimal PBKDF2-SHA256 value.
- `users.password_salt` is a unique 32-character hexadecimal value.
- New accounts use `auth.hash_utils.create_password_record`; login uses
  `auth.hash_utils.verify_password(hash, entered_password, salt)`.

## Partner hand-off

Frontend and UI code must not execute direct SQL or handle password hashes.
It passes plain form data to the backend, which validates it before database
access. This contract is ready for partner acknowledgement before merge.

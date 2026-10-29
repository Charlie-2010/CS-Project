Phase 1: Database Foundation & Connectivity
This initial phase establishes the core relational data layer, secure transactional interface pipelines, and the cryptographic authentication infrastructure required by the application.

1. Schema Deployment & Verification (database/schema.sql)
• Normalized Relational Design: A fully decoupled, 11-table relational schema structured to enforce strict data integrity across both teacher and student workflows while eliminating functional redundancies.
• Persona Isolation & Inheritance: User identities are managed via a primary parent table (users) handling structural authorization and roles (teacher, student). Specialized profile views (teachers, students) inherit identity hooks cleanly via foreign key binds.
• Data Integrity & Relationship Cascades: Implements defensive relational guardrails:
	• ON DELETE CASCADE ensures that deleting a root credential cleanly strips down child biographical dependencies to prevent orphan rows.
	• ON DELETE SET NULL protects student biographies, historic scores, and parameters if an administrative cohort or class section is disbanded.
	• Composite UNIQUE constraints across the daily attendance stream (student_id, date) and report card tables (student_id, exam_subject_id) prevent duplicate evaluations or contradictory logging.

2. Mock Data Seeding (database/seed.sql)
• Sequential Baseline Generation: Employs a specific DML constraint sequence to initialize valid test records across all internal system modules.
• Testing Coverage Parameters: Populates teacher and student accounts, foundational academic subjects (Physics, Chemistry, Mathematics, Computer Science), both class sections, and operational workloads (teacher_subjects).
• Exam Core Infrastructure: Seeds standard term test blueprints (exams) and individual test papers (exam_subjects) to supply stable, pre-populated validation scenarios for analytical frontend rendering evaluation.

3. Database Connector Architecture (database/connection.py)
• Curriculum-Aligned Interface Framework: Leverages the standard mysql.connector suite in accordance with standard Computer Science interfaces, separating raw SQL mechanics from frontend visualization screens.
• Context-Managed Pipelines: Employs Python's native with statement blocks for cursor context handlers. This protects active connection sockets by guaranteeing resource clean-up and channel closure even if unexpected calculation errors trigger mid-transaction.
• Robust Transactional Safeguards: Isolates database modification tasks (DML operations like updates, inserts, deletes) inside protective structural try-catch networks. The handler enforces automated execution parameter commits (conn.commit()) and handles automated state recovery rollbacks (conn.rollback()) to shield the relational engine against corruption during sudden failures.

4. Security & Utility Logic Foundation (auth/hash_utils.py & utils/helpers.py)
• Cryptographic Credential Hardening: Uses PBKDF2-HMAC-SHA-256 with 600,000 iterations and a unique random salt for each credential.
• Dynamic Salting Defenses: Generates a 16-byte random salt with os.urandom and stores its 32-character hexadecimal representation separately from the 64-character derived hash.
• Universal Parameterized Utility Layers: Implements clean database transaction abstractions (insert_record, update_record, get_records_by_filter) across the application utilities. By enforcing tuple-based parameterized variables matched against strict %s positional tokens, it guarantees that all frontend form elements treat inputs strictly as literal data values, completely blocking SQL Injection vulnerabilities.
## Local test logins

After loading `database/schema.sql` and `database/seed.sql`, the sample
usernames `t_albert`, `t_marie`, `t_isaac`, `s_charlie`, `s_linus`, `s_ada`,
`s_grace`, `s_katherine`, and `s_dorothy` all use the development-only password
`ChangeMe123!`. Set `DB_PASSWORD` in your
local environment before running database-dependent tests; never commit its value.

Roll numbers are unique across the student table. Authenticated teachers can
manage students, teachers, classes, subjects, and teacher-subject allocations.
Teacher deletion is blocked while class, allocation, or assignment records
reference that teacher.

Run `py -m unittest discover -s tests -v` for offline checks and configured live
MySQL checks. Live checks skip when MySQL cannot be reached. Run
`database/test_queries.sql` after seeding to inspect table coverage and report cards,
student percentages and grades, subject averages and mark ranges, and class-wise
exam rank lists. The sample aggregation queries use a configurable-in-SQL grade
scale (A >= 90%, B >= 80%, C >= 70%, D >= 60%, otherwise F); the rank query
requires MySQL 8.0 or newer.

## Phase 2: Authentication & Core CRUD

- Login verifies PBKDF2 credentials and routes profile-aware sessions to the
	matching teacher or student portal.
- Academic services enforce session roles and return structured results with
	database codes or aggregated field errors.
- Student account/profile creation and deletion are transactional; student and
	class deletions show related-row impact before confirmation.
- Teachers can manage students, teachers, classes, subjects, and teacher-subject
	allocations. Referenced teacher deletions are rejected with a clear message.
- Both dashboards load from services and include a reserved Matplotlib chart
	area. The student dashboard shows report-card and attendance summaries; the
	teacher dashboard shows student/class counts and upcoming assignments.

## Run

1. Install dependencies with `py -m pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`, then set the MySQL values from your Workbench
	connection. Workbench's saved connection name is not the schema name; set
	`DB_NAME` to the actual schema shown under Workbench's SCHEMAS panel.

	```powershell
	Copy-Item .env.example .env
	notepad .env
	```

3. The sample `.env.example` targets `127.0.0.1:3306`, user `root`, and the
	`scholarsync_db` schema created by `database/schema.sql`.
4. Test the connection without printing the password:

	```powershell
	& ".venv\Scripts\python.exe" -c "from database.connection import get_connection; c = get_connection(); print('Connected to ' + c.database) if c else print('Connection failed; check .env host, port, user, password, and schema'); c and c.close()"
	```

5. Start the web server from the same VS Code terminal with `py server.py`.
   API endpoints use `http://127.0.0.1:5000/api/...`. Set `FLASK_SECRET_KEY`
   to a long random value to keep login sessions valid across server restarts;
   set `COOKIE_SECURE=true` when serving over HTTPS.
6. To initialize a new database, apply `database/schema.sql`, then
	`database/seed.sql`. **The seed script truncates existing app tables**; do
	not run it against data you need to keep.
7. Run checks with `py -m unittest discover -s tests -v`.

## Create a Submission Zip

From the project root in PowerShell, create an archive without local environments
or bytecode:

```powershell
$files = Get-ChildItem -Force -Recurse -File | Where-Object {
	$_.FullName -notmatch '[\\/](\.git|\.venv|venv|__pycache__)[\\/]' -and
	$_.Extension -notin @('.pyc', '.pyo', '.zip')
}
Compress-Archive -Path $files.FullName -DestinationPath .\Build.zip -Force
```

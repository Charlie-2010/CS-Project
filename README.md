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
• Testing Coverage Parameters: Populates baseline user nodes (administrators, instructors, students), defines foundational academic subjects (Physics, Chemistry, Mathematics, Computer Science), maps class structural cohorts (Class 12, Sections A/B), and coordinates operational workloads (teacher_subjects).
• Exam Core Infrastructure: Seeds standard term test blueprints (exams) and individual test papers (exam_subjects) to supply stable, pre-populated validation scenarios for analytical frontend rendering evaluation.

3. Database Connector Architecture (database/connection.py)
• Curriculum-Aligned Interface Framework: Leverages the standard mysql.connector suite in accordance with standard Computer Science interfaces, separating raw SQL mechanics from frontend visualization screens.
• Context-Managed Pipelines: Employs Python's native with statement blocks for cursor context handlers. This protects active connection sockets by guaranteeing resource clean-up and channel closure even if unexpected calculation errors trigger mid-transaction.
• Robust Transactional Safeguards: Isolates database modification tasks (DML operations like updates, inserts, deletes) inside protective structural try-catch networks. The handler enforces automated execution parameter commits (conn.commit()) and handles automated state recovery rollbacks (conn.rollback()) to shield the relational engine against corruption during sudden failures.

4. Security & Utility Logic Foundation (auth/hash_utils.py & utils/helpers.py)
• Cryptographic Credential Hardening: Sidesteps vulnerable custom algorithms by implementing SHA-256 cryptographic hashing through Python's secure hashlib utilities.
• Dynamic Salting Defenses: Generates unique, high-entropy 16-byte random salt values (os.urandom) for every single credential profile during registration. By appending these strings before hashing, it creates highly differentiated database signatures to completely nullify pre-computed Rainbow Table dictionary cracking exploits.
• Universal Parameterized Utility Layers: Implements clean database transaction abstractions (insert_record, update_record, get_records_by_filter) across the application utilities. By enforcing tuple-based parameterized variables matched against strict %s positional tokens, it guarantees that all frontend form elements treat inputs strictly as literal data values, completely blocking SQL Injection vulnerabilities.
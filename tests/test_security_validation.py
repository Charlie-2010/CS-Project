"""Offline unit tests for credential security and schema-aware validation."""
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from config import DatabaseConfig
from auth.hash_utils import create_password_record, verify_password
from auth.login import Session, WrongRoleError, authenticate_user
from database.connection import (
    ConstraintViolationError,
    DatabaseUnavailableError,
    execute_dml,
    execute_transaction,
    get_connection,
)
from mysql.connector import IntegrityError
from services.academic import create_student, create_teacher, delete_teacher, list_students, update_class
from app import ScholarSync
from utils.helpers import delete_record, get_records_by_filter, insert_record
from utils.validators import ValidationError, validate_class, validate_student, validate_subject, validate_teacher


class PasswordHashTests(unittest.TestCase):
    def test_hashes_are_salted_and_verifiable(self):
        first_hash, first_salt = create_password_record("StrongPass123!")
        second_hash, second_salt = create_password_record("StrongPass123!")
        self.assertEqual(len(first_hash), 64)
        self.assertEqual(len(first_salt), 32)
        self.assertNotEqual(first_salt, second_salt)
        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(verify_password(first_hash, "StrongPass123!", first_salt))
        self.assertFalse(verify_password(first_hash, "not-the-password", first_salt))

    def test_malformed_values_are_rejected(self):
        self.assertFalse(verify_password("a" * 63, "anything", "a" * 32))
        self.assertFalse(verify_password("a" * 64, "anything", "invalid-salt"))


    def test_login_builds_profile_session_and_rejects_wrong_portal(self):
        row = (9, "teacher_one", "a" * 64, "b" * 32, "teacher", 4, None)
        with patch("auth.login.fetch_single_record", return_value=row), patch("auth.login.verify_password", return_value=True):
            session = authenticate_user("teacher_one", "secret", "teacher")
        self.assertEqual(session, Session(9, "teacher_one", "teacher", teacher_id=4))
        with patch("auth.login.fetch_single_record", return_value=row), patch("auth.login.verify_password", return_value=True):
            with self.assertRaises(WrongRoleError):
                authenticate_user("teacher_one", "secret", "student")

    def test_unknown_username_and_wrong_password_share_failure_result(self):
        row = (9, "teacher_one", "a" * 64, "b" * 32, "teacher", 4, None)
        with patch("auth.login.fetch_single_record", return_value=None):
            unknown_user = authenticate_user("missing", "wrong", "teacher")
        with patch("auth.login.fetch_single_record", return_value=row), patch("auth.login.verify_password", return_value=False):
            wrong_password = authenticate_user("teacher_one", "wrong", "teacher")
        self.assertIsNone(unknown_user)
        self.assertEqual(unknown_user, wrong_password)


class DatabaseConfigTests(unittest.TestCase):
    def test_reads_workbench_connection_settings_from_environment(self):
        values = {
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "3307",
            "DB_USER": "workbench_user",
            "DB_PASSWORD": "local-only",
            "DB_NAME": "scholarsync_db",
        }
        with patch.dict("os.environ", values):
            config = DatabaseConfig.from_env()
        self.assertEqual(
            (config.host, config.port, config.user, config.password, config.database),
            ("127.0.0.1", 3307, "workbench_user", "local-only", "scholarsync_db"),
        )


class ValidationTests(unittest.TestCase):
    def test_valid_core_entities(self):
        student = validate_student({"user_id": 1, "roll_number": " 12A-01 ", "first_name": "Ada", "last_name": "Lovelace", "email": "ADA@EXAMPLE.COM", "date_of_birth": "2009-12-10", "class_id": 2})
        self.assertEqual(student["roll_number"], "12A-01")
        self.assertEqual(student["email"], "ada@example.com")
        self.assertEqual(validate_teacher({"user_id": 2, "first_name": "Marie", "last_name": "Curie", "email": "m@example.com", "phone": "9876543210"})["user_id"], 2)
        self.assertEqual(validate_class({"class_name": "Class 12-A", "room_number": "301", "class_teacher_id": 2})["class_name"], "Class 12-A")
        self.assertEqual(validate_subject({"subject_name": "Physics", "subject_code": "phy-12"})["subject_code"], "PHY-12")

    def test_invalid_schema_values_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_student({"user_id": "1"}, partial=True)
        with self.assertRaises(ValidationError):
            validate_subject({"subject_name": "Physics", "subject_code": "bad code"})
        with self.assertRaises(ValidationError):
            validate_class({"class_name": "", "room_number": None, "class_teacher_id": None})

    def test_validation_reports_all_field_errors(self):
        with self.assertRaises(ValidationError) as raised:
            validate_student({"user_id": "bad", "roll_number": "", "first_name": "", "last_name": "",
                              "email": "invalid", "date_of_birth": "bad", "class_id": 0})
        self.assertEqual(set(raised.exception.errors), {
            "user_id", "roll_number", "first_name", "last_name", "email", "date_of_birth", "class_id"
        })
        with self.assertRaises(ValidationError) as raised:
            validate_teacher({"user_id": 1, "first_name": "N" * 51, "last_name": "Valid", "email": "bad", "phone": None})
        self.assertEqual(set(raised.exception.errors), {"first_name", "email"})

    def test_date_of_birth_rejects_future_and_implausible_dates(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        valid_student = {
            "user_id": 1, "roll_number": "R-1", "first_name": "Ada", "last_name": "Lovelace",
            "email": "ada@example.edu", "class_id": 1,
        }
        for dob in (future, "1800-01-01"):
            with self.subTest(date_of_birth=dob), self.assertRaises(ValidationError):
                validate_student({**valid_student, "date_of_birth": dob})

    def test_schema_enforces_global_roll_number_uniqueness(self):
        schema_path = Path(__file__).parents[1] / "database" / "schema.sql"
        schema = schema_path.read_text(encoding="utf-8")
        self.assertIn("UNIQUE KEY unique_roll_number (roll_number)", schema)
        self.assertIn("DROP INDEX unique_roll_number_per_class", schema)


class ServiceBoundaryTests(unittest.TestCase):
    def test_student_session_cannot_access_teacher_student_list(self):
        session = Session(1, "student", "student", student_id=3)
        with patch("services.academic.fetch_all_records") as fetch:
            result = list_students(session)
        self.assertFalse(result.ok)
        self.assertIn("access", result.error or "")
        fetch.assert_not_called()

    def test_duplicate_username_does_not_create_an_orphan_profile(self):
        class Cursor:
            rowcount = 0
            lastrowid = None
            def __init__(self, connection): self.connection = connection
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params):
                if query.startswith("INSERT INTO users"):
                    if params[0] in self.connection.users:
                        raise IntegrityError("duplicate username", errno=1062, sqlstate="23000")
                    self.connection.pending_users.append(params[0])
                    self.lastrowid = 20
                else:
                    self.connection.pending_students.append(params)
                    self.lastrowid = 30
        class Connection:
            def __init__(self):
                self.users = ["existing"]
                self.students = []
                self.pending_users = []
                self.pending_students = []
                self.rolled_back = False
            def cursor(self): return Cursor(self)
            def commit(self):
                self.users.extend(self.pending_users)
                self.students.extend(self.pending_students)
            def rollback(self):
                self.pending_users.clear()
                self.pending_students.clear()
                self.rolled_back = True
            def close(self): pass
        connection = Connection()
        teacher = Session(2, "teacher", "teacher", teacher_id=1)
        student_data = {
            "username": "existing", "password": "longpassword", "roll_number": "12A-99",
            "first_name": "New", "last_name": "Student", "email": "new@example.edu",
            "date_of_birth": "2009-01-01", "class_id": 1,
        }
        with patch("database.connection.get_connection", return_value=connection), \
                patch("services.academic.create_password_record", return_value=("a" * 64, "b" * 32)):
            result = create_student(teacher, student_data)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, 1062)
        self.assertEqual(connection.users, ["existing"])
        self.assertEqual(connection.students, [])
        self.assertTrue(connection.rolled_back)

    def test_missing_class_rolls_back_student_user_insert(self):
        class Cursor:
            rowcount = 1
            lastrowid = 70
            def __init__(self, connection): self.connection = connection
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params):
                if query.startswith("INSERT INTO users"):
                    self.connection.pending_users.append(params)
                elif query.startswith("INSERT INTO students"):
                    raise IntegrityError("missing class", errno=1452, sqlstate="23000")
        class Connection:
            def __init__(self): self.users, self.pending_users, self.rolled_back = [], [], False
            def cursor(self): return Cursor(self)
            def commit(self): self.users.extend(self.pending_users)
            def rollback(self): self.pending_users.clear(); self.rolled_back = True
            def close(self): pass
        connection = Connection()
        teacher = Session(2, "teacher", "teacher", teacher_id=1)
        student_data = {
            "username": "orphan_check", "password": "longpassword", "roll_number": "GLOBAL-99",
            "first_name": "New", "last_name": "Student", "email": "rollback@example.edu",
            "date_of_birth": "2009-01-01", "class_id": 999999,
        }
        with patch("database.connection.get_connection", return_value=connection), \
                patch("services.academic.create_password_record", return_value=("a" * 64, "b" * 32)):
            result = create_student(teacher, student_data)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, 1452)
        self.assertEqual(connection.users, [])
        self.assertTrue(connection.rolled_back)

    def test_referenced_teacher_delete_returns_friendly_message(self):
        teacher = Session(2, "teacher", "teacher", teacher_id=1)
        with patch("services.academic.fetch_single_record", side_effect=[(1,), (0,), (2,)]) as fetch:
            result = delete_teacher(teacher, 7)
        self.assertFalse(result.ok)
        self.assertIn("still reference", result.error or "")
        self.assertEqual(result.data, {"classes": 1, "allocations": 0, "assignments": 2})
        self.assertEqual(fetch.call_count, 3)

    def test_teacher_cannot_delete_their_own_active_account(self):
        teacher = Session(2, "teacher", "teacher", teacher_id=7)
        with patch("services.academic.fetch_single_record") as fetch, \
                patch("services.academic.execute_transaction") as transaction:
            result = delete_teacher(teacher, 7)
        self.assertFalse(result.ok)
        self.assertIn("currently signed in", result.error or "")
        fetch.assert_not_called()
        transaction.assert_not_called()

    def test_teacher_create_inserts_account_and_profile_in_one_transaction(self):
        class Cursor:
            rowcount = 1
            lastrowid = None
            def __init__(self): self.statements = []
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params):
                self.statements.append((query, params))
                self.lastrowid = 10 if query.startswith("INSERT INTO users") else 20
        class Connection:
            def __init__(self): self.cursor_instance, self.commits, self.rollbacks = Cursor(), 0, 0
            def cursor(self): return self.cursor_instance
            def commit(self): self.commits += 1
            def rollback(self): self.rollbacks += 1
            def close(self): pass
        connection = Connection()
        teacher = Session(2, "teacher", "teacher", teacher_id=1)
        data = {"username": "t_new", "password": "longpassword", "first_name": "New",
                "last_name": "Teacher", "email": "new.teacher@example.edu", "phone": ""}
        with patch("database.connection.get_connection", return_value=connection), \
                patch("services.academic.create_password_record", return_value=("a" * 64, "b" * 32)):
            result = create_teacher(teacher, data)
        self.assertTrue(result.ok)
        self.assertEqual(result.data, {"teacher_id": 20})
        self.assertEqual(len(connection.cursor_instance.statements), 2)
        self.assertEqual(connection.commits, 1)
        self.assertEqual(connection.rollbacks, 0)

    def test_class_update_uses_validated_parameterized_fields(self):
        teacher = Session(2, "teacher", "teacher", teacher_id=1)
        with patch("services.academic.execute_dml", return_value=1) as execute:
            result = update_class(teacher, 8, {"room_number": "R-12"})
        self.assertTrue(result.ok)
        query, params = execute.call_args.args
        self.assertIn("room_number = %s", query)
        self.assertEqual(params, ("R-12", 8))


class ParameterizedHelperTests(unittest.TestCase):
    def test_missing_or_wrong_database_password_fails_cleanly(self):
        with patch("database.connection.get_connection", return_value=None):
            with self.assertRaises(DatabaseUnavailableError):
                execute_dml("DELETE FROM subjects WHERE subject_id = %s", (4,))

    def test_invalid_database_port_fails_as_unavailable(self):
        with patch.dict("os.environ", {"DB_PORT": "not-a-port"}):
            self.assertIsNone(get_connection())

    def test_insert_binds_values_and_validates_data(self):
        values = ("Physics", "phy-12")
        with patch("utils.helpers.execute_dml", return_value=1) as execute:
            self.assertEqual(insert_record("subjects", ["subject_name", "subject_code"], values), 1)
        query, params = execute.call_args.args
        self.assertIn("VALUES (%s, %s)", query)
        self.assertEqual(params, ("Physics", "PHY-12"))

    def test_dynamic_identifier_or_filter_injection_is_rejected(self):
        with self.assertRaises(ValidationError):
            insert_record("subjects; DROP TABLE users", ["subject_name"], ("Physics",))
        with self.assertRaises(ValidationError):
            get_records_by_filter("subjects", ["subject_name"], "subject_name = %s OR 1=1", ("Physics",))

    def test_delete_requires_a_non_empty_allowlisted_filter(self):
        with self.assertRaises(ValidationError):
            delete_record("students", "", ())
        with patch("utils.helpers.execute_dml", return_value=1) as execute:
            self.assertEqual(delete_record("students", "student_id = %s", (4,)), 1)
        self.assertEqual(execute.call_args.args, ("DELETE FROM students WHERE student_id = %s", (4,)))

    def test_dml_commits_only_after_successful_parameterized_execution(self):
        class Cursor:
            rowcount = 1
            lastrowid = 7
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params): self.query, self.params = query, params
        class Connection:
            def __init__(self): self.cursor_instance, self.committed, self.closed = Cursor(), False, False
            def cursor(self): return self.cursor_instance
            def commit(self): self.committed = True
            def rollback(self): raise AssertionError("rollback should not run")
            def close(self): self.closed = True
        connection = Connection()
        with patch("database.connection.get_connection", return_value=connection):
            self.assertEqual(execute_dml("DELETE FROM subjects WHERE subject_id = %s", (4,)), 1)
        self.assertEqual(connection.cursor_instance.params, (4,))
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)

    def test_constraint_failure_rolls_back_and_is_reported(self):
        class Cursor:
            rowcount = 0
            lastrowid = None
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params):
                raise IntegrityError("duplicate", errno=1062, sqlstate="23000")
        class Connection:
            def __init__(self): self.rolled_back = self.closed = False
            def cursor(self): return Cursor()
            def commit(self): raise AssertionError("commit should not run")
            def rollback(self): self.rolled_back = True
            def close(self): self.closed = True
        connection = Connection()
        with patch("database.connection.get_connection", return_value=connection):
            with self.assertRaises(ConstraintViolationError) as raised:
                execute_dml("INSERT INTO subjects (subject_name) VALUES (%s)", ("Physics",))
        self.assertEqual(raised.exception.code, 1062)
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)

    def test_foreign_key_error_has_friendly_message(self):
        class Cursor:
            rowcount = 0
            lastrowid = None
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params):
                raise IntegrityError("foreign key", errno=1451, sqlstate="23000")
        class Connection:
            def cursor(self): return Cursor()
            def commit(self): raise AssertionError("commit should not run")
            def rollback(self): pass
            def close(self): pass
        with patch("database.connection.get_connection", return_value=Connection()):
            with self.assertRaises(ConstraintViolationError) as raised:
                execute_dml("DELETE FROM teachers WHERE teacher_id = %s", (1,))
        self.assertEqual(raised.exception.code, 1451)
        self.assertIn("still referenced", str(raised.exception))

    def test_transaction_reuses_one_connection_and_returns_lastrowid(self):
        class Cursor:
            rowcount = 1
            lastrowid = 42
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, query, params): self.query, self.params = query, params
        class Connection:
            def __init__(self): self.cursor_instance, self.commits = Cursor(), 0
            def cursor(self): return self.cursor_instance
            def commit(self): self.commits += 1
            def rollback(self): raise AssertionError("rollback should not run")
            def close(self): pass
        connection = Connection()
        def write(cursor):
            cursor.execute("INSERT INTO users (username) VALUES (%s)", ("new",))
            return "created"
        with patch("database.connection.get_connection", return_value=connection):
            result = execute_transaction(write)
        self.assertEqual((result.value, result.row_count, result.lastrowid), ("created", 1, 42))
        self.assertEqual(connection.commits, 1)

    def test_transaction_rolls_back_after_callback_failure(self):
        class Cursor:
            rowcount = 0
            lastrowid = None
            def __enter__(self): return self
            def __exit__(self, *args): return False
        class Connection:
            def __init__(self): self.rollbacks = 0
            def cursor(self): return Cursor()
            def commit(self): raise AssertionError("commit should not run")
            def rollback(self): self.rollbacks += 1
            def close(self): pass
        connection = Connection()
        with patch("database.connection.get_connection", return_value=connection):
            with self.assertRaisesRegex(ValueError, "fail after first write"):
                execute_transaction(lambda cursor: (_ for _ in ()).throw(ValueError("fail after first write")))
        self.assertEqual(connection.rollbacks, 1)


class ApplicationSessionTests(unittest.TestCase):
    def test_sign_out_clears_session_before_returning_home(self):
        application = ScholarSync.__new__(ScholarSync)
        application.session = Session(1, "teacher", "teacher", teacher_id=1)
        with patch.object(application, "home_page") as home_page:
            application.sign_out()
        self.assertIsNone(application.session)
        home_page.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

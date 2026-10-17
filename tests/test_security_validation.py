"""Offline unit tests for credential security and schema-aware validation."""
import unittest
from unittest.mock import patch

from auth.hash_utils import create_password_record, verify_password
from database.connection import execute_dml
from mysql.connector import IntegrityError
from utils.helpers import get_records_by_filter, insert_record
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


class ParameterizedHelperTests(unittest.TestCase):
    def test_missing_or_wrong_database_password_fails_cleanly(self):
        with patch("database.connection.get_connection", return_value=None):
            self.assertEqual(execute_dml("DELETE FROM subjects WHERE subject_id = %s", (4,)), 0)

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

    def test_dml_commits_only_after_successful_parameterized_execution(self):
        class Cursor:
            rowcount = 1
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
            self.assertEqual(execute_dml("INSERT INTO subjects (subject_name) VALUES (%s)", ("Physics",)), 0)
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()

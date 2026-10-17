"""Live Phase 1 sign-off checks. Requires DB_PASSWORD and a seeded local database."""
from __future__ import annotations

import os
import unittest

from auth.hash_utils import verify_password
from database.connection import execute_dml, fetch_all_records, get_connection
from utils.helpers import insert_record
from utils.validators import ValidationError


class PhaseOneLiveChecks(unittest.TestCase):
    TABLES = (
        "users", "teachers", "classes", "students", "subjects", "teacher_subjects",
        "exams", "exam_subjects", "exam_results", "attendance", "assignments",
    )

    def test_user_password_storage_and_documented_login(self):
        users = fetch_all_records("SELECT username, password_hash, password_salt FROM users")
        self.assertEqual(len(users), 6)
        for username, password_hash, password_salt in users:
            with self.subTest(username=username):
                self.assertEqual(len(password_hash), 64)
                self.assertEqual(len(password_salt), 32)
                self.assertTrue(verify_password(password_hash, "ChangeMe123!", password_salt))

    def test_all_tables_have_seed_data(self):
        for table in self.TABLES:
            with self.subTest(table=table):
                count = fetch_all_records(f"SELECT COUNT(*) FROM {table}")[0][0]
                self.assertGreater(count, 0)

    def test_no_mark_exceeds_its_paper_maximum(self):
        invalid = fetch_all_records(
            "SELECT er.result_id FROM exam_results er "
            "JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id "
            "WHERE er.marks_obtained > es.max_marks"
        )
        self.assertEqual(invalid, [])

    def test_wrong_environment_password_fails_cleanly(self):
        original = os.environ.get("DB_PASSWORD")
        os.environ["DB_PASSWORD"] = "definitely-wrong-password"
        try:
            self.assertIsNone(get_connection())
        finally:
            if original is None:
                os.environ.pop("DB_PASSWORD", None)
            else:
                os.environ["DB_PASSWORD"] = original

    def test_foreign_key_and_duplicate_username_are_rejected(self):
        self.assertEqual(
            execute_dml(
                "INSERT INTO teachers (user_id, first_name, last_name, email) VALUES (%s, %s, %s, %s)",
                (999999, "Failure", "Check", "foreign-key-check@invalid.test"),
            ),
            0,
        )
        self.assertEqual(
            execute_dml(
                "INSERT INTO users (username, password_hash, password_salt, role) VALUES (%s, %s, %s, %s)",
                ("t_albert", "a" * 64, "a" * 32, "teacher"),
            ),
            0,
        )

    def test_helpers_reject_table_names_outside_the_allow_list(self):
        with self.assertRaises(ValidationError):
            insert_record("users", ["username"], ("not-allowed",))


if __name__ == "__main__":
    unittest.main(verbosity=2)

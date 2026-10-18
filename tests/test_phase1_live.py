"""Live Phase 1 sign-off checks. Requires DB_PASSWORD and a seeded local database."""
from __future__ import annotations

import os
import unittest

from auth.hash_utils import verify_password
from database.connection import (
    ConstraintViolationError,
    execute_dml,
    fetch_all_records,
    fetch_single_record,
    get_connection,
)
from utils.helpers import insert_record
from utils.validators import ValidationError


class PhaseOneLiveChecks(unittest.TestCase):
    TABLES = (
        "users", "teachers", "classes", "students", "subjects", "teacher_subjects",
        "exams", "exam_subjects", "exam_results", "attendance", "assignments",
    )

    @classmethod
    def setUpClass(cls):
        connection = get_connection()
        if connection is None:
            raise unittest.SkipTest("Live MySQL checks require a reachable configured database.")
        connection.close()

    def test_user_password_storage_and_documented_login(self):
        users = fetch_all_records("SELECT username, password_hash, password_salt FROM users")
        self.assertEqual(len(users), 9)
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

    def test_each_class_has_exam_papers_and_multiple_students_have_results(self):
        paper_counts = fetch_all_records(
            "SELECT c.class_name, COUNT(es.exam_subject_id) FROM classes c "
            "LEFT JOIN exam_subjects es ON es.class_id = c.class_id GROUP BY c.class_id, c.class_name"
        )
        self.assertTrue(paper_counts)
        self.assertTrue(all(count > 0 for _, count in paper_counts))
        result_students = fetch_single_record("SELECT COUNT(DISTINCT student_id) FROM exam_results")
        self.assertGreater(result_students[0], 1)

    def test_roll_number_has_a_global_unique_index(self):
        indexes = fetch_all_records(
            "SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ',') "
            "FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'students' AND NON_UNIQUE = 0 GROUP BY INDEX_NAME"
        )
        self.assertIn(("roll_number",), indexes)

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
        with self.assertRaises(ConstraintViolationError):
            execute_dml(
                "INSERT INTO teachers (user_id, first_name, last_name, email) VALUES (%s, %s, %s, %s)",
                (999999, "Failure", "Check", "foreign-key-check@invalid.test"),
            )
        with self.assertRaises(ConstraintViolationError):
            execute_dml(
                "INSERT INTO users (username, password_hash, password_salt, role) VALUES (%s, %s, %s, %s)",
                ("t_albert", "a" * 64, "a" * 32, "teacher"),
            )

    def test_helpers_reject_table_names_outside_the_allow_list(self):
        with self.assertRaises(ValidationError):
            insert_record("users", ["username"], ("not-allowed",))


if __name__ == "__main__":
    unittest.main(verbosity=2)

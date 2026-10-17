"""
tests/test_connectivity.py
Unit test script to verify Parameterised Query Architecture execution boundaries.
"""

import sys
import os
import unittest
from typing import Any, cast

# Append project root directory to sys.path to handle module imports seamlessly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import fetch_single_record, fetch_all_records, get_connection


class ParameterizedConnectivityTests(unittest.TestCase):
    def require_database(self):
        connection = get_connection()
        if connection is None:
            self.skipTest("Connectivity checks require a reachable configured MySQL database.")
        connection.close()

    def test_query_parameters_must_be_a_tuple_or_list(self):
        with self.assertRaises(TypeError):
            fetch_single_record("SELECT %s", "value")

    def test_query_values_require_placeholders(self):
        with self.assertRaises(ValueError):
            fetch_single_record("SELECT 1", (1,))

    def test_parameterized_student_lookup_returns_charlie(self):
        self.require_database()
        profile = cast(
            tuple[Any, ...] | None,
            fetch_single_record(
                "SELECT student_id, first_name, last_name, roll_number FROM students WHERE user_id = %s",
                (4,),
            ),
        )
        if profile is None:
            self.fail("Expected to find the seeded Charlie profile.")
        self.assertEqual((profile[1], profile[2]), ("Charlie", "Brown"))

    def test_parameterized_report_card_is_populated(self):
        self.require_database()
        student = cast(tuple[Any, ...] | None,
                   fetch_single_record("SELECT student_id FROM students WHERE user_id = %s", (4,)))
        if student is None:
            self.fail("Expected to find the seeded Charlie student.")
        report_card = fetch_all_records(
            "SELECT sub.subject_name, er.marks_obtained, es.max_marks "
            "FROM exam_results er JOIN exam_subjects es ON er.exam_subject_id = es.exam_subject_id "
            "JOIN subjects sub ON es.subject_id = sub.subject_id JOIN exams e ON es.exam_id = e.exam_id "
            "WHERE er.student_id = %s AND e.exam_name = %s",
            (student[0], "Mid-Term Examination"),
        )
        self.assertTrue(report_card, "Expected a populated report card for s_charlie.")
        self.assertTrue(all(mark <= maximum for _, mark, maximum in report_card))

def verify_parameterised_queries():
    print("====== Running Parameterised Query Architecture Tests ======")
    
    # ------------------------------------------------------------------------
    # TEST 1: Singular Lookup with %s Specifier (Targeting User ID 4 - Charlie Brown)
    # ------------------------------------------------------------------------
    student_query = """
        SELECT student_id, first_name, last_name, roll_number 
        FROM students 
        WHERE user_id = %s;
    """
    # Parameters must ALWAYS be passed as a tuple, even if it contains only 1 item
    student_params = (4,) 
    
    print("\n[Executing Test 1] Fetching singular student record via parameter binding...")
    student_profile = fetch_single_record(student_query, student_params)
    
    if student_profile:
        print(f"[OK] Success! Retrieved Student Profile: {student_profile}")
        student_id = list(student_profile)[0]
    else:
        print("[ERROR] Test 1 Failed: Could not locate student record.")
        return

    # ------------------------------------------------------------------------
    # TEST 2: Multi-Variable Lookup (Targeting Student ID and Exam Term Name)
    # ------------------------------------------------------------------------
    report_card_query = """
        SELECT sub.subject_name, er.marks_obtained, es.max_marks
        FROM exam_results er
        JOIN exam_subjects es ON er.exam_subject_id = es.exam_subject_id
        JOIN subjects sub ON es.subject_id = sub.subject_id
        JOIN exams e ON es.exam_id = e.exam_id
        WHERE er.student_id = %s AND e.exam_name = %s;
    """
    report_params = (student_id, "Mid-Term Examination")
    
    print("\n[Executing Test 2] Fetching multi-parameter report card matrix...")
    report_card_rows = fetch_all_records(report_card_query, report_params)
    
    print(f"[OK] Success! Retrieved {len(report_card_rows)} graded paper records:")
    for row in report_card_rows:
        # Unpack variables directly to satisfy the static checking matrix parameters
        subject_name, marks_obtained, max_marks = row
        print(f"    - {subject_name}: {marks_obtained} / {max_marks}")
if __name__ == "__main__":
    verify_parameterised_queries()

USE scholarsync_db;

-- Every table should have seed rows.
SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'classes', COUNT(*) FROM classes
UNION ALL SELECT 'students', COUNT(*) FROM students
UNION ALL SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL SELECT 'teacher_subjects', COUNT(*) FROM teacher_subjects
UNION ALL SELECT 'exams', COUNT(*) FROM exams
UNION ALL SELECT 'exam_subjects', COUNT(*) FROM exam_subjects
UNION ALL SELECT 'exam_results', COUNT(*) FROM exam_results
UNION ALL SELECT 'attendance', COUNT(*) FROM attendance
UNION ALL SELECT 'assignments', COUNT(*) FROM assignments;

-- Populated report cards for all students, grouped by examination.
SELECT c.class_name, s.roll_number, CONCAT(s.first_name, ' ', s.last_name) AS student,
	   e.exam_name, sub.subject_name, er.marks_obtained, es.max_marks, er.remarks
FROM exam_results er
JOIN students s ON s.student_id = er.student_id
JOIN classes c ON c.class_id = s.class_id
JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id
JOIN exams e ON e.exam_id = es.exam_id
JOIN subjects sub ON sub.subject_id = es.subject_id
ORDER BY c.class_name, s.roll_number, e.exam_name, sub.subject_name;

-- Class paper coverage, including the previously empty Class 12-B.
SELECT c.class_name, COUNT(es.exam_subject_id) AS paper_count
FROM classes c
LEFT JOIN exam_subjects es ON es.class_id = c.class_id
GROUP BY c.class_id, c.class_name
ORDER BY c.class_name;

-- Integrity check: this query must return no rows.
SELECT er.result_id, er.marks_obtained, es.max_marks
FROM exam_results er
JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id
WHERE er.marks_obtained > es.max_marks;

-- Verify global roll-number uniqueness.
SELECT roll_number, COUNT(*) AS duplicate_count
FROM students
GROUP BY roll_number
HAVING COUNT(*) > 1;

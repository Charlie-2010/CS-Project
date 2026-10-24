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
JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id
JOIN classes c ON c.class_id = es.class_id
JOIN exams e ON e.exam_id = es.exam_id
JOIN subjects sub ON sub.subject_id = es.subject_id
ORDER BY c.class_name, s.roll_number, e.exam_name, sub.subject_name;

-- Student totals, percentage, and letter grade for each exam.
-- Grade scale: A >= 90%, B >= 80%, C >= 70%, D >= 60%, otherwise F.
-- Percentages use only papers with a recorded result.
SELECT e.exam_name, c.class_name, s.roll_number,
    CONCAT(s.first_name, ' ', s.last_name) AS student,
    COUNT(er.result_id) AS papers_graded,
    SUM(er.marks_obtained) AS total_marks,
    SUM(es.max_marks) AS possible_marks,
    ROUND(100.0 * SUM(er.marks_obtained) / NULLIF(SUM(es.max_marks), 0), 2)
    AS percentage,
    CASE
        WHEN SUM(es.max_marks) IS NULL OR SUM(es.max_marks) = 0 THEN NULL
        WHEN 100.0 * SUM(er.marks_obtained) / NULLIF(SUM(es.max_marks), 0) >= 90 THEN 'A'
        WHEN 100.0 * SUM(er.marks_obtained) / NULLIF(SUM(es.max_marks), 0) >= 80 THEN 'B'
        WHEN 100.0 * SUM(er.marks_obtained) / NULLIF(SUM(es.max_marks), 0) >= 70 THEN 'C'
        WHEN 100.0 * SUM(er.marks_obtained) / NULLIF(SUM(es.max_marks), 0) >= 60 THEN 'D'
        ELSE 'F'
    END AS grade
FROM exam_results er
JOIN students s ON s.student_id = er.student_id
JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id
JOIN classes c ON c.class_id = es.class_id
JOIN exams e ON e.exam_id = es.exam_id
GROUP BY e.exam_id, e.exam_name, c.class_id, c.class_name, s.student_id, s.roll_number, s.first_name, s.last_name
ORDER BY e.exam_name, c.class_name, percentage DESC, s.roll_number;

-- Subject averages and highest/lowest recorded marks for each exam paper.
-- The percentage average normalizes results when papers have different maximum marks.
SELECT e.exam_name, c.class_name, sub.subject_name,
    COUNT(er.result_id) AS students_graded,
    ROUND(AVG(er.marks_obtained), 2) AS average_marks,
    ROUND(AVG(100.0 * er.marks_obtained / NULLIF(es.max_marks, 0)), 2) AS average_percentage,
    MAX(er.marks_obtained) AS highest_marks,
    MIN(er.marks_obtained) AS lowest_marks
FROM exam_subjects es
JOIN exams e ON e.exam_id = es.exam_id
JOIN classes c ON c.class_id = es.class_id
JOIN subjects sub ON sub.subject_id = es.subject_id
LEFT JOIN exam_results er ON er.exam_subject_id = es.exam_subject_id
GROUP BY es.exam_subject_id, e.exam_name, c.class_name, sub.subject_name
ORDER BY e.exam_name, c.class_name, sub.subject_name;

-- Student rank list by exam and class (MySQL 8.0+).
-- RANK gives students with equal percentages the same position.
WITH student_exam_totals AS (
    SELECT e.exam_id, e.exam_name, c.class_id, c.class_name,
        s.student_id, s.roll_number, s.first_name, s.last_name,
        SUM(er.marks_obtained) AS total_marks,
        SUM(es.max_marks) AS possible_marks
    FROM exam_results er
    JOIN students s ON s.student_id = er.student_id
    JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id
    JOIN classes c ON c.class_id = es.class_id
    JOIN exams e ON e.exam_id = es.exam_id
    GROUP BY e.exam_id, e.exam_name, c.class_id, c.class_name, s.student_id, s.roll_number, s.first_name, s.last_name
),
ranked_students AS (
    SELECT student_exam_totals.*, ROUND(100.0 * total_marks / NULLIF(possible_marks, 0), 2) AS percentage,
    RANK() OVER (PARTITION BY exam_id, class_id ORDER BY total_marks / NULLIF(possible_marks, 0) DESC) AS exam_rank
    FROM student_exam_totals
)
SELECT exam_name, class_name, exam_rank, roll_number,
       CONCAT(first_name, ' ', last_name) AS student,
       total_marks, possible_marks, percentage
FROM ranked_students
ORDER BY exam_name, class_name, exam_rank, roll_number;

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

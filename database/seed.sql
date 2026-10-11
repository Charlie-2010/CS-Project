# seed.sql - Implementation placeholder
USE student_performance_system;

-- Clear any pre-existing rows before seeding (in reverse constraint order)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE exam_results;
TRUNCATE TABLE exam_subjects;
TRUNCATE TABLE exams;
TRUNCATE TABLE teacher_subjects;
TRUNCATE TABLE subjects;
TRUNCATE TABLE students;
TRUNCATE TABLE classes;
TRUNCATE TABLE teachers;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 1. POPULATE USERS (Passwords represented as mock SHA-256 strings)
-- ============================================================================
INSERT INTO users (user_id, username, password_hash, role) VALUES
(1, 't_albert', 'e9c0f8b801f1f9e2e6b2016da01f9b33a7e584', 'teacher'),
(2, 't_marie', 'b5c0f8b801f1f9e2e6b2016da01f9b33a7e585', 'teacher'),
(3, 't_isaac', 'a4c0f8b801f1f9e2e6b2016da01f9b33a7e586', 'teacher'),
(4, 's_charlie', '7c4a8d09ca3762af61e59520943dc26494f8941', 'student'),
(5, 's_linus', '8d4a8d09ca3762af61e59520943dc26494f8942', 'student'),
(6, 's_ada', '9e4a8d09ca3762af61e59520943dc26494f8943', 'student');

-- ============================================================================
-- 2. POPULATE TEACHERS
-- ============================================================================
INSERT INTO teachers (teacher_id, user_id, first_name, last_name, email, phone) VALUES
(1, 1, 'Albert', 'Einstein', 'albert.e@school.edu', '9876543210'),
(2, 2, 'Marie', 'Curie', 'marie.c@school.edu', '9876543211'),
(3, 3, 'Isaac', 'Newton', 'isaac.n@school.edu', '9876543212');

-- ============================================================================
-- 3. POPULATE CLASSES (Linking core homeroom managers)
-- ============================================================================
INSERT INTO classes (class_id, class_name, room_number, class_teacher_id) VALUES
(1, 'Class 12-A', 'Room 301', 1),
(2, 'Class 12-B', 'Room 302', 2);

-- ============================================================================
-- 4. POPULATE STUDENTS
-- ============================================================================
INSERT INTO students (student_id, user_id, roll_number, first_name, last_name, email, date_of_birth, class_id) VALUES
(1, 4, '202612A01', 'Charlie', 'Brown', 'charlie.b@student.edu', '2009-04-12', 1),
(2, 5, '202612A02', 'Linus', 'VanPelt', 'linus.v@student.edu', '2009-08-22', 1),
(3, 6, '202612B01', 'Ada', 'Lovelace', 'ada.l@student.edu', '2009-12-10', 2);

-- ============================================================================
-- 5. POPULATE SUBJECTS
-- ============================================================================
INSERT INTO subjects (subject_id, subject_name, subject_code) VALUES
(1, 'Physics', 'PHY12'),
(2, 'Chemistry', 'CHM12'),
(3, 'Mathematics', 'MAT12'),
(4, 'Computer Science', 'CS12');

-- ============================================================================
-- 6. POPULATE TEACHER_SUBJECTS (Mapping workloads)
-- ============================================================================
INSERT INTO teacher_subjects (teacher_id, class_id, subject_id) VALUES
(1, 1, 1), -- Einstein teaches Physics to 12-A
(1, 2, 1), -- Einstein teaches Physics to 12-B
(2, 1, 2), -- Curie teaches Chemistry to 12-A
(3, 1, 3), -- Newton teaches Mathematics to 12-A
(3, 1, 4); -- Newton teaches Computer Science to 12-A

-- ============================================================================
-- 7. POPULATE EXAMS
-- ============================================================================
INSERT INTO exams (exam_id, exam_name, term, academic_year) VALUES
(1, 'Mid-Term Examination', 'Term 1', '2026-2027'),
(2, 'Final-Term Examination', 'Term 2', '2026-2027');

-- ============================================================================
-- 8. POPULATE EXAM_SUBJECTS
-- ============================================================================
INSERT INTO exam_subjects (exam_subject_id, exam_id, subject_id, class_id, exam_date, max_marks, passing_marks) VALUES
(1, 1, 1, 1, '2026-10-15', 100.00, 33.00), -- 12-A Physics Mid-Term
(2, 1, 3, 1, '2026-10-17', 100.00, 33.00), -- 12-A Math Mid-Term
(3, 1, 4, 1, '2026-10-19', 50.00, 17.00);  -- 12-A CS Mid-Term
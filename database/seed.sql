-- Deterministic local demo data for every application table.
USE scholarsync_db;

-- Clear any pre-existing rows before seeding (in reverse constraint order)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE assignments;
TRUNCATE TABLE attendance;
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
-- 1. POPULATE USERS
-- Development password for each sample account: ChangeMe123!
-- Hashes use PBKDF2-HMAC-SHA256; never use this password outside local demos.
-- ============================================================================
INSERT INTO users (user_id, username, password_hash, password_salt, role) VALUES
(1, 't_albert', '5d9fd92205fd1edef95cdcc836f3b6bd71d75e699bbd0753129468f18736bd71', 'fc9481e54ab03957102477fe6a03dd22', 'teacher'),
(2, 't_marie', '9571a0156501611109243bf174a24045fa94403dceaa101f267214ae42ac19c0', '8bc7fc5dcc969ca37edc0eab6074a7f3', 'teacher'),
(3, 't_isaac', '8038e15418911a3e1ba7e21860a381c498dc0cb5943efd25d308220764a46624', '4d7ce5215ca0eda11160af540271b766', 'teacher'),
(4, 's_charlie', '2342b0f71a4eacf1afd97f8181f2263f0103fdff2f1825123d0b3e4f58730a54', 'c9a43bdae9a98cbd8bc8aa1200427323', 'student'),
(5, 's_linus', 'dd8217b7223f7b7d4790dc36a0b9c4053a01b103b0c78b81ebaa43055a913914', 'e5f8ebe1e1bc47bbbee098808ccba0ba', 'student'),
(6, 's_ada', '5cedc67ab535b6b290dedee42ad0fe77e796d0457d2067ed1803ecb6c08b31fa', '9d295de09b1107e51a445c95c0a4d4ba', 'student'),
(7, 's_grace', '7ac1a930f17f1e9c980213317ed873073c1a7648d2041747908469c7bb174040', '441a87ca02dc39033c2d92f13b9558e7', 'student'),
(8, 's_katherine', '802df7ad90d612eee3a36cb14fd2b78961d048c1f6a73461effd01c0416608ea', '091cce5f7e4b10fceae372df7c9f082f', 'student'),
(9, 's_dorothy', 'a05d83027a4352399746e71274a1c9de6a22e9c454175475433f26dfc4e18799', 'c83786859025a6ff9459109a7c82a8b2', 'student');

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
 (3, 6, '202612B01', 'Ada', 'Lovelace', 'ada.l@student.edu', '2009-12-10', 2),
 (4, 7, '202612B02', 'Grace', 'Hopper', 'grace.h@student.edu', '2009-12-09', 2),
 (5, 8, '202612B03', 'Katherine', 'Johnson', 'katherine.j@student.edu', '2009-08-26', 2),
 (6, 9, '202612A03', 'Dorothy', 'Vaughan', 'dorothy.v@student.edu', '2009-09-20', 1);

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
 (2, 2, 2), -- Curie teaches Chemistry to 12-B
 (3, 1, 3), -- Newton teaches Mathematics to 12-A
 (3, 1, 4), -- Newton teaches Computer Science to 12-A
 (3, 2, 3), -- Newton teaches Mathematics to 12-B
 (3, 2, 4); -- Newton teaches Computer Science to 12-B

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
(1, 1, 1, 1, '2026-10-10', 100.00, 33.00), -- 12-A Physics Mid-Term
(2, 1, 3, 1, '2026-10-12', 100.00, 33.00), -- 12-A Math Mid-Term
 (3, 1, 4, 1, '2026-10-14', 50.00, 17.00), -- 12-A CS Mid-Term
 (4, 1, 1, 2, '2026-10-11', 100.00, 33.00), -- 12-B Physics Mid-Term
 (5, 1, 2, 2, '2026-10-13', 100.00, 33.00), -- 12-B Chemistry Mid-Term
 (6, 1, 3, 2, '2026-10-15', 100.00, 33.00), -- 12-B Math Mid-Term
 (7, 1, 4, 2, '2026-10-16', 50.00, 17.00);  -- 12-B CS Mid-Term

-- ============================================================================
-- 9-11. RESULTS, ATTENDANCE, AND ASSIGNMENTS (all remaining tables non-empty)
-- ============================================================================
INSERT INTO exam_results (student_id, exam_subject_id, marks_obtained, remarks) VALUES
(1, 1, 91.00, 'Excellent'),
(1, 2, 88.00, 'Very good'),
 (1, 3, 47.00, 'Strong practical work'),
 (2, 1, 84.00, 'Consistent work'),
 (2, 2, 93.00, 'Excellent'),
 (2, 3, 44.00, 'Strong practical work'),
 (3, 4, 96.00, 'Excellent'),
 (3, 5, 89.00, 'Very good'),
 (3, 6, 91.00, 'Excellent'),
 (3, 7, 48.00, 'Strong practical work'),
 (4, 4, 90.00, 'Very good'),
 (4, 5, 95.00, 'Excellent'),
 (4, 6, 87.00, 'Good progress'),
 (4, 7, 46.00, 'Strong practical work'),
 (5, 4, 88.00, 'Good progress'),
 (5, 5, 82.00, 'Consistent work'),
 (5, 6, 94.00, 'Excellent'),
 (5, 7, 43.00, 'Very good'),
 (6, 1, 92.00, 'Excellent'),
 (6, 2, 85.00, 'Very good'),
 (6, 3, 49.00, 'Excellent');

INSERT INTO attendance (student_id, class_id, date, status) VALUES
(1, 1, '2026-10-14', 'Present'),
(2, 1, '2026-10-14', 'Present'),
 (3, 2, '2026-10-14', 'Late'),
 (4, 2, '2026-10-14', 'Present'),
 (5, 2, '2026-10-14', 'Present'),
 (6, 1, '2026-10-14', 'Excused');

INSERT INTO assignments (title, description, class_id, subject_id, teacher_id, due_date, max_points) VALUES
('Physics Numericals', 'Complete the assigned numerical problems.', 1, 1, 1, '2026-10-25', 20),
('Chemistry Revision', 'Revise bonding and submit notes.', 1, 2, 2, '2026-10-26', 20),
 ('Mathematics Practice', 'Solve the calculus worksheet.', 1, 3, 3, '2026-10-27', 25),
 ('Class 12-B Physics Lab', 'Submit the motion experiment report.', 2, 1, 1, '2026-10-28', 25),
 ('Class 12-B Chemistry Notes', 'Prepare notes on chemical bonding.', 2, 2, 2, '2026-10-29', 20);

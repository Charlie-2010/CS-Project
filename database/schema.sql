-- ScholarSync relational schema.
-- ============================================================================
-- DATABASE INITIALIZATION
-- ============================================================================
CREATE DATABASE IF NOT EXISTS student_performance_system;
USE student_performance_system;

-- ============================================================================
-- 1. USERS TABLE (Unified authentication for both Teacher & Student personas)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash CHAR(64) NOT NULL,     -- PBKDF2-SHA256 output
    password_salt CHAR(32) NOT NULL,     -- 16 random bytes encoded as hex
    role ENUM('teacher', 'student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. TEACHERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================================
-- 3. CLASSES TABLE (e.g., Grade 10-A, Grade 11-B)
-- ============================================================================
CREATE TABLE IF NOT EXISTS classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(20) UNIQUE NOT NULL, -- e.g., 'Class 10-A'
    room_number VARCHAR(10),
    class_teacher_id INT UNIQUE, -- One teacher can manage only one homeroom class
    FOREIGN KEY (class_teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
);

-- ============================================================================
-- 4. STUDENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    roll_number VARCHAR(20) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    class_id INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE SET NULL,
    UNIQUE KEY unique_roll_number (roll_number)
);

-- Migrate databases created with the earlier per-class roll-number index.
SET @drop_per_class_roll_index = (
    SELECT IF(COUNT(*) > 0,
        'ALTER TABLE students DROP INDEX unique_roll_number_per_class',
        'SELECT 1')
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'students'
      AND INDEX_NAME = 'unique_roll_number_per_class'
);
PREPARE drop_per_class_roll_index FROM @drop_per_class_roll_index;
EXECUTE drop_per_class_roll_index;
DEALLOCATE PREPARE drop_per_class_roll_index;

SET @add_global_roll_index = (
    SELECT IF(COUNT(*) = 0,
        'ALTER TABLE students ADD UNIQUE KEY unique_roll_number (roll_number)',
        'SELECT 1')
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'students'
      AND INDEX_NAME = 'unique_roll_number'
);
PREPARE add_global_roll_index FROM @add_global_roll_index;
EXECUTE add_global_roll_index;
DEALLOCATE PREPARE add_global_roll_index;

-- ============================================================================
-- 5. SUBJECTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'Mathematics', 'Physics'
    subject_code VARCHAR(10) UNIQUE NOT NULL  -- e.g., 'MATH101'
);

-- ============================================================================
-- 6. TEACHER_SUBJECTS TABLE (Many-to-Many allocation mapping course workloads)
-- ============================================================================
CREATE TABLE IF NOT EXISTS teacher_subjects (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    class_id INT NOT NULL,
    subject_id INT NOT NULL,
    UNIQUE KEY unique_allocation (teacher_id, class_id, subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);

-- ============================================================================
-- 7. EXAMS TABLE (The overarching exam cycle/term metadata)
-- ============================================================================
CREATE TABLE IF NOT EXISTS exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_name VARCHAR(50) NOT NULL, -- e.g., 'Mid-Term 2026', 'Final Term'
    term VARCHAR(20) NOT NULL,      -- e.g., 'Term 1', 'Term 2'
    academic_year VARCHAR(10) NOT NULL -- e.g., '2026-2027'
);

-- ============================================================================
-- 8. EXAM_SUBJECTS TABLE (Tracks specific exam papers scheduling and max marks)
-- ============================================================================
CREATE TABLE IF NOT EXISTS exam_subjects (
    exam_subject_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    subject_id INT NOT NULL,
    class_id INT NOT NULL,
    exam_date DATE NOT NULL,
    max_marks DECIMAL(5,2) DEFAULT 100.00,
    passing_marks DECIMAL(5,2) DEFAULT 33.00,
    UNIQUE KEY unique_exam_paper (exam_id, subject_id, class_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE
);

-- ============================================================================
-- 9. EXAM_RESULTS TABLE (The actual matrix tracking scores against papers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS exam_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    exam_subject_id INT NOT NULL,
    marks_obtained DECIMAL(5,2) NOT NULL,
    remarks VARCHAR(255),
    UNIQUE KEY unique_student_score (student_id, exam_subject_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_subject_id) REFERENCES exam_subjects(exam_subject_id) ON DELETE CASCADE
);

-- ============================================================================
-- 10. ATTENDANCE TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late', 'Excused') NOT NULL,
    UNIQUE KEY unique_daily_attendance (student_id, date),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE
);

-- ============================================================================
-- 11. ASSIGNMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    class_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    due_date DATE NOT NULL,
    max_points INT DEFAULT 100,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE
);

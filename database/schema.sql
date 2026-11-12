-- CogniPlan MySQL 8.0 schema. Run this file in MySQL Workbench.
CREATE DATABASE IF NOT EXISTS cogniplan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cogniplan_db;

CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_username (username), UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_preferences (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  theme_mode VARCHAR(10) NOT NULL DEFAULT 'light',
  daily_task_goal SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  widget_layout JSON NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_preferences_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT chk_preferences_theme CHECK (theme_mode IN ('light','dark','system'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  category_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  category_name VARCHAR(100) NOT NULL,
  color_code CHAR(7) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_category_name_per_user (user_id, category_name),
  KEY idx_categories_user (user_id),
  CONSTRAINT fk_categories_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS projects (
  project_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  project_name VARCHAR(150) NOT NULL,
  description TEXT NULL,
  color_code CHAR(7) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  start_date DATE NULL,
  end_date DATE NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_projects_user (user_id),
  CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT chk_projects_status CHECK (status IN ('ACTIVE','COMPLETED','ARCHIVED')),
  CONSTRAINT chk_projects_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tasks (
  task_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  client_key VARCHAR(100) NULL,
  category_id BIGINT UNSIGNED NULL,
  project_id BIGINT UNSIGNED NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  priority VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
  status VARCHAR(20) NOT NULL DEFAULT 'Draft',
  due_date DATETIME NULL,
  estimated_minutes INT UNSIGNED NOT NULL DEFAULT 0,
  actual_minutes INT UNSIGNED NOT NULL DEFAULT 0,
  progress TINYINT UNSIGNED NOT NULL DEFAULT 0,
  is_starred BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  KEY idx_tasks_user_due (user_id, due_date), KEY idx_tasks_user_status (user_id, status),
  UNIQUE KEY uq_tasks_client_key (user_id, client_key),
  CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_tasks_category FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
  CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
  CONSTRAINT chk_tasks_priority CHECK (priority IN ('LOW','MEDIUM','HIGH','URGENT')),
  CONSTRAINT chk_tasks_status CHECK (status IN ('Draft','In Progress','Editing','Done')),
  CONSTRAINT chk_tasks_progress CHECK (progress BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS calendar_events (
  event_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  task_id BIGINT UNSIGNED NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  start_at DATETIME NOT NULL,
  end_at DATETIME NULL,
  event_type VARCHAR(30) NOT NULL DEFAULT 'PERSONAL',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_events_user_start (user_id, start_at),
  CONSTRAINT fk_events_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_events_task FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE SET NULL,
  CONSTRAINT chk_events_time CHECK (end_at IS NULL OR end_at >= start_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productivity_logs (
  log_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  log_date DATE NOT NULL,
  tasks_completed INT UNSIGNED NOT NULL DEFAULT 0,
  focus_time_minutes INT UNSIGNED NOT NULL DEFAULT 0,
  streak_count INT UNSIGNED NOT NULL DEFAULT 0,
  UNIQUE KEY uq_productivity_user_date (user_id, log_date),
  CONSTRAINT fk_productivity_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversations (
  conversation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_1_id BIGINT UNSIGNED NOT NULL,
  user_2_id BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_conversation_pair (user_1_id, user_2_id),
  CONSTRAINT fk_conversations_user1 FOREIGN KEY (user_1_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_conversations_user2 FOREIGN KEY (user_2_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT chk_conversation_distinct_users CHECK (user_1_id < user_2_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS messages (
  message_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  conversation_id BIGINT UNSIGNED NOT NULL,
  sender_id BIGINT UNSIGNED NOT NULL,
  message_text TEXT NOT NULL,
  sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  KEY idx_messages_conversation_time (conversation_id, sent_at),
  CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

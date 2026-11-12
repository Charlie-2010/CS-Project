-- CogniPlan SQL reference for MySQL Connector/Python.
-- These are backend examples. Do not run the entire file as a script: %s values
-- are bound by Python cursor.execute(query, params).
USE cogniplan_db;

-- AUTH
INSERT INTO users (username,email,password_hash) VALUES (%s,%s,%s);
SELECT user_id,username,email,password_hash FROM users WHERE email=%s OR username=%s LIMIT 1;
SELECT user_id,username,email,created_at FROM users WHERE user_id=%s;
UPDATE users SET username=%s,email=%s WHERE user_id=%s;

-- TASKS
SELECT task_id,client_key,title,description,category_id,project_id,priority,status,due_date,
       estimated_minutes,actual_minutes,progress,is_starred,created_at,completed_at
FROM tasks WHERE user_id=%s ORDER BY due_date IS NULL,due_date,created_at DESC;
INSERT INTO tasks(user_id,client_key,title,description,priority,status)
VALUES(%s,%s,%s,%s,%s,%s);
UPDATE tasks SET title=%s,description=%s,priority=%s,status=%s,
  completed_at=CASE WHEN %s='Done' THEN COALESCE(completed_at,NOW()) ELSE NULL END
WHERE task_id=%s AND user_id=%s;
DELETE FROM tasks WHERE task_id=%s AND user_id=%s;

-- CATEGORIES
SELECT category_id,category_name,color_code FROM categories WHERE user_id=%s ORDER BY category_name;
INSERT INTO categories(user_id,category_name,color_code) VALUES(%s,%s,%s);
UPDATE categories SET category_name=%s,color_code=%s WHERE category_id=%s AND user_id=%s;
UPDATE tasks SET category_id=NULL WHERE category_id=%s AND user_id=%s;
DELETE FROM categories WHERE category_id=%s AND user_id=%s;

-- PREFERENCES
SELECT theme_mode,daily_task_goal,widget_layout FROM user_preferences WHERE user_id=%s;
INSERT INTO user_preferences(user_id,theme_mode,daily_task_goal,widget_layout)
VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE theme_mode=VALUES(theme_mode),
 daily_task_goal=VALUES(daily_task_goal),widget_layout=VALUES(widget_layout);

-- CALENDAR
SELECT event_id,task_id,title,description,start_at,end_at,event_type FROM calendar_events WHERE user_id=%s ORDER BY start_at;
INSERT INTO calendar_events(user_id,task_id,title,description,start_at,end_at,event_type)
VALUES(%s,%s,%s,%s,%s,%s,%s);

-- REPORTS
SELECT COUNT(*) total_tasks,COALESCE(SUM(status='Done'),0) completed_tasks,
 COALESCE(SUM(status<>'Done'),0) open_tasks,COALESCE(SUM(actual_minutes),0) actual_minutes,
 COALESCE(AVG(progress),0) average_progress FROM tasks WHERE user_id=%s;

-- PRODUCTIVITY
INSERT INTO productivity_logs(user_id,log_date,tasks_completed,focus_time_minutes,streak_count)
VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE tasks_completed=VALUES(tasks_completed),
 focus_time_minutes=VALUES(focus_time_minutes),streak_count=VALUES(streak_count);

-- MESSAGING: normalize the pair in Python or use LEAST/GREATEST.
INSERT INTO conversations(user_1_id,user_2_id) VALUES(LEAST(%s,%s),GREATEST(%s,%s))
ON DUPLICATE KEY UPDATE conversation_id=LAST_INSERT_ID(conversation_id);
SELECT message_id,sender_id,message_text,sent_at,is_read FROM messages
WHERE conversation_id=%s ORDER BY sent_at;

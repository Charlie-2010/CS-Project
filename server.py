"""CogniPlan Flask application. Run with: python server.py"""
import os
from datetime import date, datetime
from functools import wraps
from pathlib import Path

import mysql.connector
from mysql.connector import IntegrityError, Error as MySQLError
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session, send_from_directory, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
app = Flask(__name__, static_folder=None)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-only-change-this-secret")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0").lower() in ("1", "true", "yes"),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)


def db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "cogniplan_db"),
        autocommit=False,
    )


def query(sql, params=(), one=False, commit=False):
    conn = db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        return cur.fetchone() if one else cur.fetchall()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return json_error("Please sign in to continue.", 401)
        return fn(*args, **kwargs)
    return wrapped


def current_user_id():
    return int(session["user_id"])


def body():
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def valid_email(value):
    value = str(value or "").strip()
    if len(value) > 255 or value.count("@") != 1:
        return False
    local, domain = value.rsplit("@", 1)
    return bool(local and domain and "." in domain and not any(ch.isspace() for ch in value))


def clean_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return str(value).replace("T", " ")[:19]


@app.get("/api/health")
def health():
    try:
        row = query("SELECT VERSION() AS version", one=True)
        return jsonify({"ok": True, "database": "connected", "mysql_version": row["version"]})
    except MySQLError as exc:
        app.logger.warning("Database health check failed: %s", exc)
        return json_error("Database connection is unavailable. Check the MySQL settings and server.", 503)


@app.post("/api/auth/register")
def register():
    data = body()
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not username or len(username) > 50:
        return json_error("Enter a username between 1 and 50 characters.")
    if not valid_email(email):
        return json_error("Enter a valid email address.")
    if len(password) < 8:
        return json_error("Password must contain at least 8 characters.")
    try:
        conn = db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,email,password_hash) VALUES (%s,%s,%s)",
                        (username, email, generate_password_hash(password)))
            uid = cur.lastrowid
            cur.execute("INSERT INTO user_preferences (user_id) VALUES (%s)", (uid,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        session.clear()
        session["user_id"] = uid
        session["username"] = username
        return jsonify({"ok": True, "user": {"user_id": uid, "username": username, "email": email}}), 201
    except IntegrityError:
        return json_error("That username or email is already registered.", 409)
    except MySQLError as exc:
        app.logger.exception("Account creation failed")
        return json_error("Could not create account. Please try again.", 500)


@app.post("/api/auth/login")
def login():
    data = body()
    identity = str(data.get("identity", data.get("email", ""))).strip()
    password = str(data.get("password", ""))
    user = query("SELECT user_id, username, email, password_hash FROM users WHERE email=%s OR username=%s LIMIT 1",
                 (identity.lower(), identity), one=True)
    if not user or not check_password_hash(user["password_hash"], password):
        return json_error("Incorrect username/email or password.", 401)
    session.clear()
    session["user_id"] = int(user["user_id"])
    session["username"] = user["username"]
    return jsonify({"ok": True, "user": {"user_id": user["user_id"], "username": user["username"], "email": user["email"]}})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def me():
    if not session.get("user_id"):
        return jsonify({"authenticated": False})
    user = query("SELECT user_id,username,email,created_at FROM users WHERE user_id=%s", (current_user_id(),), one=True)
    return jsonify({"authenticated": bool(user), "user": user})


@app.get("/api/profile")
@login_required
def get_profile():
    user = query("SELECT user_id,username,email,timezone,created_at,updated_at FROM users WHERE user_id=%s", (current_user_id(),), one=True)
    return jsonify({"ok": True, "profile": user})


@app.put("/api/profile")
@login_required
def update_profile():
    data = body(); username = str(data.get("username", "")).strip(); email = str(data.get("email", "")).strip().lower(); timezone = str(data.get("timezone", "UTC")).strip()
    if not username or len(username) > 50 or not valid_email(email) or not timezone or len(timezone) > 64:
        return json_error("Enter a valid username and email.")
    try:
        query("UPDATE users SET username=%s,email=%s,timezone=%s WHERE user_id=%s", (username,email,timezone,current_user_id()), commit=True)
        session["username"] = username
        return get_profile()
    except IntegrityError:
        return json_error("That username or email is already in use.", 409)


@app.get("/api/tasks")
@login_required
def get_tasks():
    # Give pre-sync tasks a stable client key so the browser can update/delete
    # their existing database rows instead of creating duplicates.
    query("UPDATE tasks SET client_key=CONCAT('db-',task_id) WHERE user_id=%s AND client_key IS NULL",
          (current_user_id(),), commit=True)
    rows = query("""SELECT t.task_id,t.client_key,t.title,t.description,t.category_id,t.project_id,t.priority,t.status,
        t.due_date,t.estimated_minutes,t.actual_minutes,t.progress,t.is_starred,t.created_at,t.updated_at,t.completed_at,
        c.category_name FROM tasks t LEFT JOIN categories c ON c.category_id=t.category_id
        WHERE t.user_id=%s ORDER BY t.due_date IS NULL,t.due_date,t.created_at DESC""", (current_user_id(),))
    for r in rows:
        r["id"] = str(r.get("client_key") or r["task_id"]); r["category"] = r.get("category_name") or "Uncategorized"; r["favorite"] = bool(r["is_starred"])
        for k in ("created_at", "updated_at", "completed_at", "due_date"):
            if r.get(k): r[k] = r[k].isoformat(sep=" ") if isinstance(r[k], datetime) else str(r[k])
    return jsonify({"ok": True, "tasks": rows})


@app.post("/api/tasks")
@login_required
def create_task():
    d=body(); title=str(d.get("title", "")).strip()
    if not title: return json_error("Task title is required.")
    status=d.get("status", "Draft"); priority=str(d.get("priority", "MEDIUM")).upper()
    if status not in ("Draft","In Progress","Editing","Done") or priority not in ("LOW","MEDIUM","HIGH","URGENT"):
        return json_error("Invalid task status or priority.")
    uid=current_user_id(); category_id=d.get("category_id") or None; project_id=d.get("project_id") or None
    if category_id and not query("SELECT category_id FROM categories WHERE category_id=%s AND user_id=%s",(category_id,uid),one=True): return json_error("Invalid category.")
    if project_id and not query("SELECT project_id FROM projects WHERE project_id=%s AND user_id=%s",(project_id,uid),one=True): return json_error("Invalid project.")
    task_id=query("""INSERT INTO tasks (user_id,category_id,project_id,title,description,priority,status,due_date,estimated_minutes,actual_minutes,progress,is_starred,completed_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,IF(%s='Done',NOW(),NULL))""",
        (uid,category_id,project_id,title,d.get("description"),priority,status,clean_date(d.get("due_date")),int(d.get("estimated_minutes",0) or 0),int(d.get("actual_minutes",0) or 0),int(d.get("progress",100 if status=="Done" else 0) or 0),bool(d.get("is_starred",d.get("favorite",False))),status),commit=True)
    return jsonify({"ok":True,"task_id":task_id}),201


@app.put("/api/tasks/<int:task_id>")
@login_required
def update_task(task_id):
    d=body(); uid=current_user_id()
    existing=query("SELECT * FROM tasks WHERE task_id=%s AND user_id=%s",(task_id,uid),one=True)
    if not existing: return json_error("Task not found.",404)
    title=str(d.get("title",existing["title"])).strip(); status=d.get("status",existing["status"]); priority=str(d.get("priority",existing["priority"])).upper()
    if not title or status not in ("Draft","In Progress","Editing","Done") or priority not in ("LOW","MEDIUM","HIGH","URGENT"): return json_error("Invalid task values.")
    cat=d.get("category_id",existing["category_id"]) or None; proj=d.get("project_id",existing["project_id"]) or None
    if cat and not query("SELECT category_id FROM categories WHERE category_id=%s AND user_id=%s",(cat,uid),one=True): return json_error("Invalid category.")
    if proj and not query("SELECT project_id FROM projects WHERE project_id=%s AND user_id=%s",(proj,uid),one=True): return json_error("Invalid project.")
    query("""UPDATE tasks SET category_id=%s,project_id=%s,title=%s,description=%s,priority=%s,status=%s,due_date=%s,
        estimated_minutes=%s,actual_minutes=%s,progress=%s,is_starred=%s,
        completed_at=CASE WHEN %s='Done' THEN COALESCE(completed_at,NOW()) ELSE NULL END
        WHERE task_id=%s AND user_id=%s""",(cat,proj,title,d.get("description",existing["description"]),priority,status,clean_date(d.get("due_date",existing["due_date"])),int(d.get("estimated_minutes",existing["estimated_minutes"])),int(d.get("actual_minutes",existing["actual_minutes"])),int(d.get("progress",100 if status=="Done" else existing["progress"])),bool(d.get("is_starred",d.get("favorite",existing["is_starred"]))),status,task_id,uid),commit=True)
    return jsonify({"ok":True})


@app.delete("/api/tasks/<int:task_id>")
@login_required
def delete_task(task_id):
    query("DELETE FROM tasks WHERE task_id=%s AND user_id=%s",(task_id,current_user_id()),commit=True)
    return jsonify({"ok":True})


@app.post("/api/tasks/sync")
@login_required
def sync_tasks():
    """Sync the existing browser task model without changing its UI-facing IDs."""
    data=body(); items=data.get("tasks",[])
    if not isinstance(items,list): return json_error("Tasks must be a list.")
    deleted_ids = data.get("deleted_ids", [])
    if not isinstance(deleted_ids, list): return json_error("Deleted task IDs must be a list.")
    uid=current_user_id(); conn=db_connection(); cur=conn.cursor()
    try:
        keep=[]
        for item in items:
            key=str(item.get("id", "")).strip()
            title=str(item.get("title", "")).strip()
            status=item.get("status", "Draft"); priority=str(item.get("priority", "MEDIUM")).upper()
            if not key or not title: continue
            if status not in ("Draft","In Progress","Editing","Done") or priority not in ("LOW","MEDIUM","HIGH","URGENT"): continue
            keep.append(key)
            category_name=str(item.get("category", "")).strip()
            category_id=None
            if category_name and category_name != "Uncategorized":
                cur.execute("SELECT category_id FROM categories WHERE user_id=%s AND category_name=%s",(uid,category_name))
                found=cur.fetchone()
                if found: category_id=found[0]
                else:
                    cur.execute("INSERT INTO categories(user_id,category_name) VALUES(%s,%s)",(uid,category_name)); category_id=cur.lastrowid
            cur.execute("""INSERT INTO tasks(user_id,client_key,category_id,title,description,priority,status,progress,is_starred,completed_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,IF(%s='Done',NOW(),NULL))
                ON DUPLICATE KEY UPDATE category_id=VALUES(category_id),title=VALUES(title),description=VALUES(description),
                priority=VALUES(priority),status=VALUES(status),progress=VALUES(progress),is_starred=VALUES(is_starred),
                completed_at=IF(VALUES(status)='Done',COALESCE(completed_at,NOW()),NULL)""",
                (uid,key,category_id,title,item.get("description", ""),priority,status,100 if status=="Done" else int(item.get("progress",0) or 0),bool(item.get("favorite",False)),status))
        # A newly signed-in browser may have no local cache yet. Never interpret
        # an incomplete snapshot as a request to delete all of the user's tasks.
        ids = list(dict.fromkeys(str(value).strip() for value in deleted_ids if str(value).strip()))
        if ids:
            placeholders=','.join(['%s']*len(ids))
            cur.execute(f"DELETE FROM tasks WHERE user_id=%s AND client_key IN ({placeholders})",(uid,*ids))
        conn.commit()
        return jsonify({"ok":True,"synced":len(keep)})
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.route("/api/categories",methods=["GET","POST"])
@login_required
def categories():
    uid=current_user_id()
    if request.method=="GET": return jsonify({"ok":True,"categories":query("SELECT category_id,category_name,color_code FROM categories WHERE user_id=%s ORDER BY category_name",(uid,))})
    d=body(); name=str(d.get("category_name",d.get("name",""))).strip()
    if not name:return json_error("Category name is required.")
    try:
        cid=query("INSERT INTO categories(user_id,category_name,color_code) VALUES(%s,%s,%s)",(uid,name,d.get("color_code")),commit=True)
        return jsonify({"ok":True,"category_id":cid}),201
    except IntegrityError:return json_error("That category already exists.",409)


@app.route("/api/categories/<int:category_id>",methods=["PUT","DELETE"])
@login_required
def category_detail(category_id):
    uid=current_user_id()
    if request.method=="DELETE":
        # Tasks retain their user_id; only their category association is cleared.
        query("UPDATE tasks SET category_id=NULL WHERE category_id=%s AND user_id=%s",(category_id,uid),commit=True)
        query("DELETE FROM categories WHERE category_id=%s AND user_id=%s",(category_id,uid),commit=True)
        return jsonify({"ok":True})
    d=body(); query("UPDATE categories SET category_name=%s,color_code=%s WHERE category_id=%s AND user_id=%s",(str(d.get("category_name","")).strip(),d.get("color_code"),category_id,uid),commit=True)
    return jsonify({"ok":True})


@app.route("/api/preferences",methods=["GET","PUT"])
@login_required
def preferences():
    uid=current_user_id()
    if request.method=="GET":
        row=query("SELECT theme_mode,daily_task_goal,widget_layout FROM user_preferences WHERE user_id=%s",(uid,),one=True)
        if row and isinstance(row.get("widget_layout"), str):
            import json
            try: row["widget_layout"] = json.loads(row["widget_layout"])
            except ValueError: row["widget_layout"] = None
        return jsonify({"ok":True,"preferences":row or {"theme_mode":"light","daily_task_goal":0,"widget_layout":None}})
    d=body(); theme=d.get("theme_mode", "light"); goal=int(d.get("daily_task_goal",0) or 0)
    if theme not in ("light","dark","system") or goal<0:return json_error("Invalid preferences.")
    import json
    layout=d.get("widget_layout")
    query("INSERT INTO user_preferences(user_id,theme_mode,daily_task_goal,widget_layout) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE theme_mode=VALUES(theme_mode),daily_task_goal=VALUES(daily_task_goal),widget_layout=VALUES(widget_layout)",(uid,theme,goal,json.dumps(layout) if layout is not None else None),commit=True)
    return jsonify({"ok":True})


@app.route("/api/projects",methods=["GET","POST"])
@login_required
def projects():
    uid=current_user_id()
    if request.method=="GET":
        rows=query("SELECT project_id,project_name,description,color_code,status,start_date,end_date,created_at,updated_at FROM projects WHERE user_id=%s ORDER BY created_at DESC",(uid,))
        for row in rows:
            for key in ("start_date","end_date","created_at","updated_at"):
                if row.get(key): row[key]=row[key].isoformat(sep=" ") if isinstance(row[key],datetime) else str(row[key])
        return jsonify({"ok":True,"projects":rows})
    d=body(); name=str(d.get("project_name",d.get("name",""))).strip()
    if not name:return json_error("Project name is required.")
    status=d.get("status","ACTIVE")
    if status not in ("ACTIVE","COMPLETED","ARCHIVED"):return json_error("Invalid project status.")
    pid=query("INSERT INTO projects(user_id,project_name,description,color_code,status,start_date,end_date) VALUES(%s,%s,%s,%s,%s,%s,%s)",(uid,name,d.get("description"),d.get("color_code"),status,d.get("start_date"),d.get("end_date")),commit=True)
    return jsonify({"ok":True,"project_id":pid}),201


@app.route("/api/projects/<int:project_id>",methods=["PUT","DELETE"])
@login_required
def project_detail(project_id):
    uid=current_user_id()
    if request.method=="DELETE":
        query("DELETE FROM projects WHERE project_id=%s AND user_id=%s",(project_id,uid),commit=True)
        return jsonify({"ok":True})
    d=body(); name=str(d.get("project_name","")).strip(); status=d.get("status","ACTIVE")
    if not name or status not in ("ACTIVE","COMPLETED","ARCHIVED"):return json_error("Invalid project details.")
    query("UPDATE projects SET project_name=%s,description=%s,color_code=%s,status=%s,start_date=%s,end_date=%s WHERE project_id=%s AND user_id=%s",(name,d.get("description"),d.get("color_code"),status,d.get("start_date"),d.get("end_date"),project_id,uid),commit=True)
    return jsonify({"ok":True})


@app.route("/api/calendar/events",methods=["GET","POST"])
@login_required
def calendar_events():
    uid=current_user_id()
    if request.method=="GET":
        rows=query("SELECT event_id,task_id,title,description,start_at,end_at,event_type,priority,color_theme FROM calendar_events WHERE user_id=%s ORDER BY start_at",(uid,))
        for r in rows:
            for k in ("start_at","end_at"):
                if r.get(k):r[k]=r[k].isoformat(sep=" ")
        return jsonify({"ok":True,"events":rows})
    d=body(); title=str(d.get("title","")).strip(); start=clean_date(d.get("start_at"))
    if not title or not start:return json_error("Event title and start time are required.")
    task_id=d.get("task_id") or None
    if task_id and not query("SELECT task_id FROM tasks WHERE task_id=%s AND user_id=%s",(task_id,uid),one=True):
        return json_error("The selected task does not belong to your account.")
    priority=str(d.get("priority","MEDIUM")).upper()
    color_theme=str(d.get("color_theme","cyan")).lower()
    if priority not in ("LOW","MEDIUM","HIGH","URGENT") or color_theme not in ("cyan","blue","purple"):
        return json_error("Invalid event priority or color theme.")
    end=clean_date(d.get("end_at"))
    if end and end < start:
        return json_error("Event end time must be after its start time.")
    eid=query("INSERT INTO calendar_events(user_id,task_id,title,description,start_at,end_at,event_type,priority,color_theme) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(uid,task_id,title,d.get("description"),start,end,d.get("event_type","PERSONAL"),priority,color_theme),commit=True)
    return jsonify({"ok":True,"event_id":eid}),201


@app.route("/api/calendar/events/<int:event_id>", methods=["PUT", "DELETE"])
@login_required
def event_detail(event_id):
    uid=current_user_id()
    if request.method == "DELETE":
        query("DELETE FROM calendar_events WHERE event_id=%s AND user_id=%s",(event_id,uid),commit=True)
        return jsonify({"ok":True})
    d=body(); title=str(d.get("title","")).strip(); start=clean_date(d.get("start_at")); end=clean_date(d.get("end_at"))
    priority=str(d.get("priority","MEDIUM")).upper(); color_theme=str(d.get("color_theme","cyan")).lower()
    if not title or not start or (end and end < start): return json_error("Enter a title and a valid time range.")
    if priority not in ("LOW","MEDIUM","HIGH","URGENT") or color_theme not in ("cyan","blue","purple"): return json_error("Invalid event priority or color theme.")
    query("UPDATE calendar_events SET title=%s,description=%s,start_at=%s,end_at=%s,event_type=%s,priority=%s,color_theme=%s WHERE event_id=%s AND user_id=%s",(title,d.get("description"),start,end,d.get("event_type","PERSONAL"),priority,color_theme,event_id,uid),commit=True)
    return jsonify({"ok":True})


@app.get("/api/reports/summary")
@login_required
def report_summary():
    uid=current_user_id()
    stats=query("SELECT COUNT(*) total_tasks,COALESCE(SUM(status='Done'),0) completed_tasks,COALESCE(SUM(status<>'Done'),0) open_tasks,COALESCE(SUM(actual_minutes),0) actual_minutes,COALESCE(AVG(progress),0) average_progress FROM tasks WHERE user_id=%s",(uid,),one=True)
    logs=query("SELECT log_date,tasks_completed,focus_time_minutes,streak_count FROM productivity_logs WHERE user_id=%s ORDER BY log_date",(uid,))
    for r in logs:r["log_date"]=str(r["log_date"])
    return jsonify({"ok":True,"stats":stats,"productivity":logs})


@app.route("/api/productivity",methods=["GET","POST"])
@login_required
def productivity():
    uid=current_user_id()
    if request.method=="GET":
        return jsonify({"ok":True,"logs":query("SELECT log_date,tasks_completed,focus_time_minutes,streak_count FROM productivity_logs WHERE user_id=%s ORDER BY log_date DESC",(uid,))})
    d=body(); log_date=d.get("log_date",date.today().isoformat())
    query("INSERT INTO productivity_logs(user_id,log_date,tasks_completed,focus_time_minutes,streak_count) VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE tasks_completed=VALUES(tasks_completed),focus_time_minutes=VALUES(focus_time_minutes),streak_count=VALUES(streak_count)",(uid,log_date,int(d.get("tasks_completed",0)),int(d.get("focus_time_minutes",0)),int(d.get("streak_count",0))),commit=True)
    return jsonify({"ok":True})


@app.get("/api/users/search")
@login_required
def search_users():
    term=request.args.get("q","").strip()
    if len(term)<2:return jsonify({"ok":True,"users":[]})
    rows=query("SELECT user_id,username,email FROM users WHERE user_id<>%s AND (username LIKE %s OR email LIKE %s) ORDER BY username LIMIT 20",(current_user_id(),f"%{term}%",f"%{term}%"))
    return jsonify({"ok":True,"users":rows})


@app.route("/api/conversations",methods=["GET","POST"])
@login_required
def conversations():
    uid=current_user_id()
    if request.method=="GET":
        rows=query("""SELECT c.conversation_id,IF(c.user_1_id=%s,u2.user_id,u1.user_id) other_user_id,
            IF(c.user_1_id=%s,u2.username,u1.username) other_username,c.created_at
            FROM conversations c JOIN users u1 ON u1.user_id=c.user_1_id JOIN users u2 ON u2.user_id=c.user_2_id
            WHERE c.user_1_id=%s OR c.user_2_id=%s ORDER BY c.created_at DESC""",(uid,uid,uid,uid))
        for r in rows:r["created_at"]=r["created_at"].isoformat(sep=" ")
        return jsonify({"ok":True,"conversations":rows})
    try:
        other=int(body().get("user_id",0))
    except (TypeError, ValueError):
        return json_error("Choose a valid other user.")
    if other==uid or not query("SELECT user_id FROM users WHERE user_id=%s",(other,),one=True):return json_error("Choose a valid other user.")
    low,high=sorted((uid,other))
    query("INSERT INTO conversations(user_1_id,user_2_id) VALUES(%s,%s) ON DUPLICATE KEY UPDATE conversation_id=LAST_INSERT_ID(conversation_id)",(low,high),commit=True)
    row=query("SELECT conversation_id FROM conversations WHERE user_1_id=%s AND user_2_id=%s",(low,high),one=True)
    return jsonify({"ok":True,"conversation_id":row["conversation_id"]}),201


def conversation_member(cid,uid):
    return query("SELECT conversation_id FROM conversations WHERE conversation_id=%s AND (user_1_id=%s OR user_2_id=%s)",(cid,uid,uid),one=True)


@app.get("/api/conversations/<int:cid>/messages")
@login_required
def get_messages(cid):
    uid=current_user_id()
    if not conversation_member(cid,uid):return json_error("Conversation not found.",404)
    rows=query("SELECT message_id,sender_id,message_text,sent_at,is_read FROM messages WHERE conversation_id=%s ORDER BY sent_at",(cid,))
    for r in rows:r["sent_at"]=r["sent_at"].isoformat(sep=" ")
    query("UPDATE messages SET is_read=TRUE WHERE conversation_id=%s AND sender_id<>%s",(cid,uid),commit=True)
    return jsonify({"ok":True,"messages":rows})


@app.post("/api/conversations/<int:cid>/messages")
@login_required
def send_message(cid):
    uid=current_user_id(); text=str(body().get("message_text","")).strip()
    if not conversation_member(cid,uid):return json_error("Conversation not found.",404)
    if not text:return json_error("Message cannot be empty.")
    mid=query("INSERT INTO messages(conversation_id,sender_id,message_text) VALUES(%s,%s,%s)",(cid,uid,text),commit=True)
    return jsonify({"ok":True,"message_id":mid}),201


@app.get("/")
def home():
    return redirect("/pages/landing-page/landing.html")


@app.get("/assets/<path:requested_path>")
def asset_files(requested_path):
    return serve_project_file("assets", requested_path)


@app.get("/pages/<path:requested_path>")
def page_files(requested_path):
    return serve_project_file("pages", requested_path)


def serve_project_file(directory, requested_path):
    """Serve only public frontend assets; never expose project/config/source files."""
    allowed_suffixes = {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".woff", ".woff2"}
    if any(part.startswith(".") for part in Path(requested_path).parts):
        abort(404)
    base = (ROOT / directory).resolve()
    target = (base / requested_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        abort(404)
    if not target.is_file() or target.suffix.lower() not in allowed_suffixes:
        abort(404)
    # Flask expects URL-style separators even when the server runs on Windows.
    return send_from_directory(str(base), target.relative_to(base).as_posix())


@app.get("/<path:requested_path>")
def frontend_files(requested_path):
    # Keep root level limited to the two intended public documents.
    if requested_path in {"favicon.ico", "robots.txt"}:
        return "", 404
    abort(404)


@app.errorhandler(MySQLError)
def handle_database_error(exc):
    app.logger.exception("MySQL operation failed")
    return json_error("A database operation failed. Please try again.",500)


@app.errorhandler(404)
def not_found(_exc):
    if request.path.startswith("/api/"):
        return json_error("Endpoint or record not found.", 404)
    return "Not found", 404


@app.errorhandler(413)
def request_too_large(_exc):
    return json_error("Request body is too large.", 413)


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG","0")=="1")

"""Flask API and frontend entry point for ScholarSync."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import os
from pathlib import Path
import secrets
from typing import Any

from flask import Flask, jsonify, render_template, request, session as web_session

from auth.login import Session as UserSession
from auth.login import WrongRoleError, authenticate_user
from database.connection import DatabaseOperationError, fetch_single_record
from services import academic


BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "assets"),
    static_url_path="/assets",
    template_folder=str(BASE_DIR / "templates"),
)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

if not os.getenv("FLASK_SECRET_KEY"):
    app.logger.warning("FLASK_SECRET_KEY is not set; sessions expire when the server restarts.")

logger = logging.getLogger(__name__)


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _service_response(result: academic.ServiceResult, *, success_status: int = 200):
    if result.ok:
        return jsonify(data=_json_value(result.data)), success_status

    if result.error_code in {1062, 1451, 1452, 3819}:
        status = 409
    elif result.error_code == 1048:
        status = 422
    elif result.error_code is not None:
        status = 503
    elif result.field_errors:
        status = 422
    elif result.error and "access" in result.error.lower():
        status = 403
    elif result.error and "database" in result.error.lower():
        status = 503
    else:
        status = 400

    payload: dict[str, Any] = {"error": result.error or "The request could not be completed."}
    if result.error_code is not None:
        payload["error_code"] = result.error_code
    if result.field_errors:
        payload["field_errors"] = result.field_errors
    return jsonify(payload), status


def _student_record(record: Any) -> dict[str, Any]:
    fields = (
        "student_id", "roll_number", "first_name", "last_name", "email",
        "date_of_birth", "class_id", "class_name", "username",
    )
    return _json_value(dict(zip(fields, record)))


def _request_object():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify(error="A JSON object is required."), 400)
    return payload, None


def _current_session(required_role: str | None = None):
    identity = web_session.get("identity")
    if not isinstance(identity, dict):
        return None, (jsonify(error="Authentication is required."), 401)

    try:
        current = UserSession(
            user_id=int(identity["user_id"]),
            username=str(identity["username"]),
            role=str(identity["role"]),
            teacher_id=int(identity["teacher_id"]) if identity.get("teacher_id") is not None else None,
            student_id=int(identity["student_id"]) if identity.get("student_id") is not None else None,
        )
    except (KeyError, TypeError, ValueError):
        web_session.clear()
        return None, (jsonify(error="The stored session is invalid. Please sign in again."), 401)

    if required_role is not None and current.role != required_role:
        return None, (jsonify(error="This account does not have access to that action."), 403)
    return current, None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    try:
        fetch_single_record("SELECT 1")
    except DatabaseOperationError:
        logger.exception("Database health check failed.")
        return jsonify(status="unavailable", database="unavailable"), 503
    return jsonify(status="ok", database="ok")


@app.post("/api/auth/login")
def login():
    payload, error_response = _request_object()
    if error_response:
        return error_response
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role")
    if not isinstance(username, str) or not username.strip():
        return jsonify(error="Enter a username.", field_errors={"username": "Enter a username."}), 422
    if not isinstance(password, str) or not password:
        return jsonify(error="Enter a password.", field_errors={"password": "Enter a password."}), 422
    if not isinstance(role, str) or role not in {"teacher", "student"}:
        return jsonify(error="Choose a valid portal.", field_errors={"role": "Choose teacher or student."}), 422

    try:
        identity = authenticate_user(username, password, role)
    except WrongRoleError as error:
        return jsonify(error=str(error)), 403
    except DatabaseOperationError:
        logger.exception("Login database lookup failed.")
        return jsonify(error="The database is unavailable."), 503

    if identity is None:
        return jsonify(error="The username or password is incorrect."), 401

    web_session.clear()
    web_session.permanent = True
    web_session["identity"] = {
        "user_id": identity.user_id,
        "username": identity.username,
        "role": identity.role,
        "teacher_id": identity.teacher_id,
        "student_id": identity.student_id,
    }
    return jsonify(data={
        "user_id": identity.user_id,
        "username": identity.username,
        "role": identity.role,
    })


@app.post("/api/auth/logout")
def logout():
    web_session.clear()
    return jsonify(data={"logged_out": True})


@app.get("/api/auth/me")
def who_am_i():
    identity, error_response = _current_session()
    if error_response:
        return error_response
    return jsonify(data={
        "user_id": identity.user_id,
        "username": identity.username,
        "role": identity.role,
    })


@app.get("/api/teacher/dashboard")
def teacher_dashboard():
    identity, error_response = _current_session("teacher")
    if error_response:
        return error_response
    return _service_response(academic.teacher_dashboard_data(identity))


@app.get("/api/student/dashboard")
def student_dashboard():
    identity, error_response = _current_session("student")
    if error_response:
        return error_response
    return _service_response(academic.student_dashboard_data(identity))


@app.route("/api/students", methods=["GET", "POST"])
def students():
    identity, error_response = _current_session("teacher")
    if error_response:
        return error_response
    if request.method == "GET":
        result = academic.list_students(identity)
        if result.ok:
            return jsonify(data=[_student_record(row) for row in result.data])
        return _service_response(result)

    payload, error_response = _request_object()
    if error_response:
        return error_response
    return _service_response(academic.create_student(identity, payload), success_status=201)


@app.get("/api/students/<int:student_id>")
def student_detail(student_id: int):
    _, error_response = _current_session("teacher")
    if error_response:
        return error_response

    try:
        record = fetch_single_record(
            "SELECT s.student_id, s.roll_number, s.first_name, s.last_name, s.email, "
            "s.date_of_birth, s.class_id, c.class_name, u.username "
            "FROM students s JOIN users u ON u.user_id = s.user_id "
            "LEFT JOIN classes c ON c.class_id = s.class_id WHERE s.student_id = %s",
            (student_id,),
        )
    except DatabaseOperationError as error:
        logger.exception("Student lookup failed.")
        payload: dict[str, Any] = {"error": "The database operation failed."}
        if error.code is not None:
            payload["error_code"] = error.code
        return jsonify(payload), 503

    if record is None:
        return jsonify(error="Student not found."), 404
    return jsonify(data=_student_record(record))


@app.patch("/api/students/<int:student_id>")
def update_student(student_id: int):
    identity, error_response = _current_session("teacher")
    if error_response:
        return error_response
    payload, error_response = _request_object()
    if error_response:
        return error_response
    return _service_response(academic.update_student(identity, student_id, payload))


@app.get("/api/students/<int:student_id>/delete-impact")
def student_delete_impact(student_id: int):
    identity, error_response = _current_session("teacher")
    if error_response:
        return error_response
    return _service_response(academic.student_delete_impact(identity, student_id))


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id: int):
    identity, error_response = _current_session("teacher")
    if error_response:
        return error_response
    return _service_response(academic.delete_student(identity, student_id))


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"},
    )

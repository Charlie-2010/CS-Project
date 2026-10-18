"""Teacher and student workflows kept outside the Tkinter presentation layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from auth.hash_utils import create_password_record
from auth.login import Session
from database.connection import (
    DatabaseOperationError,
    execute_dml,
    execute_transaction,
    fetch_all_records,
    fetch_single_record,
)
from utils.validators import ValidationError, validate_class, validate_student, validate_subject, validate_teacher


@dataclass(frozen=True)
class ServiceResult:
    ok: bool
    data: Any = None
    error: str | None = None
    error_code: int | None = None
    field_errors: dict[str, str] = field(default_factory=dict)


class PermissionDeniedError(ValueError):
    """Raised when a session does not have access to a service operation."""


def _run(operation: Callable[[], Any]) -> ServiceResult:
    try:
        result = operation()
        return result if isinstance(result, ServiceResult) else ServiceResult(True, data=result)
    except ValidationError as error:
        return ServiceResult(False, error="Check the highlighted fields.", field_errors=error.errors)
    except PermissionDeniedError as error:
        return ServiceResult(False, error=str(error))
    except DatabaseOperationError as error:
        return ServiceResult(False, error=str(error), error_code=error.code)


def _require_role(session: Session, role: str) -> None:
    if not isinstance(session, Session) or session.role != role:
        raise PermissionDeniedError("This account does not have access to that action.")


def _teacher(session: Session) -> None:
    _require_role(session, "teacher")
    if session.teacher_id is None:
        raise PermissionDeniedError("The teacher profile is not available.")


def _student(session: Session) -> None:
    _require_role(session, "student")
    if session.student_id is None:
        raise PermissionDeniedError("The student profile is not available.")


def list_students(session: Session) -> ServiceResult:
    def operation():
        _teacher(session)
        return fetch_all_records(
            "SELECT s.student_id, s.roll_number, s.first_name, s.last_name, s.email, "
            "s.date_of_birth, s.class_id, c.class_name, u.username "
            "FROM students s JOIN users u ON u.user_id = s.user_id "
            "LEFT JOIN classes c ON c.class_id = s.class_id ORDER BY s.roll_number"
        )
    return _run(operation)


def create_student(session: Session, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        if not isinstance(data, dict):
            raise ValidationError({"_form": "Student data must be a dictionary."})
        profile_data = {key: value for key, value in data.items() if key in {
            "roll_number", "first_name", "last_name", "email", "date_of_birth", "class_id"
        }}
        validation_errors = {}
        try:
            cleaned = validate_student({"user_id": 1, **profile_data})
        except ValidationError as error:
            validation_errors.update(error.errors)
            cleaned = {}
            # Ensure variables default to an empty string instead of None
        raw_username = data.get("username")
        raw_password = data.get("password")
        
        username: str = str(raw_username) if raw_username is not None else ""
        password: str = str(raw_password) if raw_password is not None else ""

        if not username.strip() or len(username.strip()) > 50:
            validation_errors["username"] = "Enter a username of at most 50 characters."
        if not isinstance(raw_password, str) or len(raw_password) < 8:
            validation_errors["password"] = "Use a password with at least 8 characters."
        extra_fields = set(data) - set(profile_data) - {"username", "password"}
        for field_name in extra_fields:
            validation_errors[field_name] = "Unsupported field."
        if validation_errors:
            raise ValidationError(validation_errors)
        cleaned.pop("user_id")
        password_hash, password_salt = create_password_record(password)

        def insert(cursor):
            cursor.execute(
                "INSERT INTO users (username, password_hash, password_salt, role) VALUES (%s, %s, %s, 'student')",
                (username.strip(), password_hash, password_salt),
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO students (user_id, roll_number, first_name, last_name, email, date_of_birth, class_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, cleaned["roll_number"], cleaned["first_name"], cleaned["last_name"],
                 cleaned["email"], cleaned["date_of_birth"], cleaned["class_id"]),
            )
            return cursor.lastrowid

        return {"student_id": execute_transaction(insert).value}
    return _run(operation)


def update_student(session: Session, student_id: int, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        allowed = {"roll_number", "first_name", "last_name", "email", "date_of_birth", "class_id"}
        if not isinstance(data, dict) or not data or set(data) - allowed:
            raise ValidationError({"_form": "Provide one or more editable student fields."})
        cleaned = validate_student(data, partial=True)
        fields = list(cleaned)
        values = tuple(cleaned[field_name] for field_name in fields) + (student_id,)
        count = execute_dml(
            f"UPDATE students SET {', '.join(f'{field_name} = %s' for field_name in fields)} WHERE student_id = %s",
            values,
        )
        return {"updated": count == 1}
    return _run(operation)

def student_delete_impact(session: Session, student_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        
        # 1. Fetch raw query outputs
        exam_res = fetch_single_record("SELECT COUNT(*) FROM exam_results WHERE student_id = %s", (student_id,))
        att_res = fetch_single_record("SELECT COUNT(*) FROM attendance WHERE student_id = %s", (student_id,))
        
        # 2. Extract values safely using an open type wrapper to bypass Pylance sequence protocols
        clean_exam: Any = exam_res if exam_res is not None else (0,)
        clean_att: Any = att_res if att_res is not None else (0,)
        
        return {
            "exam_results": int(clean_exam[0]),
            "attendance": int(clean_att[0]),
            "student_account": 1,
        }
        
    return _run(operation)

def delete_student(session: Session, student_id: int) -> ServiceResult:
    def operation():
        _teacher(session)

        def delete(cursor):
            cursor.execute("SELECT user_id FROM students WHERE student_id = %s", (student_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            cursor.execute("DELETE FROM users WHERE user_id = %s", (row[0],))
            return cursor.rowcount == 1

        return {"deleted": execute_transaction(delete).value}
    return _run(operation)


def teacher_dashboard_data(session: Session) -> ServiceResult:
    def operation():
        _teacher(session)
        counts = fetch_single_record(
            "SELECT (SELECT COUNT(*) FROM students), (SELECT COUNT(*) FROM classes), "
            "(SELECT COUNT(*) FROM assignments WHERE due_date >= CURRENT_DATE)"
        )
        recent_assignments = fetch_all_records(
            "SELECT a.title, c.class_name, sub.subject_name, a.due_date FROM assignments a "
            "JOIN classes c ON c.class_id = a.class_id JOIN subjects sub ON sub.subject_id = a.subject_id "
            "WHERE a.teacher_id = %s ORDER BY a.due_date LIMIT 5", (session.teacher_id,)
        )
        return {"counts": counts, "assignments": recent_assignments}
    return _run(operation)


def student_dashboard_data(session: Session) -> ServiceResult:
    def operation():
        _student(session)
        student_id = session.student_id
        profile = fetch_single_record(
            "SELECT s.first_name, s.last_name, c.class_name FROM students s "
            "LEFT JOIN classes c ON c.class_id = s.class_id WHERE s.student_id = %s", (student_id,)
        )
        report_card = fetch_all_records(
            "SELECT e.exam_name, sub.subject_name, er.marks_obtained, es.max_marks, er.remarks "
            "FROM exam_results er JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id "
            "JOIN exams e ON e.exam_id = es.exam_id JOIN subjects sub ON sub.subject_id = es.subject_id "
            "WHERE er.student_id = %s ORDER BY e.exam_name, sub.subject_name", (student_id,)
        )
        attendance = fetch_single_record(
            "SELECT COUNT(*), SUM(status = 'Present'), SUM(status = 'Late') FROM attendance WHERE student_id = %s",
            (student_id,),
        )
        assignments = fetch_all_records(
            "SELECT a.title, sub.subject_name, a.due_date, a.max_points FROM assignments a "
            "JOIN students s ON s.class_id = a.class_id JOIN subjects sub ON sub.subject_id = a.subject_id "
            "WHERE s.student_id = %s AND a.due_date >= CURRENT_DATE ORDER BY a.due_date LIMIT 5", (student_id,)
        )
        return {"profile": profile, "report_card": report_card, "attendance": attendance, "assignments": assignments}
    return _run(operation)


def list_classes(session: Session) -> ServiceResult:
    return _run(lambda: (_teacher(session), fetch_all_records(
        "SELECT class_id, class_name FROM classes ORDER BY class_name"
    ))[1])


def list_class_details(session: Session) -> ServiceResult:
    return _run(lambda: (_teacher(session), fetch_all_records(
        "SELECT c.class_id, c.class_name, c.room_number, t.first_name, t.last_name "
        "FROM classes c LEFT JOIN teachers t ON t.teacher_id = c.class_teacher_id ORDER BY c.class_name"
    ))[1])

def class_delete_impact(session: Session, class_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        
        # 1. Fetch raw query outputs from the database
        res_students = fetch_single_record("SELECT COUNT(*) FROM students WHERE class_id = %s", (class_id,))
        res_papers = fetch_single_record("SELECT COUNT(*) FROM exam_subjects WHERE class_id = %s", (class_id,))
        res_assignments = fetch_single_record("SELECT COUNT(*) FROM assignments WHERE class_id = %s", (class_id,))
        res_attendance = fetch_single_record("SELECT COUNT(*) FROM attendance WHERE class_id = %s", (class_id,))
        
        # 2. Extract values safely using a fallback sequence if the result is None
        clean_students: Any = res_students if res_students is not None else (0,)
        clean_papers: Any = res_papers if res_papers is not None else (0,)
        clean_assignments: Any = res_assignments if res_assignments is not None else (0,)
        clean_attendance: Any = res_attendance if res_attendance is not None else (0,)
        
        # 3. Return clean, validated integer fields
        return {
            "students_reassigned": int(clean_students[0]),
            "exam_papers": int(clean_papers[0]),
            "assignments": int(clean_assignments[0]),
            "attendance": int(clean_attendance[0]),
        }
        
    return _run(operation)

def delete_class(session: Session, class_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        return {"deleted": execute_dml("DELETE FROM classes WHERE class_id = %s", (class_id,)) == 1}
    return _run(operation)


def update_class(session: Session, class_id: int, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        allowed = {"class_name", "room_number", "class_teacher_id"}
        if not isinstance(data, dict) or not data or set(data) - allowed:
            raise ValidationError({"_form": "Provide one or more editable class fields."})
        cleaned = validate_class(data, partial=True)
        fields = list(cleaned)
        values = tuple(cleaned[field_name] for field_name in fields) + (class_id,)
        count = execute_dml(
            f"UPDATE classes SET {', '.join(f'{field_name} = %s' for field_name in fields)} WHERE class_id = %s",
            values,
        )
        return {"updated": count == 1}
    return _run(operation)


def list_teachers(session: Session) -> ServiceResult:
    return _run(lambda: (_teacher(session), fetch_all_records(
        "SELECT t.teacher_id, t.first_name, t.last_name, t.email, t.phone, u.username "
        "FROM teachers t JOIN users u ON u.user_id = t.user_id ORDER BY t.last_name, t.first_name"
    ))[1])


def create_teacher(session: Session, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        if not isinstance(data, dict):
            raise ValidationError({"_form": "Teacher data must be a dictionary."})
        profile_data = {key: value for key, value in data.items() if key in {
            "first_name", "last_name", "email", "phone"
        }}
        if profile_data.get("phone") == "":
            profile_data["phone"] = None
        errors = {}
        try:
            cleaned = validate_teacher({"user_id": 1, **profile_data})
        except ValidationError as error:
            errors.update(error.errors)
            cleaned = {}
            # Ensure variables default to an empty string instead of an ambiguous NoneType object
        raw_username = data.get("username")
        raw_password = data.get("password")

        username: str = str(raw_username) if raw_username is not None else ""
        password: str = str(raw_password) if raw_password is not None else ""

        if not username.strip() or len(username.strip()) > 50:
            errors["username"] = "Enter a username of at most 50 characters."
        if not password or len(password) < 8:
            errors["password"] = "Use a password with at least 8 characters."
        extra = set(data) - set(profile_data) - {"username", "password"}
        for name in extra:
            errors[name] = "Unsupported field."
        if errors:
            raise ValidationError(errors)
        cleaned.pop("user_id")
        password_hash, password_salt = create_password_record(password)

        def insert(cursor):
            cursor.execute(
                "INSERT INTO users (username, password_hash, password_salt, role) VALUES (%s, %s, %s, 'teacher')",
                (username.strip(), password_hash, password_salt),
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO teachers (user_id, first_name, last_name, email, phone) VALUES (%s, %s, %s, %s, %s)",
                (user_id, cleaned["first_name"], cleaned["last_name"], cleaned["email"], cleaned["phone"]),
            )
            return cursor.lastrowid
        return {"teacher_id": execute_transaction(insert).value}
    return _run(operation)


def update_teacher(session: Session, teacher_id: int, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        allowed = {"first_name", "last_name", "email", "phone"}
        if not isinstance(data, dict) or not data or set(data) - allowed:
            raise ValidationError({"_form": "Provide one or more editable teacher fields."})
        validation_data = dict(data)
        if validation_data.get("phone") == "":
            validation_data["phone"] = None
        cleaned = validate_teacher(validation_data, partial=True)
        fields = list(cleaned)
        values = tuple(cleaned[field_name] for field_name in fields) + (teacher_id,)
        count = execute_dml(
            f"UPDATE teachers SET {', '.join(f'{field_name} = %s' for field_name in fields)} WHERE teacher_id = %s",
            values,
        )
        return {"updated": count == 1}
    return _run(operation)


def teacher_delete_impact(session: Session, teacher_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        
        # 1. Fetch raw query outputs safely
        res_classes = fetch_single_record("SELECT COUNT(*) FROM classes WHERE class_teacher_id = %s", (teacher_id,))
        res_allocations = fetch_single_record("SELECT COUNT(*) FROM teacher_subjects WHERE teacher_id = %s", (teacher_id,))
        res_assignments = fetch_single_record("SELECT COUNT(*) FROM assignments WHERE class_teacher_id = %s", (teacher_id,))
        
        # 2. Map to an open sequence context to clear the indexing protocol check
        clean_classes: Any = res_classes if res_classes is not None else (0,)
        clean_allocations: Any = res_allocations if res_allocations is not None else (0,)
        clean_assignments: Any = res_assignments if res_assignments is not None else (0,)
        
        return {
            "classes": int(clean_classes[0]),
            "allocations": int(clean_allocations[0]),
            "assignments": int(clean_assignments[0]),
        }
        
    return _run(operation)

def delete_teacher(session: Session, teacher_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        if session.teacher_id == teacher_id:
            return ServiceResult(False, error="You cannot delete the account you are currently signed in with.")
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c039d6b832b45efef6b58ca0df1562f08b67baa9
            
        # 1. Fetch raw relationship validation metrics from database records
        res_classes = fetch_single_record("SELECT COUNT(*) FROM classes WHERE class_teacher_id = %s", (teacher_id,))
        res_allocations = fetch_single_record("SELECT COUNT(*) FROM teacher_subjects WHERE teacher_id = %s", (teacher_id,))
        res_assignments = fetch_single_record("SELECT COUNT(*) FROM assignments WHERE class_teacher_id = %s", (teacher_id,))
        
        # 2. Convert database result types into explicit sequence objects to clear protocols
        clean_classes: Any = res_classes if res_classes is not None else (0,)
        clean_allocations: Any = res_allocations if res_allocations is not None else (0,)
        clean_assignments: Any = res_assignments if res_assignments is not None else (0,)
<<<<<<< HEAD
=======
        
=======
>>>>>>> e8928334bff1e19b995891ef0629072efc54de1f
>>>>>>> c039d6b832b45efef6b58ca0df1562f08b67baa9
        impact = {
            "classes": int(clean_classes[0]),
            "allocations": int(clean_allocations[0]),
            "assignments": int(clean_assignments[0]),
        }
        
        if any(impact.values()):
            return ServiceResult(
                False,
                data=impact,
                error="Cannot delete this teacher while classes, allocations, or assignments still reference them.",
            )
            
        def delete(cursor):
            cursor.execute("SELECT user_id FROM teachers WHERE teacher_id = %s", (teacher_id,))
            row = cursor.fetchone()
            if row is None:
                return False
                
            # Treat row sequence as open type to ensure bracket safety inside custom database transaction structures
            clean_row: Any = row
            cursor.execute("DELETE FROM users WHERE user_id = %s", (clean_row[0],))
            return cursor.rowcount == 1
            
        return {"deleted": execute_transaction(delete).value}
        
    return _run(operation)

def create_class(session: Session, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        cleaned = validate_class(data)
        return {"created": execute_dml(
            "INSERT INTO classes (class_name, room_number, class_teacher_id) VALUES (%s, %s, %s)",
            (cleaned["class_name"], cleaned["room_number"], cleaned["class_teacher_id"]),
        ) == 1}
    return _run(operation)


def create_subject(session: Session, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        cleaned = validate_subject(data)
        return {"created": execute_dml(
            "INSERT INTO subjects (subject_name, subject_code) VALUES (%s, %s)",
            (cleaned["subject_name"], cleaned["subject_code"]),
        ) == 1}
    return _run(operation)


def update_subject(session: Session, subject_id: int, data: dict[str, Any]) -> ServiceResult:
    def operation():
        _teacher(session)
        allowed = {"subject_name", "subject_code"}
        if not isinstance(data, dict) or not data or set(data) - allowed:
            raise ValidationError({"_form": "Provide one or more editable subject fields."})
        cleaned = validate_subject(data, partial=True)
        fields = list(cleaned)
        values = tuple(cleaned[field_name] for field_name in fields) + (subject_id,)
        count = execute_dml(
            f"UPDATE subjects SET {', '.join(f'{field_name} = %s' for field_name in fields)} WHERE subject_id = %s",
            values,
        )
        return {"updated": count == 1}
    return _run(operation)

def subject_delete_impact(session: Session, subject_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        
        # 1. Fetch raw query outputs safely from the connection layer
        res_allocations = fetch_single_record("SELECT COUNT(*) FROM teacher_subjects WHERE subject_id = %s", (subject_id,))
        res_papers = fetch_single_record("SELECT COUNT(*) FROM exam_subjects WHERE subject_id = %s", (subject_id,))
        res_results = fetch_single_record(
            "SELECT COUNT(*) FROM exam_results er JOIN exam_subjects es ON es.exam_subject_id = er.exam_subject_id "
            "WHERE es.subject_id = %s", (subject_id,)
        )
        res_assignments = fetch_single_record("SELECT COUNT(*) FROM assignments WHERE subject_id = %s", (subject_id,))
        
        # 2. Enforce explicit fallback sequence type configurations using open Any references
        clean_allocations: Any = res_allocations if res_allocations is not None else (0,)
        clean_papers: Any = res_papers if res_papers is not None else (0,)
        clean_results: Any = res_results if res_results is not None else (0,)
        clean_assignments: Any = res_assignments if res_assignments is not None else (0,)
        
        # 3. Clean numeric indexing conversions now compile without errors
        return {
            "allocations": int(clean_allocations[0]),
            "papers": int(clean_papers[0]),
            "results": int(clean_results[0]),
            "assignments": int(clean_assignments[0]),
        }
        
    return _run(operation)

def delete_subject(session: Session, subject_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        return {"deleted": execute_dml("DELETE FROM subjects WHERE subject_id = %s", (subject_id,)) == 1}
    return _run(operation)


def list_allocations(session: Session) -> ServiceResult:
    return _run(lambda: (_teacher(session), fetch_all_records(
        "SELECT ts.allocation_id, t.teacher_id, t.first_name, t.last_name, c.class_id, c.class_name, "
        "sub.subject_id, sub.subject_name "
        "FROM teacher_subjects ts JOIN teachers t ON t.teacher_id = ts.teacher_id "
        "JOIN classes c ON c.class_id = ts.class_id JOIN subjects sub ON sub.subject_id = ts.subject_id "
        "ORDER BY c.class_name, sub.subject_name"
    ))[1])


def list_subjects(session: Session) -> ServiceResult:
    return _run(lambda: (_teacher(session), fetch_all_records(
        "SELECT subject_id, subject_name, subject_code FROM subjects ORDER BY subject_name"
    ))[1])


def allocate_subject(session: Session, teacher_id: int, class_id: int, subject_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        return {"created": execute_dml(
            "INSERT INTO teacher_subjects (teacher_id, class_id, subject_id) VALUES (%s, %s, %s)",
            (teacher_id, class_id, subject_id),
        ) == 1}
    return _run(operation)


def update_allocation(session: Session, allocation_id: int, teacher_id: int, class_id: int, subject_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        count = execute_dml(
            "UPDATE teacher_subjects SET teacher_id = %s, class_id = %s, subject_id = %s WHERE allocation_id = %s",
            (teacher_id, class_id, subject_id, allocation_id),
        )
        return {"updated": count == 1}
    return _run(operation)


def delete_allocation(session: Session, allocation_id: int) -> ServiceResult:
    def operation():
        _teacher(session)
        return {"deleted": execute_dml("DELETE FROM teacher_subjects WHERE allocation_id = %s", (allocation_id,)) == 1}
    return _run(operation)
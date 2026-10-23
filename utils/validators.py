"""Validation for data written to students, teachers, classes, and subjects."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Callable


class ValidationError(ValueError):
    """Raised when form data cannot satisfy the database schema."""

    def __init__(self, errors: dict[str, str] | str):
        self.errors = errors if isinstance(errors, dict) else {"_form": errors}
        super().__init__("; ".join(f"{field}: {message}" for field, message in self.errors.items()))


_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE = re.compile(r"^[0-9+() -]{7,15}$")
_SUBJECT_CODE = re.compile(r"^[A-Z0-9-]{1,10}$")


def _required_string(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValidationError(f"{field} must be a non-empty string of at most {maximum} characters.")
    return value.strip()


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{field} must be a positive integer.")
    return value


def _optional_positive_int(value: Any, field: str) -> int | None:
    return None if value is None else _positive_int(value, field)


def _email(value: Any) -> str:
    value = _required_string(value, "email", 100).lower()
    if not _EMAIL.fullmatch(value):
        raise ValidationError("email must be a valid email address.")
    return value


def _dob(value: Any) -> date:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError("date_of_birth must use YYYY-MM-DD.") from exc
    else:
        raise ValidationError("date_of_birth must be a date or YYYY-MM-DD string.")
    today = date.today()
    earliest = date(today.year - 120, today.month, today.day)
    if parsed > today:
        raise ValidationError("date_of_birth cannot be in the future.")
    if parsed < earliest:
        raise ValidationError("date_of_birth must be within the last 120 years.")
    return parsed


def _validate(data: dict[str, Any], rules: dict[str, Callable[[Any], Any]], partial: bool) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError({"_form": "Entity data must be a dictionary."})
    errors: dict[str, str] = {}
    unknown = set(data) - set(rules)
    if unknown:
        for field in sorted(unknown):
            errors[field] = "Unsupported field."
    if not partial:
        missing = set(rules) - set(data)
        for field in sorted(missing):
            errors[field] = "Required field is missing."
    cleaned = {}
    for field, value in data.items():
        if field not in rules:
            continue
        try:
            cleaned[field] = rules[field](value)
        except ValidationError as error:
            errors[field] = str(error).split(": ", 1)[-1]
    if errors:
        raise ValidationError(errors)
    return cleaned


def validate_student(data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    return _validate(data, {
        "user_id": lambda v: _positive_int(v, "user_id"),
        "roll_number": lambda v: _required_string(v, "roll_number", 20),
        "first_name": lambda v: _required_string(v, "first_name", 50),
        "last_name": lambda v: _required_string(v, "last_name", 50),
        "email": _email, "date_of_birth": _dob,
        "class_id": lambda v: _optional_positive_int(v, "class_id"),
    }, partial)


def validate_teacher(data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    def phone(value: Any) -> str | None:
        if value is None:
            return None
        value = _required_string(value, "phone", 15)
        if not _PHONE.fullmatch(value):
            raise ValidationError("phone contains unsupported characters.")
        return value
    return _validate(data, {
        "user_id": lambda v: _positive_int(v, "user_id"),
        "first_name": lambda v: _required_string(v, "first_name", 50),
        "last_name": lambda v: _required_string(v, "last_name", 50),
        "email": _email, "phone": phone,
    }, partial)


def validate_class(data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    return _validate(data, {
        "class_name": lambda v: _required_string(v, "class_name", 20),
        "room_number": lambda v: None if v is None else _required_string(v, "room_number", 10),
        "class_teacher_id": lambda v: _optional_positive_int(v, "class_teacher_id"),
    }, partial)


def validate_subject(data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    def code(value: Any) -> str:
        value = _required_string(value, "subject_code", 10).upper()
        if not _SUBJECT_CODE.fullmatch(value):
            raise ValidationError("subject_code may contain only A-Z, 0-9, and hyphens.")
        return value
    return _validate(data, {"subject_name": lambda v: _required_string(v, "subject_name", 50),
                            "subject_code": code}, partial)


def _mark_0_to_100(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ValidationError(f"{field} must be a number between 0 and 100.")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{field} must be a number between 0 and 100.") from None
    if not parsed.is_finite() or parsed < 0 or parsed > 100:
        raise ValidationError(f"{field} must be between 0 and 100.")
    return parsed


def _attendance_status(value: Any) -> str:
    statuses = {"Present", "Absent", "Late", "Excused"}
    if not isinstance(value, str) or value not in statuses:
        raise ValidationError("status must be Present, Absent, Late, or Excused.")
    return value


def _attendance_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError("date must use YYYY-MM-DD.") from exc
        if parsed.isoformat() != value:
            raise ValidationError("date must use YYYY-MM-DD.")
        return parsed
    raise ValidationError("date must be a date or YYYY-MM-DD string.")


def validate_attendance(data: dict[str, Any]) -> dict[str, Any]:
    """Validate one attendance row before applying its per-student/day uniqueness rule."""
    return _validate(data, {
        "student_id": lambda value: _positive_int(value, "student_id"),
        "class_id": lambda value: _positive_int(value, "class_id"),
        "date": _attendance_date,
        "status": _attendance_status,
    }, partial=False)


def validate_exam_result(data: dict[str, Any]) -> dict[str, Any]:
    """Validate an exam mark as a finite number in the inclusive 0-100 range."""
    if not isinstance(data, dict):
        return _validate(data, {}, partial=False)
    return _validate({**data, "remarks": data.get("remarks")}, {
        "student_id": lambda value: _positive_int(value, "student_id"),
        "exam_subject_id": lambda value: _positive_int(value, "exam_subject_id"),
        "marks_obtained": lambda value: _mark_0_to_100(value, "marks_obtained"),
        "remarks": lambda value: None if value is None or value == "" else _required_string(value, "remarks", 255),
    }, partial=False)


_ENTITY_VALIDATORS = {"students": validate_student, "teachers": validate_teacher,
                      "classes": validate_class, "subjects": validate_subject}


def validate_entity(entity: str, data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    """Validate one supported entity before passing it to an SQL helper."""
    try:
        return _ENTITY_VALIDATORS[entity](data, partial=partial)
    except KeyError as exc:
        raise ValidationError(f"No validator is defined for {entity!r}.") from exc

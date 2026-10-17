"""Authentication lookup and role-bound session creation."""
from dataclasses import dataclass

from auth.hash_utils import verify_password
from database.connection import fetch_single_record


@dataclass(frozen=True)
class Session:
    user_id: int
    username: str
    role: str
    teacher_id: int | None = None
    student_id: int | None = None


class WrongRoleError(ValueError):
    """Raised when valid credentials are used at the other persona portal."""


def authenticate_user(username: str, password: str, portal_role: str | None = None) -> Session | None:
    """Return a profile-aware session for valid credentials, otherwise ``None``."""
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    user = fetch_single_record(
        "SELECT u.user_id, u.username, u.password_hash, u.password_salt, u.role, "
        "t.teacher_id, s.student_id FROM users u "
        "LEFT JOIN teachers t ON t.user_id = u.user_id "
        "LEFT JOIN students s ON s.user_id = u.user_id WHERE u.username = %s",
        (username.strip(),),
    )
    if not user:
        return None
    user_id, stored_username, password_hash, password_salt, role, teacher_id, student_id = user
    if not isinstance(password_hash, str) or not isinstance(password_salt, str):
        return None
    if not verify_password(password_hash, password, password_salt):
        return None
    if portal_role is not None and role != portal_role.strip().lower():
        raise WrongRoleError("These credentials do not belong to this portal.")
    if role == "teacher" and teacher_id is not None:
        return Session(user_id, stored_username, role, teacher_id=teacher_id)
    if role == "student" and student_id is not None:
        return Session(user_id, stored_username, role, student_id=student_id)
    return None

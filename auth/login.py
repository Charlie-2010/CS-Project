"""Authentication lookup and role-bound session creation."""
from dataclasses import dataclass
from typing import Any

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
        
    user_record = fetch_single_record(
        "SELECT u.user_id, u.username, u.password_hash, u.password_salt, u.role, "
        "t.teacher_id, s.student_id FROM users u "
        "LEFT JOIN teachers t ON t.user_id = u.user_id "
        "LEFT JOIN students s ON s.user_id = u.user_id WHERE u.username = %s",
        (username.strip(),),
    )
    if not user_record:
        return None

    # Cast to Any tuple sequence to completely bypass internal Pylance protocol warnings
    clean_sequence: Any = user_record
    
    raw_user_id = clean_sequence[0]
    raw_username = clean_sequence[1]
    password_hash = clean_sequence[2]
    password_salt = clean_sequence[3]
    raw_role = clean_sequence[4]
    raw_teacher_id = clean_sequence[5]
    raw_student_id = clean_sequence[6]

    # Verify string structures before passing into cryptographic utility layer
    if not isinstance(password_hash, str) or not isinstance(password_salt, str):
        return None
        
    # Re-implemented cryptographic match check
    if not verify_password(password_hash, password, password_salt):
        return None
        
    # Enforce type casting for custom Session object creation
    user_id = int(raw_user_id)
    stored_username = str(raw_username)
    role = str(raw_role)
    
    teacher_id = int(raw_teacher_id) if raw_teacher_id is not None else None
    student_id = int(raw_student_id) if raw_student_id is not None else None
    
    if portal_role is not None and role != portal_role.strip().lower():
        raise WrongRoleError("These credentials do not belong to this portal.")
        
    if role == "teacher" and teacher_id is not None:
        return Session(user_id=user_id, username=stored_username, role=role, teacher_id=teacher_id)
        
    if role == "student" and student_id is not None:
        return Session(user_id=user_id, username=stored_username, role=role, student_id=student_id)
        
    return None
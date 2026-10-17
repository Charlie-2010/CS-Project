"""Authentication lookup used by the UI layer."""

from auth.hash_utils import verify_password
from database.connection import fetch_single_record


def authenticate_user(username: str, password: str):
    """Return ``(user_id, username, role)`` for valid credentials, else ``None``."""
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    user = fetch_single_record(
        "SELECT user_id, username, password_hash, password_salt, role "
        "FROM users WHERE username = %s",
        (username.strip(),),
    )
    if not user:
        return None
    user_id, stored_username, password_hash, password_salt, role = user
    if not verify_password(password_hash, password, password_salt):
        return None
    return user_id, stored_username, role

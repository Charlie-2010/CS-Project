"""Password hashing helpers for the ``users`` table.

The database contract deliberately stores a 32-character hexadecimal salt and
a 64-character hexadecimal hash in separate columns. PBKDF2-HMAC-SHA-256 with
a high iteration count provides secure password stretching while preserving
that fixed schema shape.
"""
from __future__ import annotations

import hashlib
import hmac
import os


_ITERATIONS = 600_000


def generate_salt() -> str:
    """Return a cryptographically random 16-byte salt as 32 hex characters."""
    return os.urandom(16).hex()


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    return password.encode("utf-8")


def _salt_bytes(salt: str) -> bytes:
    if not isinstance(salt, str) or len(salt) != 32:
        raise ValueError("salt must be a 32-character hexadecimal string")
    try:
        return bytes.fromhex(salt)
    except ValueError as exc:
        raise ValueError("salt must be a 32-character hexadecimal string") from exc


def hash_password(plain_text_password: str, salt: str) -> str:
    """Return a 64-character PBKDF2-HMAC-SHA-256 hash for storage."""
    return hashlib.pbkdf2_hmac(
        "sha256", _password_bytes(plain_text_password), _salt_bytes(salt), _ITERATIONS, dklen=32
    ).hex()


def create_password_record(plain_text_password: str) -> tuple[str, str]:
    """Create a ``(password_hash, password_salt)`` pair for a new user."""
    salt = generate_salt()
    return hash_password(plain_text_password, salt), salt


def verify_password(stored_hash: str, input_password: str, stored_salt: str) -> bool:
    """Constant-time verification of a login password against stored values."""
    if not isinstance(stored_hash, str) or len(stored_hash) != 64:
        return False
    try:
        candidate = hash_password(input_password, stored_salt)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(candidate, stored_hash)

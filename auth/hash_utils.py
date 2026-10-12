"""Password hashing utilities using Python's salted, memory-hard scrypt."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

_ALGORITHM, _N, _R, _P = "scrypt", 2**14, 8, 1


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    if not password:
        raise ValueError("password cannot be empty")
    return password.encode("utf-8")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def hash_password(plain_text_password: str) -> str:
    """Create a random-salted, storage-ready scrypt password hash."""
    salt = os.urandom(16)
    key = hashlib.scrypt(_password_bytes(plain_text_password), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"{_ALGORITHM}${_N}${_R}${_P}${_encode(salt)}${_encode(key)}"


def verify_password(stored_hash: str, input_password: str, stored_salt: str | None = None) -> bool:
    """Constant-time check of an entered password against a stored scrypt hash.

    ``stored_salt`` remains optional only for source compatibility. New hashes
    include their salt; unsupported legacy SHA-256 hashes are rejected.
    """
    del stored_salt
    try:
        algorithm, n, r, p, encoded_salt, encoded_key = stored_hash.split("$")
        if algorithm != _ALGORITHM:
            return False
        expected_key = _decode(encoded_key)
        actual_key = hashlib.scrypt(
            _password_bytes(input_password), salt=_decode(encoded_salt),
            n=int(n), r=int(r), p=int(p), dklen=len(expected_key),
        )
        return hmac.compare_digest(actual_key, expected_key)
    except (AttributeError, TypeError, ValueError, UnicodeError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """Identify malformed, legacy, or weaker hashes for replacement at login."""
    try:
        algorithm, n, r, p, *_ = stored_hash.split("$")
        return (algorithm, int(n), int(r), int(p)) != (_ALGORITHM, _N, _R, _P)
    except (AttributeError, ValueError):
        return True

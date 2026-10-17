"""Small parameterized MySQL data-access layer.

Values must be supplied separately from SQL using MySQL Connector's ``%s``
placeholders. Never format form values into a query string.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence, TypeVar, cast

import mysql.connector
from mysql.connector import Error, IntegrityError
from config import DatabaseConfig


class DatabaseOperationError(RuntimeError):
    """Raised when a database operation cannot be completed."""

    def __init__(self, message: str, *, code: int | None = None, category: str = "database"):
        super().__init__(message)
        self.code = code
        self.category = category


class ConstraintViolationError(DatabaseOperationError):
    """Raised for duplicate-key and foreign-key/check constraint failures."""


class DatabaseUnavailableError(DatabaseOperationError):
    """Raised when a configured database connection cannot be opened."""


T = TypeVar("T")


@dataclass(frozen=True)
class TransactionResult:
    value: Any
    row_count: int
    lastrowid: int | None


_CONSTRAINT_ERROR_CODES = {1062, 1451, 1452, 3819}
_ERROR_MESSAGES = {
    1048: "A required value is missing.",
    1062: "A record with that unique value already exists.",
    1451: "This record is still referenced by other records.",
    1452: "A related record does not exist.",
    3819: "The record violates a database check constraint.",
}


def _mapped_error(error: Error) -> DatabaseOperationError:
    code = getattr(error, "errno", None)
    message = _ERROR_MESSAGES.get(code, "The database operation failed.") if isinstance(code, int) else "The database operation failed."
    if isinstance(error, IntegrityError) or code in _CONSTRAINT_ERROR_CODES:
        return ConstraintViolationError(message, code=code, category="constraint")
    return DatabaseOperationError(message, code=code)


def get_connection():
    """Create a connection using the environment-backed application config."""
    try:
        settings = DatabaseConfig.from_env()
        return mysql.connector.connect(**settings.__dict__)
    except (Error, ValueError):
        # Callers can show a clean unavailable-state message instead of crashing
        # when DB_PASSWORD is absent or incorrect.
        return None


def _normalise_params(params: Sequence[Any] | None) -> tuple[Any, ...]:
    if params is None:
        return ()
    if isinstance(params, (str, bytes)) or not isinstance(params, (tuple, list)):
        raise TypeError("Query parameters must be supplied as a tuple or list.")
    return tuple(params)


def _validate_query(query: str, params: tuple[Any, ...]) -> None:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("SQL query must be a non-empty string.")
    if params and "%s" not in query:
        raise ValueError("Parameterized values require %s placeholders in the SQL query.")


def execute_transaction(operation: Callable[[Any], T]) -> TransactionResult:
    """Run cursor work on one connection and commit once, rolling back on failure."""
    connection = get_connection()
    if connection is None:
        raise DatabaseUnavailableError("The database is unavailable.", category="unavailable")
    try:
        with connection.cursor() as cursor:
            value = operation(cursor)
            row_count = cursor.rowcount
            lastrowid = cursor.lastrowid
        connection.commit()
        return TransactionResult(value, row_count, lastrowid)
    except Error as error:
        connection.rollback()
        raise _mapped_error(error) from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_dml(query: str, params: Sequence[Any] | None = None) -> int:
    """Run one parameterized DML statement and return affected rows on success."""
    bound_params = _normalise_params(params)
    _validate_query(query, bound_params)
    return execute_transaction(lambda cursor: cursor.execute(query, bound_params)).row_count


def _fetch(query: str, params: Sequence[Any] | None, one: bool):
    bound_params = _normalise_params(params)
    _validate_query(query, bound_params)
    connection = get_connection()
    if connection is None:
        raise DatabaseUnavailableError("The database is unavailable.", category="unavailable")
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, bound_params)
            return cursor.fetchone() if one else cursor.fetchall()
    except Error as error:
        raise _mapped_error(error) from error
    finally:
        connection.close()


def fetch_all_records(query: str, params: Sequence[Any] | None = None) -> list[tuple[Any, ...]]:
    """Run a parameterized SELECT and return all matching records."""
    return cast(list[tuple[Any, ...]], _fetch(query, params, one=False))


def fetch_single_record(query: str, params: Sequence[Any] | None = None):
    """Run a parameterized SELECT and return one record or ``None``."""
    return _fetch(query, params, one=True)

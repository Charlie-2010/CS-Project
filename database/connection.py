"""Small parameterized MySQL data-access layer.

Values must be supplied separately from SQL using MySQL Connector's ``%s``
placeholders. Never format form values into a query string.
"""
from __future__ import annotations

import os
from typing import Any, Sequence, cast

import mysql.connector
from mysql.connector import Error, IntegrityError


class DatabaseOperationError(RuntimeError):
    """Raised when a database operation cannot be completed."""


class ConstraintViolationError(DatabaseOperationError):
    """Raised for duplicate-key and foreign-key/check constraint failures."""


def get_connection():
    """Create a connection from environment configuration."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "student_performance_system"),
        )
    except Error as exc:
        raise DatabaseOperationError("Could not connect to the database.") from exc


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


def execute_dml(query: str, params: Sequence[Any] | None = None) -> int:
    """Run INSERT/UPDATE/DELETE atomically and return its affected-row count."""
    bound_params = _normalise_params(params)
    _validate_query(query, bound_params)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, bound_params)
            row_count = cursor.rowcount
        connection.commit()
        return row_count
    except IntegrityError as exc:
        connection.rollback()
        raise ConstraintViolationError("The change violates a uniqueness or foreign-key rule.") from exc
    except Error as exc:
        connection.rollback()
        raise DatabaseOperationError("Database write failed; the transaction was rolled back.") from exc
    finally:
        connection.close()


def _fetch(query: str, params: Sequence[Any] | None, one: bool):
    bound_params = _normalise_params(params)
    _validate_query(query, bound_params)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, bound_params)
            return cursor.fetchone() if one else cursor.fetchall()
    except Error as exc:
        raise DatabaseOperationError("Database read failed.") from exc
    finally:
        connection.close()


def fetch_all_records(query: str, params: Sequence[Any] | None = None) -> list[tuple[Any, ...]]:
    """Run a parameterized SELECT and return all matching records."""
    return cast(list[tuple[Any, ...]], _fetch(query, params, one=False))


def fetch_single_record(query: str, params: Sequence[Any] | None = None):
    """Run a parameterized SELECT and return one record or ``None``."""
    return _fetch(query, params, one=True)

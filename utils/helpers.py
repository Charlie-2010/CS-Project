"""Safe convenience helpers for the four validated core entities.

Parameterized SQL protects values, while this module's allow-list protects the
identifiers that cannot be sent to MySQL as ``%s`` parameters.
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from database.connection import execute_dml, fetch_all_records
from utils.validators import ValidationError, validate_entity


_COLUMNS = {
    "students": {"user_id", "roll_number", "first_name", "last_name", "email", "date_of_birth", "class_id"},
    "teachers": {"user_id", "first_name", "last_name", "email", "phone"},
    "classes": {"class_name", "room_number", "class_teacher_id"},
    "subjects": {"subject_name", "subject_code"},
}
_FILTER_COLUMNS = {table: set(columns) for table, columns in _COLUMNS.items()}
_FILTER_COLUMNS["students"].add("student_id")
_FILTER_COLUMNS["teachers"].add("teacher_id")
_FILTER_COLUMNS["classes"].add("class_id")
_FILTER_COLUMNS["subjects"].add("subject_id")
_EQUALITY = re.compile(r"^\s*([a-z_]+)\s*=\s*%s\s*$")


def _columns_for(table_name: str, columns: Sequence[str]) -> list[str]:
    if table_name not in _COLUMNS:
        raise ValidationError(f"Unsupported table: {table_name!r}.")
    if not columns or len(set(columns)) != len(columns) or not set(columns) <= _COLUMNS[table_name]:
        raise ValidationError("One or more requested columns are not valid for this table.")
    return list(columns)


def _where_clause(table_name: str, condition: str, params: Sequence[Any] | None) -> tuple[str, tuple[Any, ...]]:
    match = _EQUALITY.fullmatch(condition or "")
    if not match or match.group(1) not in _FILTER_COLUMNS[table_name]:
        raise ValidationError("Filters must be one allowed column followed by = %s.")
    if not isinstance(params, (tuple, list)) or len(params) != 1:
        raise ValidationError("A filter requires exactly one parameter in a tuple or list.")
    return f"{match.group(1)} = %s", tuple(params)


def insert_record(table_name: str, columns_list: Sequence[str], values_tuple: Sequence[Any]) -> int:
    """Validate and insert one complete core-entity row using ``%s`` values."""
    columns = _columns_for(table_name, columns_list)
    if not isinstance(values_tuple, (tuple, list)) or len(columns) != len(values_tuple):
        raise ValidationError("columns_list and values_tuple must have the same length.")
    cleaned = validate_entity(table_name, dict(zip(columns, values_tuple)))
    placeholders = ", ".join(["%s"] * len(columns))
    return execute_dml(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", tuple(cleaned[column] for column in columns))


def update_record(table_name: str, update_dict: dict[str, Any], condition_str: str, condition_params_tuple: Sequence[Any]) -> int:
    """Validate and update selected fields using one allow-listed equality filter."""
    columns = _columns_for(table_name, list(update_dict))
    cleaned = validate_entity(table_name, update_dict, partial=True)
    where_sql, where_params = _where_clause(table_name, condition_str, condition_params_tuple)
    assignments = ", ".join(f"{column} = %s" for column in columns)
    return execute_dml(f"UPDATE {table_name} SET {assignments} WHERE {where_sql}", tuple(cleaned[column] for column in columns) + where_params)


def delete_record(table_name: str, condition_str: str, condition_params_tuple: Sequence[Any]) -> int:
    """Delete matching rows only when a non-empty allow-listed filter is provided."""
    if table_name not in _COLUMNS:
        raise ValidationError(f"Unsupported table: {table_name!r}.")
    where_sql, where_params = _where_clause(table_name, condition_str, condition_params_tuple)
    return execute_dml(f"DELETE FROM {table_name} WHERE {where_sql}", where_params)


def get_records_by_filter(table_name: str, columns_to_select: Sequence[str], condition_str: str | None = None, params_tuple: Sequence[Any] | None = None):
    """Read allowed columns, optionally with one parameterized equality filter."""
    columns = _columns_for(table_name, columns_to_select)
    query = f"SELECT {', '.join(columns)} FROM {table_name}"
    if condition_str is None:
        if params_tuple is not None:
            raise ValidationError("Parameters require a filter.")
        return fetch_all_records(query)
    where_sql, params = _where_clause(table_name, condition_str, params_tuple)
    return fetch_all_records(f"{query} WHERE {where_sql}", params)

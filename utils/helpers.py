"""
utils/helpers.py
Defines simplified parameter wrapper utilities for core DML transactions 
and entity fetches across teacher and student frontend panels.
"""

from database.connection import execute_dml, fetch_all_records, fetch_single_record

def insert_record(table_name, columns_list, values_tuple):
    """
    Constructs and executes a safe parameterized INSERT query statement.
    
    Example usage:
        insert_record("subjects", ["subject_name", "subject_code"], ("Biology", "BIO12"))
    """
    columns_str = ", ".join(columns_list)
    # Generate the correct number of %s positional anchors safely
    placeholders_str = ", ".join(["%s"] * len(columns_list))
    
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str});"
    
    return execute_dml(query, values_tuple)

def update_record(table_name, update_dict, condition_str, condition_params_tuple):
    """
    Constructs and executes a safe parameterized UPDATE query statement.
    
    Example usage:
        update_record("users", {"username": "new_user"}, "user_id = %s", (5,))
    """
    set_clauses = []
    values_list = []
    
    for column, val in update_dict.items():
        set_clauses.append(f"{column} = %s")
        values_list.append(val)
        
    set_str = ", ".join(set_clauses)
    query = f"UPDATE {table_name} SET {set_str} WHERE {condition_str};"
    
    # Merge values matching columns with condition variables into a single tuple
    full_params = tuple(values_list) + condition_params_tuple
    
    return execute_dml(query, full_params)

def get_records_by_filter(table_name, columns_to_select, condition_str=None, params_tuple=None):
    """
    Fetches clean datasets using safe parameterized tracking.
    
    Example usage:
        get_records_by_filter("students", ["first_name", "last_name"], "class_id = %s", (1,))
    """
    select_str = ", ".join(columns_to_select)
    query = f"SELECT {select_str} FROM {table_name}"
    
    if condition_str:
        query += f" WHERE {condition_str};"
        return fetch_all_records(query, params_tuple)
        
    query += ";"
    return fetch_all_records(query)
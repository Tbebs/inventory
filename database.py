from flask import g, session
import sqlite3
import os
from datetime import datetime

def connect_to_database(db_path):
    """Connect to the SQLite database."""
    sql = sqlite3.connect(db_path)
    sql.row_factory = sqlite3.Row
    return sql

def get_database():
    """Get the SQLite database connection."""
    if not hasattr(g, 'Inventory_db'):
        db_path = 'C:/Users/I_melo/Downloads/Cool_Flask/Inventory.db'
        g.Inventory_db = connect_to_database(db_path)
    return g.Inventory_db

    # Fetch user information from the database based on user_id
    db = get_database()
    cursor = db.execute('SELECT * FROM users WHERE id = ?', [user_id])
    user_data = cursor.fetchone()
    print("User Data:", user_data)  # Print user data

    # Convert user_data to a dictionary
    user_dict = dict(user_data) if user_data else None
    print("User Dict:", user_dict)  # Print user dictionary
    return user_dict


def get_department_database(department_id):
    """Get the connection to the department-specific database."""
    department_db_file = os.path.join('C:/Users/I_melo/Downloads/Cool_Flask', f'{department_id}.db')
    if not os.path.exists(department_db_file):
        raise FileNotFoundError(f'Database file for department {department_id} not found.')
    if not hasattr(g, 'department_conn'):
        g.department_conn = connect_to_database(department_db_file)
    return g.department_conn


def get_current_user():
    user = None
    if 'user' in session:
        user = session['user']
        db = get_database()
        user_cur = db.execute('SELECT * FROM users WHERE full_name = ?', [user])
        user_data = user_cur.fetchone()
        if user_data is not None:
            user = dict(user_data)
    return user



def add_item(item_name, quantity, location, category, availability, purchase_date):
    try:
        db = get_database()
        db.execute('INSERT INTO campus_inventory (item_name, quantity, location, category, availability, purchase_date) VALUES (?, ?, ?, ?, ?, ?)',
                   [item_name, quantity, location, category, availability, purchase_date])
        db.commit()
        return True  # Item added successfully
    except sqlite3.IntegrityError as e:
        # Handle constraint violation (duplicate item_name)
        print(f"Failed to add item: {e}")
        return False  # Failed to add item

def log_operation(user, action, item_id, details=""):
    try:
        if user is None:
            raise ValueError("User is None. Cannot log operation without a valid user.")
        
        department_id = user.get('department_id')
        db = get_department_database(department_id)
        
        db.execute('INSERT INTO operation_logs (user_id, action, item_id, details, timestamp) VALUES (?, ?, ?, ?, ?)', 
                   [user['id'], action, item_id, details, datetime.now()])
        db.commit()
    except Exception as e:
        print(f"An error occurred while logging operation: {e}")
        
def close_department_database(department_conn):
    """Close the connection to the department-specific database."""
    if department_conn is not None:
        department_conn.close()

def close_databases(exception=None):
    """Close all database connections."""
    db = getattr(g, 'Inventory_db', None)
    if db is not None:
        db.close()
    department_conn = getattr(g, 'department_conn', None)
    if department_conn is not None:
        department_conn.close()
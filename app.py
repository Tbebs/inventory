from flask import Flask, url_for, request, session, g
from flask.templating import render_template
from werkzeug.utils import redirect
from database import get_database
from database import get_department_database
from database import close_databases
from database import log_operation
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_login import LoginManager
from flask_login import current_user
from datetime import datetime

import os
import sqlite3

app = Flask(__name__)
login_manager = LoginManager(app)

def create_department_database(department_name):
    db_file = os.path.join('C:\\Users\\I_melo\\Downloads\\Cool_Flask', f'{department_name}.db')
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # Create tables and schema for the department database
    cursor.execute('''CREATE TABLE IF NOT EXISTS department_inventory (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        location TEXT,
                        category TEXT,
                        purchase_date DATE DEFAULT CURRENT_DATE,
                        purchase_price DECIMAL(10, 2) DEFAULT 0.00,
                        supplier TEXT,
                        condition TEXT,
                        availability TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS department_users (
                        id INTEGER PRIMARY KEY,
                        full_name TEXT NOT NULL,
                        password TEXT NOT NULL,
                        role_id INTEGER NOT NULL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS department_permissions (
                        id INTEGER PRIMARY KEY,
                        department_id INTEGER,
                        user_id INTEGER,
                        permission_type TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS department_audit (
                        id INTEGER PRIMARY KEY,
                        department_id INTEGER,
                        user_id INTEGER,
                        action_type TEXT,
                        timestamp TIMESTAMP
                    )''')
    # Add more tables as needed
    conn.commit()
    conn.close()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_database(error):
    if hasattr(g, 'Inventory_db'):
        g.Inventory_db.close()

@app.before_request
def load_current_user():
    """Load the current user before each request."""
    g.current_user = get_current_user()
    
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

@app.route('/')
def index():
    user = get_current_user()
    if user:
        return redirect(url_for('dashboard'))
    return render_template('home.html', user=user)

@app.route('/login', methods=["POST", "GET"])
def login():
    error = None
    if request.method == 'POST':
        full_name = request.form["full_name"]
        password = request.form['password']
        
        # Connect to the main database
        db = get_database()
        
        # Query the main database for user information
        user_cursor = db.execute('SELECT * FROM users WHERE full_name = ?', [full_name])
        user = user_cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user'] = user['full_name']
            if user['role_id'] == 1:  # Admin
                return redirect(url_for('admin_dashboard'))
            elif user['role_id'] == 2:  # Department Head
                department_id = user['department_id']
                if department_id == 1:
                    return redirect(url_for('admin_dashboard'))
                elif department_id == 2:
                    return redirect(url_for('dashboard'))
                elif department_id == 3:
                    return redirect(url_for('CSE_dashboard'))
                elif department_id == 4:
                    return redirect(url_for('EEE_dashboard'))
                elif department_id == 5:
                    return redirect(url_for('ECE_dashboard'))
                elif department_id == 6:
                    return redirect(url_for('BIOCHEM_dashboard'))
                elif department_id == 7:
                    return redirect(url_for('MATSCI_dashboard'))
                elif department_id == 8:
                    return redirect(url_for('Dormitory_dashboard'))
                elif department_id == 9:
                    return redirect(url_for('office_dashboard'))
                else:
                    return redirect(url_for('index'))  # Default dashboard route
            else:
                return redirect(url_for('index'))  # Non-department head user
        else:
            error = "Username or Password did not match, Try again."
    
    return render_template('login.html', loginerror=error)
@app.route('/register', methods=["POST", "GET"])
def register():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        full_name = request.form['full_name']
        password = request.form['password']
        role_id = request.form['role_id']  # Retrieve the selected role ID from the form
        department_id = request.form['department_id']
        
        hashed_password = generate_password_hash(password)
        dbuser_cur = db.execute('SELECT * FROM users WHERE full_name = ?', [full_name])
        existing_username = dbuser_cur.fetchone()
        if existing_username:
            return render_template('register.html', registererror='Username already taken , try different username.')
        
        # Create a new database file for the department if it doesn't exist
        create_department_database(department_id)
        
        # Insert user information into the department database
        department_db_file = os.path.join('C:\\Users\\I_melo\\Downloads\\Cool_Flask', f'{department_id}.db')
        department_conn = sqlite3.connect(department_db_file)
        department_cursor = department_conn.cursor()
        department_cursor.execute('INSERT INTO department_users (full_name, password, role_id) VALUES (?, ?, ?)', [full_name, hashed_password, role_id])
        department_conn.commit()
        department_conn.close()
        
        # Insert user information into the main database (inventory.db)
        db.execute('INSERT INTO users (full_name, password, role_id, department_id) VALUES (?, ?, ?, ?)', [full_name, hashed_password, role_id, department_id])
        db.commit()
        
        # Store the new user's username in the session
        session['new_user'] = full_name
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/addnewemployee', methods=["POST", "GET"])
def addnewemployee():
    user = get_current_user()
    if not user:
        # Redirect to login page if user is not authenticated
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve form data if the request method is POST
        name = request.form['name']
        quantity = request.form['quantity']
        location = request.form['location']
        category = request.form['category']
        availability = request.form['availability']
            
        # Retrieve department-specific database file
        department_db_file = os.path.join('C:/Users/I_melo/Downloads/Cool_Flask', f'{user["department_id"]}.db')
        
        # Connect to the department database
        department_conn = sqlite3.connect(department_db_file)
        department_cursor = department_conn.cursor()
        
        try:
            # Insert the item into the department's inventory table
            department_cursor.execute('INSERT INTO department_inventory (item_name, quantity, location, category, availability) VALUES (?, ?, ?, ?, ?)', 
                                      [name, quantity, location, category, availability])
            department_conn.commit()  # Commit changes to the department-specific database

            # Insert the item into the main database (inventory.db)
            db = get_database()
            db.execute('INSERT INTO campus_inventory (item_name, quantity, location, category, availability) VALUES (?, ?, ?, ?, ?)', 
                                      [name, quantity, location, category, availability])
            db.commit()  # Commit changes to the main database

            # Redirect to the dashboard after successfully adding the item
            if user['role_id'] == 1:  # Admin
                return redirect(url_for('admin_dashboard'))
            elif user['role_id'] == 2:  # Department Head
                department_id = user['department_id']
                if department_id == 1:
                    return redirect(url_for('admin_dashboard'))
                elif department_id == 2:
                    return redirect(url_for('dashboard'))
                elif department_id == 3:
                    return redirect(url_for('CSE_dashboard'))
                elif department_id == 4:
                    return redirect(url_for('EEE_dashboard'))
                elif department_id == 5:
                    return redirect(url_for('ECE_dashboard'))
                elif department_id == 6:
                    return redirect(url_for('BIOCHEM_dashboard'))
                elif department_id == 7:
                    return redirect(url_for('MATSCI_dashboard'))
                elif department_id == 8:
                    return redirect(url_for('Dormitory_dashboard'))
                elif department_id == 9:
                    return redirect(url_for('office_dashboard'))
            # Add other department dashboard routes as needed
            else:
                error = "You do not have permission to access this page."
        except sqlite3.IntegrityError as e:
            print("IntegrityError:", e)  # Print the error for debugging
            error_message = "An error occurred while adding the item to the database."
            return render_template('addnewemployee.html', user=user, error_message=error_message)
        finally:
            department_conn.close()  # Ensure the connection is closed

    # Render the form template for GET requests
    user = get_current_user()
    return render_template('addnewemployee.html', user=user)


@app.route('/admin_dashboard')
def admin_dashboard():
    user = get_current_user()
    if user:
        db = get_database()
        campus_inventory_cur = db.execute('SELECT * FROM campus_inventory')
        all_inventory = campus_inventory_cur.fetchall()
        
        # Check if the user is authenticated and is an admin
        if user['role_id'] == 1:
            return render_template('admin_dashboard.html', user=user, all_inventory=all_inventory)
        else:
            return render_template('admin_dashboard.html', user=None, all_inventory=all_inventory)
    else:
        return render_template('admin_dashboard.html', user=None, all_inventory=None)
@app.route('/admin_dashboard/inventory_manager')
def inventory_manager():
    user = get_current_user()
    new_user = session.pop('new_user', None)  # Retrieve the new user's username from the session
    if user and user['role_id'] == 1:  # Check if the user is an admin
        # Fetch all users under the admin, excluding the admin himself
        db = get_database()
        users_cur = db.execute('SELECT * FROM users WHERE role_id = ? AND id != ?', [1, user['id']])
        users = users_cur.fetchall()
        return render_template('inventory_manager.html', user=user, users=users)
    elif user:
        return redirect(url_for('index'))  # Redirect to the dashboard for non-admin users
    else:
        return redirect(url_for('login'))  # Redirect to the login page if the user is not logged in


@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 2] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
@app.route('/CSE_dashboard')
def CSE_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 3] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('CSE_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    
@app.route('/ECE_dashboard')
def ECE_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 4] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('ECE_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    

@app.route('/EEE_dashboard')
def EEE_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 5] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('EEE_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    

@app.route('/BIOCHEM_dashboard')
def BIOCHEM_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 6] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('BIOCHEM_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    
    
@app.route('/MATSCI_dashboard')
def MATSCI_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 7] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('MATSCI_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    

@app.route('/Dormitory_dashboard')
def Dormitory_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 8] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('Dormitory_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    
@app.route('/office_dashboard')
def office_dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['department_id'] in [1, 9] or user['role_id'] in [1, 2]:
        # Fetch the inventory for the department of the authenticated user
        department_conn = get_department_database(user['department_id'])
        department_inventory_cur = department_conn.cursor()
        department_inventory_cur.execute('SELECT * FROM department_inventory')
        all_inventory = department_inventory_cur.fetchall()
        department_conn.close()  # Close the database connection

        return render_template('office_dashboard.html', current_user=user, all_inventory=all_inventory)
    else:   
        return "You are not authorized to access this page."
    


@app.route('/search', methods=['GET'])
def search():
    item_name = request.args.get('item_name')
    building_name = request.args.get('building_name')

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = None
    cursor = None
    filtered_inventory = None

    if user['role_id'] == 1:  # Administrator
        conn = get_database()
        cursor = conn.cursor()
        query = "SELECT * FROM campus_inventory WHERE 1=1"
        params = []

        if item_name:
            query += " AND item_name LIKE ?"
            params.append(f"%{item_name}%")
        if building_name:
            query += " AND location LIKE ?"
            params.append(f"%{building_name}%")

        cursor.execute(query, params)
        filtered_inventory = cursor.fetchall()
    elif user['role_id'] == 2:  # Department Head
        department_id = user.get('department_id')
        department_conn = get_department_database(department_id)
        cursor = department_conn.cursor()
        query = "SELECT * FROM department_inventory WHERE 1=1"
        params = []

        if item_name:
            query += " AND item_name LIKE ?"
            params.append(f"%{item_name}%")
        if building_name:
            query += " AND location LIKE ?"
            params.append(f"%{building_name}%")

        cursor.execute(query, params)
        filtered_inventory = cursor.fetchall()
        department_conn.close()
    else:
        return "You are not authorized to access this page."

    if conn:
        conn.close()

    return render_template('search_results.html', filtered_inventory=filtered_inventory)



@app.route('/crud_report/<int:log_id>', methods=['GET', 'POST'])
def crud_report(log_id):
    conn = get_database()
    cursor = conn.cursor()

    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']
        item_name = request.form['item_name']
        details = request.form['details']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO operation_logs (user_id, action, item_name, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, action, item_name, details, timestamp))

        conn.commit()
        conn.close()
        return redirect(url_for('admin_reports'))

    cursor.execute("SELECT * FROM operation_logs WHERE id = ?", (log_id,))
    log = cursor.fetchone()  # Fetch the log or None if not found
    conn.close()

    return render_template('crud_report.html', log=log)

@app.route('/updateoperationlog/<int:log_id>', methods=['POST'])
def updateoperationlog(log_id):
    conn = get_database()
    cursor = conn.cursor()

    user_id = request.form['user_id']
    action = request.form['action']
    item_name = request.form['item_name']
    details = request.form['details']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        UPDATE operation_logs
        SET user_id = ?, action = ?, item_name = ?, details = ?, timestamp = ?
        WHERE id = ?
    """, (user_id, action, item_name, details, timestamp, log_id))

    conn.commit()
    conn.close()

    return redirect(url_for('admin_reports'))
@app.route('/singleemployeeprofile/<int:id>')
def singleemployee(id):
    user = get_current_user()
    db = get_database()
    single_item_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    single_item = single_item_cur.fetchone()
    return render_template('singleemployeeprofile.html', user=user, single_item=single_item)

@app.route('/BIOCHEM_empprofile/<int:id>')
def BIOCHEM_empprofile(user_id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [user_id])
    profile = profile_cur.fetchone()
    return render_template('BIOCHEM_empprofile.html', user=user, profile=profile)

@app.route('/CSE_empprofile/<int:id>')
def CSE_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('CSE_empprofile.html', user=user, profile=profile)

@app.route('/EEE_empprofile/<int:id>')
def EEE_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('EEE_empprofile.html', user=user, profile=profile)

@app.route('/ECE_empprofile/<int:id>')
def ECE_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('ECE_empprofile.html', user=user, profile=profile)

@app.route('/OnL_empprofile/<int:id>')
def OnL_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('OnL_empprofile.html', user=user, profile=profile)

@app.route('/MATSCI_empprofile/<int:id>')
def MATSCI_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('MATSCI_empprofile.html', user=user, profile=profile)

@app.route('/DORM_empprofile/<id>')
def DORM_empprofile(id):
    user = get_current_user()
    db = get_database()
    profile_cur = db.execute('SELECT * FROM users WHERE id = ?', [id])
    profile = profile_cur.fetchone()
    return render_template('DORM_empprofile.html', user=user, profile=profile)



@app.route('/fetchone/<int:item_id>')
def fetchone(item_id):
    user = get_current_user()
    if user:
        db = get_database()
        single_item_cur = db.execute('SELECT * FROM campus_inventory WHERE item_id = ?', (item_id,))
        single_item = single_item_cur.fetchone()
        if single_item:
            return render_template('updatecampusinventory.html', user=user, item=single_item)
        else:
            return "Item not found", 404
    else:
        return redirect(url_for('login'))
@app.route('/updatecampusinventory', methods=["POST", "GET"])
def updatecampusinventory():
    user = get_current_user()
    if request.method == 'POST':
        try:
            item_id = request.form.get('item_id')
            item_name = request.form.get('item_name')
            quantity = int(request.form['quantity'])  # Ensure quantity is an integer
            location = request.form.get('location')
            category = request.form.get('category')
            purchase_date = request.form.get('purchase_date')
            availability = request.form.get('availability')
            
            # Debug: Print received data
            print(f"Received data: {item_id}, {item_name}, {quantity}, {location}, {category}, {purchase_date}, {availability}")
            
            db = get_database()
            query = '''UPDATE campus_inventory
                       SET item_name=?, quantity=?, location=?, category=?, purchase_date=?, availability=?
                       WHERE item_id=?'''
            db.execute(query, [item_name, quantity, location, category, purchase_date, availability, item_id])
            db.commit()
            
            # Debug: Print success message
            print("Update successful")
            
        
            if user and user['role_id'] == 1:  # If user is authenticated and is an admin
               return redirect(url_for('admin_dashboard'))
            else:
           
               department_id = user['department_id']
            if department_id == 2:
                return redirect(url_for('dashboard'))
            elif department_id == 3:
                return redirect(url_for('CSE_dashboard'))
            elif department_id == 4:
                return redirect(url_for('EEE_dashboard'))
            elif department_id == 5:
                return redirect(url_for('ECE_dashboard'))
            elif department_id == 6:
                return redirect(url_for('BIOCHEM_dashboard'))
            elif department_id == 7:
                return redirect(url_for('MATSCI_dashboard'))
            elif department_id == 8:
                return redirect(url_for('Dormitory_dashboard'))
            elif department_id == 9:
                return redirect(url_for('office_dashboard'))
    
    # If request method is GET, render the update form
            return render_template('updatecampusinventory.html', user=user)
    
        except Exception as e:
            # Debug: Print error message
            print(f"Error: {e}")
            #  might want to add error handling logic here, such as rendering an error page
@app.route('/deletecampus_inventory/<int:item_id>', methods=["GET", "POST"])
def deletecampus_inventory(item_id):
    user = get_current_user()
    
    if user is None:
        return redirect(url_for('login'))  # Redirect to login page or show error message
    
    if request.method == 'POST':
        try:
            user = get_current_user()
            if user is None:
                return redirect(url_for('login'))  # Redirect if user is not logged in

            department_id = user.get('department_id')
            if department_id == 1:  # Admin
                db = get_database()  # Main database
                table_name = 'campus_inventory'
            elif department_id in [2, 3, 4, 5, 6, 7, 8, 9]:  # Department heads
                db = get_department_database(department_id)
                table_name = 'department_inventory'
            else:
                raise ValueError("Invalid department ID")

            if db is None:
                raise ValueError(f"Database connection is None for department ID: {department_id}")

            db.execute(f'DELETE FROM {table_name} WHERE item_id = ?', [item_id])
            db.commit()

            # Log the operation only for department heads
            if user['role_id'] == 2:  # Department Head
                log_operation(user, 'delete', item_id, f'Deleted an item from {table_name}.')

            # Redirect based on user's department_id
            if user['role_id'] == 1:  # Admin
                return redirect(url_for('admin_dashboard'))
            elif user['role_id'] == 2:  # Department Head
                department_id = user['department_id']
                if department_id == 1:
                    return redirect(url_for('admin_dashboard'))
                elif department_id == 2:
                    return redirect(url_for('dashboard'))
                elif department_id == 3:
                    return redirect(url_for('CSE_dashboard'))
                elif department_id == 4:
                    return redirect(url_for('EEE_dashboard'))
                elif department_id == 5:
                    return redirect(url_for('ECE_dashboard'))
                elif department_id == 6:
                    return redirect(url_for('BIOCHEM_dashboard'))
                elif department_id == 7:
                    return redirect(url_for('MATSCI_dashboard'))
                elif department_id == 8:
                    return redirect(url_for('Dormitory_dashboard'))
                elif department_id == 9:
                    return redirect(url_for('office_dashboard'))
            # Add other department dashboard routes as needed

        except Exception as e:
            # Handle deletion error
            return f"An error occurred while deleting: {e}"

@app.route('/admin/reports')
def admin_reports():
    # Fetch operation logs from the database
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operation_logs")
    operation_logs = cursor.fetchall()
    conn.close()

    return render_template('admin_reports.html', operation_logs=operation_logs)

# Route for the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Route for the Contact Us page
@app.route('/contact')
def contact():
    return render_template('contact.html')
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.teardown_appcontext
def teardown_db(error):
    close_databases(error)
    
if __name__ == '__main__':
    app.run(debug=True)
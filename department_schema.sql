CREATE TABLE department_inventory (
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
);

CREATE TABLE IF NOT EXISTS department_users (
    id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES department_inventory(id)
    -- Add additional columns as needed
);

CREATE TABLE IF NOT EXISTS department_permissions (
    id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    permission_type TEXT,
    FOREIGN KEY (department_id) REFERENCES department_inventory(id),
    FOREIGN KEY (user_id) REFERENCES department_users(id)
    -- Add additional columns as needed
);

CREATE TABLE IF NOT EXISTS department_audit (
    id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES department_inventory(id),
    FOREIGN KEY (user_id) REFERENCES department_users(id)
    -- Add additional columns as needed
);
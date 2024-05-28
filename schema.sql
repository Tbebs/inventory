CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL
);
INSERT INTO roles (role_name) VALUES ('department head'), ('Admin');

CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL
);
INSERT INTO departments (department_name) VALUES ('ADMINISTRATION'), ('IT'), ('CSE'), ('EEE'), ('ECE'), ('BIOCHEM'), ('MATSCI'), ('DORMITORY'), ('OFFICES');

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT,
    department_id INTEGER,
    password TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments (id),
    FOREIGN KEY (role_id) REFERENCES roles (id)
);

CREATE TABLE campus_inventory (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,
    quantity INTEGER DEFAULT 1,
    location TEXT,
    category TEXT,
    purchase_date DATE DEFAULT CURRENT_DATE,
    purchase_price DECIMAL(10, 2) DEFAULT 0.00,
    supplier TEXT,
    condition TEXT,
    availability TEXT
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    item_id INTEGER,
    details TEXT,
    timestamp DATETIME
);
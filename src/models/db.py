import sqlite3
import os

def get_db_path():
    # Find the root of the project (one directory above 'src')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "urban_mobility.db")
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path

db_path = get_db_path()

def open_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    return conn

def close_connection(conn):
    """Close the SQLite database connection."""
    if conn:
        conn.close()

def initialize_database():
    conn = open_connection()
    cursor = conn.cursor()

    # Tabel: users (service engineer, system administrator, super administrator)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            registration_date TEXT NOT NULL,
            temporary_password BOOLEAN NOT NULL DEFAULT 0
        )
    ''')

    # Tabble: travelers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT NOT NULL,
            street TEXT NOT NULL,
            house_number TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            city TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone_number TEXT NOT NULL,
            license_number TEXT NOT NULL UNIQUE,
            registration_date TEXT NOT NULL
        )
    ''')

    # Table: scooters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scooters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            serial_number TEXT NOT NULL UNIQUE,
            top_speed INTEGER NOT NULL,
            battery_capacity REAL NOT NULL,
            soc INTEGER NOT NULL,
            soc_range_min INTEGER NOT NULL,
            soc_range_max INTEGER NOT NULL,
            location_latitude REAL NOT NULL,
            location_longitude REAL NOT NULL,
            out_of_service BOOLEAN NOT NULL DEFAULT 0,
            mileage INTEGER NOT NULL DEFAULT 0,
            last_maintenance_date DATE NOT NULL
        
            
        )
    ''')
    
    # Table: logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            suspicious BOOLEAN NOT NULL DEFAULT 0,
            is_read BOOLEAN NOT NULL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS restore_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            system_admin_id TEXT NOT NULL,  -- Geëncrypte waarde, dus TEXT type
            backup_filename TEXT NOT NULL,
            FOREIGN KEY(system_admin_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    close_connection(conn)
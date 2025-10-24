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
            temporary_password TEXT NOT NULL
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
            last_maintenance_date DATE NOT NULL,
            in_service_date DATE NOT NULL
        )
    ''')
    
    # Add migration for existing databases that don't have in_service_date column
    try:
        cursor.execute('ALTER TABLE scooters ADD COLUMN in_service_date DATE')
        print("Added in_service_date column to existing scooters table")
    except sqlite3.OperationalError:
        # Column already exists, ignore the error
        pass
    
    # Migrate existing temporary_password values from integer (0/1) to encrypted text
    try:
        from security.encryption import encrypt_message, decrypt_message, load_symmetric_key
        key = load_symmetric_key()
        
        # Check if there are any non-encrypted values (integers 0 or 1)
        cursor.execute("SELECT id, temporary_password FROM users")
        rows = cursor.fetchall()
        
        migrated_count = 0
        for user_id, temp_pass in rows:
            # Try to decrypt - if it fails, it's not encrypted yet
            try:
                # Attempt to decrypt the value
                decrypted = decrypt_message(temp_pass, key)
                # If decryption succeeds, it's already encrypted - skip it
                continue
            except Exception:
                # Decryption failed - this is a plain integer value that needs encryption
                # Convert to string and encrypt
                if temp_pass in (0, 1, '0', '1'):
                    encrypted_value = encrypt_message(str(temp_pass), key)
                    cursor.execute("UPDATE users SET temporary_password = ? WHERE id = ?", (encrypted_value, user_id))
                    migrated_count += 1
        
        if migrated_count > 0:
            conn.commit()
            print(f"Migrated {migrated_count} temporary_password value(s) to encrypted format")
    except Exception as e:
        # If migration fails, continue
        print(f"Temporary password migration skipped or failed: {e}")
    
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

    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS restore_codes (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         code TEXT NOT NULL UNIQUE,
    #         system_admin_id TEXT NOT NULL,  -- Geëncrypte waarde, dus TEXT type
    #         backup_filename TEXT NOT NULL,
    #         FOREIGN KEY(system_admin_id) REFERENCES users(id)
    #     )
    # ''')
    conn.commit()
    close_connection(conn)
from models.db import open_connection, close_connection
from security.encryption import encrypt_message, decrypt_message, load_symmetric_key
from security.password_hashing import hash_password
from datetime import datetime

class User:
    def __init__(self, id, username, firstname, lastname, role, registration_date):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.role = role
        self.registration_date = registration_date

    
    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', role='{self.role}', registration_date='{self.registration_date}')"
    
def create_user(username, firstname, lastname,  password, role):
        """Create a new user in the database."""
        conn = open_connection()
        cursor = conn.cursor()
        key = load_symmetric_key()

        try:
            encrypted_username = encrypt_message(username, key)
            encrypted_firstname = encrypt_message(firstname, key)
            encrypted_lastname = encrypt_message(lastname, key)
            encrypted_role = encrypt_message(role, key)
            hashed_password = hash_password(password)
            date_time_now1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format the date as needed
            date_time_now = encrypt_message(date_time_now1, key)  # Example date, replace with actual date logic

            cursor.execute('''
                INSERT INTO users (username, firstname, lastname, password, role, registration_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (encrypted_username, encrypted_firstname, encrypted_lastname, hashed_password, encrypted_role, date_time_now))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            close_connection(conn)

def list_users():
    """List all users in the database."""
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()  # Ensure the symmetric key is loaded for decryption
    
    try:
        cursor.execute('SELECT id, username, firstname, lastname, role, registration_date FROM users')
        rows = cursor.fetchall()

        users = []
        for row in rows:
            id = row[0]
            username = decrypt_message(row[1], key)
            firstname = decrypt_message(row[2], key)
            lastname = decrypt_message(row[3], key)
            role = decrypt_message(row[4], key)
            registration_date = decrypt_message(row[5], key)


            users.append(User(id, username, firstname, lastname,  role, registration_date))
        return users
    except Exception as e:
        print(f"An error occurred while listing users: {e}")
        return []
    finally:
        close_connection(conn)


def get_user_by_username(username):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        # Step 1: fetch only username and id (minimal decryption)
        cursor.execute('SELECT id, username FROM users')
        rows = cursor.fetchall()

        matched_id = None
        for row in rows:
            user_id = row[0]
            username_dec = decrypt_message(row[1], key)
            if username_dec.lower() == username.lower():
                matched_id = user_id
                break

        if not matched_id:
            return None

        # Step 2: retrieve all info for this specific user
        cursor.execute('''
            SELECT id, username, firstname, lastname, role, registration_date
            FROM users
            WHERE id = ?
        ''', (matched_id,))
        user_row = cursor.fetchone()

        if user_row:
            id = user_row[0]
            username_dec = decrypt_message(user_row[1], key)
            firstname_dec = decrypt_message(user_row[2], key)
            lastname_dec = decrypt_message(user_row[3], key)
            role_dec = decrypt_message(user_row[4], key)
            registration_date_dec = decrypt_message(user_row[5], key)

            return User(id, username_dec, firstname_dec, lastname_dec, role_dec, registration_date_dec)
        else:
            return None

    except Exception as e:
        print(f"An error occurred while fetching user by username: {e}")
        return None
    finally:
        close_connection(conn)


def update_password(username, new_password):
    """Update the password for a user."""
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()  # Ensure the symmetric key is loaded for encryption
    
    try:
        hashed_password = hash_password(new_password)  # Hash the new password
        cursor.execute('SELECT id, username from users')
        rows = cursor.fetchall()

        user_id = None
        for row in rows:
            id = row[0]
            username_dec = decrypt_message(row[1], key)
            if username_dec == username:
                user_id = id
                break

        if user_id is None:
            print(f"User with username '{username}' not found.")
            return False
        
        cursor.execute('''
            UPDATE users
            SET password = ?
            WHERE id = ?
        ''', (hashed_password, user_id))

        conn.commit()
        return cursor.rowcount > 0  # Return True if the update was successful
    except Exception as e:
        print(f"An error occurred while updating password: {e}")
        return False
    finally:
        close_connection(conn)

def clear_temporary_passwords(user_id):
    """Clear the temporary password flag for a user with id."""
    # print("DEBUG: Clearing temporary password for user_id:", user_id)
    conn = open_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET temporary_password = 0 WHERE id = ?', (user_id,))
        conn.commit()
    finally:
        close_connection(conn)

def delete_user_by_id(user_id):
    """Delete a user by ID."""
    conn = open_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    close_connection(conn)
    
    return cursor.rowcount > 0  # Return True if the deletion was successful

def update_user_by_id(user_id, fields):
    """Update user information by ID."""
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()  # Load the symmetric key for encryption/decryption
    
    try:
        # Encrypt the field values
        encrypted_fields = {}
        for field_name, field_value in fields.items():
            # Password is handled separately with hash_password
            if field_name == 'password':
                encrypted_fields[field_name] = hash_password(field_value)
            # Other fields are encrypted
            else:
                encrypted_fields[field_name] = encrypt_message(field_value, key)
       
    
        set_clause = ', '.join(f"{key} = ?" for key in encrypted_fields.keys())
        values = list(encrypted_fields.values())
        values.append(user_id)
        
        cursor.execute(f'''
            UPDATE users
            SET {set_clause}
            WHERE id = ?
        ''', values)
        
        conn.commit()
        return cursor.rowcount > 0  # Return True if the update was successful
    except Exception as e:
        print(f"An error occurred while updating user: {e}")
        return False
    finally:
        close_connection(conn)

# Update password for user and set temporary password flag
def update_password_by_id(user_id, new_password):
    """Update the password for a user by ID."""
    conn = open_connection()
    cursor = conn.cursor()
    
    try:
        hashed_password = hash_password(new_password)  # Hash the new password
        
        cursor.execute('''
            UPDATE users
            SET password = ?, temporary_password = 1
            WHERE id = ?
        ''', (hashed_password, user_id))
        
        conn.commit()
        return cursor.rowcount > 0  # Return True if the update was successful
    except Exception as e:
        print(f"An error occurred while updating password: {e}")
        return False
    finally:
        close_connection(conn)

def get_user_password_by_username(username):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        # Step 1: find user-id via username
        cursor.execute('SELECT id, username FROM users')
        rows = cursor.fetchall()

        user_id = None
        for row in rows:
            decrypted_username = decrypt_message(row[1], key)
            if decrypted_username.lower() == username.lower():
                user_id = row[0]
                break

        if user_id is None:
            return None

        # Step 2: retrieve password for this user
        cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"An error occurred while getting user password: {e}")
        return None
    finally:
        close_connection(conn)
    
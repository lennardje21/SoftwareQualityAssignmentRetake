import sqlite3
from models.db import open_connection, close_connection
from security.password_hashing import validate_password
from logs.log import log_instance
from models.user import User
from controllers.user_controller import change_own_password
from models.user import clear_temporary_passwords
from security.validation import Validation
from security.encryption import encrypt_message, decrypt_message, load_symmetric_key
from security.password_hashing import hash_password
from controllers.user_controller import change_own_password
from models.user import clear_temporary_passwords
import sys


login_attempts ={}
MAX_ATTEMPTS = 3

def login():
    print("Welcome to the Urban Mobility System")
    key = load_symmetric_key()

    for attempt in range(3):
        username_input = input("Username: ").strip().lower()
        password_input = input("Password: ").strip()

        # Super admin bypass
        if username_input == "super_admin":
            if password_input == "Admin_123?":
                log_instance.addlog("super_admin", "Login successful", "Hardcoded login", False)
                print("Login successful! You are logged in as Super Administrator.")
                return User(id=0, username="super_admin", firstname="Super", lastname="Admin", role="super_administrator", registration_date="2025-01-01")
            else:
                print("Login failed.")
                log_instance.addlog("super_admin", "Login failed", "Invalid hardcoded password", suspicious=True)
                continue

        if not Validation.username_validation(username_input) or not Validation.password_validation(password_input, username_input):
            print("Login failed.")
            log_instance.log_invalid_input(username_input, "login", "Invalid login format")
            continue

        # Search for user in the database
        conn = open_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id, username FROM users")
            all_users = cursor.fetchall()

            matching_user = None
            for row in all_users:
                try:
                    decrypted_username = decrypt_message(row[1], key).lower()
                    if decrypted_username == username_input:
                        matching_user = row[0]  # user_id
                        break
                except:
                    continue

            if not matching_user:
                print("Login failed.")  # NIET zeggen "username bestaat niet"
                log_instance.addlog(username_input, "Login failed", "Invalid credentials", suspicious=True)
                continue

            # Fetch additional info
            cursor.execute("SELECT password, role, registration_date, temporary_password, firstname, lastname FROM users WHERE id = ?", (matching_user,))
            result = cursor.fetchone()
            if not result:
                print("Login failed.")
                log_instance.addlog(username_input, "Login failed", "User not found after matching id", suspicious=True)
                continue

            hashed_password, enc_role, enc_date, temp_flag, enc_firstname, enc_lastname = result

            if not validate_password(password_input, hashed_password):
                print("Login failed.")
                log_instance.addlog(username_input, "Login failed", "Invalid credentials", suspicious=True)
                continue

            # Login correct
            role = decrypt_message(enc_role, key)
            reg_date = decrypt_message(enc_date, key)
            first_name = decrypt_message(enc_firstname, key)
            last_name = decrypt_message(enc_lastname, key)

            # check if password is temporary
            if temp_flag == 1:
                print("Your password is temporary. Please change it immediately.")
                temp_user = User(id=matching_user, username=username_input, firstname=first_name, lastname=last_name, role=role, registration_date=reg_date)
                success = change_own_password(temp_user)
                
                # print("DEBUG: Temporary password change success:")
                if success:
                    clear_temporary_passwords(matching_user)
                    print("Please login again with your new password.")
                    return login()
                else:
                    print("Password change failed. Please contact your administrator.")
                    return None

            print(f"Login successful! You are logged in as {role.replace('_', ' ').title()}.")
            log_instance.addlog(username_input, "Login successful", "", False)
            return User(id=matching_user, username=username_input, firstname=first_name, lastname=last_name, role=role, registration_date=reg_date)

        finally:
            close_connection(conn)

    print("Too many failed login attempts. You are now locked out.")
    log_instance.addlog(username_input, "Login failed", "Too many attempts", suspicious=True)
    sys.exit()
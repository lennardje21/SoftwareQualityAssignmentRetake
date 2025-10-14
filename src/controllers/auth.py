import sqlite3, sys, time
from models.db import open_connection, close_connection
from security.password_hashing import validate_password
from logs.log import log_instance
from models.user import User
from controllers.user_controller import change_own_password
from models.user import clear_temporary_passwords
from security.validation import Validation
from security.encryption import decrypt_message, load_symmetric_key
from helpers.general_methods import general_methods



MAX_ATTEMPTS = 3
SUPER_ADMIN_USERNAME = "super_admin"
SUPER_ADMIN_PASSWORD = "Admin_123?"


def login() -> User | None:
    """Main login function that handles the authentication flow."""
    key = load_symmetric_key()
    
    for attempt in range(MAX_ATTEMPTS):
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + "Welcome to the Urban Mobility System".center(75) + "|")
        print("----------------------------------------------------------------------------")
        username_input = input("Username: ").strip().lower()
        password_input = input("Password: ").strip()
        
        general_methods.clear_console()
        
        user = _attempt_login(username_input, password_input, key)
        if user:
            return user
    
    _handle_lockout(username_input)
    return None


def _attempt_login(username: str, password: str, key: bytes) -> User | None:
    """Attempt a single login with given credentials."""
    # Check super admin first
    if username == SUPER_ADMIN_USERNAME:
        return _handle_super_admin_login(password)
    
    # Validate input format
    if not _validate_credentials_format(username, password):
        return None
    
    # Try database authentication
    return _authenticate_database_user(username, password, key)


def _handle_super_admin_login(password: str) -> User | None:
    """Handle super admin authentication."""
    if password == SUPER_ADMIN_PASSWORD:
        log_instance.addlog("super_admin", "Login successful", "Hardcoded login", False)
        print("Login successful! You are logged in as Super Administrator.")
        return User(
            id=0, 
            username="super_admin", 
            firstname="Super", 
            lastname="Admin", 
            role="super_administrator", 
            registration_date="2025-01-01"
        )
    else:
        print("Login failed.")
        log_instance.addlog("super_admin", "Login failed", "Invalid hardcoded password", suspicious=True)
        time.sleep(2)
        return None


def _validate_credentials_format(username: str, password: str) -> bool:
    """Validate the format of username and password."""
    if not Validation.username_validation(username) or not Validation.password_validation(password, username):
        print("Login failed.")
        log_instance.log_invalid_input(username, "login", "Invalid login format")
        time.sleep(2)
        return False
    return True


def _authenticate_database_user(username: str, password: str, key: bytes) -> User | None:
    """Authenticate user against database."""
    conn = open_connection()
    try:
        user_id = _find_user_by_username(conn, username, key)
        if not user_id:
            print("Login failed.")
            log_instance.addlog(username, "Login failed", "Invalid credentials", suspicious=True)
            time.sleep(2)
            return None
        
        user_data = _fetch_user_data(conn, user_id)
        if not user_data:
            print("Login failed.")
            log_instance.addlog(username, "Login failed", "User not found after matching id", suspicious=True)
            time.sleep(2)
            return None
        
        if not validate_password(password, user_data['password']):
            print("Login failed.")
            log_instance.addlog(username, "Login failed", "Invalid credentials", suspicious=True)
            time.sleep(2)
            return None
        
        return _create_authenticated_user(username, user_id, user_data, key)
    
    finally:
        close_connection(conn)


def _find_user_by_username(conn: sqlite3.Connection, username: str, key: bytes) -> int | None:
    """Find user ID by decrypting and matching username."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    all_users = cursor.fetchall()
    
    for user_id, encrypted_username in all_users:
        try:
            decrypted_username = decrypt_message(encrypted_username, key).lower()
            if decrypted_username == username:
                return user_id
        except Exception:
            continue
    
    return None


def _fetch_user_data(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """Fetch user data from database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, role, registration_date, temporary_password, firstname, lastname FROM users WHERE id = ?", 
        (user_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        return None
    
    return {
        'password': result[0],
        'role': result[1],
        'registration_date': result[2],
        'temporary_password': result[3],
        'firstname': result[4],
        'lastname': result[5]
    }


def _create_authenticated_user(username: str, user_id: int, user_data: dict, key: bytes) -> User | None:
    """Create User object and handle temporary password logic."""
    role = decrypt_message(user_data['role'], key)
    reg_date = decrypt_message(user_data['registration_date'], key)
    first_name = decrypt_message(user_data['firstname'], key)
    last_name = decrypt_message(user_data['lastname'], key)
    
    user = User(
        id=user_id,
        username=username,
        firstname=first_name,
        lastname=last_name,
        role=role,
        registration_date=reg_date
    )
    
    # Handle temporary password
    if user_data['temporary_password'] == 1:
        return _handle_temporary_password(user)
    
    # Regular successful login
    print(f"Login successful! You are logged in as {role.replace('_', ' ').title()}.")
    log_instance.addlog(username, "Login successful", "", False)
    return user


def _handle_temporary_password(user: User) -> User | None:
    """Handle temporary password change flow."""
    print("Your password is temporary. Please change it immediately.")
    success = change_own_password(user)
    
    if success:
        clear_temporary_passwords(user.id)
        print("Please login again with your new password.")
        return login()  # Recursive call - could be improved
    else:
        print("Password change failed. Please contact your administrator.")
        return None


def _handle_lockout(username: str) -> None:
    """Handle user lockout after too many attempts."""
    print("Too many failed login attempts. You are now locked out.")
    log_instance.addlog(username, "Login failed", "Too many attempts", suspicious=True)
    sys.exit()
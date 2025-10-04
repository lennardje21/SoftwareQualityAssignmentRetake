import bcrypt

def hash_password(password: str) -> str:

    """
    Generates a secure hash of the password using bcrypt with an automatically generated salt.
    Returns: hashed password string (including salt)
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # store as string in DB

def validate_password(password: str, hashed_password: str) -> bool:
    """
    Verifies whether the entered password matches the stored hash.
    Returns: True if correct, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

    
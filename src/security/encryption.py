from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64

def generate_symmetric_key():
    """
    Generate a random AES key and save it to a file.
    """
    key = os.urandom(32)  # 256-bit key for AES-256
    with open('security/symmetric.key', 'wb') as f:
        f.write(key)
    print("Symmetrische sleutel gegenereerd en opgeslagen.")

def get_key_path():
    # Find the root of the project (one directory above 'src')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    key_path = os.path.join(base_dir, "security", "symmetric.key")
    # Ensure the security directory exists
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    return key_path
    
def load_symmetric_key():
    key_path = get_key_path()
    with open(key_path, 'rb') as f:
        return f.read()

def encrypt_message(message, key):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + ct).decode()

def decrypt_message(token, key):
    data = base64.b64decode(token)
    iv = data[:16]
    ct = data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    message = unpadder.update(padded_data) + unpadder.finalize()
    return message.decode()
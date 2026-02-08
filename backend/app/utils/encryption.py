from cryptography.fernet import Fernet
import base64
import json
from typing import Dict, Any

from app.config import settings

# Generate key from secret
def get_fernet_key() -> bytes:
    """Generate Fernet key from settings"""
    # Use first 32 bytes of secret key
    key = settings.SECRET_KEY[:32].encode()
    return base64.urlsafe_b64encode(key.ljust(32)[:32])

cipher = Fernet(get_fernet_key())

def encrypt_string(data: str) -> str:
    """Encrypt a string"""
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()

def decrypt_string(encrypted_data: str) -> str:
    """Decrypt a string"""
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()

def encrypt_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields in dictionary"""
    json_str = json.dumps(data)
    encrypted = encrypt_string(json_str)
    return {"encrypted": encrypted}

def decrypt_dict(encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt dictionary"""
    if "encrypted" in encrypted_data:
        decrypted_str = decrypt_string(encrypted_data["encrypted"])
        return json.loads(decrypted_str)
    return encrypted_data
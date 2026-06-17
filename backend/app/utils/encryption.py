import os
from cryptography.fernet import Fernet


def _get_cipher() -> Fernet:
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise RuntimeError('ENCRYPTION_KEY environment variable is not set')
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str) -> str:
    return _get_cipher().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_cipher().decrypt(encrypted.encode()).decode()

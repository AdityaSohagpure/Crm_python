import base64
import os
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend_python.common.config import settings

security_bearer = HTTPBearer()

def get_aes_gcm_key() -> bytes:
    key_hex = settings.TOKEN_ENCRYPTION_KEY
    return bytes.fromhex(key_hex)

def encrypt_token(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    key = get_aes_gcm_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_token(cipher_text: str) -> str:
    if not cipher_text:
        return cipher_text
    try:
        data = base64.b64decode(cipher_text)
        nonce, ciphertext = data[:12], data[12:]
        key = get_aes_gcm_key()
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    except Exception:
        return cipher_text

def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security_bearer)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if "tenantId" not in payload:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Token lacks valid tenant context scope."
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired or is invalid."
        )

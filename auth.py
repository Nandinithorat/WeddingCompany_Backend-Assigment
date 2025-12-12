# auth.py
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MIN
from database import admins

security = HTTPBearer()


# password hashing
def hash_pwd(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def check_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return bcrypt.checkpw(
        plain_pwd.encode('utf-8'),
        hashed_pwd.encode('utf-8')
    )


# jwt token stuff
def create_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN)
    payload["exp"] = expire

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


# dependency for protected routes
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    payload = verify_token(token)

    admin_id = payload.get("admin_id")
    org_id = payload.get("organization_id")

    if not admin_id or not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # check if admin exists
    try:
        admin = admins.find_one({"_id": ObjectId(admin_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin ID"
        )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )

    return {
        "admin_id": str(admin["_id"]),
        "organization_id": org_id,
        "email": admin.get("email")
    }
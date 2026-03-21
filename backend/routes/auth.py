from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import SessionLocal
from backend.models import User
from pydantic import BaseModel, EmailStr
from passlib.hash import pbkdf2_sha256
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

# 🔐 Config
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("SECRET_KEY NOT SET ❌")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


# 📦 Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# 🗄️ DB Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session


# 📝 REGISTER (SMART FRAUD DETECTION)
@router.post("/register")
async def register(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email = user.email.strip().lower()
    password = user.password.strip()

    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    # 🔐 Get IP + DEVICE
    ip = request.client.host
    device = request.headers.get("user-agent")

    # 📊 Count accounts from IP
    result = await db.execute(
        select(func.count()).select_from(User).where(User.ip_address == ip)
    )
    ip_count = result.scalar()

    # 📊 Count accounts from DEVICE
    result = await db.execute(
        select(func.count()).select_from(User).where(User.device == device)
    )
    device_count = result.scalar()

    # 🚫 STRONG BLOCK (both high)
    if ip_count >= 3 and device_count >= 2:
        raise HTTPException(
            status_code=403,
            detail="Suspicious activity detected (IP + Device limit)"
        )

    # ⚠️ MEDIUM BLOCK (either too high)
    if ip_count >= 5:
        raise HTTPException(
            status_code=403,
            detail="Too many accounts from this IP"
        )

    if device_count >= 3:
        raise HTTPException(
            status_code=403,
            detail="Too many accounts from this device"
        )

    # 🔍 Check if email already exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔐 Hash password
    hashed_password = pbkdf2_sha256.hash(password)

    # ✅ Create user
    new_user = User(
        email=email,
        password=hashed_password,
        ip_address=ip,
        device=device
    )

    db.add(new_user)
    await db.commit()

    return {"message": "User registered successfully"}


# 🔐 LOGIN (TRACK + SECURITY)
@router.post("/login")
async def login(
    user: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email = user.email.strip().lower()
    password = user.password.strip()

    # 🔍 Fetch user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # 🚫 Blocked user
    if db_user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")

    # 🔐 Verify password
    if not pbkdf2_sha256.verify(password, db_user.password):
        raise HTTPException(status_code=400, detail="Wrong password")

    # 🔄 Update tracking
    db_user.ip_address = request.client.host
    db_user.device = request.headers.get("user-agent")

    await db.commit()

    # 🔥 Create token
    payload = {
        "user_id": int(db_user.id),
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
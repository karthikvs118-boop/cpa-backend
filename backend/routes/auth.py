from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


# 📝 REGISTER (ANTI-FRAUD ENABLED)
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

    # 🔐 Get user IP
    ip = request.client.host

    # 🚫 LIMIT MULTIPLE ACCOUNTS FROM SAME IP
    result = await db.execute(
        select(User).where(User.ip_address == ip)
    )
    users_from_ip = result.scalars().all()

    if len(users_from_ip) >= 3:
        raise HTTPException(
            status_code=403,
            detail="Too many accounts from this IP"
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
        ip_address=ip  # 🔥 STORE IP
    )

    db.add(new_user)
    await db.commit()

    return {"message": "User registered successfully"}


# 🔐 LOGIN (WITH BLOCK CHECK)
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):

    email = user.email.strip().lower()
    password = user.password.strip()

    # 🔍 Fetch user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # 🚫 Check if user is blocked
    if db_user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")

    # 🔐 Verify password
    if not pbkdf2_sha256.verify(password, db_user.password):
        raise HTTPException(status_code=400, detail="Wrong password")

    # 🔥 CREATE TOKEN
    payload = {
        "user_id": int(db_user.id),
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
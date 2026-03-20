from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import SessionLocal
from backend.models import User
from pydantic import BaseModel, EmailStr
from passlib.hash import pbkdf2_sha256
from jose import jwt
from datetime import datetime, timedelta

router = APIRouter()

# 🔐 Config
SECRET_KEY = "your_secret_key"
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

# 📝 REGISTER
@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):

    email = user.email.strip().lower()
    password = user.password.strip()

    # basic validation
    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    # check if user already exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # hash password
    hashed_password = pbkdf2_sha256.hash(password)

    new_user = User(
        email=email,
        password=hashed_password
    )

    db.add(new_user)
    await db.commit()

    return {"message": "User registered successfully"}

# 🔐 LOGIN
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):

    email = user.email.strip().lower()
    password = user.password.strip()

    # fetch user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # verify password
    valid = pbkdf2_sha256.verify(password, db_user.password)

    if not valid:
        raise HTTPException(status_code=400, detail="Wrong password")

    # create JWT token
    payload = {
        "user_id": db_user.id,
        "email": db_user.email,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
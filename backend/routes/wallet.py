from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Withdrawal, Click
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import os

router = APIRouter()

# 🔐 Config
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("SECRET_KEY NOT SET ❌")

ALGORITHM = "HS256"

# 🔐 Security
security = HTTPBearer()

# 🔥 Rate limiter
limiter = Limiter(key_func=get_remote_address)

# 🗄️ DB Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session


# 🔐 Get current user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return int(user_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# 🔥 Generate sub_id
def generate_sub_id(user_id: int):
    return f"{user_id}_{uuid.uuid4().hex}"


# 🔥 Generate CPA tracking link
@router.get("/generate-link")
@limiter.limit("10/minute")
async def generate_link(
    request: Request,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 🔍 Check user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🚫 Blocked user
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    # 🔐 Get IP
    ip = request.client.host

    # 🚀 FAST click count
    result = await db.execute(
        select(func.count()).select_from(Click).where(Click.user_id == user_id)
    )
    click_count = result.scalar()

    # 🚫 Click spam protection
    if click_count >= 100:
        raise HTTPException(status_code=403, detail="Too many clicks")

    # 🔥 Generate sub_id
    sub_id = generate_sub_id(user_id)

    # 💾 Save click
    click = Click(
        user_id=user_id,
        sub_id=sub_id,
        ip_address=ip
    )

    db.add(click)
    await db.commit()

    # ✅ REAL CPA LINK (IMPORTANT 🔥)
    base_url = "https://singingfiles.com/show.php?l=0&u=712357&id=70069&subid={subid}"
    offer_link = base_url.replace("{subid}", sub_id)

    return {
        "sub_id": sub_id,
        "offer_link": offer_link
    }


# 💰 Get balance
@router.get("/balance")
async def get_balance(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"balance": user.balance}


# 💸 Request withdrawal
@router.post("/withdraw")
async def request_withdrawal(
    amount: float,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🚫 Blocked user
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is ₹100")

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user.balance -= amount

    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        status="pending"
    )

    db.add(withdrawal)

    await db.commit()
    await db.refresh(user)

    return {
        "message": "Withdrawal request submitted",
        "remaining_balance": user.balance
    }


# 👤 Get profile
@router.get("/me")
async def get_me(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "email": user.email,
        "balance": user.balance
    }
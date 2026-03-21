from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Withdrawal, Click
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
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


# 🔥 Generate CPA tracking link (ANTI-FRAUD ENABLED)
@router.get("/generate-link")
async def generate_link(
    request: Request,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 🔍 Check user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🚫 Blocked user check
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    # 🔐 Get IP
    ip = request.client.host

    # 🚫 Click spam protection (max 100 clicks)
    result = await db.execute(
        select(Click).where(Click.user_id == user_id)
    )
    clicks = result.scalars().all()

    if len(clicks) >= 100:
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

    # 🔗 CPA link
    base_url = "https://example.cpagrip.com/offer123"
    offer_link = f"{base_url}?subid={sub_id}"

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
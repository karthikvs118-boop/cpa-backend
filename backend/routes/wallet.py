from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import SessionLocal
from backend.models import User, Withdrawal, Click, Transaction
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta
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

# 🚦 Rate limiter
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


# 🔗 Generate CPA tracking link
@router.get("/generate-link")
@limiter.limit("10/minute")
async def generate_link(
    request: Request,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    ip = request.client.host

    # 🚨 Recent clicks (5 min)
    time_limit = datetime.utcnow() - timedelta(minutes=5)

    result = await db.execute(
        select(func.count()).select_from(Click).where(
            Click.user_id == user_id,
            Click.created_at >= time_limit
        )
    )
    recent_clicks = result.scalar()

    if recent_clicks > 20:
        raise HTTPException(status_code=403, detail="Too many clicks (cooldown)")

    # 🚫 IP abuse protection
    result = await db.execute(
        select(func.count()).select_from(Click).where(Click.ip_address == ip)
    )
    ip_clicks = result.scalar()

    if ip_clicks > 200:
        raise HTTPException(status_code=403, detail="Suspicious IP activity")

    # 🔥 Generate sub_id
    sub_id = generate_sub_id(user_id)

    click = Click(
        user_id=user_id,
        sub_id=sub_id,
        ip_address=ip
    )

    db.add(click)
    await db.commit()

    # ✅ CPA LINK (replace with your offer anytime)
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


# 💸 Withdrawal system (SMART AUTO + FRAUD SAFE)
@router.post("/withdraw")
async def request_withdrawal(
    amount: float,
    method: str,
    account: str,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    # 💰 Validation
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is ₹100")

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # 💳 Validate method
    if method not in ["upi", "paytm", "bank"]:
        raise HTTPException(status_code=400, detail="Invalid method")

    if not account:
        raise HTTPException(status_code=400, detail="Account required")

    # ⏱️ Cooldown (1 hour)
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.user_id == user_id)
        .order_by(Withdrawal.id.desc())
    )
    last_withdrawal = result.scalars().first()

    if last_withdrawal and last_withdrawal.created_at:
        if last_withdrawal.created_at > datetime.utcnow() - timedelta(hours=1):
            raise HTTPException(status_code=400, detail="Wait before next withdrawal")

    # 📊 Total transactions (trust)
    result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
    )
    txn_count = result.scalar()

    # 🚨 Recent transactions (10 min)
    time_limit = datetime.utcnow() - timedelta(minutes=10)

    result = await db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.created_at >= time_limit
        )
    )
    recent_txn = result.scalar()

    auto_approve = False

    # 🚫 suspicious burst
    if recent_txn > 5:
        auto_approve = False

    # ✅ trusted user
    elif txn_count >= 10:
        auto_approve = True

    # ⚠️ mid user
    elif txn_count >= 3 and amount <= 200:
        auto_approve = True

    # 🚨 large withdrawal always manual
    if amount > 500:
        auto_approve = False

    # 💰 Deduct balance
    user.balance -= amount

    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        method=method,
        account=account,
        status="approved" if auto_approve else "pending"
    )

    db.add(withdrawal)
    await db.commit()
    await db.refresh(user)

    return {
        "message": "Withdrawal auto-approved ✅" if auto_approve else "Withdrawal pending ⏳",
        "method": method,
        "account": account,
        "remaining_balance": user.balance
    }


# 👤 Profile
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
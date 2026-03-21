from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Transaction, Click
from sqlalchemy import select, func
from datetime import datetime, timedelta
import os

router = APIRouter()

# 🔐 Load secret
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET")
if not POSTBACK_SECRET:
    raise Exception("POSTBACK_SECRET NOT SET ❌")


# 🗄️ DB Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session


# 🔌 CPA Postback Endpoint
@router.get("/postback")
async def postback(
    sub_id: str,
    amount: float,
    secret: str,
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):

    # 🔐 1. Validate secret
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 🧹 2. Clean tx_id
    tx_id = tx_id.strip()

    # 🔐 3. Validate tx_id
    if len(tx_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid tx_id")

    # 💰 4. Validate amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if amount > 500:
        raise HTTPException(status_code=400, detail="Suspicious amount")

    # 🔁 5. Prevent duplicate transactions
    result = await db.execute(
        select(Transaction).where(Transaction.tx_id == tx_id)
    )
    existing_tx = result.scalar_one_or_none()

    if existing_tx:
        return {"status": "duplicate ignored"}

    # 🔥 6. Verify sub_id
    result = await db.execute(
        select(Click).where(Click.sub_id == sub_id)
    )
    click = result.scalar_one_or_none()

    if not click:
        raise HTTPException(status_code=400, detail="Invalid or fake sub_id")

    # 🚫 7. Expired click (24h)
    if click.created_at < datetime.utcnow() - timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Expired click")

    user_id = click.user_id

    # 🔍 8. Find user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🚫 9. Blocked user
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    # 💰 10. Credit balance
    user.balance += amount

    # 🧾 11. Save transaction
    txn = Transaction(
        user_id=user_id,
        amount=amount,
        type="credit",
        tx_id=tx_id
    )

    db.add(txn)

    # 💾 12. Commit
    await db.commit()
    await db.refresh(user)

    # 🔥 13. TOTAL FRAUD CHECK (lifetime)
    result = await db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user_id
        )
    )
    total_txn = result.scalar()

    if total_txn > 50:
        user.is_blocked = 1
        await db.commit()

    # 🔥 14. RAPID CONVERSION FRAUD (10 min window)
    time_limit = datetime.utcnow() - timedelta(minutes=10)

    result = await db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.created_at >= time_limit
        )
    )

    recent_txn = result.scalar()

    if recent_txn > 10:
        user.is_blocked = 1
        await db.commit()
        raise HTTPException(
            status_code=403,
            detail="Suspicious activity detected"
        )

    # ✅ 15. Response
    return {
        "status": "success",
        "credited": amount,
        "balance": user.balance
    }
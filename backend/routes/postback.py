from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Transaction, Click
from sqlalchemy import select, func
from datetime import datetime, timedelta
import os

# ✅ IMPORT HELPER
from backend.utils.currency import convert_and_apply_margin

router = APIRouter()

# 🔐 Secret
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET")
if not POSTBACK_SECRET:
    raise Exception("POSTBACK_SECRET NOT SET ❌")


# 🗄️ DB
async def get_db():
    async with SessionLocal() as session:
        yield session


# 🔌 CPA POSTBACK
@router.get("/postback")
async def postback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 📥 Params (CPAGrip format)
    sub_id = request.query_params.get("subid")
    payout = request.query_params.get("payout")
    tx_id = request.query_params.get("trans_id")
    secret = request.query_params.get("secret")

    # 🔐 1. Validate secret
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 🔐 2. Validate params
    if not sub_id or not payout or not tx_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    tx_id = tx_id.strip()

    if len(tx_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid tx_id")

    # 💰 3. Validate payout
    try:
        payout = float(payout)
    except:
        raise HTTPException(status_code=400, detail="Invalid payout")

    if payout <= 0:
        raise HTTPException(status_code=400, detail="Invalid payout")

    if payout > 10:  # safety cap (optional)
        raise HTTPException(status_code=400, detail="Suspicious payout")

    # 💰 4. Convert + margin
    user_amount = convert_and_apply_margin(payout)

    if user_amount <= 0 or user_amount > 1000:
        raise HTTPException(status_code=400, detail="Suspicious amount")

    # 🔁 5. Prevent duplicate transactions
    result = await db.execute(
        select(Transaction).where(Transaction.tx_id == tx_id)
    )
    if result.scalar_one_or_none():
        return {"status": "duplicate ignored"}

    # 🔍 6. Verify sub_id
    result = await db.execute(
        select(Click).where(Click.sub_id == sub_id)
    )
    click = result.scalar_one_or_none()

    if not click:
        raise HTTPException(status_code=400, detail="Invalid sub_id")

    # 🚫 Expired click (24h)
    if click.created_at < datetime.utcnow() - timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Expired click")

    # 🔍 7. Get user
    user = await db.get(User, click.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    # 💰 8. Credit balance
    user.balance += user_amount

    # 🧾 9. Save transaction
    txn = Transaction(
        user_id=user.id,
        amount=user_amount,
        type="credit",
        tx_id=tx_id
    )

    db.add(txn)

    # 💾 10. Commit
    await db.commit()
    await db.refresh(user)

    # 🔥 11. TOTAL FRAUD CHECK
    result = await db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user.id
        )
    )
    total_txn = result.scalar()

    if total_txn > 50:
        user.is_blocked = True
        await db.commit()

    # 🔥 12. RAPID FRAUD CHECK (10 min)
    time_limit = datetime.utcnow() - timedelta(minutes=10)

    result = await db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.created_at >= time_limit
        )
    )

    recent_txn = result.scalar()

    if recent_txn > 10:
        user.is_blocked = True
        await db.commit()
        raise HTTPException(
            status_code=403,
            detail="Suspicious activity detected"
        )

    # ✅ 13. Response
    return {
        "status": "success",
        "credited": user_amount,
        "balance": round(user.balance, 2)
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Transaction, Click
from sqlalchemy import select
import os

router = APIRouter()

# 🔐 Load secret from environment
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET")

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
    if not POSTBACK_SECRET or secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 🧹 2. Clean tx_id
    tx_id = tx_id.strip()

    # 💰 3. Validate amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # 🔁 4. Prevent duplicate transactions
    result = await db.execute(
        select(Transaction).where(Transaction.tx_id == tx_id)
    )
    existing_tx = result.scalar_one_or_none()

    if existing_tx:
        return {"status": "duplicate ignored"}

    # 🔥 5. Verify sub_id from DB
    result = await db.execute(
        select(Click).where(Click.sub_id == sub_id)
    )
    click = result.scalar_one_or_none()

    if not click:
        raise HTTPException(status_code=400, detail="Invalid or fake sub_id")

    user_id = click.user_id

    # 🔍 6. Find user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 💰 7. Credit balance
    user.balance += amount

    # 🧾 8. Save transaction
    txn = Transaction(
        user_id=user_id,
        amount=amount,
        type="credit",
        tx_id=tx_id
    )

    db.add(txn)

    # 💾 9. Commit
    await db.commit()
    await db.refresh(user)

    # ✅ 10. Response
    return {
        "status": "success",
        "credited": amount,
        "balance": user.balance
    }
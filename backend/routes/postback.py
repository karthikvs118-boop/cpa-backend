from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Transaction
from sqlalchemy import select

router = APIRouter()

POSTBACK_SECRET = "super_secret_key"

# DB Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

@router.get("/postback")
async def postback(
    user_id: int,
    amount: float,
    secret: str,
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):

    # 🔐 Validate secret
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 🧹 Clean tx_id
    tx_id = tx_id.strip()

    # 💰 Validate amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # 🔁 Prevent duplicate
    result = await db.execute(
        select(Transaction).where(Transaction.tx_id == tx_id)
    )
    existing_tx = result.scalar_one_or_none()

    if existing_tx:
        return {"status": "duplicate ignored"}

    # 🔍 Check user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 💰 Credit balance
    user.balance += amount

    # 🧾 Save transaction
    txn = Transaction(
        user_id=user_id,
        amount=amount,
        type="credit",
        tx_id=tx_id
    )

    db.add(txn)

    await db.commit()
    await db.refresh(user)

    return {
        "status": "success",
        "credited": amount,
        "balance": user.balance
    }
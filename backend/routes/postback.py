from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import User, Transaction

router = APIRouter()

# 🔐 Secret key (must match CPA network)
POSTBACK_SECRET = "super_secret_key"

# 🗄️ DB
async def get_db():
    async with SessionLocal() as session:
        yield session

# 🔌 Secure postback
@router.get("/postback")
async def postback(
    user_id: int,
    amount: float,
    secret: str,
    db: AsyncSession = Depends(get_db)
):

    # 🔐 1. Validate secret
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 🔍 2. Check user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 💰 3. Credit balance
    user.balance += amount

    # 🧾 4. Save transaction
    txn = Transaction(
        user_id=user_id,
        amount=amount,
        type="credit"
    )
    db.add(txn)

    await db.commit()

    return {"status": "Reward credited"}
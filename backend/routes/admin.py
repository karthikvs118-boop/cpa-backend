from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import Withdrawal, User
from sqlalchemy import select

router = APIRouter()

# 🔐 Simple admin key (for now)
ADMIN_KEY = "admin123"

# 🗄️ DB
async def get_db():
    async with SessionLocal() as session:
        yield session

# 🔐 Admin auth
def verify_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")

# 📋 Get all withdrawals
@router.get("/withdrawals")
async def get_withdrawals(
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    result = await db.execute(select(Withdrawal))
    withdrawals = result.scalars().all()

    return withdrawals

# ✅ Approve withdrawal
@router.post("/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    withdrawal = await db.get(Withdrawal, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Already processed")

    withdrawal.status = "approved"

    await db.commit()

    return {"message": "Withdrawal approved"}

# ❌ Reject withdrawal
@router.post("/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    withdrawal = await db.get(Withdrawal, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="Already processed")

    # refund user
    user = await db.get(User, withdrawal.user_id)
    user.balance += withdrawal.amount

    withdrawal.status = "rejected"

    await db.commit()

    return {"message": "Withdrawal rejected & refunded"}
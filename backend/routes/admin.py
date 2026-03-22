from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import SessionLocal
from backend.models import Withdrawal, User, Transaction
import os

# ✅ IMPORTANT: prefix added
router = APIRouter(prefix="/admin")

# 🔐 Admin key
ADMIN_KEY = os.getenv("ADMIN_KEY")


# 🗄️ DB
async def get_db():
    async with SessionLocal() as session:
        yield session


# 🔐 Verify admin
def verify_admin(admin_key: str):
    if not ADMIN_KEY or admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")


# 📊 STATS
@router.get("/stats")
async def get_stats(admin_key: str, db: AsyncSession = Depends(get_db)):
    verify_admin(admin_key)

    total_users = await db.scalar(select(func.count()).select_from(User))
    total_txns = await db.scalar(select(func.count()).select_from(Transaction))
    total_withdrawals = await db.scalar(select(func.count()).select_from(Withdrawal))

    return {
        "total_users": total_users,
        "total_transactions": total_txns,
        "total_withdrawals": total_withdrawals
    }


# 📋 WITHDRAWALS (FIXED JSON)
@router.get("/withdrawals")
async def get_withdrawals(admin_key: str, db: AsyncSession = Depends(get_db)):
    verify_admin(admin_key)

    result = await db.execute(
        select(Withdrawal).order_by(Withdrawal.id.desc())
    )
    withdrawals = result.scalars().all()

    return [
        {
            "id": w.id,
            "user_id": w.user_id,
            "amount": w.amount,
            "method": w.method,
            "account": w.account,
            "status": w.status
        }
        for w in withdrawals
    ]


# ✅ APPROVE
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

    return {"message": "Approved ✅"}


# ❌ REJECT + REFUND
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

    user = await db.get(User, withdrawal.user_id)

    if user:
        user.balance += withdrawal.amount

    withdrawal.status = "rejected"

    await db.commit()

    return {"message": "Rejected & refunded 💸"}


# 🚫 BLOCK USER
@router.post("/block-user")
async def block_user(
    user_id: int,
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_blocked = True
    await db.commit()

    return {"message": "User blocked 🚫"}


# ✅ UNBLOCK USER
@router.post("/unblock-user")
async def unblock_user(
    user_id: int,
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_blocked = False
    await db.commit()

    return {"message": "User unblocked ✅"}
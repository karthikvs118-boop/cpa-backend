from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal
from backend.models import Withdrawal, User
from sqlalchemy import select
import os

router = APIRouter()

# 🔐 Load admin key from env
ADMIN_KEY = os.getenv("ADMIN_KEY")
if not ADMIN_KEY:
    raise Exception("ADMIN_KEY NOT SET ❌")


# 🗄️ DB
async def get_db():
    async with SessionLocal() as session:
        yield session


# 🔐 Admin auth
def verify_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")


# 📋 Get all withdrawals (latest first)
@router.get("/withdrawals")
async def get_withdrawals(
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    result = await db.execute(
        select(Withdrawal).order_by(Withdrawal.id.desc())
    )
    withdrawals = result.scalars().all()

    return withdrawals


# 📊 Get pending withdrawals only
@router.get("/withdrawals/pending")
async def get_pending_withdrawals(
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_key)

    result = await db.execute(
        select(Withdrawal).where(Withdrawal.status == "pending")
    )
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


# ❌ Reject withdrawal + refund
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

    # 🔍 Get user
    user = await db.get(User, withdrawal.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 💰 Refund
    user.balance += withdrawal.amount

    withdrawal.status = "rejected"

    await db.commit()

    return {"message": "Withdrawal rejected & refunded"}


# 🚫 Block user manually
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

    user.is_blocked = 1

    await db.commit()

    return {"message": "User blocked"}


# ✅ Unblock user
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

    user.is_blocked = 0

    await db.commit()

    return {"message": "User unblocked"}
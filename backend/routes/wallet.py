from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import User, Withdrawal
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

# 🔐 Config (MUST match auth.py exactly)
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# 🔐 Security
security = HTTPBearer()

# 🗄️ DB Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# 🔐 Get current user from token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    print("TOKEN RECEIVED:", token)   # 🔍 DEBUG

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("PAYLOAD:", payload)    # 🔍 DEBUG

        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id

    except Exception as e:
        print("ERROR:", str(e))       # 🔍 DEBUG
        raise HTTPException(status_code=401, detail="Invalid token")

# 💰 Get balance (protected)
@router.get("/balance")
async def get_balance(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"balance": user.balance}

# 💸 Request withdrawal (protected)
@router.post("/withdraw")
async def request_withdrawal(
    amount: float,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # minimum withdrawal
    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is ₹100")

    # balance check
    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # deduct balance
    user.balance -= amount

    # create withdrawal
    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        status="pending"
    )

    db.add(withdrawal)
    await db.commit()

    return {"message": "Withdrawal request submitted"}

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
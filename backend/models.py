from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.database import Base


# 👤 USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    balance = Column(Float, default=0.0)


# 💰 TRANSACTION MODEL (VERY IMPORTANT FOR CPA)
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)

    # 🔥 NEW FIELDS (IMPORTANT)
    type = Column(String)  # credit / debit
    tx_id = Column(String, unique=True, index=True)  # unique CPA conversion ID


# 💸 WITHDRAWAL MODEL
class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending / approved / rejected
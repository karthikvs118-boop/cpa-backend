from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime


# 👤 USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    balance = Column(Float, default=0.0)

    # 🔥 ANTI-FRAUD
    ip_address = Column(String)
    device = Column(String)  # ✅ NEW (device fingerprint)
    is_blocked = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # relationships
    transactions = relationship("Transaction", backref="user")
    withdrawals = relationship("Withdrawal", backref="user")
    clicks = relationship("Click", backref="user")


# 💰 TRANSACTION MODEL
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float)

    type = Column(String)
    tx_id = Column(String, unique=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# 💸 WITHDRAWAL MODEL
class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float)

    status = Column(String, default="pending")

    # 🔥 NEW
    method = Column(String)         # upi / paytm / bank
    account = Column(String)        # upi id / number / account

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# 🔥 CLICK MODEL
class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    sub_id = Column(String, unique=True, index=True)

    ip_address = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
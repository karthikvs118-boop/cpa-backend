from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
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
    is_blocked = Column(Integer, default=0)

    # 🕒 tracking
    created_at = Column(DateTime, default=datetime.utcnow)


# 💰 TRANSACTION MODEL
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)

    type = Column(String)  # credit / debit
    tx_id = Column(String, unique=True, index=True)

    # 🔥 REQUIRED FOR FRAUD DETECTION
    created_at = Column(DateTime, default=datetime.utcnow)


# 💸 WITHDRAWAL MODEL
class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)


# 🔥 CLICK MODEL
class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sub_id = Column(String, unique=True, index=True)

    # 🔥 ANTI-FRAUD
    ip_address = Column(String)

    # 🕒 REQUIRED
    created_at = Column(DateTime, default=datetime.utcnow)